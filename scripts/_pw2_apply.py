"""Pass-2 enrichment join: pw2_*.json (notional indicators + liquidity providers) -> private_wealth.json.
Usage: python _pw2_apply.py <dir-with-pw2_*.json>
Adds per firm: notional_indicators[], none_found, size_band, size_band_basis, liquidity{status,providers,notes},
trades_pm, new_products_found[], pass2 (bool). Liquidity providers are also appended to counterparties[] (deduped).
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pw_merge import cp_short, norm  # noqa

SRC = sys.argv[1]
PW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'private_wealth.json')
d = json.load(open(PW, encoding='utf-8'))
idx = {norm(f['firm']): f for f in d['firms']}
exact = {f['firm']: f for f in d['firms']}
ROLE_MAP = {'liquidity_provider': 'liquidity_provider', 'bullion_supplier': 'bullion_supplier', 'hedge_counterparty': 'liquidity_provider',
            'authorised_participant': 'liquidity_provider', 'custodian': 'custodian_vault', 'refiner': 'refiner'}
SIZE_RANK = {'very large': 4, 'large': 3, 'mid': 2, 'small': 1, 'unknown': 0}

hit = miss = 0; searches = 0; unmatched = []
for fn in sorted(glob.glob(os.path.join(SRC, 'pw2_*.json'))):
    try: g = json.load(open(fn, encoding='utf-8'))
    except Exception as ex: print('SKIP', fn, ex); continue
    if not isinstance(g, dict): continue
    searches += int(g.get('search_count') or 0)
    for r in g.get('firms') or []:
        f = exact.get(r.get('firm')) or idx.get(norm(r.get('firm')))
        if not f:
            # fuzzy: first 25 chars
            k = norm(r.get('firm'))[:25]
            cands = [v for kk, v in idx.items() if kk.startswith(k) or k.startswith(kk[:25])]
            f = cands[0] if len(cands) == 1 else None
        if not f: miss += 1; unmatched.append(r.get('firm')); continue
        hit += 1
        f['pass2'] = True
        f['notional_indicators'] = [x for x in (r.get('notional_indicators') or []) if x.get('value') or x.get('metric')]
        f['none_found'] = bool(r.get('none_found')) and not f['notional_indicators']
        sb = str(r.get('size_band') or 'unknown')
        f['size_band'] = sb; f['size_band_key'] = next((k for k in SIZE_RANK if sb.lower().startswith(k)), 'unknown')
        f['size_band_basis'] = r.get('size_band_basis') or ''
        liq = r.get('liquidity') or {}
        f['liquidity'] = {'status': liq.get('status') or 'undisclosed', 'providers': liq.get('providers') or [], 'notes': liq.get('notes') or ''}
        f['trades_pm'] = r.get('trades_pm') or ''
        f['new_products_found'] = r.get('new_products_found') or []
        if r.get('sources'): f['sources'] = sorted(set(f.get('sources') or []) | set(r['sources']))
        have = {(c['name'].lower(), c['role']) for c in f['counterparties']}
        for p in f['liquidity']['providers']:
            if not p.get('name'): continue
            role = ROLE_MAP.get(p.get('role'), 'other'); short = cp_short(p['name'])
            if (short.lower(), role) in have: continue
            f['counterparties'].append({'name': short, 'name_full': p['name'], 'role': role, 'evidence': p.get('evidence', ''),
                                        'url': p.get('source_url', ''), 'confidence': p.get('confidence', 'knowledge'), 'pass2': True})
            have.add((short.lower(), role))

st = d.setdefault('stats', {})
st['pass2_firms'] = sum(1 for f in d['firms'] if f.get('pass2'))
st['pass2_searches'] = searches
st['pass2_with_notional'] = sum(1 for f in d['firms'] if f.get('notional_indicators'))
st['pass2_liquidity'] = {}
for f in d['firms']:
    if f.get('pass2'):
        s = f['liquidity']['status']; st['pass2_liquidity'][s] = st['pass2_liquidity'].get(s, 0) + 1
st['pass2_size_bands'] = {}
for f in d['firms']:
    if f.get('pass2'):
        s = f.get('size_band_key', 'unknown'); st['pass2_size_bands'][s] = st['pass2_size_bands'].get(s, 0) + 1
# recompute counterparty tally (pass-2 providers count)
tally = {}
for f in d['firms']:
    for c in f['counterparties']:
        if c['name'] != 'undisclosed': tally.setdefault(c['name'], set()).add(f['firm'])
st['top_counterparties'] = sorted(((k, len(v)) for k, v in tally.items()), key=lambda x: -x[1])[:40]
json.dump(d, open(PW, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('joined', hit, 'firms; unmatched', miss, unmatched[:10])
print('pass2 stats', {k: st[k] for k in ('pass2_firms', 'pass2_searches', 'pass2_with_notional', 'pass2_liquidity', 'pass2_size_bands')})
