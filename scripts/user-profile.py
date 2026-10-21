"""Long-term creator profile that is independent of any model or API key.

Signals (explicit topic feedback, adopting a topic, saved works) are stored in our own
SQLite database. The profile is computed by deterministic rules (evidence threshold,
time decay, length cap) and rendered as a short text that is handed to whichever model
connection is configured. Switching models or keys therefore keeps the understanding.

Users can view every inferred item, delete items, switch personalization off, or clear
everything. Sensitive terms are never stored as profile items.
"""
import json
import math
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

DEFAULTS = {
    'enabled': True,
    'minEvidence': 3,
    'halfLifeDays': 30,
    'maxProfileChars': 400,
    'historyTurns': 6,
    'creationRecords': 10,
    'exploreCount': 1,
    'weights': {'up': 3, 'down': 3, 'adopt': 2, 'work': 1},
}
LIMITS = {'minEvidence': (1, 10), 'halfLifeDays': (1, 365), 'maxProfileChars': (50, 1000),
          'historyTurns': (0, 12), 'creationRecords': (0, 20), 'exploreCount': (0, 2)}
KINDS = ('up', 'down', 'adopt')
FACETS = {'interest': '感兴趣的方向', 'avoid': '不想要的方向', 'audience': '常写给', 'tone': '常用语气', 'goal': '常见目标'}
SENSITIVE = re.compile(r'病|医院|药|诊断|抑郁|焦虑|怀孕|贷款|负债|欠款|工资|收入|存款|银行|身份证|手机号|住址|宗教|信仰|民族|政治|党|性取向|同性|犯罪|自杀|自残|\d{5,}')
STOP = set('的了和与在是我你他她它这那一个一些一种如何怎么什么为什么以及或者还有就是可以'.split()) | {'视频', '内容', '创作', '主题', '一个', '我们', '你们', '自己', '方法', '技巧', '推荐', '分享', '教程', '合集', '清单', '日常', '时候', '问题', '东西', '大家', '第一次', '今天', '明天', '搞定', '推荐', '怎么办', '如何', '重样', '踩坑', '入门', '新手', '讲', '用', '做', '看看', '试试', '学会', '告诉', '知道', '需要', '开始', '记录'}
NUMERIC = re.compile(r'^[\d一二三四五六七八九十百千几两半]+[个次天周月年道分钟秒条步种件款招]*$')


def validate_settings(value):
    """Return a normalized copy or raise ValueError with a Chinese message."""
    if not isinstance(value, dict) or set(value) != set(DEFAULTS):
        raise ValueError('个性化配置字段无效')
    if type(value['enabled']) is not bool:
        raise ValueError('个性化开关必须为布尔值')
    for key, (low, high) in LIMITS.items():
        if type(value[key]) is not int or not low <= value[key] <= high:
            raise ValueError('%s 需在 %d–%d 之间' % (key, low, high))
    weights = value['weights']
    if not isinstance(weights, dict) or set(weights) != set(DEFAULTS['weights']) or any(type(w) is not int or not 0 <= w <= 10 for w in weights.values()):
        raise ValueError('信号权重需为 0–10 的整数')
    return json.loads(json.dumps(value))


def terms(text, limit=6):
    """Extract a few topic terms; jieba when available (in the server image), simple fallback otherwise."""
    text = str(text or '')[:300]
    try:
        import jieba.analyse  # noqa: WPS433 (optional dependency)
        # Content words only; generic verbs and fillers (搞定/推荐/怎么办) are in STOP, since they would pile up across unrelated topics.
        words = jieba.analyse.extract_tags(text, topK=limit * 2, allowPOS=('n', 'nz', 'vn', 'ns', 'nr', 'nt', 'nw', 'eng', 'v', 'l', 'i'))
    except Exception:
        words = re.findall(r'[一-鿿]{2,6}|[A-Za-z][A-Za-z0-9+.-]{2,20}', text)
    result = []
    for word in words:
        word = word.strip()
        if len(word) < 2 or word in STOP or NUMERIC.match(word) or SENSITIVE.search(word) or word in result:
            continue
        result.append(word)
        if len(result) >= limit:
            break
    return result


