"""Recognise which platform a pasted share text points to, so each platform can use its own parser.

Rules mirror utils/link-platform.js. Phase 1 only parses Douyin; other platforms are recognised so the
user is told to upload the original video instead of waiting for a parser that does not exist.
"""
import re

PLATFORMS = [
    ('douyin', '抖音', re.compile(r"https://(?:v\.|www\.|m\.)?(?:douyin|iesdouyin)\.com/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+", re.I), 'douyin-v1'),
    ('kuaishou', '快手', re.compile(r"https?://(?:v\.|www\.|m\.)?(?:kuaishou|gifshow|chenzhongtech)\.com/[^\s]+", re.I), None),
    ('xiaohongshu', '小红书', re.compile(r"https?://(?:www\.)?(?:xiaohongshu\.com|xhslink\.com)/[^\s]+", re.I), None),
    ('bilibili', '哔哩哔哩', re.compile(r"https?://(?:www\.|m\.)?(?:bilibili\.com|b23\.tv)/[^\s]+", re.I), None),
    ('weixin', '视频号', re.compile(r"https?://(?:channels\.weixin\.qq\.com|weixin\.qq\.com/sph)/[^\s]+", re.I), None),
]
TRAILING = '.,;!?，。；！？、）》】'


def detect(text):
    text = text if isinstance(text, str) else ''
    for ident, name, pattern, parser in PLATFORMS:
        match = pattern.search(text)
        if match:
            url = match.group(0).rstrip(TRAILING)
            supported = parser is not None
            return {'platform': ident, 'name': name, 'url': url, 'parser': parser, 'supported': supported,
                    'message': '' if supported else '暂只支持抖音链接，%s视频请上传原视频' % name}
    if re.search(r'https?://', text):
        return {'platform': 'unknown', 'name': '未知平台', 'url': '', 'parser': None, 'supported': False, 'message': '暂只支持抖音链接，其他视频请上传原视频'}
    return {'platform': 'none', 'name': '', 'url': '', 'parser': None, 'supported': False, 'message': '请粘贴抖音分享链接或上传原视频'}


HASHTAG = re.compile(r'#([^\s#@]{1,30})')


CONTACT = re.compile(r'(?:(?:微信|威信|薇信|vx|wx|qq|扣扣|电话|手机|tel|vx号|微信号)\s*[:：]?\s*[\w\-🌿]{2,})|(?:\bv\s*[:：]\s*[\w\-🌿]{3,})|(?:1[3-9]\d{9})|(?:\d{3,4}-?\d{7,8})|(?:[\w.]+@[\w.]+\.\w+)', re.I)


def strip_contacts(value):
    """Account bios often carry WeChat IDs or phone numbers: replace them, keep only the fact that contact info exists."""
    value = value if isinstance(value, str) else ''
    cleaned, count = CONTACT.subn('[联系方式]', value)
    return cleaned, bool(count)


def source_meta(parsed, now_iso=''):
    """Public facts about the original post, kept for matching plans, judging difficulty and comparing performance later.
    Public counters, the post caption and the account bio with contact details removed; no avatars."""
    data = parsed.get('data') if isinstance(parsed, dict) and isinstance(parsed.get('data'), dict) else (parsed if isinstance(parsed, dict) else {})
    author = data.get('author') if isinstance(data.get('author'), dict) else {}
    author_stats = author.get('stats') if isinstance(author.get('stats'), dict) else {}
    stats = data.get('stats') if isinstance(data.get('stats'), dict) else {}
    music = data.get('music') if isinstance(data.get('music'), dict) else {}
    text = ' '.join(str(data.get(k) or '') for k in ('description', 'title'))
    tags = []
    for item in (data.get('tags') if isinstance(data.get('tags'), list) else []):
        value = item if isinstance(item, str) else (item.get('name') or item.get('hashtag_name') if isinstance(item, dict) else '')
        if isinstance(value, str) and value.strip():
            tags.append(value.strip().lstrip('#')[:30])
    tags += HASHTAG.findall(text)
    def number(value):
        return value if isinstance(value, int) and value >= 0 else None
    def short(value, limit):
        return value.strip()[:limit] if isinstance(value, str) else ''
    media = data.get('media') if isinstance(data.get('media'), dict) else {}
    images = media.get('images') if isinstance(media.get('images'), list) else []
    signature, has_contact = strip_contacts(author.get('signature'))
    return {
        'platform': short(data.get('platform'), 20) or 'douyin',
        'contentId': short(str(data.get('content_id') or data.get('aweme_id') or ''), 40),
        'kind': 'gallery' if images and not media.get('video') else 'video',
        'imageCount': len(images),
        'coverUrl': next((c.get('url') if isinstance(c, dict) else c for c in (media.get('covers') or []) if isinstance(c.get('url') if isinstance(c, dict) else c, str) and str(c.get('url') if isinstance(c, dict) else c).startswith('https://')), ''),
        'description': short(data.get('description') or data.get('title'), 300),
        'author': {'uid': short(author.get('sec_uid') or author.get('uid'), 120), 'nickname': short(author.get('nickname'), 40),
                   'followerCount': number(author_stats.get('follower_count')), 'totalLikes': number(author_stats.get('total_digg')),
                   'verified': bool(author.get('verified')), 'signature': short(signature, 160), 'hasContact': has_contact},
        'hashtags': list(dict.fromkeys(t for t in tags if t))[:12],
        'createdAt': short(data.get('created_at'), 40),
        'stats': {k: number(stats.get(k)) for k in ('digg_count', 'comment_count', 'share_count', 'collect_count', 'play_count')},
        'music': {'title': short(music.get('title'), 60), 'author': short(music.get('author'), 40), 'id': short(str(music.get('music_id') or ''), 40)},
        'fetchedAt': short(data.get('fetched_at'), 40) or now_iso,
    }
