"""Zero-cost real WeChat identity -> public HTTPS -> render -> signed download."""
import json,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
base='https://youai888.top/youai'
text=Path(sys.argv[1]).read_text(encoding='utf-8-sig');result=json.loads(text[text.index('{'):]);code=result['result']['result']['code']
def call(path,payload=None,token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    request=Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
    try:
        with urlopen(request,timeout=45) as response:return json.load(response)
    except HTTPError as error:
        try:message=json.loads(error.read()).get('error','')
        except Exception:message='upstream request failed'
        raise RuntimeError(f'HTTP {error.code}: {message}') from None
login=call('/auth/login',{'code':code});token=login['token'];assert call('/auth/me',token=token)['userId']==login['userId']
board={'version':1,'status':'approved','referenceMode':'same-topic','shots':[{'role':'开场','narration':'手机云端验收','visual':'纯文字画面'},{'role':'展开','narration':'生成播放保存','visual':'纯文字画面'},{'role':'收束','narration':'免费测试样片','visual':'纯文字画面'}]}
job=call('/jobs',{'idea':'手机云端免费验收','duration':2,'mood':'温柔治愈','visualStyle':'纯文字画面','source':{'type':'idea'},'storyboard':board},token);run=job['id'];deadline=time.time()+180
while time.time()<deadline:
    result=call('/jobs/'+run,token=token)
    if result.get('status')=='done':break
    if result.get('status')=='failed':raise RuntimeError(result.get('error','render failed'))
    time.sleep(2)
else:raise RuntimeError('cloud render timed out')
manifest=call('/asset-runs/'+run,token=token)
with urlopen(Request(base+result['url'],headers={'Range':'bytes=0-31'}),timeout=45) as response:
    assert response.status==206;assert b'ftyp' in response.read(32)
with urlopen(base+result['url'],timeout=45) as response:video=response.read()
assert len(video)>1000;target=Path(sys.argv[2]);target.write_bytes(video)
summary={'runId':run,'publicLogin':True,'generated':True,'downloadBytes':len(video),'rangeVerified':True,'databaseStatus':manifest.get('database',{}).get('status'),'paidModelCalls':0,'phoneAlbumVerified':False}
Path(str(target)+'.json').write_text(json.dumps(summary),encoding='utf-8')
print(json.dumps(summary))
