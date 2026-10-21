import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location('feed', Path(__file__).with_name('hotspot-feed.py'))
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        feed.ROOT = Path(self.temp.name) / 'snapshot.json'
        feed.STATE.clear()
        feed.STATE['sources'] = {}
    def tearDown(self):
        self.temp.cleanup()
    def payload(self, key):
        return {'code': 200, 'updateTime': 'source-time', 'data': [{'title': key+'热榜', 'url': 'https://example.com/a'}, {'title': '第二名'}]}
    def test_rank_source_and_no_fake_fallback(self):
        self.assertEqual(feed.snapshot(1000)['rows'], [])
        feed.refresh(self.payload, 1000)
        result = feed.snapshot(1001)
        self.assertEqual([r['rank'] for r in result['rows']], [1]*4+[2]*4)
        self.assertEqual(result['refreshSeconds'], 600)
        self.assertEqual(result['sources']['douyin']['sourceUpdatedAt'], 'source-time')
        self.assertTrue(feed.ROOT.is_file())
    def test_partial_failure_preserves_timestamp_then_expires_and_recovers(self):
        feed.refresh(self.payload, 1000)
        def partial(key):
            if key=='weibo': raise TimeoutError()
            return self.payload(key)
        feed.refresh(partial, 1600)
        result = feed.snapshot(1601)
        self.assertEqual(result['sources']['weibo']['fetchedAt'], 1000)
        self.assertEqual(result['sources']['weibo']['status'], 'stale')
        self.assertEqual(result['sources']['douyin']['status'], 'fresh')
        self.assertEqual(feed.snapshot(100000)['rows'], [])
        feed.refresh(self.payload, 100001)
        self.assertEqual(feed.snapshot(100002)['sources']['weibo']['status'], 'fresh')
    def test_empty_bad_feed_not_success(self):
        for payload in [{'code':500,'data':[]},{'code':200,'data':[]},{'code':200,'data':[{}]}]:
            with self.assertRaises(ValueError): feed.normalize('weibo',payload,1000)
    def test_snapshot_isolation(self):
        feed.refresh(self.payload,1000)
        feed.snapshot(1001)['rows'][0]['title']='changed'
        self.assertNotEqual(feed.snapshot(1001)['rows'][0]['title'],'changed')
    def test_restart_loads_disk_before_background_refresh(self):
        feed.refresh(self.payload,1000)
        feed.STATE.clear()
        feed.STATE['sources'] = {}
        with patch.object(feed, 'BASE', 'http://internal'), patch.object(feed.threading, 'Thread') as thread:
            feed.start()
            self.assertEqual(len(feed.snapshot(1001)['rows']), 8)
            thread.return_value.start.assert_called_once()
    def test_rising_new_and_falling_compare_real_previous_positions(self):
        feed.refresh(self.payload,1000)
        def changed(key):
            return {'code':200, 'data':[{'title':'第二名'},{'title':'新增'},{'title':key+'热榜'}]}
        feed.refresh(changed,1600)
        rows=feed.snapshot(1601)['rows']
        rising=next(r for r in rows if r['platform']=='微博' and r['title']=='第二名')
        self.assertEqual((rising['trend'],rising['rankChange'],rising['previousRank']),('rising',1,2))
        self.assertEqual(rising['comparisonSeconds'],600)
        self.assertEqual([p['rank'] for p in rising['rankTrail']],[2,1])
        self.assertEqual(next(r for r in rows if r['title']=='新增')['trend'],'new')
        self.assertEqual(next(r for r in rows if r['title']=='weibo热榜')['trend'],'falling')
    def test_cold_start_long_gap_and_history_bound(self):
        feed.refresh(self.payload,1000)
        self.assertTrue(all(r['trend']=='baseline' for r in feed.snapshot(1001)['rows']))
        feed.refresh(self.payload,5000)
        self.assertTrue(all(r['trend']=='baseline' for r in feed.snapshot(5001)['rows']))
        for i in range(1,9):feed.refresh(self.payload,5000+i*600)
        self.assertTrue(all(len(r['rankTrail'])==6 for r in feed.snapshot(9801)['rows']))

if __name__=='__main__': unittest.main()
