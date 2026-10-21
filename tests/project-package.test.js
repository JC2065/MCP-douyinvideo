const test=require('node:test'),assert=require('node:assert/strict'),cp=require('node:child_process');
test('源码归档校验拒绝文件损坏和遗漏，支持中文路径',()=>{
 const python=process.env.YOUAI_TEST_PYTHON||'C:/Users/one/MoneyPrinterTurbo/.venv/Scripts/python.exe';
 const code=`import importlib.util,tempfile,zipfile,pathlib,subprocess
spec=importlib.util.spec_from_file_location('pack','scripts/package-baseline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with tempfile.TemporaryDirectory() as folder:
 a=pathlib.Path(folder)/'source.zip';raw='内容'.encode()
 with zipfile.ZipFile(a,'w') as z:z.writestr('源码/a.txt',raw)
 files={'源码/a.txt':{'bytes':len(raw),'sha256':p.digest(raw)}}
 assert p.verify_source(a,files)==1
 for bad in [{}, {'源码/a.txt':{'bytes':len(raw),'sha256':'0'*64}}]:
  try:p.verify_source(a,bad)
  except ValueError:pass
  else:raise AssertionError('Bad package accepted')
with tempfile.TemporaryDirectory() as folder:
 repo=pathlib.Path(folder)/'repo';repo.mkdir()
 subprocess.run(['git','init','-q',str(repo)],check=True)
 subprocess.run(['git','config','core.autocrlf','true'],cwd=repo,check=True)
 (repo/'line.txt').write_bytes(b'a\\r\\nb\\r\\n')
 subprocess.run(['git','add','line.txt'],cwd=repo,check=True)
 subprocess.run(['git','-c','user.name=Package Test','-c','user.email=package@example.invalid','commit','-qm','fixture'],cwd=repo,check=True)
 out=pathlib.Path(folder)/'out';p.build(repo,out)
 with zipfile.ZipFile(out/'source.zip') as z:assert z.read('line.txt')==b'a\\nb\\n'
`;
 const result=cp.spawnSync(python,['-c',code],{encoding:'utf8'});assert.equal(result.status,0,result.stderr);
});
