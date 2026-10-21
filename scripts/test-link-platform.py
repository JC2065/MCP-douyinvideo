import importlib.util,io,json,tempfile,unittest,types
from pathlib import Path
spec=importlib.util.spec_from_file_location('link',Path(__file__).with_name('link-platform.py'));link=importlib.util.module_from_spec(spec);spec.loader.exec_module(link)
SAMPLE={'success':True,'data':{'platform':'douyin','content_id':'7689250555358140598','title':'中秋快乐～#dj润 #御姐#手势舞','description':'中秋快乐～#dj润 #御姐#手势舞','tags':[],'created_at':'2026-09-25T10:39:00Z','fetched_at':'2026-10-17T18:27:40Z',
 'stats':{'digg_count':12543,'play_count':None,'share_count':4508,'collect_count':2715,'comment_count':136},'music':{'title':'@某某的原声','author':'某某','music_id':765},
 'author':{'uid':'U','sec_uid':'S','nickname':'DJ','signature':'演出对接 微信xxx','avatar':{'urls':['https://a']},'stats':{'follower_count':130380}}}}
class Tests(unittest.TestCase):
    def test_detect_routes_platforms(self):
        self.assertEqual(link.detect('3.02 nDH:/ 复制 https://v.douyin.com/V2-jkijASP8/ 复制此链接')['url'],'https://v.douyin.com/V2-jkijASP8/')
        self.assertTrue(link.detect('https://www.douyin.com/video/123')['supported'])
        for text,ident in (('https://v.kuaishou.com/abc','kuaishou'),('http://xhslink.com/a/b','xiaohongshu'),('https://b23.tv/xyz','bilibili'),('https://example.com/v','unknown'),('只是文字','none')):
            found=link.detect(text);self.assertEqual(found['platform'],ident);self.assertFalse(found['supported']);self.assertTrue(found['message'])
        self.assertIn('上传原视频',link.detect('https://v.kuaishou.com/abc')['message'])
    def test_source_meta_keeps_public_facts_only(self):
        meta=link.source_meta(SAMPLE)
        self.assertEqual({k:meta['author'][k] for k in ('uid','nickname','followerCount','hasContact')},{'uid':'S','nickname':'DJ','followerCount':130380,'hasContact':True})
        self.assertEqual(meta['author']['signature'],'演出对接 [联系方式]');self.assertEqual(meta['kind'],'video')
        for bio,cleaned in (('V：zxyy🌿902 本人回复','[联系方式] 本人回复'),('合作电话13812345678','合作[联系方式]'),('爱拍vlog的上班族','爱拍vlog的上班族')):self.assertEqual(link.strip_contacts(bio)[0],cleaned)
        gallery=link.source_meta({'data':{'media':{'video':None,'images':[{'url':'https://p/1.jpg'},{'url':'https://p/2.jpg'}]},'description':'避雷帖 #找工作','author':{'stats':{'total_digg':99}}}})
        self.assertEqual((gallery['kind'],gallery['imageCount'],gallery['description'],gallery['author']['totalLikes']),('gallery',2,'避雷帖 #找工作',99))
        self.assertEqual(meta['hashtags'],['dj润','御姐','手势舞']);self.assertEqual(meta['stats']['digg_count'],12543);self.assertIsNone(meta['stats']['play_count'])
        dumped=json.dumps(meta,ensure_ascii=False);self.assertNotIn('微信',dumped);self.assertNotIn('https://a',dumped)
        self.assertEqual(link.source_meta({})['hashtags'],[])
if __name__=='__main__':unittest.main()
