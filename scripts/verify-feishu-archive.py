"""Create a non-sensitive local sample and verify the real Feishu archive cycle."""
import importlib.util,json,uuid,shutil
from pathlib import Path
spec=importlib.util.spec_from_file_location('video_server',Path(__file__).with_name('video-server.py'));server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
job=uuid.uuid4().hex
board={'version':1,'status':'approved','referenceMode':'same-topic','shots':[{'role':'开场','narration':'资产闭环测试','visual':'本地文字样片'},{'role':'展开','narration':'同步与归档','visual':'本地文字样片'},{'role':'收束','narration':'恢复校验','visual':'本地文字样片'}]}
data=server.validate({'idea':'资产闭环验收样片','duration':2,'mood':'温柔治愈','visualStyle':'纯文字画面','source':{'type':'idea'},'storyboard':board})
sample=server.render(job,data);sha=server.hashlib.sha256(sample.read_bytes()).hexdigest();source=server.REFERENCE_ROOT/f'{sha}.mp4';shutil.copy2(sample,source)
reference={'status':'acquired','asset':{'sha256':sha,'storagePath':str(source),'media':server._probe_video(source)}}
analysis,_=server.analyze_reference(reference,transcriber=lambda _:{'status':'silent','confidence':0,'text':'','segments':[]});reference.update(status='analyzed',analysis=analysis);data['source']={'type':'douyin','reference':reference};server.persist_run_assets(job,data,'local-text');manager=server.ARCHIVE
try:
    manager.process(job)
    result=manager.restore(job)
    manager.feedback(job,{'rating':'满意','reason':'真实归档恢复校验','adopted':'测试样片'})
    manager.process(job)
    with manager.db() as db:db.execute("UPDATE jobs SET status='archived',error='' WHERE id=?",(job,))
    print(json.dumps({'runId':job,'status':manager.status(job),'restore':result,'paidModelCalls':0},ensure_ascii=True))
except Exception as e:
    print(json.dumps({'runId':job,'error':str(e),'paidModelCalls':0},ensure_ascii=True));raise SystemExit(1)
