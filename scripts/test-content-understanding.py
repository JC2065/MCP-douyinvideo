import copy, importlib.util, json, unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('understanding',Path(__file__).with_name('content-understanding.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def result():
    return {'overview':'一只猫在窗边看雨','facts':[{'text':'窗边的猫','frameTimes':[0,5],'speechEvidence':''}],
            'segments':[{'start':0,'end':5,'description':'猫走到窗前'},{'start':5,'end':10,'description':'镜头转向窗外雨景'}],
            'uncertainties':['无法确认猫的品种'], 'recommendations':{k:[{'key':'tone','value':'细腻安静','reason':'与猫看雨的画面相符','factIndexes':[0]}] for k in ('video','text','image')}}
class Tests(unittest.TestCase):
    def test_watch_card_free_type_tags_value_sources_and_screen_text(self):
        calls=[]
        class G:
            def complete(self,scene,messages):
                calls.append((scene,messages));return {'choices':[{'message':{'content':json.dumps({'overview':'对口型唱歌','type':'深情对口型','tags':['老歌','对口型','x'*40],'valueSources':{'text':3,'performance':1,'visual':'bad'},'timeline':[]},ensure_ascii=False)}}]}
        card=m.watch(G(),[(1.0,Image.new('RGB',(36,64)))],{'text':''},17.0,{},[{'start':0,'end':2,'text':'有人问我你究竟是哪里好'}])
        self.assertEqual(card['type'],'深情对口型');self.assertEqual(card['tags'][2],'x'*16)
        self.assertEqual(card['valueSources'],{'text':0.75,'performance':0.25});self.assertEqual(card['valueShares'][0],{'key':'text','label':'文字','percent':75})
        payload=json.loads(calls[0][1][1]['content'][0]['text']);self.assertEqual(payload['screenText'][0]['text'],'有人问我你究竟是哪里好')
        self.assertIn('valueSources',m.WATCH_SYSTEM);self.assertIn('不套固定分类',m.WATCH_SYSTEM)
    def test_truncated_watch_output_is_retried_compact_instead_of_syntax_repair(self):
        good=json.dumps({'overview':'长发女生对口型','type':'对口型','tags':['对口型'],'timeline':[{'start':0,'end':5,'what':'对着镜头说话'}]},ensure_ascii=False)
        replies=[{'choices':[{'message':{'content':'{"overview":"长发女生对口型","timeline":[{"start":0,"end":3,"what":"对着镜'},'finish_reason':'length'}]},{'choices':[{'message':{'content':good},'finish_reason':'stop'}]}];calls=[]
        class G:
            def complete(self,scene,messages):calls.append(messages);return replies[len(calls)-1]
        card=m.watch(G(),[(1.0,Image.new('RGB',(36,64)))],{'text':''},22.0,{})
        self.assertEqual(card['overview'],'长发女生对口型');self.assertEqual(len(calls),2)
        self.assertIn('上一次输出太长被截断',calls[1][0]['content']);self.assertEqual(calls[1][1]['content'],calls[0][1]['content'],'重看用同一份画面和文字')
        spec=importlib.util.spec_from_file_location('ai',Path(__file__).with_name('inspiration-ai.py'));ai=importlib.util.module_from_spec(spec);spec.loader.exec_module(ai)
        self.assertGreaterEqual(ai.DEFAULTS['video_watch'][1],4000,'22 秒以上的视频看图输出不能被 1500 截断')

    def test_glance_is_short_and_lenient(self):
        class G:
            def __init__(self,text):self.text=text;self.scene=None
            def complete(self,scene,messages):self.scene=scene;self.n=sum(1 for c in messages[1]['content'] if c['type']=='image_url');return {'choices':[{'message':{'content':self.text}}]}
        g=G('```json\n{"overview":"'+'一位女生在客厅跳手势舞'*8+'","type":"手势舞","tags":["舞蹈"],"confidence":1.5}\n```')
        value=m.glance(g,[(1.0,Image.new('RGB',(36,64))),(3.0,Image.new('RGB',(36,64)))])
        self.assertEqual(g.scene,'video_glance');self.assertEqual(g.n,2);self.assertEqual(len(value['overview']),60);self.assertEqual(value['confidence'],1);self.assertEqual(value['status'],'ready')
        self.assertEqual(m.glance(G('看不清'),[(1.0,Image.new('RGB',(8,8)))])['overview'],'看不清')
        self.assertEqual(m.glance(G(''),[(1.0,Image.new('RGB',(8,8)))])['status'],'unavailable')
    def test_music_dance_requires_visual_action_not_lyrics_as_copy(self):
        self.assertIn('无口播视频同样可以完整拆解',m.SYSTEM)
        self.assertIn('不得用歌词替代画面拆解',m.SYSTEM)
        self.assertIn('人物运动不等于切镜',m.SYSTEM)
        raw=result();raw['overview']='固定机位的舞蹈练习'
        raw['facts']=[{'text':'人物抬起双臂，随后向右侧转身','frameTimes':[0,5],'speechEvidence':''}]
        raw['segments']=[{'start':0,'end':10,'description':'全身固定机位；从双手抬起变为侧身，背景保持不变'}]
        raw['recommendations']={'video':[{'key':'goal','value':'固定全身机位复刻抬手到侧身的动作顺序','reason':'画面以连续动作展示为主','factIndexes':[0]}]}
        class Gateway:
            def complete(self,*args):return {'choices':[{'message':{'content':json.dumps(raw)}}]}
        image=Image.new('RGB',(20,30))
        value=m.understand(Gateway(),[(0,image),(5,image),(10,image)],{'text':'歌曲歌词'},10)
        self.assertEqual(value['facts'][0]['speechEvidence'],'')
        self.assertIn('全身固定机位',value['segments'][0]['description'])
    def test_multimodal_payload_has_actual_frames_and_real_speech(self):
        calls=[]
        class Gateway:
            def complete(self,scene,messages):
                calls.append((scene,messages));return {'choices':[{'message':{'content':json.dumps(result())}}]}
        image=Image.new('RGB',(20,30),'white')
        value=m.understand(Gateway(),[(0,image),(5,image),(10,image)],{'text':'下雨了'},10)
        self.assertEqual(value['status'],'ready');self.assertEqual(len(value['segments']),2)
        self.assertEqual(calls[0][0],'reference_understanding')
        content=calls[0][1][1]['content'];self.assertEqual(sum(x['type']=='image_url' for x in content),3)
        self.assertTrue(content[2]['image_url']['url'].startswith('data:image/jpeg;base64,'))
        self.assertIn('下雨了',content[0]['text'])
    def test_recommendations_are_free_text_but_require_real_fact_references(self):
        value=m.normalize(result(),[0,5,10],10)
        self.assertEqual(value['recommendations']['image'][0]['value'],'细腻安静')
        for indexes in ([],[99],[-1],[True]):
            raw=result();raw['recommendations']['image'][0]['factIndexes']=indexes
            with self.assertRaises(ValueError):m.normalize(raw,[0,5,10],10)
    def test_no_fabricated_timepoints_or_overlapping_segments(self):
        for mutation in ('time','overlap','nan','missing'):
            raw=result()
            if mutation=='time':raw['facts'][0]['frameTimes']=[123]
            if mutation=='overlap':raw['segments'][1]['start']=4
            if mutation=='nan':raw['segments'][0]['end']=float('nan')
            if mutation=='missing':raw['facts']=[]
            with self.assertRaises(ValueError):m.normalize(raw,[0,5,10],10)
    def test_speech_evidence_must_exist_in_transcription(self):
        raw=result();raw['facts'][0]['speechEvidence']='不存在的原声';raw['facts'][0]['frameTimes']=[0]
        class Gateway:
            def complete(self,*args):return {'choices':[{'message':{'content':json.dumps(raw)}}]}
        with self.assertRaisesRegex(ValueError,'实际转写'):m.understand(Gateway(),[(0,Image.new('RGB',(10,10)))],{'text':'下雨了'},10)
    def test_gateway_failure_is_not_converted_to_a_fake_understanding(self):
        class Gateway:
            def complete(self,*args):raise RuntimeError('not configured')
        with self.assertRaises(RuntimeError):m.understand(Gateway(),[(0,Image.new('RGB',(10,10)))],{},10)
if __name__=='__main__':unittest.main()
