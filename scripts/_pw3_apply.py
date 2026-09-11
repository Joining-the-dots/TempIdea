"""Pass-3 join: pw3_*.json (advertised product catalogue of the private-bank / wealth arms) ->
pw_products.json (one row per product) + per-firm shelf fields written into private_wealth.json.
Usage: python _pw3_apply.py <dir-with-pw3_*.json>
"""
import glob, json, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pw_merge import norm  # main guarded

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
PW = os.path.join(HERE, 'private_wealth.json'); OUT = os.path.join(HERE, 'pw_products.json')
d = json.load(open(PW, encoding='utf-8'))
exact = {f['firm']: f for f in d['firms']}; idx = {norm(f['firm']): f for f in d['firms']}
PT = ['gold_account_unallocated', 'gold_account_allocated', 'physical_bullion', 'gold_savings_plan', 'digital_gold_token', 'gold_deposit_dci',
      'structured_note', 'otc_derivative', 'lombard_vs_metal', 'own_fund_etf', 'third_party_fund_etf', 'advisory_allocation', 'other', 'none_found']
PT_ALIAS = [(r'unalloc|paper|passbook|pool', 'gold_account_unallocated'), (r'alloc|segregat', 'gold_account_allocated'), (r'physical|bar|coin|bullion', 'physical_bullion'),
            (r'saving|accumul|plan|sip', 'gold_savings_plan'), (r'token|digital', 'digital_gold_token'), (r'deposit|dci|dual', 'gold_deposit_dci'),
            (r'structured|note|autocall|certificate', 'structured_note'), (r'otc|option|forward|accumulator|swap', 'otc_derivative'), (r'lombard|loan|lend|margin|credit', 'lombard_vs_metal'),
            (r'own.*(fund|etf)|in-house|house fund', 'own_fund_etf'), (r'third|3p|distribut|etf|fund', 'third_party_fund_etf'), (r'advis|allocation|view', 'advisory_allocation'), (r'none', 'none_found')]


def ptype(v):
    v = str(v or '').strip().lower().replace(' ', '_')
    if v in PT: return v
    for rx, k in PT_ALIAS:
        if re.search(rx, v): return k
    return 'other'


def yn(v):
    v = str(v or '?').strip().upper()
    return 'Y' if v.startswith('Y') else ('N' if v.startswith('N') else '?')


rows, hit, miss, searches, unmatched = [], 0, 0, 0, []
for fn in sorted(glob.glob(os.path.join(SRC, 'pw3_*.json'))):
    try: g = json.load(open(fn, encoding='utf-8'))
    except Exception as ex: print('SKIP', fn, ex); continue
    if not isinstance(g, dict): continue
    searches += int(g.get('search_count') or 0)
    for r in g.get('firms') or []:
        f = exact.get(r.get('firm')) or idx.get(norm(r.get('firm')))
        if not f:
            k = norm(r.get('firm'))[:25]; c = [v for kk, v in idx.items() if kk.startswith(k) or k.startswith(kk[:25])]
            f = c[0] if len(c) == 1 else None
        if not f: miss += 1; unmatched.append(r.get('firm')); continue
        hit += 1
        f['pass3'] = True
        f['pb_arm_name'] = r.get('pb_arm_name') or ''
        f['shelf_summary'] = r.get('shelf_summary') or ''
        f['gold_view_p3'] = r.get('gold_view') or ''
        f['partner_named'] = [p for p in (r.get('partner_named') or []) if p.get('name')]
        f['firm_actual'] = r.get('firm_actual') or f['firm']
        prods = [p for p in (r.get('products') or []) if isinstance(p, dict)]
        f['n_products'] = sum(1 for p in prods if ptype(p.get('product_type')) != 'none_found')
        for p in prods:
            rows.append({
                'firm': f['firm'], 'firm_actual': f['firm_actual'], 'pb_arm': f['pb_arm_name'] or f['firm_actual'], 'country': f['country'], 'region': f['region'],
                'firm_type': f['type'], 'is_pb': f.get('is_pb', True), 'score': f.get('score'), 'citi_status': f.get('citi_status', ''),
                'product_name': str(p.get('product_name') or '').strip(), 'product_type': ptype(p.get('product_type')),
                'segment': str(p.get('segment') or '?'), 'metals': p.get('metals') or [], 'description': str(p.get('description') or ''),
                'unit_and_minimum': str(p.get('unit_and_minimum') or '?'), 'fees': str(p.get('fees') or '?'), 'custody': str(p.get('custody') or '?'),
                'physical_delivery': yn(p.get('physical_delivery')), 'currency': str(p.get('currency') or '?'), 'pricing_basis': str(p.get('pricing_basis') or '?'),
                'shariah': str(p.get('shariah') or 'n/a'), 'url': str(p.get('url') or ''), 'quote': str(p.get('quote') or ''),
                'confidence': 'verified' if str(p.get('confidence', '')).lower().startswith('ver') else 'knowledge', 'notes': str(p.get('notes') or ''),
            })
        if r.get('sources'): f['sources'] = sorted(set(f.get('sources') or []) | set(r['sources']))

rows.sort(key=lambda x: (-(x['score'] or 0), x['country'], x['pb_arm'], PT.index(x['product_type']) if x['product_type'] in PT else 99))
st = {'generated': datetime.date.today().isoformat(), 'firms_joined': hit, 'unmatched': miss, 'search_count': searches,
      'products': sum(1 for x in rows if x['product_type'] != 'none_found'), 'none_found_firms': sum(1 for x in rows if x['product_type'] == 'none_found'),
      'verified': sum(1 for x in rows if x['confidence'] == 'verified' and x['product_type'] != 'none_found'),
      'by_type': {}, 'by_region': {}, 'by_segment': {}}
for x in rows:
    if x['product_type'] == 'none_found': continue
    st['by_type'][x['product_type']] = st['by_type'].get(x['product_type'], 0) + 1
    st['by_region'][x['region']] = st['by_region'].get(x['region'], 0) + 1
    seg = x['segment'].split('/')[0].strip().lower()[:24]; st['by_segment'][seg] = st['by_segment'].get(seg, 0) + 1
json.dump({'generated': st['generated'], 'stats': st, 'products': rows}, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
d['stats']['pass3'] = st
json.dump(d, open(PW, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('joined', hit, 'firms; unmatched', miss, unmatched[:8]); print(json.dumps({k: st[k] for k in ('products', 'verified', 'none_found_firms', 'search_count')}), json.dumps(st['by_type']))
