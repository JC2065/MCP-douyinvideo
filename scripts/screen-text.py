"""On-screen text (subtitles, titles, captions) with timings, via local OCR (RapidOCR, CPU, no model fees).

Returns spans [{start, end, text, box:[x,y,w,h] (0–1), confidence, persistent}] merged across samples.
`persistent` marks text that stays on screen for most of the video (watermarks, account IDs, fixed titles).
If the OCR package is missing the result is {'status':'unavailable'} and callers continue without it.
"""
import io
import difflib
import re
import subprocess
import tempfile
from pathlib import Path
import threading
import time

import imageio_ffmpeg

_ENGINE = None
_LOCK = threading.Lock()
MIN_CONFIDENCE = 0.6


def lexicon(source):
    """Bounded vocabulary from public post metadata; numbers are never correction targets."""
    source = source if isinstance(source, dict) else {}
    values = [source.get('description', ''), (source.get('author') or {}).get('nickname', ''),
              (source.get('music') or {}).get('title', '')] + list(source.get('hashtags') or [])[:12]
    words = set()
    for value in values:
        for token in re.findall(r'[\u4e00-\u9fffA-Za-z]+', str(value)[:300]):
            if 2 <= len(token) <= 12:
                words.add(token)
            elif len(token) > 12:
                try:
                    import jieba
                    words.update(word for word in jieba.lcut(token) if 2 <= len(word) <= 12)
                except ImportError:
                    pass
    return sorted(words, key=lambda word: (-len(word), word))[:100]


def correct(items, vocabulary):
    """Correct unambiguous near matches in author text; preserve timing and provenance."""
    result = []
    for item in items:
        row = dict(item)
        if row.get('layer', 'caption') not in ('title', 'caption'):
            result.append(row)
            continue
        text = row.get('text', '')
        edits = []
        def replace(match):
            token = match.group()
            if token in vocabulary:
                return token
            output, index = '', 0
            while index < len(token):
                candidates = []
                for word in vocabulary:
                    if len(word) < 3 or index + len(word) > len(token):
                        continue
                    original = token[index:index + len(word)]
                    difference = sum(a != b for a, b in zip(original, word))
                    score = difflib.SequenceMatcher(None, original, word).ratio()
                    if difference <= 2 and score >= .75:
                        candidates.append((score, len(word), word, original))
                candidates.sort(reverse=True)
                if candidates and (len(candidates) == 1 or candidates[0][:2] > candidates[1][:2]):
                    _, size, word, original = candidates[0]
                    if word != original:
                        edits.append({'from': original, 'to': word, 'by': 'lexicon'})
                    output += word
                    index += size
                else:
                    output += token[index]
                    index += 1
            return output
        row['text'] = re.sub(r'[\u4e00-\u9fffA-Za-z]{3,}', replace, text)
        if edits:
            row['corrected'] = edits[0] if len(edits) == 1 else edits
        result.append(row)
    return result


def engine():
    global _ENGINE
    with _LOCK:
        if _ENGINE is None:
            from rapidocr_onnxruntime import RapidOCR  # noqa: WPS433 (optional, present in the server image)
            _ENGINE = RapidOCR()
        return _ENGINE


def available():
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


def sample_times(duration, max_frames=40):
    interval = max(1.0, duration / max_frames)
    times, t = [], interval / 2
    while t < duration and len(times) < max_frames:
        times.append(round(t, 2))
        t += interval
    return times, interval


