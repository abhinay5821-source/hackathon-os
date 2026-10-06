"""Narrow fixed-camera baseline; visible changes are not proof of fraud."""
import argparse
from collections import deque
from html import escape
import json
from pathlib import Path
import cv2
import numpy as np


def snapshot(path):
    cap = cv2.VideoCapture(str(path))
    frames = deque(maxlen=5)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
            frame_count += 1
    finally:
        cap.release()
    if not frames or fps <= 0:
        raise ValueError(f'Unreadable video: {path}')
    shapes = {f.shape for f in frames}
    if len(shapes) != 1:
        raise ValueError('Inconsistent frame dimensions')
    # Final stable view: hand movement earlier in a clip is outside this scope.
    tail = list(frames)
    stable = max(
        float(np.mean(cv2.absdiff(tail[index - 1], tail[index])))
        for index in range(1, len(tail))
    ) if len(tail) > 1 else 0.0
    return np.median(tail, axis=0).astype(np.uint8), (frame_count-1)/fps, stable


def write_review_page(output, result):
    reasons = ''.join(f'<li>{escape(reason)}</li>' for reason in result['uncertainty_reasons'])
    status = escape(result['status'].replace('_', ' ').title())
    html = f'''<!doctype html><meta charset="utf-8"><title>ParcelProof review</title>
<style>body{{font:16px system-ui;max-width:960px;margin:40px auto;padding:0 20px;background:#101418;color:#edf2f7}}.notice{{background:#342b08;padding:16px;border-left:5px solid #f4c542}}.frames{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}img{{width:100%}}code{{color:#9ae6b4}}</style>
<h1>ParcelProof review</h1><p class="notice"><strong>{status}</strong> — visible evidence only. A human must review it; this page does not establish fraud or item identity.</p>
<p>Packing: <code>{result['packing_seconds']:.3f}s</code> · Return: <code>{result['return_seconds']:.3f}s</code> · Changed regions: <code>{len(result['changed_regions'])}</code></p>
<ul>{reasons or '<li>No uncertainty guard fired.</li>'}</ul>
<div class="frames"><figure><img src="packing.png"><figcaption>Packing evidence</figcaption></figure><figure><img src="returned.png"><figcaption>Return evidence with visible-change boxes</figcaption></figure></div>
<p>Synthetic evaluation is not real-world validation.</p>'''
    (output/'review.html').write_text(html + '\n', encoding='utf-8')


def analyze(packing, returned, output):
    if Path(packing).resolve() == Path(returned).resolve():
        raise ValueError('Two different recordings are required')
    a, ta, stable_a = snapshot(packing)
    b, tb, stable_b = snapshot(returned)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    reasons = []
    if a.shape != b.shape:
        reasons.append('Frame dimensions differ; alignment unavailable')
    if max(stable_a, stable_b) > 3:
        reasons.append('Final view is not stable')
    for f in (a, b):
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if np.mean(gray) < 45:
            reasons.append('Insufficient lighting')
        # Conservative guard for broad obstruction of the calibrated background.
        if np.mean(gray < 55) > .30:
            reasons.append('Possible broad occlusion')
    boxes = []
    if not reasons:
        ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
        gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
        # Background border is the alignment check, not inferred camera registration.
        border = np.ones(ga.shape, dtype=bool)
        border[20:-20, 20:-20] = False
        border_delta = cv2.absdiff(ga, gb)[border]
        newly_dark = (gb < 55) & (ga >= 55)
        dark_contours, _ = cv2.findContours(newly_dark.astype(np.uint8)*255,
                                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if any(cv2.contourArea(c) >= 400 for c in dark_contours):
            reasons.append('Possible localized obstruction or dark object; identity unresolved')
        if np.mean(border_delta > 20) > .002:
            reasons.append('Background changed; fixed-camera alignment unverified')
        if not reasons:
            mask = (cv2.absdiff(a,b).max(axis=2) > 35).astype(np.uint8)*255
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) >= 100:
                    boxes.append(list(cv2.boundingRect(c)))
    annotated = b.copy()
    for x,y,w,h in boxes:
        cv2.rectangle(annotated,(x,y),(x+w,y+h),(0,0,255),2)
    cv2.imwrite(str(out/'packing.png'), a)
    cv2.imwrite(str(out/'returned.png'), annotated)
    result = {'status': 'uncertain' if reasons else ('review_required' if boxes else 'no_discrepancy_observed'),
              'packing_seconds': ta, 'return_seconds': tb, 'changed_regions': boxes,
              'uncertainty_reasons': sorted(set(reasons)), 'opencv_version': cv2.__version__,
              'tail_motion_score': {'packing': stable_a, 'returned': stable_b},
              'evidence_frames': ['packing.png','returned.png'], 'review_page': 'review.html',
              'limitations': ['Calibrated fixed camera and stable final view only',
                              'Visible change only: no item identity, damage or fraud determination',
                              'Local occlusion and camera shifts may evade these conservative guards',
                              'Synthetic evaluation is not real-world validation']}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    write_review_page(out, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('packing'); p.add_argument('returned'); p.add_argument('--output',default='evidence')
    args=p.parse_args()
    try:
        print(json.dumps(analyze(args.packing,args.returned,args.output),indent=2))
    except ValueError as e:
        p.exit(2,str(e)+'\n')

if __name__ == '__main__':
    main()
