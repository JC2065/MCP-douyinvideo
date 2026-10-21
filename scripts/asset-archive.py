"""Durable local asset sync/archive worker. Credentials stay outside the repository."""
import hashlib,json,os,re,sqlite3,time,zipfile,threading,uuid,shutil
from pathlib import Path
from urllib.request import Request,urlopen,build_opener,HTTPRedirectHandler
from urllib.parse import urlencode,urlparse
from urllib.error import HTTPError
from contextlib import contextmanager

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urlparse(newurl).scheme!='https':raise RuntimeError('拒绝非HTTPS下载跳转')
        redirect=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirect:redirect.remove_header('Authorization')
        return redirect

class Feishu:
    def __init__(self,config,state):self.config=config;self.tables=state['roles']['management']['tables'];self.token='';self.expires=0
    def auth(self):
        if time.time()<self.expires:return
        try:
            with urlopen(Request('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',data=json.dumps({'app_id':self.config['appId'],'app_secret':self.config['appSecret']}).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:data=json.load(response)
        except Exception:raise RuntimeError('飞书鉴权连接失败') from None
        if data.get('code')!=0:raise RuntimeError(f"飞书鉴权失败 code={data.get('code')}")
        self.token=data['tenant_access_token'];self.expires=time.time()+max(0,data.get('expire',0)-60)
    def call(self,method,path,body=None,raw=None,content_type=None):
        self.auth();headers={'Authorization':'Bearer '+self.token,'Content-Type':content_type or 'application/json'}
        try:
            with urlopen(Request('https://open.feishu.cn/open-apis'+path,data=raw if raw is not None else json.dumps(body).encode() if body is not None else None,headers=headers,method=method),timeout=90) as response:data=json.load(response)
        except HTTPError as e:
            try:code=json.loads(e.read()).get('code')
            except Exception:code='unknown'
            raise RuntimeError(f'飞书权限或接口失败 HTTP={e.code} code={code}') from None
        except Exception:raise RuntimeError('飞书接口连接或响应失败') from None
        if data.get('code')!=0:raise RuntimeError(f"飞书接口失败 code={data.get('code')}")
        return data.get('data') or {}
    def upsert(self,table,key,fields):
        prefix=f"/bitable/v1/apps/{self.config['baseToken']}/tables/{self.tables[table]['id']}/records"
        found=self.call('POST',prefix+'/search',{'filter':{'conjunction':'and','conditions':[{'field_name':key,'operator':'is','value':[fields[key]]}]},'page_size':100}).get('items',[])
        if len(found)>1:raise RuntimeError('飞书稳定ID出现重复记录，请人工核对')
        if found:return self.call('PUT',prefix+'/'+found[0]['record_id'],{'fields':fields})['record']['record_id']
        token=str(uuid.uuid5(uuid.NAMESPACE_URL,prefix+'|'+key+'|'+str(fields[key])))
        return self.call('POST',prefix,{'fields':fields,'client_token':token})['record']['record_id']
    def find_file(self,name):
        token=''
        while True:
            result=self.call('GET','/drive/v1/files?'+urlencode({'folder_token':self.config['folderToken'],'page_size':200,**({'page_token':token} if token else {})}))
            matches=[f for f in result.get('files',[]) if f.get('name')==name]
            if len(matches)>1:raise RuntimeError('归档目录存在重名文件，请人工核对')
            if matches:return matches[0]['token']
            if not result.get('has_more'):return None
            token=result.get('next_page_token') or result.get('page_token')
            if not token:raise RuntimeError('归档分页状态异常')
    def upload(self,path,name):
        existing=self.find_file(name)
        if existing:return existing
        data=Path(path).read_bytes();boundary='youai'+uuid.uuid4().hex;body=b''
        for key,value in {'file_name':name,'parent_type':'explorer','parent_node':self.config['folderToken'],'size':str(len(data))}.items():body+=f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
        body+=f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+data+f'\r\n--{boundary}--\r\n'.encode()
        return self.call('POST','/drive/v1/files/upload_all',raw=body,content_type='multipart/form-data; boundary='+boundary)['file_token']
    def download(self,token,path):
        self.auth()
        try:
            with build_opener(SafeRedirect()).open(Request('https://open.feishu.cn/open-apis/drive/v1/files/'+token+'/download',headers={'Authorization':'Bearer '+self.token}),timeout=90) as response,Path(path).open('wb') as stream:
                size=0
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>20*1024*1024:raise RuntimeError('下载分片超过大小上限')
                    stream.write(chunk)
        except Exception:raise RuntimeError('飞书文件下载失败，请检查下载权限') from None

class ArchiveManager:
    def __init__(self,root,config_path,state_path,client_factory=Feishu):
        self.root=Path(root).resolve();self.work=self.root/'archive';self.work.mkdir(parents=True,exist_ok=True);self.config_path=Path(config_path);self.state_path=Path(state_path);self.factory=client_factory;self.guard=threading.Lock()
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,status TEXT,attempts INTEGER DEFAULT 0,next REAL DEFAULT 0,error TEXT DEFAULT "",phase TEXT DEFAULT "queued")')
            db.execute("UPDATE jobs SET status='pending' WHERE status='running'")
    @contextmanager
    def db(self):
        connection=sqlite3.connect(self.work/'queue.sqlite',timeout=10)
        try:
            with connection:yield connection
        finally:connection.close()
    def valid(self,id):
        if not re.fullmatch('[a-f0-9]{32}',id):raise ValueError('运行ID无效')
        path=self.root/'runs'/id/'manifest.json'
        if not path.is_file():raise ValueError('资产包不存在')
        return json.loads(path.read_text(encoding='utf-8'))
    def enqueue(self,id):
        self.valid(id)
        with self.db() as db:db.execute("INSERT INTO jobs(id,status) VALUES(?,'pending') ON CONFLICT(id) DO UPDATE SET status=CASE WHEN jobs.status='archived' THEN jobs.status ELSE 'pending' END,next=0",(id,))
    def status(self,id):
        with self.db() as db:row=db.execute('SELECT status,attempts,error,phase FROM jobs WHERE id=?',(id,)).fetchone()
        return {'status':row[0],'attempts':row[1],'error':row[2],'phase':row[3]} if row else {'status':'not_queued','attempts':0,'error':'','phase':''}
    def phase(self,id,value):
        with self.db() as db:db.execute('UPDATE jobs SET phase=? WHERE id=?',(value,id))
    def files(self,id,manifest):
        folder=self.root/'runs'/id;items={}
        for p in folder.glob('*'):
            if p.is_file() and p.name not in ('manifest.json','request.json'):items['run/'+p.name]=p
        source=(manifest.get('source') or {}).get('storageUri')
        if source:items['source.mp4']=Path(source)
        for i,p in enumerate((manifest.get('analysis') or {}).get('keyframes',[])):items[f'frames/{i}.jpg']=Path(p)
        for p in items.values():
            if not p.resolve().is_relative_to(self.root) or not p.is_file():raise ValueError('资产文件缺失或越界')
        return items
    def bundle(self,id,manifest):
        folder=self.work/id;folder.mkdir(exist_ok=True);path=folder/'bundle.zip';items=self.files(id,manifest)
        if sum(p.stat().st_size for p in items.values())>512*1024*1024:raise ValueError('资产包超过512MB，需拆分项目')
        proof={name:{'sha256':digest(p),'bytes':p.stat().st_size} for name,p in items.items()}
        summary={'runId':id,'communication':manifest.get('communication'),'storyboard':manifest.get('storyboard',{}).get('shots'),'lineage':manifest.get('lineage'),'generation':{'provider':manifest.get('generation',{}).get('provider'),'model':manifest.get('generation',{}).get('model'),'settings':manifest.get('generation',{}).get('settings')},'files':proof}
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for name,p in sorted(items.items()):archive.writestr(zipfile.ZipInfo(name),p.read_bytes())
            archive.writestr(zipfile.ZipInfo('index.json'),json.dumps(summary,ensure_ascii=False).encode())
        return path,proof
    def client(self):
        try:config=json.loads(self.config_path.read_text(encoding='utf-8-sig'))['management'];state=json.loads(self.state_path.read_text(encoding='utf-8'))
        except Exception:raise RuntimeError('归档配置或六表映射未就绪') from None
        if not config.get('folderToken') or config.get('folderToken')=='REPLACE':raise RuntimeError('请配置飞书归档目录 folderToken')
        if state.get('roles',{}).get('management',{}).get('baseToken')!=config.get('baseToken'):raise RuntimeError('飞书配置与六表映射不属于同一个Base')
        if not re.fullmatch('[A-Za-z0-9]+',str(config.get('folderToken'))):raise RuntimeError('飞书归档目录标识无效')
        return self.factory(config,state)
    def process(self,id):
        manifest=self.valid(id);client=self.client();folder=self.work/id;folder.mkdir(exist_ok=True);receipt_path=folder/'receipt.json';receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
        request_path=self.root/'runs'/id/'request.json'
        try:title=str(json.loads(request_path.read_text(encoding='utf-8')).get('idea') or '创作 '+id[:8])[:80]
        except Exception:title='创作 '+id[:8]
        self.phase(id,'syncing');work=client.upsert('works','作品ID',{'作品ID':id,'标题':title,'来源':manifest.get('source',{}).get('type','idea'),'阶段':'已生成','成片资产ID':manifest['final']['sha256'],'方案版本':manifest['storyboard']['version']})
        client.upsert('plans','方案ID',{'方案ID':id+'-v'+str(manifest['storyboard']['version']),'作品ID':id,'版本':manifest['storyboard']['version'],'分析版本':manifest.get('lineage',{}).get('analysisVersion') or '无','沟通答案':json.dumps(manifest.get('communication',{}),ensure_ascii=False),'分镜':json.dumps(manifest['storyboard']['shots'],ensure_ascii=False),'提示词':(self.root/'runs'/id/'prompt.txt').read_text(encoding='utf-8')[:10000],'关联作品':[work]})
        feedback_path=folder/'feedback.json';feedback=json.loads(feedback_path.read_text(encoding='utf-8')) if feedback_path.exists() else {}
        client.upsert('feedback','反馈ID',{'反馈ID':id+'-cost','作品ID':id,'模型':manifest['generation']['model'],'费用已核实':False,'用户评价':feedback.get('rating','待反馈'),'修改原因':feedback.get('reason',''),'采纳项':feedback.get('adopted',''),'关联作品':[work]})
        self.phase(id,'packing');bundle,proof=self.bundle(id,manifest);sha=digest(bundle)
        if receipt and receipt.get('sha256')!=sha:raise RuntimeError('资产包内容变更，请保留旧归档并生成新作品版本')
        receipt.update(runId=id,sha256=sha,files=proof,parts=receipt.get('parts',[]));write_json(receipt_path,receipt)
        self.phase(id,'uploading')
        with bundle.open('rb') as stream:
            i=0
            while True:
                data=stream.read(18*1024*1024)
                if not data:break
                part=folder/f'part-{i:04d}';part.write_bytes(data);part_sha=digest(part)
                if len(receipt['parts'])<=i:
                    token=client.upload(part,f'youai-{sha}-{i:04d}.part');receipt['parts'].append({'token':token,'sha256':part_sha,'bytes':len(data)});write_json(receipt_path,receipt)
                check=folder/'check.part';client.download(receipt['parts'][i]['token'],check)
                if digest(check)!=part_sha:raise RuntimeError('归档上传后的下载哈希不一致')
                check.unlink();part.unlink();i+=1
        asset_id=client.upsert('assets','资产ID',{'资产ID':sha,'作品ID':id,'SHA256':sha,'类型':'完整资产包','大小字节':bundle.stat().st_size,'资源池ID':'feishu-main','存储文件标识':json.dumps(receipt['parts']),'引用次数':1,'校验状态':'上传下载哈希一致','归档时间':int(time.time()*1000)})
        for name,item in proof.items():
            client.upsert('assets','资产ID',{'资产ID':id+'-'+name,'作品ID':id,'SHA256':item['sha256'],'类型':name,'大小字节':item['bytes'],'来源资产ID':sha,'资源池ID':'feishu-main','存储文件标识':json.dumps({'bundle':sha,'entry':name}),'引用次数':1,'校验状态':'包内SHA256已核验'})
        client.upsert('pools','资源池ID',{'资源池ID':'feishu-main','组织':'商业标准版主组织','套餐':'实际权益请核验','告警状态':'需定期核验额度'})
        client.upsert('archive_jobs','任务ID',{'任务ID':id+'-archive','资产ID':sha,'源资源池ID':'local','目标资源池ID':'feishu-main','状态':'已归档','校验结果':'SHA256通过','重试次数':self.status(id)['attempts'],'完成时间':int(time.time()*1000),'关联资产':[asset_id]})
        self.phase(id,'verified');receipt['verified']=True;write_json(receipt_path,receipt)
    def feedback(self,id,values):
        self.valid(id)
        if not isinstance(values,dict) or values.get('rating') not in ('满意','需要修改'):raise ValueError('请选择满意或需要修改')
        data={'rating':values['rating'],'reason':str(values.get('reason') or '')[:240],'adopted':str(values.get('adopted') or '')[:240]};write_json(self.work/id/'feedback.json',data)
        with self.db() as db:db.execute("INSERT INTO jobs(id,status) VALUES(?,'pending') ON CONFLICT(id) DO UPDATE SET status='pending',next=0",(id,))
        return {'status':'saved','message':'反馈已保存，等待同步'}
    def tick(self):
        if not self.guard.acquire(False):return
        try:
            with self.db() as db:
                row=db.execute("SELECT id FROM jobs WHERE status IN ('pending','failed') AND next<=? ORDER BY next LIMIT 1",(time.time(),)).fetchone()
                if not row:return
                id=row[0];db.execute("UPDATE jobs SET status='running',attempts=attempts+1,error='' WHERE id=?",(id,))
            try:
                self.process(id)
                with self.db() as db:db.execute("UPDATE jobs SET status='archived',error='' WHERE id=? AND status='running'",(id,))
            except Exception as e:
                error=str(e) if isinstance(e,(RuntimeError,ValueError)) else '资产同步失败，请检查配置和服务日志'
                with self.db() as db:db.execute("UPDATE jobs SET status='failed',error=?,next=? WHERE id=?",(error[:160],time.time()+min(3600,30*2**min(self.status(id)['attempts'],6)),id))
        finally:self.guard.release()
    def restore(self,id,client=None):
        if not self.guard.acquire(False):raise RuntimeError('资产同步正在进行，请稍后恢复')
        try:return self._restore(id,client)
        finally:self.guard.release()
    def _restore(self,id,client=None):
        manifest=self.valid(id);folder=self.work/id;receipt_path=folder/'receipt.json'
        if not receipt_path.is_file():raise ValueError('尚无可恢复归档')
        receipt=json.loads(receipt_path.read_text());
        if not receipt.get('verified'):raise ValueError('归档未完成校验')
        client=client or self.client();zip_path=folder/'restore.zip';destination=self.root/'restored'/id;temporary=self.root/'restored'/('.'+id);temporary.mkdir(parents=True,exist_ok=True)
        try:
            with zip_path.open('wb') as output:
                for p in receipt['parts']:
                    part=folder/'restore.part';client.download(p['token'],part)
                    if digest(part)!=p['sha256']:raise ValueError('恢复分片哈希不一致')
                    with part.open('rb') as stream:shutil.copyfileobj(stream,output)
                    part.unlink()
            if digest(zip_path)!=receipt['sha256']:raise ValueError('恢复资产包哈希不一致')
            with zipfile.ZipFile(zip_path) as archive:
                if sum(x.file_size for x in archive.infolist())>512*1024*1024:raise ValueError('恢复解压大小超限')
                for item in archive.infolist():
                    if item.filename not in receipt['files'] and item.filename!='index.json':raise ValueError('归档存在未知文件')
                    if not (temporary/item.filename).resolve().is_relative_to(temporary.resolve()):raise ValueError('归档路径越界')
                archive.extractall(temporary)
            for name,proof in receipt['files'].items():
                if digest(temporary/name)!=proof['sha256']:raise ValueError('恢复文件哈希不一致')
            if destination.exists():shutil.rmtree(destination)
            temporary.replace(destination)
            for name in receipt['files']:
                if name.startswith('run/'):
                    target=self.root/'runs'/id/name[4:]
                    if not target.exists():shutil.copy2(destination/name,target)
            source=(manifest.get('source') or {}).get('storageUri')
            if source and 'source.mp4' in receipt['files']:
                target=Path(source).resolve()
                if target.is_relative_to(self.root/'sources') and not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(destination/'source.mp4',target)
            for i,frame in enumerate((manifest.get('analysis') or {}).get('keyframes',[])):
                target=Path(frame).resolve();name=f'frames/{i}.jpg'
                if name in receipt['files'] and target.is_relative_to(self.root/'keyframes') and not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(destination/name,target)
            return {'status':'restored','files':len(receipt['files'])}
        finally:
            zip_path.unlink(missing_ok=True)
            (folder/'restore.part').unlink(missing_ok=True)
            if temporary.exists():shutil.rmtree(temporary)
    def start(self):
        def loop():
            while True:
                try:self.tick()
                except Exception:pass
                time.sleep(5)
        threading.Thread(target=loop,daemon=True).start()
