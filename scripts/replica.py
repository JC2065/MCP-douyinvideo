"""1:1 replica with the user's own model key (BYOK).

The user's Bailian / Qwen AI key is used only for the request that carries it: it is never
written to disk, logged or returned. Jobs store the provider task id; every status poll
must present the key again, so a server restart never loses a job and we never hold keys.
Billing goes directly to the user's own account.
"""
import base64, io, json, re, shutil, subprocess, threading, time, uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASES = {'bailian': 'https://dashscope.aliyuncs.com/api/v1', 'qianwen': 'https://maas.qianwenaiapi.com/api/v1'}
MODEL = 'wan2.2-animate-move'
# Observed on a real bill (2026-10): standard mode CNY 0.40 per output second; pro is pricier.
MODES = {'wan-std': {'name': '标准', 'yuanPerSecond': 0.4}, 'wan-pro': {'name': '高质量', 'yuanPerSecond': None}}
MIN_SECONDS, MAX_SECONDS = 2, 30
DAILY_LIMIT, ACTIVE_LIMIT = 20, 2
PHOTO_MAX_BYTES = 6 * 1024 * 1024
TERMINAL = ('done', 'failed')


class ReplicaError(ValueError):
    def __init__(self, message, code='invalid'):
        super().__init__(message)
        self.code = code


def credentials(payload):
    base = payload.get('provider') if isinstance(payload, dict) else None
    key = payload.get('key') if isinstance(payload, dict) else None
    if base not in BASES:
        raise ReplicaError('请选择 Key 所属平台', 'provider')
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_.\-]{8,256}', key.strip()):
        raise ReplicaError('请填写有效的 API Key', 'key')
    return base, key.strip()


def provider_message(status, body, key=''):
    try:
        data = json.loads(body or '{}')
    except ValueError:
        data = {}
    code = str(data.get('code') or '')
    message = str(data.get('message') or '')[:160].replace(key, '***') if key else str(data.get('message') or '')[:160]
    if status == 401 or code in ('InvalidApiKey', 'Unauthorized'):
        return ReplicaError('API Key 无效或已失效，请检查后重试', 'key')
    if code in ('Arrearage', 'Throttling.AllocationQuota') or 'arrear' in message.lower():
        return ReplicaError('你的账户余额不足或额度已用完，请到百炼/千问平台充值后重试', 'balance')
    if code in ('AccessDenied', 'Model.AccessDenied', 'AccessDenied.Unpurchased') or status == 403:
        return ReplicaError('你的账户尚未开通 %s，请在平台控制台开通后重试' % MODEL, 'access')
    if 'DataInspection' in code:
        return ReplicaError('素材未通过平台内容安全审核，请更换视频或照片', 'inspection')
    if code == 'InvalidParameter' or status == 400:
        return ReplicaError('平台拒绝了素材：' + (message or '参数无效') + '（照片需清晰单人、视频 2–30 秒）', 'input')
    if status == 429 or 'Throttling' in code:
        return ReplicaError('平台限流，请稍后再试', 'throttle')
    return ReplicaError('模型平台暂不可用，请稍后重试' + ('（%s）' % code if code else ''), 'provider')


