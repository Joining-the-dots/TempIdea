# -*- coding: utf-8 -*-
"""Upsert a bank-group deep pass (verify/hsbc_asia.json, scb.json, anz.json ...) into private_wealth.json + pw_products.json.
Usage: python _hsbc_apply.py <path-to-group.json>   (group name + LBMA text taken from the file / entity)
"""
import json, os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pw_merge import norm, cp_short, region_of  # main guarded
HERE = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(sys.argv[1], encoding='utf-8'))
GROUP = src.get('group') or 'HSBC'; TAG = os.path.basename(sys.argv[1])
GKEY = GROUP.split()[0].lower()
PW = os.path.join(HERE, 'private_wealth.json'); PP = os.path.join(HERE, 'pw_products.json')
d = json.load(open(PW, encoding='utf-8')); pp = json.load(open(PP, encoding='utf-8'))
F = d['firms']; P = pp['products']
PT2CELL = {'gold_account_unallocated': 'metal_account_unallocated', 'gold_account_allocated': 'metal_account_allocated', 'physical_bullion': 'physical_bullion',
           'gold_savings_plan': 'gold_savings_plan', 'digital_gold_token': 'gold_savings_plan', 'gold_deposit_dci': 'gold_deposit_dci', 'structured_note': 'structured_notes',
           'otc_derivative': 'otc_derivatives', 'lombard_vs_metal': 'lombard_vs_metal', 'own_fund_etf': 'own_etf_etc', 'third_party_fund_etf': 'third_party_etf'}
