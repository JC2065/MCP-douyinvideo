"""Run inside the image (via stdin): fail if the server cannot load.

1. every module video-server.py loads must exist;
2. the server module itself must import cleanly (catches data files missing from the image),
   using throwaway directories so nothing real is touched and no server is started.
"""
import importlib.util
import os
import pathlib
import re
import sys
import tempfile

source = pathlib.Path('scripts/video-server.py').read_text(encoding='utf-8')
modules = sorted(set(re.findall(r"with_name\('([a-z-]+\.py)'\)", source)))
missing = [name for name in modules if not pathlib.Path('scripts', name).exists()]
if missing:
    sys.exit('missing modules: ' + ', '.join(missing))
print('modules ok:', len(modules))

scratch = tempfile.mkdtemp()
for name in ('YOUAI_ADMIN_ROOT', 'YOUAI_ASSET_ROOT', 'YOUAI_TOOL_ASSET_ROOT', 'YOUAI_RENDER_ROOT'):
    os.environ[name] = os.path.join(scratch, name.lower())
for name in ('YOUAI_WECHAT_CONFIG', 'YOUAI_FEISHU_CONFIG', 'YOUAI_MPT_CONFIG'):
    os.environ.pop(name, None)
os.environ['YOUAI_MPT_CONFIG'] = os.path.join(scratch, 'none.toml')
spec = importlib.util.spec_from_file_location('video_server_check', 'scripts/video-server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # __name__ is not "__main__", so no server starts
print('server import ok; platform video model:', module.PLATFORM.config()['video']['model'])
