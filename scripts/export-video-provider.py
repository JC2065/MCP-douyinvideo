"""Export only video provider settings to a repository-external env file."""
import pathlib,sys,tomllib
source=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2])
config=tomllib.loads(source.read_text(encoding='utf-8-sig'));config=config.get('app',config)
mapping={'qianwen_video_api_key':'YOUAI_QIANWEN_API_KEY','qianwen_video_base_url':'YOUAI_QIANWEN_BASE_URL','qianwen_video_model':'YOUAI_QIANWEN_MODEL','qianwen_video_resolution':'YOUAI_QIANWEN_RESOLUTION'}
lines=[]
for key,name in mapping.items():
    value=str(config.get(key) or '')
    if not value:continue
    if any(char in value for char in "\r\n'"):raise ValueError('Provider setting contains unsupported characters')
    lines.append(name+"='"+value+"'")
target.parent.mkdir(parents=True,exist_ok=True);target.write_text('\n'.join(lines)+'\n',encoding='utf-8');target.chmod(0o600)
print({'providerKeyPresent':bool(config.get('qianwen_video_api_key')),'settingsExported':len(lines)})
