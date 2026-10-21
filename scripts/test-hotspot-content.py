import importlib.util
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('content',Path(__file__).with_name('hotspot-content.py'))
content=importlib.util.module_from_spec(spec)
spec.loader.exec_module(content)

class ContentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        content.ROOT=Path(self.tmp.name)
        content.JOBS.clear()
        self.row={'id':'weibo-'+'a'*20,'title':'咖啡新品发布','url':'https://s.weibo.com/a'}
    def tearDown(self):self.tmp.cleanup()
    def test_actual_excerpts_relevance_dedup_and_safe_link_protocol(self):
        xml='''<rss><channel><item><title>咖啡新品发布消息</title><description>厂商发布咖啡新品，具体信息以公告为准。</description><link>https://news.cn/a</link></item><item><title>咖啡新品发布消息</title><description>重复</description><link>https://news.cn/a</link></item><item><title>其他话题</title><description>完全无关的气象信息</description><link>https://news.cn/b</link></item><item><title>咖啡新品发布</title><description>坏链接</description><link>javascript:alert(1)</link></item></channel></rss>'''
        rows=content.parse_rss(xml.encode(),self.row['title'])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['source'],'news.cn')
        self.assertIn('厂商发布',rows[0]['excerpt'])
        self.assertEqual(rows[0]['contentType'],'网页检索摘录')
    def test_empty_and_failure_are_explicit(self):
        content.run(self.row,lambda _:[])
        self.assertEqual(content.content(self.row['id'],[self.row])['status'],'empty')
        content.run(self.row,lambda _: (_ for _ in ()).throw(TimeoutError()))
        self.assertEqual(content.content(self.row['id'],[self.row])['status'],'error')
    def test_cached_read_survives_restart_and_rejects_expired_topic(self):
        content.run(self.row,lambda _:[{'title':'真实内容','excerpt':'摘录'}])
        content.JOBS.clear()
        with patch.object(content.POOL,'submit') as submit:
            self.assertEqual(content.content(self.row['id'],[self.row])['status'],'ready')
            submit.assert_not_called()
        self.assertEqual(content.content(self.row['id'],[])['status'],'expired')
    def test_pending_deduplicated_and_bounded(self):
        with patch.object(content.POOL,'submit') as submit:
            content.content(self.row['id'],[self.row]);content.content(self.row['id'],[self.row])
            self.assertEqual(submit.call_count,1)
            second=dict(self.row,id='weibo-'+'b'*20);third=dict(self.row,id='weibo-'+'c'*20)
            content.content(second['id'],[second])
            self.assertEqual(content.content(third['id'],[third])['status'],'busy')
            self.assertEqual(submit.call_count,2)
    def test_stale_cache_refreshes(self):
        content.JOBS[self.row['id']]={'status':'ready','retrievedAt':time.time()-2000,'items':[]}
        with patch.object(content.POOL,'submit') as submit:
            self.assertEqual(content.content(self.row['id'],[self.row])['status'],'pending')
            submit.assert_called_once()
    def test_explicit_retry_refreshes_negative_cache_but_keeps_ready_cache(self):
        content.run(self.row,lambda _:[])
        with patch.object(content.POOL,'submit') as submit:
            self.assertEqual(content.content(self.row['id'],[self.row],retry=True)['status'],'pending')
            submit.assert_called_once()
        content.run(self.row,lambda _:[{'title':'来源摘录'}])
        with patch.object(content.POOL,'submit') as submit:
            self.assertEqual(content.content(self.row['id'],[self.row],retry=True)['status'],'ready')
            submit.assert_not_called()
    def test_empty_search_falls_back_without_accepting_unrelated_entries(self):
        calls=[]
        unrelated=b'<rss><channel><item><title>Dictionary</title><description>Other subject</description><link>https://example.com/a</link></item></channel></rss>'
        matched='<rss><channel><item><title>中朝新鸭绿江大桥将开通</title><description>双方商定大桥将正式开通。</description><link>https://www.news.cn/a</link></item></channel></rss>'.encode()
        def reader(url):
            calls.append(url)
            return unrelated if len(calls)==1 else matched
        rows=content.fetch('中朝新鸭绿江大桥将开通',reader,lambda _:['中朝','新','鸭绿江','大桥','将','开通'])
        self.assertEqual(len(rows),1)
        self.assertEqual(len(calls),2)
        self.assertIn('%20',calls[1])
    def test_requests_bounded_and_transport_failure_differs_from_empty(self):
        calls=[]
        def reader(url):calls.append(url);return b'<rss><channel/></rss>'
        self.assertEqual(content.fetch('话题标题',reader,lambda _:['话题','标题']),[])
        self.assertEqual(len(calls),3)
        with self.assertRaises(RuntimeError):content.fetch('标题',lambda _:(_ for _ in ()).throw(TimeoutError()),lambda _:['标题'])
    def test_old_negative_cache_does_not_hide_new_retrieval(self):
        content.JOBS[self.row['id']]={'status':'empty','retrievedAt':time.time(),'items':[]}
        with patch.object(content.POOL,'submit') as submit:
            self.assertEqual(content.content(self.row['id'],[self.row])['status'],'pending')
            submit.assert_called_once()

if __name__=='__main__':unittest.main()
