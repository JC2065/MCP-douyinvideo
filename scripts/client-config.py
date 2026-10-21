"""Public data-only configuration; unknown fields never reach clients."""
import json
import os
from pathlib import Path
TOOLS = ('download','transcript','audio','eraser','cover')

def client_config():
    value = {}
    try:
        path = os.environ.get('YOUAI_CLIENT_CONFIG','')
        if path:
            raw = Path(path).read_text(encoding='utf-8-sig')
            if len(raw) <= 16384:
                value = json.loads(raw)
    except (OSError, ValueError):
        pass
    if not isinstance(value,dict): value = {}
    tools = value.get('tools',{})
    if not isinstance(tools,dict): tools = {}
    return {'schemaVersion':1,'revision':str(value.get('revision','default'))[:64],
            'tools':{key:{'maintenance':isinstance(tools.get(key),dict) and tools[key].get('maintenance') is True} for key in TOOLS}}
