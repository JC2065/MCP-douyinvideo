import json
from pathlib import Path
CATALOG=json.loads((Path(__file__).parent.parent/'utils'/'platform-boundaries.json').read_text(encoding='utf-8'))
def validate(value):
 if value is None:return None
 if not isinstance(value,dict) or set(value)!={'version','platforms'} or value['version']!=CATALOG['version']:raise ValueError('内容边界版本无效，请刷新配置')
 ids=value['platforms'];allowed={p['id'] for p in CATALOG['platforms']}
 if not isinstance(ids,list) or not 1<=len(ids)<=len(allowed) or any(not isinstance(i,str) or i not in allowed for i in ids):raise ValueError('请选择有效的发布平台')
 return {'version':CATALOG['version'],'platforms':sorted(set(ids))}
def instruction(value):
 value=validate(value)
 if not value:return ''
 rows=CATALOG['common']+[p['name']+'：'+r for p in CATALOG['platforms'] if p['id'] in value['platforms'] for r in p['rules']]
 return '；平台内容边界：'+'；'.join(rows)
