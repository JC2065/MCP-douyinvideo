"""Run on cloud host against a private endpoint; never print the session token."""
import json,sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
result=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
token=result['token']
logout='--logout' in sys.argv
if logout:
    with urlopen(Request('http://127.0.0.1:8765/auth/logout',data=b'{}',headers={'Authorization':'Bearer '+token}),timeout=10) as response:
        assert json.load(response).get('status')=='signed_out'
try:
    request=Request('http://127.0.0.1:8765/auth/me',headers={'Authorization':'Bearer '+token})
    with urlopen(request,timeout=10) as response:identity=json.load(response)
    assert identity.get('userId')==result['userId']
    print(json.dumps({'sessionVerified':True,'tokenPrinted':False}))
except HTTPError as error:
    if logout and error.code==401:
        print(json.dumps({'logoutVerified':True,'tokenPrinted':False}));raise SystemExit(0)
    print(json.dumps({'sessionVerified':False,'httpStatus':error.code}));raise SystemExit(1)
