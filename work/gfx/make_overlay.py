#!/usr/bin/env python3
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plan = json.load(open(os.path.join(W, 'plan.json')))
END = plan['end']
runs = plan['runs']
ZONE = {'R1': 1027, 'R2': 1400, 'R3': 1027, 'R4': 430, 'R5': 1400, 'R6': 430, 'R7': 1027, 'R8': 1400, 'R9': 430}
# split chunks that straddle a run boundary so the position jumps exactly at the cut
items = []
for c in plan['chunks']:
    for r in runs:
        a, b = max(c['start'], r['start']), min(c['end'], r['end'])
        if b - a > 0.004:
            items.append(dict(words=c['words'], start=a if a > 0 else 0.0, end=b, y=ZONE[r['id']], run=r['id']))
# the first caption appears on frame 1 (16.7 ms): frame 0 stays clean for the cover
items[0]['start'] = 0.0166
data = dict(END=END, items=items)
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes', 'overlay.tpl.html'), encoding='utf8').read()
html = html.replace('%%DATA%%', json.dumps(data, ensure_ascii=False)).replace('%%DUR%%', f'{END:.4f}').replace('%%CTA_T0%%','39.25').replace('%%CTA_TYPE0%%','39.98').replace('%%CTA_POST%%','40.66')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes', 'overlay.html'), 'w', encoding='utf8').write(html)
print(len(items), 'caption items')
