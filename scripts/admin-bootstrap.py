"""Generate initial credentials outside the checkout; never print the password."""
import argparse
import importlib.util
import json
import secrets
from pathlib import Path
spec=importlib.util.spec_from_file_location('console',Path(__file__).with_name('admin-console.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
parser=argparse.ArgumentParser()
parser.add_argument('--directory',required=True)
args=parser.parse_args()
root=Path(args.directory).resolve()
repo=Path(__file__).resolve().parent.parent
if root==repo or repo in root.parents: raise SystemExit('Credentials must be outside the checkout.')
root.mkdir(parents=True,exist_ok=True)
auth=root/'admin-auth.json';login=root/'admin-login.txt'
if auth.exists() or login.exists(): raise SystemExit('Existing credentials preserved. Move both files aside explicitly before rotating.')
password=secrets.token_urlsafe(24)
auth.write_text(json.dumps(m.credential(password)),encoding='utf-8')
auth.chmod(0o600)
login.write_text('YOUAI 管理中台\n网址：https://youai888.top/youai/admin/\n账号：admin\n密码：'+password+'\n仅供管理员本机查看，不上传仓库。\n',encoding='utf-8')
login.chmod(0o600)
print('Admin hash and local login file created; no credentials printed.')
