"""Package a committed checkout and verify every source file without extracting it."""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

def digest(raw):return hashlib.sha256(raw).hexdigest()

def verify_source(archive, files):
    with zipfile.ZipFile(archive) as package:
        names=[i.filename for i in package.infolist() if not i.is_dir()]
        if len(names)!=len(set(names)) or set(names)!=set(files):raise ValueError('File inventory mismatch')
        for name in names:
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe source path')
            raw=package.read(name)
            if len(raw)!=files[name]['bytes'] or digest(raw)!=files[name]['sha256']:raise ValueError('Source integrity mismatch: '+name)
        if package.testzip():raise ValueError('ZIP CRC failure')
    return len(names)

def build(repo, output):
    repo=Path(repo).resolve();output=Path(output).resolve()
    if output==repo or repo in output.parents:raise ValueError('Output must stay outside checkout')
    if subprocess.check_output(['git','status','--porcelain'],cwd=repo):raise ValueError('Commit changes before packaging')
    if output.exists() and (output/'source.zip').exists():raise ValueError('Do not overwrite an existing baseline')
    output.mkdir(parents=True,exist_ok=True)
    (output/'private').mkdir(exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    archive=output/'source.zip'
    subprocess.run(['git','-c','core.autocrlf=false','archive','--format=zip','-o',str(archive),commit],cwd=repo,check=True)
    bundle=output/'private/project.bundle'
    subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=repo,check=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    files={}
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            if entry.is_dir():continue
            raw=package.read(entry)
            original=subprocess.check_output(['git','show',commit+':'+entry.filename],cwd=repo)
            if raw!=original:raise ValueError('Archive differs from commit')
            files[entry.filename]={'bytes':len(raw),'sha256':digest(raw)}
    count=verify_source(archive,files)
    manifest={'commit':commit,'files':files,'sourceSha256':digest(archive.read_bytes()),
              'gitBundleSha256':digest(bundle.read_bytes()),'verifiedFiles':count,'gitBundleVerified':True}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'commit':commit,'verifiedFiles':count,'sourceBytes':archive.stat().st_size,'bundleVerified':True}))

if __name__=='__main__':build(sys.argv[1],sys.argv[2])