class Profiles:
    def __init__(self, path, settings=None, owned_runs=None):
        """settings: callable -> personalization dict; owned_runs: callable(user) -> [{'audience','tone','goal','at'}]."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings or (lambda: DEFAULTS)
        self.owned_runs = owned_runs or (lambda user: [])
        self.lock = threading.Lock()
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS signals(id INTEGER PRIMARY KEY, user TEXT, kind TEXT, term TEXT, at REAL)')
            db.execute('CREATE INDEX IF NOT EXISTS signals_user ON signals(user, at)')
            db.execute('CREATE TABLE IF NOT EXISTS removed(user TEXT, facet TEXT, value TEXT, PRIMARY KEY(user, facet, value))')
            db.execute('CREATE TABLE IF NOT EXISTS prefs(user TEXT PRIMARY KEY, enabled INTEGER, cleared REAL)')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def config(self):
        try:
            return validate_settings(self.settings())
        except Exception:
            return json.loads(json.dumps(DEFAULTS))

    def user_state(self, user):
        with self.db() as db:
            row = db.execute('SELECT enabled, cleared FROM prefs WHERE user=?', (user,)).fetchone()
        return {'enabled': True if row is None else bool(row[0]), 'cleared': (row[1] or 0) if row else 0}

    # ---------- writes from the user ----------
    def signal(self, user, payload, now=None):
        if not isinstance(payload, dict) or set(payload) != {'kind', 'title', 'angle'}:
            raise ValueError('反馈字段无效')
        kind, title, angle = payload['kind'], payload['title'], payload['angle']
        if kind not in KINDS or not isinstance(title, str) or not isinstance(angle, str) or not 1 <= len(title.strip()) <= 60 or len(angle) > 120:
            raise ValueError('反馈内容无效')
        now = time.time() if now is None else now
        found = terms(title + ' ' + angle)
        with self.lock, self.db() as db:
            recent = db.execute('SELECT COUNT(*) FROM signals WHERE user=? AND at>?', (user, now - 3600)).fetchone()[0]
            if recent >= 200:
                raise ValueError('反馈过于频繁，请稍后再试')
            # One signal per topic per kind: tapping twice does not double count.
            key = kind + ':' + title.strip()[:60]
            if db.execute("SELECT 1 FROM signals WHERE user=? AND kind='topic' AND term=?", (user, key)).fetchone():
                return {'recorded': False, 'terms': found}
            db.execute("INSERT INTO signals(user, kind, term, at) VALUES(?, 'topic', ?, ?)", (user, key, now))
            db.executemany('INSERT INTO signals(user, kind, term, at) VALUES(?,?,?,?)', [(user, kind, t, now) for t in found])
        return {'recorded': True, 'terms': found}

    def remove(self, user, payload):
        if not isinstance(payload, dict) or set(payload) != {'facet', 'value'} or payload['facet'] not in FACETS or not isinstance(payload['value'], str) or not 1 <= len(payload['value']) <= 40:
            raise ValueError('删除内容无效')
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO removed VALUES(?,?,?)', (user, payload['facet'], payload['value']))
        return self.view(user)

    def set_enabled(self, user, payload):
        if not isinstance(payload, dict) or set(payload) != {'enabled'} or type(payload['enabled']) is not bool:
            raise ValueError('开关字段无效')
        state = self.user_state(user)
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO prefs VALUES(?,?,?)', (user, int(payload['enabled']), state['cleared']))
        return self.view(user)

    def clear(self, user, now=None):
        now = time.time() if now is None else now
        state = self.user_state(user)
        with self.db() as db:
            db.execute('DELETE FROM signals WHERE user=?', (user,))
            db.execute('DELETE FROM removed WHERE user=?', (user,))
            db.execute('INSERT OR REPLACE INTO prefs VALUES(?,?,?)', (user, int(state['enabled']), now))
        return self.view(user)

    # ---------- computation ----------
    def facets(self, user, now=None):
        now = time.time() if now is None else now
        cfg, state = self.config(), self.user_state(user)
        half = cfg['halfLifeDays'] * 86400
        decay = lambda at: math.pow(0.5, max(0.0, now - at) / half)
        weights = cfg['weights']
        scores = {}

        def add(facet, value, amount, at):
            if not value or SENSITIVE.search(value):
                return
            entry = scores.setdefault((facet, value), {'score': 0.0, 'evidence': 0, 'last': 0})
            entry['score'] += amount * decay(at)
            entry['evidence'] += 1
            entry['last'] = max(entry['last'], at)

        with self.db() as db:
            rows = db.execute("SELECT kind, term, at FROM signals WHERE user=? AND kind!='topic' AND at>?", (user, state['cleared'])).fetchall()
            removed = set(db.execute('SELECT facet, value FROM removed WHERE user=?', (user,)).fetchall())
        for kind, term, at in rows:
            if kind == 'down':
                add('avoid', term, weights['down'], at)
            else:
                add('interest', term, weights['up' if kind == 'up' else 'adopt'], at)
        for run in self.owned_runs(user) or []:
            at = float(run.get('at') or now)
            if at <= state['cleared']:
                continue
            for facet in ('audience', 'tone', 'goal'):
                value = str(run.get(facet) or '').strip()[:20]
                if value:
                    add(facet, value, weights['work'], at)
        # A term both liked and disliked keeps only its net side.
        for value in [v for f, v in scores if f == 'avoid']:
            if ('interest', value) in scores:
                liked, disliked = scores[('interest', value)], scores[('avoid', value)]
                if liked['score'] >= disliked['score']:
                    liked['score'] -= disliked['score']
                    del scores[('avoid', value)]
                else:
                    disliked['score'] -= liked['score']
                    del scores[('interest', value)]
        result = []
        for (facet, value), entry in scores.items():
            if (facet, value) in removed or entry['evidence'] < cfg['minEvidence'] or entry['score'] <= 0.05:
                continue
            result.append({'facet': facet, 'facetName': FACETS[facet], 'value': value, 'score': round(entry['score'], 2),
                           'evidence': entry['evidence'], 'lastAt': int(entry['last'])})
        result.sort(key=lambda r: (list(FACETS).index(r['facet']), -r['score']))
        return result

    def text(self, user, now=None):
        """Profile text for the model; empty when disabled (globally or by the user)."""
        cfg = self.config()
        if not cfg['enabled'] or not self.user_state(user)['enabled']:
            return ''
        groups = {}
        for row in self.facets(user, now):
            groups.setdefault(row['facet'], []).append(row['value'])
        parts = ['%s：%s' % (FACETS[f], '、'.join(groups[f][:6])) for f in FACETS if groups.get(f)]
        if not parts:
            return ''
        text = '长期偏好（由该用户的明确反馈、采纳与作品统计得出，仅作参考；与用户本次要求或明确设置冲突时以用户为准）：' + '；'.join(parts) + '。'
        return text[:cfg['maxProfileChars']]

    def view(self, user, now=None):
        cfg, state = self.config(), self.user_state(user)
        return {'enabled': state['enabled'], 'serviceEnabled': cfg['enabled'], 'minEvidence': cfg['minEvidence'],
                'halfLifeDays': cfg['halfLifeDays'], 'items': self.facets(user, now),
                'notice': '这些内容只根据你点的“喜欢/不想要”、采纳的选题和保存的作品统计得出，存在有AI自己的服务器上，更换 AI 模型也会保留。你可以删除任意一条、关闭个性化或全部清空。'}
