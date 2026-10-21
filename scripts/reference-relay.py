"""HTTPS tunnel origin that exposes only signed reference videos."""
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

SPEC=importlib.util.spec_from_file_location('youai_video_server',Path(__file__).with_name('video-server.py'))
VIDEO=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VIDEO)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass
    def reply(self,status,payload):
        body=VIDEO.json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if urlparse(self.path).path=='/health':return self.reply(200,{'status':'ok'})
        file=VIDEO.verified_reference_video(self.path)
        if not file:return self.reply(403,{'error':'参考素材地址无效或已过期'})
        size=file.stat().st_size;start,end=0,size-1;requested=self.headers.get('Range')
        if requested:
            match=VIDEO.re.fullmatch(r'bytes=(\d+)-(\d*)',requested)
            if not match:return self.reply(416,{'error':'Unsupported range'})
            start=int(match[1]);end=min(int(match[2]) if match[2] else end,end)
            if start>end:return self.reply(416,{'error':'Invalid range'})
        self.send_response(206 if requested else 200);self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
        if requested:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        with file.open('rb') as stream:stream.seek(start);self.wfile.write(stream.read(end-start+1))

if __name__=='__main__':
    print('YOUAI reference relay: http://127.0.0.1:8766',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