def frame(path, second, height=720, runner=subprocess.run, timeout=30):
    from PIL import Image
    result = runner([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-ss', str(second), '-i', str(path), '-frames:v', '1',
                     *(['-vf', 'scale=-2:%d' % height] if height else []), '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, timeout=timeout)
    if result.returncode or not result.stdout:
        return None
    return Image.open(io.BytesIO(result.stdout)).convert('RGB')


def lines(image, recognise=None):
    import numpy as np
    recognise = recognise or engine()
    width, height = image.size
    found, _ = recognise(np.array(image), use_cls=False) if recognise is _ENGINE else recognise(np.array(image))
    rows = []
    for box, text, score in found or []:
        text = str(text).strip()
        if len(text) < 2 or float(score) < MIN_CONFIDENCE or (len(text) <= 3 and text.replace('.', '').replace(':', '').isdigit()):
            continue
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        rows.append({'text': text[:80], 'confidence': round(float(score), 6),
                     'box': [round(min(xs) / width, 3), round(min(ys) / height, 3), round((max(xs) - min(xs)) / width, 3), round((max(ys) - min(ys)) / height, 3)]})
    return rows


def merge(samples, interval, duration):
    """samples: [(time, rows)] in time order → spans; identical text on consecutive samples is one span."""
    open_spans, spans = {}, []
    for second, rows in samples:
        seen = set()
        for row in rows:
            key = row['text']
            seen.add(key)
            span = open_spans.get(key)
            if span:
                span['end'] = round(min(duration, second + interval / 2), 2)
                span['confidence'] = max(span['confidence'], row['confidence'])
            else:
                open_spans[key] = dict(start=round(max(0, second - interval / 2), 2), end=round(min(duration, second + interval / 2), 2),
                                       text=key, box=row['box'], confidence=row['confidence'])
        for key in [k for k in open_spans if k not in seen]:
            spans.append(open_spans.pop(key))
    spans.extend(open_spans.values())
    for span in spans:
        span['persistent'] = (span['end'] - span['start']) >= 0.8 * duration and duration > 4
    spans = _vote(spans)
    threshold = big_threshold(spans)
    for span in spans:
        span['layer'] = layer(span, threshold)
    return sorted(spans, key=lambda s: (s['start'], s['box'][1]))


WATERMARK = re.compile(r'(抖音号|快手号|小红书号|视频号|ID[:：]|@\S)')


def big_threshold(spans):
    """Author captions are the biggest text in a video, but sizes differ between videos: relative to the largest text box."""
    heights = [(s.get('box') or [0, 0, 0, 0])[3] for s in spans]
    return max(0.018, 0.65 * max(heights)) if heights else 0.018


def layer(span, threshold=0.024):
    """title: big text on screen the whole time; caption: big text that changes; watermark: account marks or small text that stays; ui: small passing text."""
    if WATERMARK.search(span.get('text') or ''):
        return 'watermark'
    if not span.get('box'):
        return 'watermark' if span.get('persistent') else 'caption'   # size unknown: the old rule
    big = span['box'][3] >= threshold - 1e-9
    if span.get('persistent'):
        return 'title' if big else 'watermark'
    return 'caption' if big else 'ui'


def _vote(spans):
    """Merge OCR variants of the same text at the same place (e.g. one misread character) and keep the most confident reading."""
    import difflib
    kept = []
    for span in sorted(spans, key=lambda s: -s['confidence']):
        for other in kept:
            near = abs(other['box'][1] - span['box'][1]) < 0.03 and abs(other['box'][0] - span['box'][0]) < 0.08
            overlap = span['start'] <= other['end'] and other['start'] <= span['end']
            if near and overlap and len(span['text']) >= 3 and difflib.SequenceMatcher(None, other['text'], span['text']).ratio() >= 0.6:
                other['start'], other['end'] = min(other['start'], span['start']), max(other['end'], span['end'])
                other['persistent'] = other['persistent'] or span['persistent']
                break
        else:
            kept.append(dict(span))
    return kept


def refine(path, spans, deadline, runner=subprocess.run, recognise=None, clock=time.monotonic):
    """Re-read at most twelve author-text crops; never lower the original confidence."""
    from PIL import Image
    stop = min(deadline, clock() + 15)
    candidates = [s for s in spans if s.get('layer') in ('title', 'caption') and
                  (s['confidence'] < .9 or re.search(r'\d|[A-Za-z]', s['text']))]
    candidates.sort(key=lambda s:(not bool(re.search(r'\d',s['text'])),s['layer']!='caption',-s['box'][3],s['confidence']))
    jobs=[]
    for span in candidates:
        jobs.append((span,(span['start']+span['end'])/2))
        if re.search(r'\d',span['text']) and span['end']-span['start']>.2:
            jobs.append((span,span['start']+(span['end']-span['start'])*.25))
    evidence={}
    for span,second in jobs[:12]:
        remaining = stop - clock()
        if remaining <= 0:
            break
        try:
            image = frame(path, second, height=None,
                          runner=runner, timeout=remaining)
            if image is None or clock() >= stop:
                continue
            w, h = image.size
            x, y, bw, bh = span['box']
            crop = image.crop((max(0, int((x - bw * .15) * w)), max(0, int((y - bh * .4) * h)),
                               min(w, int((x + bw * 1.15) * w)), min(h, int((y + bh * 1.4) * h))))
            if bh * h < 48:
                crop = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.LANCZOS)
            if recognise is None:
                # The subtitle box is already known: do not run a detector again.
                # A second detector can clip a narrow digit from its own text box.
                import numpy as np
                found, _ = engine().text_rec([np.array(crop)])
                rows = [{'text':str(text).strip()[:80],'confidence':round(float(score),6)}
                        for text, score in found if str(text).strip() and float(score)>=MIN_CONFIDENCE]
            else:
                rows = lines(crop, recognise)
            if clock() >= stop:
                break
            if len(rows) == 1 and rows[0]['confidence'] > span['confidence']:
                span.update(text=rows[0]['text'], confidence=rows[0]['confidence'], refined=True)
            elif len(rows)==1 and rows[0]['confidence']>=.9 and rows[0]['text']!=span['text']:
                new=rows[0]
                # User-approved exception: two independent crops corroborate a numeric correction.
                if re.search(r'\d',span['text']) and re.sub(r'\d+','#',span['text'])==re.sub(r'\d+','#',new['text']):
                    key=(id(span),span['text'],new['text'])
                    votes=evidence.setdefault(key,{})
                    votes[second]=new['confidence']
                    if len(votes)>=2:
                        span['refinement']={'from':span['text'],'to':new['text'],'by':'crop-consensus',
                                            'originalConfidence':span['confidence'],'confidences':list(votes.values()),'frameTimes':list(votes)}
                        span.update(text=new['text'],confidence=min(votes.values()),refined=True)
        except Exception:
            continue
    return spans


def extract(path, duration, budget_seconds=45.0, max_frames=24, height=540, runner=subprocess.run, recognise=None, clock=time.monotonic):
    """One ffmpeg pass writes all sample frames (much faster than seeking per frame), then OCR within a time budget."""
    from PIL import Image
    if recognise is None and not available():
        return {'status': 'unavailable', 'items': [], 'interval': None}
    _, interval = sample_times(duration, max_frames)
    started = clock()
    deadline, samples, status = started + budget_seconds, [], 'ready'
    scan_deadline = deadline - min(10, budget_seconds / 3)
    try:
        with tempfile.TemporaryDirectory(prefix='screen-text-') as root:
            runner([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-t', str(duration), '-i', str(path), '-an',
                    '-vf', 'fps=1/%s,scale=-2:%d' % (round(interval, 3), height), '-q:v', '3', str(Path(root) / '%04d.jpg')],
                   capture_output=True, timeout=max(.01, deadline - clock()))
            files = sorted(Path(root).glob('*.jpg'))[:max_frames]
            for index, file in enumerate(files):
                if clock() > scan_deadline:
                    status = 'partial'
                    break
                with Image.open(file) as image:
                    samples.append((round(index * interval + interval / 2, 2), lines(image.convert('RGB'), recognise)))
    except Exception:
        status = 'partial' if samples else 'unavailable'
    if not samples and status == 'ready':
        status = 'unavailable'
    refinement_started = clock()
    items = refine(path, merge(samples, interval, duration)[:120], deadline, runner, recognise, clock)
    return {'status': status, 'items': items, 'interval': round(interval, 2),
            'seconds':round(clock()-started,2), 'refinementSeconds':round(clock()-refinement_started,2),
            'coveredSeconds': round(min(duration, samples[-1][0] + interval / 2), 2) if samples else 0}


def author_text(result, limit=40):
    """Text the author put on screen (titles and captions), in time order; UI text and watermarks are left out."""
    items = (result or {}).get('items', [])
    threshold = big_threshold(items)
    rows = [s for s in items if (s.get('layer') or layer(s, threshold)) in ('title', 'caption')]
    return [{'start': s['start'], 'end': s['end'], 'text': s['text'], 'layer': s.get('layer') or layer(s, threshold)} for s in rows][:limit]


def as_context(result, limit=40):
    """Compact form handed to the model: the author's titles and captions (a persistent big title is kept, it is often the hook)."""
    return author_text(result, limit)
