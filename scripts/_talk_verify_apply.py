# -*- coding: utf-8 -*-
"""Stamp the fact-check verdicts (verify/verified_*.json) onto pw_talking_points.html by claim id (data-cid).
The talk text already incorporates every correction; the badge shows the verdict the checker returned for the
ORIGINAL claim so the audience can see what was re-checked. cid=0 lines are badged "sourced, not re-checked".
Usage: python _talk_verify_apply.py <verify-dir>
"""
import re, json, glob, html, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); VD = sys.argv[1]
src = os.path.join(HERE, 'pw_talking_points.html'); s = open(src, encoding='utf-8').read()
res = {}
for fn in glob.glob(os.path.join(VD, 'verified_*.json')):
    try:
        for r in json.load(open(fn, encoding='utf-8')).get('results', []): res[int(r['id'])] = r
    except Exception as ex: print('SKIP', fn, ex)
BADGE = {'confirmed': ('&#10003; verified', '#0a7d22', '#e3f5e8'), 'corrected': ('&#9998; corrected in text', '#8a6d00', '#fff3cd'),
         'partly': ('&#9684; partly verified, text amended', '#8a6d00', '#fff3cd'), 'unsupported': ('&#9888; not independently supported', '#b3261e', '#fde8e6'),
         'new': ('&#9679; sourced, not re-checked', '#0b4a9c', '#e8f0fe'), '': ('? not checked', '#888', '#f0f0f0')}
def badge(v, r):
    l, c, b = BADGE.get(v, BADGE[''])
    tip = html.escape(((r or {}).get('found_quote') or (r or {}).get('notes') or '')[:300])
    return ' <span class="pwt-b" style="color:%s;background:%s" title="%s">%s</span>' % (c, b, tip, l)
n = {'stamped': 0}
def li_sub(m):
    cid = int(m.group(1)); inner = m.group(2); r = res.get(cid)
    v = 'new' if cid == 0 else (r.get('verdict', '') if r else '')
    pu = (r or {}).get('primary_url') or ''
    extra = (' <a href="%s" target="_blank" rel="noopener">checked</a>' % html.escape(pu)) if pu and pu not in inner else ''
    n['stamped'] += 1
    return '<li data-cid="%d">%s%s%s</li>' % (cid, inner, extra, badge(v, r))
s = re.sub(r'<li data-cid="(\d+)">(.*?)</li>', li_sub, s, flags=re.S)
def tr_sub(m):
    cid = int(m.group(1)); r = res.get(cid); v = 'new' if cid == 0 else (r.get('verdict', '') if r else '')
    n['stamped'] += 1
    return '<tr data-cid="%d"><td><b>%s</b><div class="pwt-m">%s</div>%s</td>' % (cid, m.group(2), m.group(3), badge(v, r))
s = re.sub(r'<tr data-cid="(\d+)"><td><b>(.*?)</b><div class="pwt-m">(.*?)</div></td>', tr_sub, s, flags=re.S)
counts = {}
for r in res.values(): counts[r.get('verdict', '?')] = counts.get(r.get('verdict', '?'), 0) + 1
summary = ('<p class="pwt-lede" style="border-left:3px solid #1f5b8d;padding-left:8px"><b>Fact-check:</b> %d claims in this talk were re-checked against primary sources by an adversarial pass (%s). '
           'Every correction is already written into the text; the badge on each line shows what the checker found for the original wording (hover for the quote). '
           'Lines marked <i>not independently supported</i> are our own findings or figures the checker could not reach; treat them as such on a slide.</p>') % (
    len(res), ', '.join('%s %d' % (k, v) for k, v in sorted(counts.items(), key=lambda z: -z[1])))
s = s.replace('<div class="pwt-run">', summary + '<div class="pwt-run">', 1)
open(src, 'w', encoding='utf-8').write(s)
print('verdicts loaded', len(res), '| lines stamped', n['stamped'], '| verdicts', counts)
