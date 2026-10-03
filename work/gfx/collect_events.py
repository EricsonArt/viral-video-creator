#!/usr/bin/env python3
import json, re, os
G = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(G)
plan = json.load(open(os.path.join(W, 'plan.json')))
start = {r['id']: r['start'] for r in plan['runs']}
scene_run = {'r1': 'R1', 'r3': 'R3', 'r5': 'R5', 'r7': 'R7', 'r8': 'R8'}
out = []
for sc, rid in scene_run.items():
    h = open(os.path.join(G, 'scenes', sc + '.html'), encoding='utf8').read()
    m = re.search(r'<script type="application/json" id="events">(.*?)</script>', h, re.S)
    for e in json.loads(m.group(1)):
        e = dict(e); e['t'] = round(start[rid] + e['t'], 4); e['run'] = rid; out.append(e)
h = open(os.path.join(G, 'scenes', 'overlay.tpl.html'), encoding='utf8').read()
m = re.search(r'<script type="application/json" id="events">(.*?)</script>', h, re.S)
for e in json.loads(m.group(1)):
    e = dict(e); e['run'] = 'R9'; out.append(e)
out.sort(key=lambda e: e['t'])
json.dump(out, open(os.path.join(W, 'events.json'), 'w'), indent=1)
for e in out: print(f"{e['t']:8.3f}  {e['run']}  {e['type']:12s} {e.get('note','')}")
