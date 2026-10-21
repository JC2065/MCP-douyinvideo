import importlib.util,io,unittest,itertools
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen-text.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def png():
    b=io.BytesIO();Image.new('RGB',(400,720),'white').save(b,'PNG');return b.getvalue()
class Run:
    def __init__(self,count=5):self.count=count;self.cmd=None
    def __call__(self,cmd,**k):
        self.cmd=cmd;pattern=cmd[-1]
        for i in range(self.count):Image.new('RGB',(304,540),'white').save(pattern.replace('%04d','%04d'%(i+1)))
        return type('R',(),{'returncode':0})()
class Tests(unittest.TestCase):
    def test_confidence_keeps_precision_for_refinement(self):
        rows=m.lines(Image.new('RGB',(100,100)),lambda a:([[[[0,0],[80,0],[80,20],[0,20]],'跑了4分钟',.996123]],None))
        self.assertEqual(rows[0]['confidence'],.996123)
    def test_lexicon_correction_and_numeric_identity(self):
        words=m.lexicon({'description':'似水流年 #行业内幕','hashtags':['专有名词'],
                         'author':{'nickname':'创作作者'},'music':{'title':'岁月如歌'}})
        for word in ['似水流年','行业内幕','专有名词','创作作者','岁月如歌']:self.assertIn(word,words)
        rows=m.correct([{'text':'这是似水汽年的故事，跑了47分钟','layer':'caption'},
                        {'text':'似水汽年','layer':'watermark'}, {'text':'无关的文字123'}],words)
        self.assertEqual(rows[0]['text'],'这是似水流年的故事，跑了47分钟')
        self.assertEqual(rows[0]['corrected'],{'from':'似水汽年','to':'似水流年','by':'lexicon'})
        self.assertEqual(rows[1]['text'],'似水汽年');self.assertEqual(rows[2]['text'],'无关的文字123')
        self.assertEqual(m.correct([{'text':'似水汽年'}],['似水流年','似水华年'])[0]['text'],'似水汽年')
    def test_refine_author_only_confidence_and_crop(self):
        calls=[]
        def runner(cmd,**kwargs):
            calls.append((cmd,kwargs))
            return type('R',(),{'returncode':0,'stdout':png()})()
        def recognise(arr):
            self.assertGreater(arr.shape[0],40)
            return [[[[0,0],[100,0],[100,20],[0,20]],'跑了47分钟',.98]],None
        spans=[dict(start=0,end=2,box=[.1,.5,.5,.04],text='跑了4分钟',confidence=c,layer=l)
               for l,c in [('title',.8),('caption',.99),('ui',.7),('watermark',.7)]]
        result=m.refine('v',spans,10,runner,recognise,lambda:0)
        self.assertEqual(result[0]['text'],'跑了47分钟');self.assertTrue(result[0]['refined'])
        self.assertEqual(result[1]['text'],'跑了47分钟');self.assertEqual(len(calls),4)
        self.assertEqual(result[1]['refinement']['by'],'crop-consensus')
        self.assertEqual(result[1]['refinement']['originalConfidence'],.99)
        self.assertNotIn('-vf',calls[0][0]);self.assertEqual(calls[0][1]['timeout'],10)
    def test_large_numeric_caption_precedes_small_noise(self):
        calls=[]
        def runner(cmd,**kwargs):
            calls.append(float(cmd[cmd.index('-ss')+1]));return type('R',(),{'returncode':0,'stdout':png()})()
        spans=[dict(start=0,end=1,box=[.1,.5,.5,.02],text='4K文字',confidence=.7,layer='caption') for _ in range(12)]
        spans.append(dict(start=4,end=6,box=[.1,.5,.5,.04],text='跑了4分钟',confidence=.995,layer='caption'))
        m.refine('v',spans,10,runner,lambda a:([],None),lambda:0)
        self.assertEqual(calls[:2],[5,4.5]);self.assertEqual(len(calls),12)
    def test_refine_deadline_and_cap(self):
        calls=[]
        def runner(cmd,**kwargs):
            calls.append(cmd);return type('R',(),{'returncode':0,'stdout':png()})()
        spans=[dict(start=0,end=1,box=[.1,.5,.5,.04],text='字幕文字',confidence=.8,layer='caption') for _ in range(20)]
        m.refine('v',spans,10,runner,lambda a:([],None),lambda:0)
        self.assertEqual(len(calls),12)
        calls.clear();m.refine('v',spans,0,runner,lambda a:([],None),lambda:0)
        self.assertEqual(calls,[])
    def test_numeric_consensus_needs_two_matching_reads_and_preserves_other_text(self):
        runner=lambda *a,**k:type('R',(),{'returncode':0,'stdout':png()})()
        for texts in [('跑了47分钟','跑了48分钟'),('跑完47分钟','跑完47分钟')]:
            values=iter(texts)
            recognise=lambda a:([[[[0,0],[100,0],[100,20],[0,20]],next(values),.96]],None)
            span=dict(start=0,end=2,box=[.1,.5,.5,.04],text='跑了4分钟',confidence=.995,layer='caption')
            m.refine('v',[span],10,runner,recognise,lambda:0)
            self.assertEqual(span['text'],'跑了4分钟')
    def test_sampling_caps_frames(self):
        times,interval=m.sample_times(17.3,40);self.assertEqual(interval,1.0);self.assertEqual(len(times),17)
        times,interval=m.sample_times(120,40);self.assertEqual(len(times),40);self.assertEqual(interval,3.0)
    def test_extract_merges_spans_marks_watermark_and_filters_noise(self):
        script={0.5:['有人问我你究竟是哪里好'],1.5:['有人问我你究竟是哪里好'],2.5:['这么多年我还忘不了'],3.5:[],4.5:['这么多年我还忘不了']}
        run=Run();order=iter([0.5,1.5,2.5,3.5,4.5])
        def recognise(arr):
            t=next(order);rows=[[[[10,450],[290,450],[290,480],[10,480]],x,0.95] for x in script.get(t,[])]
            rows.append([[[0,0],[100,0],[100,20],[0,20]],'抖音号:123',0.9]);rows.append([[[0,0],[10,0],[10,10],[0,10]],'噪',0.99]);rows.append([[[0,0],[10,0],[10,10],[0,10]],'低分文字',0.3])
            return rows,None
        result=m.extract('v.mp4',5.0,runner=run,recognise=recognise)
        self.assertEqual(result['status'],'ready');texts=[(s['text'],s['start'],s['end']) for s in result['items']]
        self.assertIn(('有人问我你究竟是哪里好',0,2.0),texts);self.assertIn(('这么多年我还忘不了',2.0,3.0),texts);self.assertIn(('这么多年我还忘不了',4.0,5.0),texts)
        mark=[s for s in result['items'] if s['text']=='抖音号:123'][0];self.assertTrue(mark['persistent'])
        self.assertNotIn('噪',[s['text'] for s in result['items']]);self.assertNotIn('低分文字',[s['text'] for s in result['items']])
        context=m.as_context(result);self.assertNotIn('抖音号:123',[c['text'] for c in context])
        sub=[s for s in result['items'] if s['text']=='有人问我你究竟是哪里好'][0];self.assertAlmostEqual(sub['box'][1],450/540,2);self.assertIn('fps=1/1.0,scale=-2:540',run.cmd)
    def test_budget_and_missing_engine(self):
        clock=itertools.chain([0,0],itertools.repeat(100)).__next__
        result=m.extract('v.mp4',5.0,runner=Run(),recognise=lambda a:([],None),clock=clock,budget_seconds=1)
        self.assertEqual(result['status'],'partial')
        original=m.available;m.available=lambda:False
        try:self.assertEqual(m.extract('v.mp4',5.0)['status'],'unavailable')
        finally:m.available=original
if __name__=='__main__':unittest.main()