class Replica:
    def __init__(self, root, opener=urlopen, ffmpeg=None, clock=time.time):
        self.root = Path(root)
        (self.root / 'jobs').mkdir(parents=True, exist_ok=True)
        self.opener, self.clock = opener, clock
        self.ffmpeg = ffmpeg
        self.lock = threading.Lock()
        self.job_locks = {}

    # ---------- provider calls (key only in memory) ----------
    def call(self, base, key, path, payload=None, timeout=60):
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'X-DashScope-OssResourceResolve': 'enable'}
        if payload is not None:
            headers['X-DashScope-Async'] = 'enable'
        request = Request(BASES[base] + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers, method='POST' if payload is not None else 'GET')
        try:
            with self.opener(request, timeout=timeout) as response:
                return json.loads(response.read(1 << 20))
        except HTTPError as error:
            raise provider_message(error.code, error.read(65536).decode('utf-8', 'replace'), key) from None
        except (URLError, TimeoutError, OSError):
            raise ReplicaError('无法连接模型平台，请稍后重试', 'network') from None
        except ValueError:
            raise ReplicaError('模型平台返回无法识别', 'provider') from None

    def upload(self, base, key, path, mime):
        policy = (self.call(base, key, '/uploads?action=getPolicy&model=' + MODEL) or {}).get('data') or {}
        try:
            name = path.name
            object_key = policy['upload_dir'] + '/' + name
            fields = {'OSSAccessKeyId': policy['oss_access_key_id'], 'Signature': policy['signature'], 'policy': policy['policy'], 'key': object_key,
                      'x-oss-object-acl': policy['x_oss_object_acl'], 'x-oss-forbid-overwrite': policy['x_oss_forbid_overwrite'], 'success_action_status': '200'}
            host = policy['upload_host']
        except (KeyError, TypeError):
            raise ReplicaError('模型平台上传通道不可用', 'provider') from None
        if urlparse(host).scheme != 'https' or not urlparse(host).hostname.endswith('.aliyuncs.com'):
            raise ReplicaError('模型平台上传地址无效', 'provider')
        boundary = uuid.uuid4().hex
        body = b''.join(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)).encode() for k, v in fields.items())
        body += ('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\nContent-Type: %s\r\n\r\n' % (boundary, name, mime)).encode() + path.read_bytes() + ('\r\n--%s--\r\n' % boundary).encode()
        try:
            with self.opener(Request(host, data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST'), timeout=180) as response:
                response.read(4096)
        except (HTTPError, URLError, TimeoutError, OSError):
            raise ReplicaError('素材上传到模型平台失败，请重试', 'upload') from None
        return 'oss://' + object_key

    # ---------- jobs ----------
    def job_path(self, ident):
        if not re.fullmatch('[a-f0-9]{32}', str(ident)):
            raise ReplicaError('任务不存在', 'missing')
        return self.root / 'jobs' / (ident + '.json')

    def load(self, user, ident):
        path = self.job_path(ident)
        if not path.is_file():
            raise ReplicaError('任务不存在', 'missing')
        job = json.loads(path.read_text(encoding='utf-8'))
        if job.get('user') != user:
            raise ReplicaError('任务不存在', 'missing')
        return job

    def save(self, job):
        path = self.job_path(job['id'])
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
        tmp.replace(path)

    def jobs(self, user):
        rows = []
        for path in (self.root / 'jobs').glob('*.json'):
            try:
                job = json.loads(path.read_text(encoding='utf-8'))
            except ValueError:
                continue
            if job.get('user') == user:
                rows.append(job)
        return sorted(rows, key=lambda j: -j['createdAt'])

    @staticmethod
    def public(job):
        keys = ('id', 'status', 'message', 'mode', 'seconds', 'estimateYuan', 'video', 'createdAt', 'provider')
        return {k: job.get(k) for k in keys}

    def check(self, payload):
        base, key = credentials(payload)
        self.call(base, key, '/uploads?action=getPolicy&model=' + MODEL)
        return {'ok': True, 'message': 'Key 可用（检测不产生费用）'}

    def photo(self, value, folder):
        from PIL import Image, ImageOps
        if not isinstance(value, str) or not value:
            raise ReplicaError('请选择人物照片', 'photo')
        try:
            raw = base64.b64decode(value.split(',', 1)[-1], validate=True)
        except (ValueError, TypeError):
            raise ReplicaError('照片数据无效', 'photo') from None
        if len(raw) > PHOTO_MAX_BYTES:
            raise ReplicaError('照片过大，请压缩后重试', 'photo')
        try:
            image = Image.open(io.BytesIO(raw))
            image.verify()
            image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
        except Exception:
            raise ReplicaError('无法识别的照片格式', 'photo') from None
        image.thumbnail((2048, 2048))
        w, h = image.size
        if min(w, h) < 200 or max(w, h) / min(w, h) > 3:
            raise ReplicaError('照片分辨率过低或比例过长（短边至少 200 像素，长宽比不超过 3:1）', 'photo')
        target = folder / 'photo.jpg'
        image.save(target, 'JPEG', quality=90)  # re-encoded: strips EXIF/location
        return target

    def source(self, path, duration, folder):
        if duration <= MAX_SECONDS:
            return path, duration
        target = folder / 'source.mp4'
        ffmpeg = self.ffmpeg
        if ffmpeg is None:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(path), '-t', str(MAX_SECONDS), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', str(target)], check=True, timeout=300)
        return target, float(MAX_SECONDS)

    def create(self, user, reference, payload):
        if not isinstance(payload, dict) or payload.get('consent') is not True:
            raise ReplicaError('请确认原视频与照片为本人所有或已获授权', 'consent')
        mode = payload.get('mode', 'wan-std')
        if mode not in MODES:
            raise ReplicaError('请选择生成质量', 'mode')
        base, key = credentials(payload)
        asset = (reference or {}).get('asset') or {}
        path = Path(str(asset.get('storagePath') or ''))
        duration = float(((asset.get('media') or {}).get('durationSeconds')) or 0)
        if not path.is_file():
            raise ReplicaError('参考视频不存在，请重新获取', 'reference')
        if duration < MIN_SECONDS:
            raise ReplicaError('参考视频需至少 2 秒', 'reference')
        now = self.clock()
        with self.lock:
            mine = self.jobs(user)
            if sum(1 for j in mine if now - j['createdAt'] < 86400) >= DAILY_LIMIT:
                raise ReplicaError('今日复刻次数已达上限，请明天再试', 'limit')
            if sum(1 for j in mine if j['status'] not in TERMINAL and now - j['createdAt'] < 3600) >= ACTIVE_LIMIT:
                raise ReplicaError('已有复刻任务在生成，请等待完成后再提交', 'limit')
            ident = uuid.uuid4().hex
            folder = self.root / ident
            folder.mkdir(parents=True)
            job = {'id': ident, 'user': user, 'provider': base, 'mode': mode, 'status': 'submitting', 'message': '正在上传素材', 'createdAt': now, 'sha': asset.get('sha256')}
            self.save(job)
        try:
            photo = self.photo(payload.get('photo'), folder)
            video, seconds = self.source(path, duration, folder)
            price = MODES[mode]['yuanPerSecond']
            job.update(seconds=round(seconds, 1), estimateYuan=round(seconds * price, 2) if price else None)
            image_url = self.upload(base, key, photo, 'image/jpeg')
            video_url = self.upload(base, key, video, 'video/mp4')
            created = self.call(base, key, '/services/aigc/image2video/video-synthesis',
                                {'model': MODEL, 'input': {'image_url': image_url, 'video_url': video_url, 'watermark': True}, 'parameters': {'mode': mode}})
            task = (created.get('output') or {}).get('task_id')
            if not isinstance(task, str) or not task:
                raise ReplicaError('模型平台没有返回任务编号', 'provider')
            job.update(taskId=task, status='running', message='已提交，正在生成（通常 3–6 分钟）')
        except Exception as error:
            job.update(status='failed', message=str(error) if isinstance(error, ReplicaError) else '提交失败，请重试')
            self.save(job)
            if isinstance(error, ReplicaError):
                raise
            raise ReplicaError(job['message'], 'provider') from None
        self.save(job)
        return self.public(job)

    def status(self, user, ident, payload):
        job = self.load(user, ident)
        if job['status'] in TERMINAL or not job.get('taskId'):
            return self.public(job)
        base, key = credentials(payload)
        if base != job['provider']:
            raise ReplicaError('请使用提交任务时的同一平台 Key 查询', 'provider')
        with self.lock:
            job_lock = self.job_locks.setdefault(ident, threading.Lock())
        with job_lock:
            job = self.load(user, ident)
            if job['status'] in TERMINAL:
                return self.public(job)
            output = (self.call(base, key, '/tasks/' + job['taskId']) or {}).get('output') or {}
            state = output.get('task_status')
            if state == 'SUCCEEDED':
                url = (output.get('results') or {}).get('video_url') or output.get('video_url')
                parsed = urlparse(str(url or ''))
                if parsed.scheme not in ('http', 'https') or not (parsed.hostname or '').endswith('.aliyuncs.com'):
                    raise ReplicaError('模型平台返回的视频地址无效', 'provider')
                target = self.root / ident / 'result.mp4'
                tmp = target.with_suffix('.part')
                try:
                    with self.opener(Request(url), timeout=180) as response, open(tmp, 'wb') as handle:
                        shutil.copyfileobj(response, handle, 1 << 20)
                except (HTTPError, URLError, TimeoutError, OSError):
                    raise ReplicaError('视频已生成，下载暂时失败，请稍后再查', 'download') from None
                tmp.replace(target)
                job.update(status='done', message='已完成', video='/replica-media/%s.mp4' % ident, finishedAt=self.clock())
            elif state in ('FAILED', 'CANCELED', 'UNKNOWN'):
                job.update(status='failed', message='生成失败：' + str(output.get('message') or output.get('code') or state)[:160])
            else:
                job.update(status='running', message='排队中' if state == 'PENDING' else '生成中（通常 3–6 分钟）')
            self.save(job)
            return self.public(job)

    def media(self, ident):
        if not re.fullmatch('[a-f0-9]{32}', str(ident)):
            return None
        file = self.root / ident / 'result.mp4'
        return file if file.is_file() else None