PK = ['physical_bullion', 'metal_account_allocated', 'metal_account_unallocated', 'gold_savings_plan', 'gold_deposit_dci', 'structured_notes', 'otc_derivatives', 'lombard_vs_metal', 'own_etf_etc', 'third_party_etf', 'metal_funds']
added = updated = 0; prod_rows = 0
for ent in src.get('entities') or []:
    name = ent.get('entity') or ''; country = (ent.get('country') or '').split('/')[0].strip()
    key = norm(name)
    f = next((x for x in F if norm(x['firm']) == key), None)
    if not f:  # try to match an existing HSBC row for the same country
        f = next((x for x in F if GKEY in x['firm'].lower() and x['country'] == country and ('private' in x['firm'].lower()) == ('private' in name.lower())), None)
    prods = [p for p in (ent.get('products') or []) if isinstance(p, dict) and p.get('product_type') != 'none_found']
    if not f:
        f = {'firm': name, 'group': GROUP, 'country': country, 'region': region_of(country, 'APAC'), 'booking_centres': [], 'type': 'universal-bank PB arm',
             'client_assets_usd_bn': None, 'assets_year': None, 'products': {k: '?' for k in PK}, 'metals_covered': [], 'advisory_view': '', 'own_etf_detail': '', 'lombard_ltv': '',
             'product_evidence': [], 'counterparties': [], 'lbma_lppm_membership': ent.get('lbma_lppm_membership') or ('%s group: LBMA market maker' % GROUP), 'in_house_trading_desk': ent.get('in_house_trading_desk') or ('yes — %s group bullion desk' % GROUP),
             'citi_status': 'Citi not named', 'desk_angle': '', 'score': 6, 'confidence': 'verified', 'sources': [], 'src_file': TAG, 'is_pb': True}
        F.append(f); added += 1
    else: updated += 1
    f['firm'] = f['firm'] if f['firm'] else name
    f['is_pb'] = True; f['pass2'] = True; f['pass3'] = True; f['src_file'] = (f.get('src_file') or '') + ',' + TAG
    f['pb_arm_name'] = ent.get('pb_arm_name') or f.get('pb_arm_name') or name
    f['shelf_summary'] = ent.get('shelf_summary') or f.get('shelf_summary', '')
    if ent.get('gold_view'): f['advisory_view'] = ent['gold_view']; f['gold_view_p3'] = ent['gold_view']
    for p in prods:
        cell = PT2CELL.get(p.get('product_type'))
        if cell: f['products'][cell] = 'Y' if str(p.get('confidence', '')).startswith('ver') else ('Y?' if f['products'].get(cell) != 'Y' else 'Y')
        for m in p.get('metals') or []:
            if m not in f['metals_covered']: f['metals_covered'].append(m)
        if p.get('url') and p.get('quote'): f['product_evidence'].append({'claim': p.get('product_name', ''), 'quote': p['quote'], 'url': p['url']})
    f['n_products'] = len(prods)
    f['notional_indicators'] = ent.get('notional_indicators') or []
    f['none_found'] = not f['notional_indicators']
    f['size_band'] = ent.get('size_band') or f.get('size_band') or 'unknown'; f['size_band_key'] = next((k for k in ('very large', 'large', 'mid', 'small') if f['size_band'].lower().startswith(k)), 'unknown')
    f['size_band_basis'] = ent.get('size_band_basis') or f.get('size_band_basis', '')
    liq = ent.get('liquidity') or {}
    f['liquidity'] = {'status': liq.get('status') or 'in-house', 'providers': [(pv if isinstance(pv, dict) else {'name': str(pv), 'role': 'liquidity_provider', 'confidence': 'knowledge'}) for pv in (liq.get('providers') or [])], 'notes': liq.get('notes') or ''}
    f['trades_pm'] = 'yes-in-house-desk'
    have = {(c['name'].lower(), c['role']) for c in f['counterparties']}
    for pv in f['liquidity']['providers']:
        if pv.get('name') and (cp_short(pv['name']).lower(), 'liquidity_provider') not in have:
            f['counterparties'].append({'name': cp_short(pv['name']), 'name_full': pv['name'], 'role': 'liquidity_provider', 'evidence': pv.get('evidence', ''), 'url': pv.get('source_url', ''), 'confidence': pv.get('confidence', 'knowledge')})
    f['sources'] = sorted(set(f.get('sources') or []) | set(ent.get('sources') or []))
    if f.get('score', 0) < 6: f['score'] = 6
    # products: replace this firm's rows
    P[:] = [x for x in P if x['firm'] != f['firm']]
    for p in prods:
        P.append({'firm': f['firm'], 'firm_actual': name, 'pb_arm': f['pb_arm_name'], 'country': f['country'], 'region': f['region'], 'firm_type': f['type'], 'is_pb': True,
                  'score': f['score'], 'citi_status': f['citi_status'], 'product_name': str(p.get('product_name') or ''), 'product_type': p.get('product_type') or 'other',
                  'segment': str(p.get('segment') or '?'), 'metals': p.get('metals') or [], 'description': str(p.get('description') or ''), 'unit_and_minimum': str(p.get('unit_and_minimum') or '?'),
                  'fees': str(p.get('fees') or '?'), 'custody': str(p.get('custody') or '?'), 'physical_delivery': str(p.get('physical_delivery') or '?')[:1].upper(), 'currency': str(p.get('currency') or '?'),
                  'pricing_basis': str(p.get('pricing_basis') or '?'), 'shariah': str(p.get('shariah') or 'n/a'), 'url': str(p.get('url') or ''), 'quote': str(p.get('quote') or ''),
                  'confidence': 'verified' if str(p.get('confidence', '')).startswith('ver') else 'knowledge', 'notes': str(p.get('notes') or ''), 'src': TAG})
        prod_rows += 1
d.setdefault('stats', {}).setdefault('group_passes', {})[GKEY] = {'generated': src.get('generated'), 'search_count': src.get('search_count'), 'entities': len(src.get('entities') or []), 'group_indicators': src.get('group_indicators') or [], 'citi_angle': src.get('citi_angle', '')}
d['stats']['total'] = len(F); d['stats']['pb_arms'] = sum(1 for x in F if x.get('is_pb', True))
pp['products'] = sorted(P, key=lambda x: (-(x['score'] or 0), x['country'], x['pb_arm']))
pp['stats']['products'] = sum(1 for x in pp['products'] if x['product_type'] != 'none_found'); pp['stats']['verified'] = sum(1 for x in pp['products'] if x['confidence'] == 'verified' and x['product_type'] != 'none_found')
json.dump(d, open(PW, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); json.dump(pp, open(PP, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(GROUP, 'entities: added', added, 'updated', updated, '| product rows', prod_rows, '| firms now', len(F), '| products now', pp['stats']['products'])
