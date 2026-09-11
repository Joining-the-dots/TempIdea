# -*- coding: utf-8 -*-
"""Render private_wealth.json into the shareable "Private Wealth Metals Map" report page.
Usage: python _pw_report.py <out.html>
"""
import json, os, sys, html, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'private_wealth_report.html')
d = json.load(open(os.path.join(HERE, 'private_wealth.json'), encoding='utf-8'))
F = d['firms']; ST = d['stats']
try:
    PRODS = [x for x in json.load(open(os.path.join(HERE, 'pw_products.json'), encoding='utf-8'))['products'] if x.get('product_type') != 'none_found']
except Exception:
    PRODS = []
PTL = {'gold_account_unallocated': 'Gold account (unallocated)', 'gold_account_allocated': 'Metal account (allocated)', 'physical_bullion': 'Physical bars / coins',
       'gold_savings_plan': 'Savings / accumulation plan', 'digital_gold_token': 'Digital gold / token', 'gold_deposit_dci': 'Gold deposit / DCI',
       'structured_note': 'Structured note', 'otc_derivative': 'OTC derivative', 'lombard_vs_metal': 'Lombard vs metal', 'own_fund_etf': 'Own fund / ETF',
       'third_party_fund_etf': 'Third-party fund / ETF', 'advisory_allocation': 'Advisory allocation', 'other': 'Other'}
e = lambda s: html.escape(str(s if s is not None else ''))

PK = [('physical_bullion', 'Physical', 'Physical bullion (bars/coins) sold to clients'),
      ('metal_account_allocated', 'Alloc', 'Allocated / segregated metal account'),
      ('metal_account_unallocated', 'Unalloc', 'Unallocated / pool / passbook account'),
      ('gold_savings_plan', 'Savings', 'Gold savings plan / gram accumulation / digital gold'),
      ('gold_deposit_dci', 'Depo', 'Gold-linked deposit / dual-currency-style deposit'),
      ('structured_notes', 'Notes', 'Gold/silver-linked structured notes'),
      ('otc_derivatives', 'OTC', 'OTC forwards / options / accumulators for HNW'),
      ('lombard_vs_metal', 'Lombard', 'Lombard / margin lending against bullion or metal'),
      ('own_etf_etc', 'Own ETF', 'Sponsors its own physical-metal ETF / ETC'),
      ('third_party_etf', '3P ETF', 'Distributes third-party metal ETFs'),
      ('metal_funds', 'Funds', 'Own precious-metal / mining funds')]
ROLE = {'bullion_supplier': 'bullion supplier', 'liquidity_provider': 'liquidity provider', 'custodian_vault': 'custodian / vault',
        'etf_custodian': 'ETF custodian', 'refiner': 'refiner', 'note_issuer': 'note issuer', 'account_partner': 'account partner',
        'clearing_lpmcl': 'clearing', 'other': 'other'}
REG_NAME = {'EMEA': 'EMEA', 'APAC': 'APAC', 'NAM': 'North America', 'LATAM': 'Latin America'}


def citi_cls(v):
    v = str(v or '').lower()
    if v.startswith('reference franchise'): return ('citi', 'Ref.')
    if 'reference bank named' in v: return ('in', 'Named')
    if 'not named' in v: return ('out', 'Not named')
    return ('unk', '?')


def cell(v):
    v = str(v or '?')
    return '<td class="c c-%s" title="%s">%s</td>' % ({'Y': 'y', 'Y?': 'yq', 'N': 'n'}.get(v, 'u'), e(v), e(v))


def cp_short_list(f, n=5):
    seen, out = set(), []
    for c in f['counterparties']:
        nm = c['name']
        if nm in seen or nm == 'undisclosed': continue
        seen.add(nm); out.append('<span class="cp%s">%s</span>' % ('' if c.get('confidence') == 'verified' else ' cp-k', e(nm)))
    und = sum(1 for c in f['counterparties'] if c['name'] == 'undisclosed')
    s = ', '.join(out[:n]) + (' <span class="mute">+%d</span>' % (len(out) - n) if len(out) > n else '')
    if und and not out: s = '<span class="mute">undisclosed</span>'
    elif und: s += ' <span class="mute">(+%d undisclosed)</span>' % und
    return s or '<span class="mute">—</span>'


TP = {'yes-in-house-desk': ('in-house desk', 'tp-desk'), 'yes-price-taker': ('price-taker', 'tp-pt'), 'distributes-only': ('distributes only', 'tp-dist'), 'no': ('no PM', 'tp-no')}
LQ = {'named-verified': 'lq-v', 'named-knowledge': 'lq-k', 'in-house': 'lq-i', 'undisclosed': 'lq-u', 'n/a': 'lq-na'}


def p2cell(f):
    if not f.get('pass2'): return '<td class="p2 mute">—</td>'
    tp = str(f.get('trades_pm') or ''); tl, tc = TP.get(tp, (tp or '?', 'tp-dist'))
    ni = f.get('notional_indicators') or []; top = ni[0] if ni else None
    sz = '<b>%s</b>' % e(f.get('size_band_key') or 'unknown')
    if top: sz += ' <span class="mono">%s %s</span>' % (e(str(top.get('value', ''))[:16]), e(str(top.get('unit', ''))[:10]))
    elif f.get('none_found'): sz += ' <span class="mute">nothing public</span>'
    lq = f.get('liquidity') or {}; ls = str(lq.get('status') or '?')
    names = [str(p.get('name', ''))[:24] for p in (lq.get('providers') or []) if p.get('name')][:3]
    return '<td class="p2"><div class="%s">%s</div><div>%s</div><div><span class="%s">%s</span>%s</div></td>' % (tc, e(tl), sz, LQ.get(ls, 'lq-na'), e(ls), (' ' + e(', '.join(names))) if names else '')


def p2detail(f):
    if not f.get('pass2'): return ''
    out = ['<h4>Size and liquidity (pass 2)</h4>']
    out.append('<p><b>Size band:</b> %s <span class="mute">%s</span></p>' % (e(f.get('size_band') or 'unknown'), e(str(f.get('size_band_basis') or '')[:300])))
    ni = f.get('notional_indicators') or []
    if ni:
        out.append('<ul class="ev">')
        for n in ni[:8]:
            out.append('<li><b>%s</b>: <span class="mono">%s %s</span>%s%s%s</li>' % (e(str(n.get('metric', ''))[:90]), e(str(n.get('value', ''))[:40]), e(str(n.get('unit', ''))[:20]),
                (' <span class="mute">(%s)</span>' % e(str(n.get('as_of', ''))[:24])) if n.get('as_of') else '',
                (' <q>%s</q>' % e(str(n.get('quote', ''))[:260])) if n.get('quote') else '',
                (' <a href="%s" target="_blank" rel="noopener">source</a>' % e(n['source_url'])) if n.get('source_url') else ''))
        out.append('</ul>')
    elif f.get('none_found'): out.append('<p class="mute">No public size or notional figure found.</p>')
    lq = f.get('liquidity') or {}
    out.append('<p><b>Liquidity / physical provider:</b> <span class="%s">%s</span>%s</p>' % (LQ.get(str(lq.get('status')), 'lq-na'), e(lq.get('status') or '?'), (' — ' + e(str(lq.get('notes') or '')[:400])) if lq.get('notes') else ''))
    if lq.get('providers'):
        out.append('<ul class="cps">')
        for p in lq['providers'][:8]:
            out.append('<li><b>%s</b> <span class="role">%s</span>%s%s%s</li>' % (e(str(p.get('name', ''))[:70]), e(str(p.get('role', ''))),
                ' <span class="tag-k">unverified</span>' if p.get('confidence') != 'verified' else '',
                (' — %s' % e(str(p.get('evidence', ''))[:320])) if p.get('evidence') else '',
                (' <a href="%s" target="_blank" rel="noopener">source</a>' % e(p['source_url'])) if p.get('source_url') else ''))
        out.append('</ul>')
    if f.get('new_products_found'): out.append('<p><b>New products found:</b> %s</p>' % e('; '.join(str(v) for v in f['new_products_found'])[:400]))
    return ''.join(out)


def detail(f):
    p = f['products']
    parts = ['<div class="det">']
    parts.append('<div class="det-meta">%s · %s · booking: %s · confidence: %s%s</div>' % (
        e(f['type']), e(f['country']), e(', '.join(f['booking_centres']) or '?'), e(f['confidence']),
        (' · client assets US$%sbn' % e(f['client_assets_usd_bn'])) if f.get('client_assets_usd_bn') else ''))
    if f.get('strategic_idea'): parts.append('<p class="angle"><b>Strategic idea.</b> %s</p>' % e(f['strategic_idea']))
    parts.append(p2detail(f))
    kv = []
    if f.get('metals_covered'): kv.append(('Metals', ', '.join(map(str, f['metals_covered']))))
    if f.get('in_house_trading_desk'): kv.append(('In-house bullion desk', f['in_house_trading_desk']))
    if f.get('lbma_lppm_membership'): kv.append(('LBMA / LPPM', f['lbma_lppm_membership']))
    if f.get('own_etf_detail'): kv.append(('Own ETF / ETC', f['own_etf_detail']))
    if f.get('lombard_ltv'): kv.append(('Lombard LTV', f['lombard_ltv']))
    if f.get('advisory_view'): kv.append(('House view on gold', f['advisory_view']))
    kv.append(('Reference-bank status', f['ref_bank_status']))
    parts.append('<dl class="kv">' + ''.join('<dt>%s</dt><dd>%s</dd>' % (e(k), e(str(v)[:400])) for k, v in kv) + '</dl>')
    if f['counterparties']:
        parts.append('<h4>Works with</h4><ul class="cps">')
        for c in f['counterparties']:
            nf = str(c.get('name_full') or '')
            parts.append('<li><b>%s</b>%s <span class="role">%s</span>%s%s%s</li>' % (
                e(c['name']), (' <span class="mute">%s</span>' % e(nf[:140])) if nf and nf != c['name'] else '', e(ROLE.get(c.get('role'), 'other')),
                ' <span class="tag-k">unverified</span>' if c.get('confidence') != 'verified' else '',
                (' — %s' % e(str(c.get('evidence', ''))[:360])) if c.get('evidence') else '',
                (' <a href="%s" target="_blank" rel="noopener">source</a>' % e(c['url'])) if c.get('url') else ''))
        parts.append('</ul>')
    ev = f.get('product_evidence') or []
    if ev:
        parts.append('<h4>Product evidence</h4><ul class="ev">')
        for x in ev[:6]:
            parts.append('<li>%s%s%s</li>' % (e(str(x.get('claim', ''))[:220]),
                                              (' <q>%s</q>' % e(str(x.get('quote', ''))[:320])) if x.get('quote') else '',
                                              (' <a href="%s" target="_blank" rel="noopener">source</a>' % e(x['url'])) if x.get('url') else ''))
        parts.append('</ul>')
    if f.get('sources'):
        parts.append('<p class="src">Sources: ' + ' · '.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(u), e(re.sub(r'^https?://(www\.)?', '', str(u))[:42])) for u in f['sources'][:8]) + '</p>')
    parts.append('</div>')
    return ''.join(parts)


def row(f, rank=None):
    p = f['products']; cc, cl = citi_cls(f['ref_bank_status'])
    ykeys = ' '.join(k for k, _, _ in PK if p.get(k) in ('Y', 'Y?'))
    aum = f.get('client_assets_usd_bn')
    aums = ('<span class="mute mono">US$%sbn</span>' % ('{:,.0f}'.format(float(aum)) if float(aum) >= 10 else aum)) if isinstance(aum, (int, float)) else ''
    return ('<tr class="r" data-region="%s" data-country="%s" data-type="%s" data-p="%s" data-citi="%s" data-score="%s" data-pb="%s" tabindex="0">'
            '<td class="fm"><b>%s</b>%s%s</td><td class="ct">%s</td>%s%s<td class="ww">%s</td><td class="ci"><span class="pill pill-%s">%s</span></td><td class="sc mono">%s</td></tr>'
            '<tr class="x" hidden><td colspan="%d">%s</td></tr>') % (
        e(f['region']), e(f['country']), e(f['type']), ykeys, cc, f.get('score') or 0, '1' if f.get('is_pb', True) else '0',
        e(f['firm']), ('<div class="mute">%s</div>' % e(f['group'])) if f.get('group') and f['group'] != f['firm'] else '', ('<div>%s</div>' % aums) if aums else '',
        e(f['country']), p2cell(f), ''.join(cell(p.get(k)) for k, _, _ in PK), cp_short_list(f), cc, cl, e(f.get('score') or ''), len(PK) + 6, detail(f))


# ---- product catalogue
def prow(x):
    mets = ', '.join(str(m) for m in (x.get('metals') or []))
    url = x.get('url') or ''
    det = '<div class="det">'
    if x.get('description'): det += '<p class="angle">%s</p>' % e(str(x['description'])[:700])
    kv = [(lab, x.get(k)) for lab, k in (('Unit / minimum', 'unit_and_minimum'), ('Fees', 'fees'), ('Custody', 'custody'), ('Pricing basis', 'pricing_basis'), ('Currency', 'currency'), ('Shariah', 'shariah'), ('Notes', 'notes')) if x.get(k) and str(x.get(k)) not in ('?', 'n/a')]
    if kv: det += '<dl class="kv">' + ''.join('<dt>%s</dt><dd>%s</dd>' % (e(k), e(str(v)[:400])) for k, v in kv) + '</dl>'
    if x.get('quote'): det += '<p><q>%s</q></p>' % e(str(x['quote'])[:300])
    if url: det += '<p class="src">Source: <a href="%s" target="_blank" rel="noopener">%s</a></p>' % (e(url), e(re.sub(r'^https?://(www\.)?', '', url)[:90]))
    det += '<p class="src">Firm row: %s · %s</p>' % (e(x.get('firm_actual') or x.get('firm')), e(x.get('firm_type') or ''))
    det += '</div>'
    return ('<tr class="r" data-region="%s" data-country="%s" data-ptype="%s" data-seg="%s" data-conf="%s" data-metals="%s" tabindex="0">'
            '<td class="fm"><b>%s</b><div class="mute">%s</div></td><td><b>%s</b>%s</td><td><span class="ptype">%s</span></td><td class="ct">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="sc">%s</td></tr>'
            '<tr class="x" hidden><td colspan="10">%s</td></tr>') % (
        e(x.get('region') or ''), e(x.get('country') or ''), e(x.get('product_type') or ''), e(str(x.get('segment') or '').lower()[:40]), e(x.get('confidence') or ''), e('|'.join(str(m) for m in x.get('metals') or [])),
        e(str(x.get('pb_arm') or '')[:60]), e(x.get('country') or ''), e(str(x.get('product_name') or '')[:80]), '' if x.get('confidence') == 'verified' else ' <span class="tag-k">knowledge</span>',
        e(PTL.get(x.get('product_type'), x.get('product_type'))), e(str(x.get('segment') or '')[:30]), e(mets), e(str(x.get('unit_and_minimum') or '?')[:70]), e(str(x.get('fees') or '?')[:80]), e(str(x.get('custody') or '?')[:70]), e(x.get('physical_delivery') or '?'), det)


n_prod = len(PRODS); n_prod_firms = len({x['firm'] for x in PRODS}); n_prod_ver = sum(1 for x in PRODS if x.get('confidence') == 'verified')
ptypes = collections.Counter(x['product_type'] for x in PRODS)
ptype_boxes = ''.join('<label><input type="checkbox" value="%s"> %s <span class="mono mute">%d</span></label>' % (t, e(PTL.get(t, t)), n) for t, n in ptypes.most_common())
pmetals = collections.Counter(str(m) for x in PRODS for m in (x.get('metals') or []))
pmetal_boxes = ''.join('<label><input type="checkbox" value="%s"> %s <span class="mono mute">%d</span></label>' % (e(m), e(m), n) for m, n in pmetals.most_common())
pcountries = sorted({x['country'] for x in PRODS if x.get('country')})
p_thead = '<tr><th class="fm">PB / wealth arm</th><th>Product</th><th>Type</th><th>Segment</th><th>Metals</th><th>Unit / minimum</th><th>Fees</th><th>Custody</th><th>Deliv.</th></tr>'
# the three most common product designs per type, for the intro
n_pb = sum(1 for f in F if f.get('is_pb', True))

try:
    TALK = open(os.path.join(HERE, 'pw_talking_points.html'), encoding='utf-8').read()
except Exception:
    TALK = ''

# ---- headline numbers
n_ver = sum(1 for f in F if str(f['confidence']).startswith('verified')) + sum(1 for f in F if f['confidence'] == 'mixed')
n_top = sum(1 for f in F if (f['score'] or 0) >= 7)
n_out = sum(1 for f in F if citi_cls(f['ref_bank_status'])[0] == 'out')
n_und = sum(1 for f in F if f['counterparties'] and all(c['name'] == 'undisclosed' for c in f['counterparties']))
top = [f for f in F if (f['score'] or 0) >= 7]

# ---- counterparty leaderboard (exclude memberships / undisclosed)
skip = {'undisclosed', 'LBMA', 'LPMCL', 'SGE', 'SGX', 'CME/COMEX', 'LME', 'HKPMCC', 'CGSE'}
lead = collections.defaultdict(lambda: collections.defaultdict(set))
for f in F:
    for c in f['counterparties']:
        if c['name'] in skip: continue
        lead[c['name']][c.get('role', 'other')].add(f['firm'])
lb = sorted(((n, len(set().union(*r.values())), r) for n, r in lead.items()), key=lambda x: -x[1])[:22]
mx = lb[0][1] if lb else 1
lb_html = ''.join('<li><span class="lb-n">%s</span><span class="lb-bar"><i style="width:%.0f%%"></i></span><span class="lb-v mono">%d</span><span class="lb-r">%s</span></li>' % (
    e(n), 100.0 * k / mx, k, e(', '.join('%s %d' % (ROLE[r], len(s)) for r, s in sorted(rr.items(), key=lambda z: -len(z[1]))[:3]))) for n, k, rr in lb)

# ---- Citi's own shelf
citi_rows = [f for f in F if citi_cls(f['ref_bank_status'])[0] == 'citi']

REGIONAL = [
    ('Switzerland & Liechtenstein', 'Only UBS, ZKB and Julius Baer run bullion desks; every other house (Pictet, Lombard Odier, UBP, EFG, Safra Sarasin, Vontobel, LGT, VP Bank, LLB, all cantonal banks) buys metal in. Pictet is the prime target: a multi-billion physical metals fund self-custodied at the bank, no LBMA membership, a US$780bn book. Raiffeisen self-vaults its Solid Gold ETFs with Argor-Heraeus as refiner and no LBMA membership. Swiss Lombard LTV on bullion is capped around 60%. Deutsche (Suisse) and Barclays (Suisse) lost their group desks and are the most displaceable foreign arms.'),
    ('United Kingdom, Ireland & Channel Islands', 'Citi now appears on the LBMA list of London vaulting custodians (33 Canada Square) after joining LPMCL in July 2026. Personal Assets Trust holds direct bullion with JPMorgan as custodian, the cleanest allocated-custody displacement. Barclays Private Bank and Coutts have no metals shelf and no desk (Barclays "arranges access" through an undisclosed counterparty; Coutts uses an ETC sleeve). Royal Mint RMAU is custodied at Llantrisant, not a bank. Lombard against physical gold is essentially absent among UK banks outside HSBC and the Swiss bookings.'),
    ('United States', 'Gold Bullion International is the white-label plumbing behind wirehouse and RIA physical programmes (US$8bn, 200k accounts, 12+ vaults) with no disclosed bullion-bank liquidity provider. Morgan Stanley\'s programme holds bars at an unnamed third-party depository. Wells Fargo picked The Wyoming Reserve for institutional custody in February 2026 with no bullion desk behind it. Fidelity outsources wholly to FideliTrade and Delaware Depository. JPMorgan Private Bank sells fee-light unallocated gold in a JPM vault. No US-booked allocated or Lombard-vs-bullion product was found on Citi\'s own wealth shelf.'),
    ('Continental Europe', 'Two wholesale chokepoints with no bullion desk: Reisebank (DZ Bank) supplies the German co-operative sector plus about 600 other banks; CPoR Devises (Loomis) supplies the French bank network. Deutsche Bank returned as an LBMA market maker on 20 March 2026; Xtrackers physical gold is custodied at JPMorgan London. Quintet runs a Luxembourg bullion desk without LBMA membership. Société Générale exited market-making in 2019 so SG Private Banking needs an external physical provider. Turkey is the region\'s largest gold-banking market, vaulted at Borsa Istanbul under the central-bank reserve mechanism; Kuveyt Türk has the deepest Sharia suite.'),
    ('Hong Kong, Singapore, China, Taiwan, Japan & Korea', 'Loco-Singapore clearing is being built by six founding members (DBS, Deutsche, ICBC Standard, JPMorgan, OCBC, UOB) without Citi; HKPMCC went live July 2026 with Standard Chartered clearing. The most displaceable books are the Korean gold-banking banks (KB, Shinhan, Woori) and Taiwan\'s gold-passbook banks, none with a bullion-bank parent. Julius Baer Asia makes its own prices from Zurich and Singapore. Mainland paper gold is in regulatory retreat, pushing HNW demand to HK/SG shelves. HSBC owns the tokenised-gold template end to end; Citi\'s HK shelf is "Gold Manager" plus a gold premium deposit.'),
    ('India, South-East Asia & Australia', 'India\'s nominated-importer list (April 2026 to March 2029) has 17 banks and excludes Citi, HSBC and Standard Chartered, so the route is consignment to HDFC/ICICI/Kotak/Axis or supply via IIBX; silver consignment is under-served. Indonesia\'s two new licensed bullion banks (Pegadaian with 155t under management, BSI with 22.5t) have no international counterpart. Vietnam ended the SJC monopoly in October 2025 and eight banks can now import raw gold. Malaysian and Thai gold accounts run on third-party physical with undisclosed hedge counterparties. Australian private banks own no metal shelf; the franchise sits with Perth Mint, ABC/Pallion and ETP custodians.'),
    ('Middle East, Africa & Israel', 'Emirates NBD built a full bullion franchise in 18 months (branded bars, gold loans and leasing, precious-metals repo, lease rates) with no disclosed bullion-bank partner. FAB, ADCB and Emirates Islamic all run Dubai-vaulted metal programmes naming no liquidity provider; Citi UAE wealth has no physical-gold shelf. Saudi banks hold pooled unassigned gold (SNB, Riyad, Al Rajhi); the only Tadawul physical ETF is Albilad at 470kg. In Africa, Absa\'s NewGold ETF is custodied at ICBC Standard and Standard Bank\'s 1nvest metal ETFs at JPMorgan. Israel and Egypt have no physical bank gold to supply.'),
    ('Canada & Latin America', 'Every Canadian bank bullion programme routes custody to the Royal Canadian Mint; none clears in London, so the angle is Toronto-London clearing and location swaps. CIBC is the best displacement target (large retail book, unallocated certificates, no bullion desk); Scotia Wealth has had no metals shelf since ScotiaMocatta closed; Wealthsimple launched fractional physical gold with an undisclosed liquidity provider; CI\'s VALT is the one Canadian gold ETF custodied loco-London at JPMorgan. Banamex is a Banxico coin distributor and Citi still holds 51% pending IPO. Brazilian gold is onshore-only through B3, so the opening for Itaú, BTG, XP and Bradesco is via their offshore booking centres.'),
]

regions_opts = ''.join('<option value="%s">%s (%d)</option>' % (r, REG_NAME.get(r, r), n) for r, n in sorted(ST['by_region'].items()))
countries = sorted({f['country'] for f in F if f['country']})
types = [t for t, _ in collections.Counter(f['type'] for f in F).most_common() if t]
prod_boxes = ''.join('<label><input type="checkbox" value="%s"> %s <span class="mono mute">%d</span></label>' % (k, l, sum(1 for f in F if f['products'].get(k) in ('Y', 'Y?'))) for k, l, _ in PK)
thead = '<tr><th class="fm">Firm</th><th>Country</th><th title="Pass 2: trades PM / size band + best public figure / liquidity-provider status">Desk · size · liquidity</th>' + ''.join('<th class="c" title="%s">%s</th>' % (e(t), l) for k, l, t in PK) + '<th>Works with</th><th>Ref.&nbsp;bank</th><th>Score</th></tr>'

page = '''<title>Private Wealth Metals Map</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#f6f4ee;--surface:#fffdf8;--ink:#1b2233;--ink2:#4a5468;--mute:#7a8394;--rule:#dcd6c8;--rule2:#ebe6da;--gold:#a67c1e;--gold-bg:#f3e9cf;--green:#2e7d4f;--green-bg:#e2f1e7;--amber:#9a6200;--amber-bg:#f7ecd2;--red:#a8382f;--red-bg:#f7e3df;--blue:#2c4f8f;--blue-bg:#e3eaf7;--focus:#2c4f8f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15181f;--surface:#1c2029;--ink:#e9e4d8;--ink2:#c3bdb0;--mute:#8d95a4;--rule:#2f3441;--rule2:#262b36;--gold:#d5a94a;--gold-bg:#2f2a1b;--green:#6fc292;--green-bg:#1c3226;--amber:#e0ac45;--amber-bg:#332a14;--red:#e58a80;--red-bg:#3a2320;--blue:#8fb0ea;--blue-bg:#1f2a40;--focus:#8fb0ea}}
:root[data-theme="dark"]{--bg:#15181f;--surface:#1c2029;--ink:#e9e4d8;--ink2:#c3bdb0;--mute:#8d95a4;--rule:#2f3441;--rule2:#262b36;--gold:#d5a94a;--gold-bg:#2f2a1b;--green:#6fc292;--green-bg:#1c3226;--amber:#e0ac45;--amber-bg:#332a14;--red:#e58a80;--red-bg:#3a2320;--blue:#8fb0ea;--blue-bg:#1f2a40;--focus:#8fb0ea}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Source Sans 3",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:15.5px;line-height:1.5}
.mono{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding:40px 28px 80px}
h1,h2,h3{font-family:Fraunces,Georgia,"Times New Roman",serif;font-weight:600;letter-spacing:-.01em;text-wrap:balance;margin:0}
h1{font-size:clamp(30px,4vw,44px);line-height:1.08;font-variation-settings:"opsz" 96}
h2{font-size:24px;margin:0 0 6px}
h3{font-size:18px}
h4{font:600 12px/1.2 "Source Sans 3",sans-serif;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);margin:14px 0 6px}
.eyebrow{font:600 12px/1 "Source Sans 3",sans-serif;text-transform:uppercase;letter-spacing:.1em;color:var(--gold);margin-bottom:12px}
.lede{max-width:68ch;color:var(--ink2);font-size:17px;margin:14px 0 0}
p{margin:.5em 0}
a{color:var(--blue)}
.mute{color:var(--mute)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin:28px 0 8px}
.stat{padding:14px 16px 12px;border-right:1px solid var(--rule2)}.stat:last-child{border-right:0}
.stat b{display:block;font:500 28px/1 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;color:var(--ink)}
.stat span{display:block;font-size:12.5px;color:var(--mute);margin-top:6px;text-transform:uppercase;letter-spacing:.05em}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--ink2);margin:8px 0 0}
section{margin-top:44px}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:14px}
.sec-head p{margin:0;color:var(--mute);font-size:14px;max-width:70ch}
.tbl-wrap{overflow-x:auto;border:1px solid var(--rule);background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:1100px;font-size:14px}
th{position:sticky;top:0;background:var(--surface);text-align:left;font:600 11.5px/1.2 "Source Sans 3",sans-serif;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);padding:10px 8px;border-bottom:1px solid var(--rule);z-index:1}
td{padding:9px 8px;border-bottom:1px solid var(--rule2);vertical-align:top}
tr.r{cursor:pointer}tr.r:hover td{background:color-mix(in srgb,var(--gold-bg) 45%,var(--surface))}
tr.r:focus{outline:2px solid var(--focus);outline-offset:-2px}
td.fm{min-width:230px;max-width:330px}td.fm b{font-weight:600}
td.ct{white-space:nowrap;color:var(--ink2)}
td.c,th.c{text-align:center;width:52px;font-family:"IBM Plex Mono",monospace;font-size:13px}
.c-y{color:var(--green);font-weight:600}.c-yq{color:var(--amber);font-weight:500}.c-n{color:var(--mute);opacity:.6}.c-u{color:var(--rule);}
td.ww{min-width:190px;max-width:280px;font-size:13.5px}
.cp{font-weight:600}.cp-k::after{content:"?";color:var(--amber);font-size:.8em;margin-left:1px}
.pill{display:inline-block;font:600 11px/1 "Source Sans 3",sans-serif;letter-spacing:.04em;padding:5px 8px;border-radius:3px;white-space:nowrap}
.pill-citi{background:var(--blue-bg);color:var(--blue)}.pill-in{background:var(--green-bg);color:var(--green)}.pill-out{background:var(--red-bg);color:var(--red)}.pill-unk{background:var(--rule2);color:var(--mute)}
td.sc{text-align:center;font-weight:500}
td.p2{min-width:150px;max-width:210px;font-size:12.5px;line-height:1.35}
.ptype{display:inline-block;font:600 11px/1.2 "Source Sans 3",sans-serif;letter-spacing:.03em;padding:3px 7px;border-radius:3px;background:var(--gold-bg);color:var(--gold);white-space:nowrap}
.pbtog{display:inline-flex;gap:6px;align-items:center;font-size:14px;cursor:pointer}
#prod-t td{font-size:13.5px}
.tp-desk{color:var(--green);font-weight:600}.tp-pt{color:var(--amber);font-weight:600}.tp-dist{color:var(--mute);font-weight:600}.tp-no{color:var(--red);font-weight:600}
.lq-v{color:var(--green);font-weight:600}.lq-k{color:var(--amber);font-weight:600}.lq-i{color:var(--blue);font-weight:600}.lq-u{color:var(--red);font-weight:600}.lq-na{color:var(--mute)}
tr.x td{background:color-mix(in srgb,var(--gold-bg) 30%,var(--surface));padding:14px 18px 18px 26px;border-left:3px solid var(--gold)}
.det{max-width:110ch;font-size:14px}.det-meta{color:var(--mute);font-size:13px}
.angle{margin:8px 0 4px;color:var(--ink);border-left:3px solid var(--gold);padding-left:10px}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:3px 16px;margin:8px 0 0}.kv dt{font-weight:600;color:var(--ink2);font-size:13px}.kv dd{margin:0}
ul.cps,ul.ev{margin:4px 0 0;padding-left:18px}ul.cps li,ul.ev li{margin:3px 0}
.role{font:500 11px/1 "IBM Plex Mono",monospace;background:var(--rule2);color:var(--ink2);padding:2px 5px;border-radius:2px;margin-left:4px}
.tag-k{font:500 10.5px/1 "Source Sans 3",sans-serif;color:var(--amber);background:var(--amber-bg);padding:2px 5px;border-radius:2px;text-transform:uppercase;letter-spacing:.04em}
q{color:var(--ink2);font-style:italic}
.src{font-size:12.5px;color:var(--mute);margin-top:10px}
.controls{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:0 0 12px}
.controls input[type=search],.controls select{font:inherit;font-size:14px;padding:7px 10px;border:1px solid var(--rule);border-radius:3px;background:var(--surface);color:var(--ink);min-width:170px}
.controls input[type=search]{min-width:260px}
.boxes{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:13.5px;margin:0 0 12px}.boxes label{display:inline-flex;gap:5px;align-items:center;cursor:pointer}
.count{font-size:13px;color:var(--mute)}
button{font:inherit;font-size:13px;padding:6px 10px;border:1px solid var(--rule);background:var(--surface);color:var(--ink);border-radius:3px;cursor:pointer}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
.lb{list-style:none;margin:0;padding:0;display:grid;gap:5px;max-width:900px}
.lb li{display:grid;grid-template-columns:170px 1fr 44px minmax(220px,1fr);align-items:center;gap:10px;font-size:14px}
.lb-n{font-weight:600;text-align:right}.lb-bar{height:14px;background:var(--rule2);position:relative}.lb-bar i{display:block;height:100%;background:var(--gold)}
.lb-v{text-align:right}.lb-r{font-size:12.5px;color:var(--mute)}
.regions{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px 32px}
.regions h3{margin-bottom:4px}.regions p{margin:0;color:var(--ink2);font-size:14.5px;max-width:62ch}
.citibox{background:var(--surface);border:1px solid var(--rule);border-top:3px solid var(--blue);padding:16px 20px;max-width:900px}
.citibox ul{margin:6px 0 0;padding-left:18px}.citibox li{margin:4px 0}
.caveats{font-size:14px;color:var(--ink2);max-width:80ch}
.caveats li{margin:4px 0}
@media (max-width:720px){.wrap{padding:24px 14px 60px}.lb li{grid-template-columns:120px 1fr 40px}.lb-r{display:none}}
@media (prefers-reduced-motion:no-preference){tr.x td{animation:fade .18s ease-out}}@keyframes fade{from{opacity:.5}to{opacity:1}}
</style>
<div class="wrap">
<div class="eyebrow">Metals desk · private banks &amp; wealth managers · global mandate · generated __GEN__</div>
<h1>Private Wealth Metals Map</h1>
<p class="lede">Every private bank and private-wealth manager identified worldwide: the metals products each puts in front of clients, and the bullion banks, custodians and refiners that sit behind those products. Built for one question: where could a bullion desk supply, custody, finance or clear what a wealth manager is currently buying from someone else.</p>
<div class="stats">
<div class="stat"><b>__N__</b><span>firms covered</span></div>
<div class="stat"><b>__NVER__</b><span>with web-verified evidence</span></div>
<div class="stat"><b>__NTOP__</b><span>priority targets (score ≥ 7)</span></div>
<div class="stat"><b>__NOUT__</b><span>reference bank not named</span></div>
<div class="stat"><b>__NUND__</b><span>counterparty fully undisclosed</span></div>
<div class="stat"><b>__NS__</b><span>web searches behind it</span></div>
<div class="stat"><b>__NPB__</b><span>private-bank / wealth arms</span></div>
<div class="stat"><b>__NPROD__</b><span>advertised products catalogued</span></div>
<div class="stat"><b>__P2N__</b><span>enriched for size &amp; liquidity</span></div>
<div class="stat"><b>__P2NOT__</b><span>with a public size figure</span></div>
</div>
<div class="legend"><span><b class="c-y">Y</b> verified on the firm's own pages / prospectus</span><span><b class="c-yq">Y?</b> known, unverified</span><span><b class="c-n">N</b> verified not offered</span><span><b class="c-u">?</b> unknown</span><span>Counterparty with <span class="cp-k"></span> = unverified</span><span>Score = franchise size × displaceability × no in-house bullion bank</span><span>Desk · size · liquidity column (firms scoring ≥ 6 only): <span class="tp-desk">in-house desk</span> / <span class="tp-pt">price-taker</span>; size band is an ESTIMATE from the best public figure; liquidity status <span class="lq-v">named-verified</span> / <span class="lq-k">named-knowledge</span> / <span class="lq-i">in-house</span> / <span class="lq-u">undisclosed</span></span></div>

<section id="talk">
<div class="sec-head"><h2>Talking points for the wealth business</h2><p>A 45-minute run-sheet: uptake evidence, the products explained, who is winning by country, competitor designs, one franchise's shelf today, sizing, a potential shelf and the questions to expect.</p></div>
__TALK__
</section>

<section id="targets">
<div class="sec-head"><h2>Where a bullion desk could displace</h2><p>The __NTOP__ firms scoring 7 or more. Click a row for the counterparty list with evidence, the product evidence and the strategic idea.</p></div>
<div class="tbl-wrap"><table><thead>__THEAD__</thead><tbody>__TOPROWS__</tbody></table></div>
</section>

<section id="citi">
<div class="sec-head"><h2>One global franchise, as the web sees it</h2><p>What is publicly documented for one global franchise across booking centres, shown against the peer shelves above. Included because the same sweep was run on every firm in the set.</p></div>
<div class="citibox">
<ul>__CITI__</ul>
</div>
</section>

<section id="banks">
<div class="sec-head"><h2>Who the private banks work with</h2><p>Named counterparties across the whole set, by number of wealth firms that use them (memberships and exchanges excluded). Roles shown for the top three uses of each name.</p></div>
<ul class="lb">__LB__</ul>
<p class="mute" style="font-size:13px;margin-top:10px">__NUNDROWS__ counterparty rows across the set are "undisclosed": the firm sells the product but names no bank behind it. Those are the open doors.</p>
</section>

<section id="regions">
<div class="sec-head"><h2>Regional read</h2><p>What each sweep found, condensed to what changes the pitch.</p></div>
<div class="regions">__REGIONS__</div>
</section>

<section id="products">
<div class="sec-head"><h2>Product catalogue</h2><p>What the private-bank and wealth arms actually put in front of clients: __NPROD__ named products across __NPRODF__ firms (__NPRODV__ verified on the firm's own page). Institutional bullion-desk services are excluded. Click a row for the description in the firm's words, pricing basis and the page link.</p></div>
<div class="controls">
<input type="search" id="pq" placeholder="search product, firm, custody, fees…" aria-label="Search products">
<select id="pfr" aria-label="Region"><option value="">all regions</option>__REGOPTS__</select>
<select id="pfc" aria-label="Country"><option value="">all countries</option>__PCTRYOPTS__</select>
<select id="pfs" aria-label="Segment"><option value="">any segment</option><option value="private">private-banking / HNW</option><option value="uhnw">UHNW / family office</option><option value="affluent">affluent / premier</option><option value="retail">retail</option></select>
<select id="pfv" aria-label="Confidence"><option value="">any confidence</option><option value="verified">verified only</option></select>
<button type="button" id="pclr">clear</button><span class="count" id="pcnt"></span>
</div>
<div class="boxes" id="ppt"><span class="mute">Type:</span>__PTYPEBOXES__</div>
<div class="boxes" id="ppm"><span class="mute">Metal:</span>__PMETALBOXES__</div>
<div class="tbl-wrap"><table id="prod-t"><thead>__PTHEAD__</thead><tbody>__PRODROWS__</tbody></table></div>
</section>

<section id="all">
<div class="sec-head"><h2>Every firm</h2><p>All __N__ rows (__NPB__ private-bank / wealth arms shown by default; untick the toggle to include bullion dealers, refiners, mints, vaults and ETF issuers). Filter by region, country, firm type, product and Citi status; free-text search covers the expanded detail too.</p></div>
<div class="controls">
<input type="search" id="q" placeholder="search firm, counterparty, evidence…" aria-label="Search">
<select id="fr" aria-label="Region"><option value="">all regions</option>__REGOPTS__</select>
<select id="fc" aria-label="Country"><option value="">all countries</option>__CTRYOPTS__</select>
<select id="ft" aria-label="Firm type"><option value="">all types</option>__TYPEOPTS__</select>
<select id="fci" aria-label="Reference-bank status"><option value="">any reference-bank status</option><option value="citi">reference franchise</option><option value="in">reference bank named</option><option value="out">reference bank not named</option><option value="unk">unknown</option></select>
<label class="pbtog"><input type="checkbox" id="fpb" checked> private-bank / wealth arms only</label>
<select id="fs" aria-label="Minimum score"><option value="0">any score</option><option value="5">score ≥ 5</option><option value="6">score ≥ 6</option><option value="7">score ≥ 7</option><option value="8">score ≥ 8</option></select>
<button type="button" id="clr">clear</button><span class="count" id="cnt"></span>
</div>
<div class="boxes" id="pb"><span class="mute">Offers:</span>__PRODBOXES__</div>
<div class="tbl-wrap"><table id="all-t"><thead>__THEAD__</thead><tbody>__ALLROWS__</tbody></table></div>
</section>

<section id="method">
<div class="sec-head"><h2>Method and caveats</h2></div>
<ul class="caveats">
<li>Eight regional research passes (knowledge first, then __NS__ web searches and page reads against firms' own product pages, factsheets, prospectuses, annual reports and press releases). Cells are Y only where the firm's own material or a primary document says so; Y? and "knowledge" rows are unverified and should be checked before they go in a pitch.</li>
<li>Pass 2 (size and liquidity) re-visited the __P2N__ firms scoring 6 or more with __P2S__ further searches, hunting notional proxies (metal-account balances, ETF AUM, import volumes, regulator statistics, LBMA tier, client counts) and the wholesale liquidity or physical provider (prospectus counterparties, annual-report derivative notes, T&amp;Cs, press). Liquidity status across those firms: __P2LQ__. Size bands: __P2SB__. Private banks rarely publish notionals, so most bands are estimates from proxies and are labelled as such.</li>
<li>Confidence across the set: __CONF__. The tail of small firms is deliberately breadth-first (one row, mostly "?" cells).</li>
<li>The LBMA member directory did not render for several agents, so LBMA tier for some names (Julius Baer, ZKB, Vontobel, Safra, Commerzbank, BayernLB, Indian nominated banks, Macquarie, Maybank) is tagged from knowledge, not verified.</li>
<li>Betashares QAU: the issuer's May 2026 PDS is on file naming the custodian; the Australia sweep read the public fund page as JPMorgan London. Reconcile against the saved PDS before citing either.</li>
<li>Counterparty names are canonicalised for the tally (JPMorgan Chase Bank N.A. and J.P. Morgan SE both count as JPMorgan); the expanded row keeps the full original description.</li>
<li>Dataset: <span class="mono">private_wealth.json</span> in the leads folder; the same data drives the "Private wealth" tab of the metals client database. Rebuild with <span class="mono">_pw_merge.py</span> then <span class="mono">deep_dives_index.py</span>; this page with <span class="mono">_pw_report.py</span>.</li>
</ul>
</section>
</div>
<script>
(function(){
  function wire(tbl){
    tbl.addEventListener('click',function(ev){var r=ev.target.closest('tr.r');if(!r||ev.target.closest('a'))return;var x=r.nextElementSibling;if(x&&x.classList.contains('x'))x.hidden=!x.hidden;});
    tbl.addEventListener('keydown',function(ev){if(ev.key!=='Enter'&&ev.key!==' ')return;var r=ev.target.closest('tr.r');if(!r)return;ev.preventDefault();var x=r.nextElementSibling;if(x)x.hidden=!x.hidden;});
  }
  document.querySelectorAll('table').forEach(wire);
  var q=document.getElementById('q'),fr=document.getElementById('fr'),fc=document.getElementById('fc'),ft=document.getElementById('ft'),fci=document.getElementById('fci'),fs=document.getElementById('fs'),cnt=document.getElementById('cnt'),pb=document.getElementById('pb');
  var rows=Array.prototype.slice.call(document.querySelectorAll('#all-t tr.r'));
  var fpb=document.getElementById('fpb');
  function apply(){
    var s=(q.value||'').toLowerCase(),R=fr.value,C=fc.value,T=ft.value,CI=fci.value,S=+fs.value||0,PB=fpb&&fpb.checked;
    var ps=Array.prototype.slice.call(pb.querySelectorAll('input:checked')).map(function(b){return b.value;});
    var n=0;
    rows.forEach(function(r){
      var x=r.nextElementSibling;var d=r.dataset;var ok=true;
      if(PB&&d.pb==='0')ok=false; if(ok&&R&&d.region!==R)ok=false; if(ok&&C&&d.country!==C)ok=false; if(ok&&T&&d.type!==T)ok=false; if(ok&&CI&&d.citi!==CI)ok=false; if(ok&&S&&(+d.score||0)<S)ok=false;
      if(ok&&ps.length){var have=d.p.split(' ');ok=ps.every(function(p){return have.indexOf(p)>=0;});}
      if(ok&&s){ok=(r.textContent+' '+(x?x.textContent:'')).toLowerCase().indexOf(s)>=0;}
      r.hidden=!ok; if(x){if(!ok)x.hidden=true;}
      if(ok)n++;
    });
    cnt.textContent=n+' of '+rows.length+' shown';
  }
  [q,fr,fc,ft,fci,fs,fpb].forEach(function(el){if(!el)return;el.addEventListener('input',apply);el.addEventListener('change',apply);});
  pb.addEventListener('change',apply);
  document.getElementById('clr').addEventListener('click',function(){q.value='';fr.value='';fc.value='';ft.value='';fci.value='';fs.value='0';pb.querySelectorAll('input').forEach(function(b){b.checked=false;});apply();});
  apply();
  // product catalogue filter
  var pq=document.getElementById('pq'),pfr=document.getElementById('pfr'),pfc=document.getElementById('pfc'),pfs=document.getElementById('pfs'),pfv=document.getElementById('pfv'),pcnt=document.getElementById('pcnt'),ppt=document.getElementById('ppt'),ppm=document.getElementById('ppm');
  var prows=Array.prototype.slice.call(document.querySelectorAll('#prod-t tr.r'));
  function papply(){
    if(!pq)return;
    var s=(pq.value||'').toLowerCase(),R=pfr.value,C=pfc.value,SG=pfs.value,V=pfv.value;
    var ts=Array.prototype.slice.call(ppt.querySelectorAll('input:checked')).map(function(b){return b.value;});
    var ms=Array.prototype.slice.call(ppm.querySelectorAll('input:checked')).map(function(b){return b.value;});
    var n=0;
    prows.forEach(function(r){
      var x=r.nextElementSibling;var d=r.dataset;var ok=true;var seg=d.seg||'';
      if(R&&d.region!==R)ok=false; if(ok&&C&&d.country!==C)ok=false; if(ok&&V&&d.conf!==V)ok=false;
      if(ok&&SG){ok=(SG==='private'&&(seg.indexOf('private')>=0||seg.indexOf('hnw')>=0||seg==='all'))||(SG==='uhnw'&&(seg.indexOf('uhnw')>=0||seg.indexOf('family')>=0))||(SG==='affluent'&&(seg.indexOf('affluent')>=0||seg.indexOf('premier')>=0||seg.indexOf('priority')>=0||seg==='all'))||(SG==='retail'&&(seg.indexOf('retail')>=0||seg==='all'));}
      if(ok&&ts.length)ok=ts.indexOf(d.ptype)>=0;
      if(ok&&ms.length){var have=(d.metals||'').split('|');ok=ms.some(function(m){return have.indexOf(m)>=0;});}
      if(ok&&s)ok=(r.textContent+' '+(x?x.textContent:'')).toLowerCase().indexOf(s)>=0;
      r.hidden=!ok; if(x&&!ok)x.hidden=true; if(ok)n++;
    });
    pcnt.textContent=n+' of '+prows.length+' shown';
  }
  if(pq){[pq,pfr,pfc,pfs,pfv].forEach(function(el){el.addEventListener('input',papply);el.addEventListener('change',papply);});ppt.addEventListener('change',papply);ppm.addEventListener('change',papply);
    document.getElementById('pclr').addEventListener('click',function(){pq.value='';pfr.value='';pfc.value='';pfs.value='';pfv.value='';ppt.querySelectorAll('input').forEach(function(b){b.checked=false;});ppm.querySelectorAll('input').forEach(function(b){b.checked=false;});papply();});
    papply();}
})();
</script>'''

citi_li = []
for f in citi_rows:
    p = f['products']
    offered = [l for k, l, _ in PK if p.get(k) == 'Y']; maybe = [l for k, l, _ in PK if p.get(k) == 'Y?']; no = [l for k, l, _ in PK if p.get(k) == 'N']
    citi_li.append('<li><b>%s</b> <span class="mute">(%s)</span> — verified: %s%s%s%s</li>' % (
        e(f['firm']), e(f['country']), e(', '.join(offered) or 'nothing found'), (' · unverified: ' + e(', '.join(maybe))) if maybe else '',
        (' · not offered: ' + e(', '.join(no))) if no else '', (' · <i>%s</i>' % e(str(f.get('strategic_idea', ''))[:260])) if f.get('strategic_idea') else ''))

conf = collections.Counter(f['confidence'] for f in F)
page = (page.replace('__GEN__', e(d['generated'])).replace('__N__', str(len(F))).replace('__NVER__', str(n_ver)).replace('__NTOP__', str(n_top))
        .replace('__NOUT__', str(n_out)).replace('__NUND__', str(n_und)).replace('__NS__', str(ST['search_count'])).replace('__THEAD__', thead)
        .replace('__TOPROWS__', ''.join(row(f) for f in top)).replace('__CITI__', ''.join(citi_li)).replace('__LB__', lb_html)
        .replace('__NUNDROWS__', str(ST.get('undisclosed_counterparty_rows', 0)))
        .replace('__REGIONS__', ''.join('<div><h3>%s</h3><p>%s</p></div>' % (e(h), e(t)) for h, t in REGIONAL))
        .replace('__REGOPTS__', regions_opts).replace('__CTRYOPTS__', ''.join('<option>%s</option>' % e(c) for c in countries))
        .replace('__TYPEOPTS__', ''.join('<option>%s</option>' % e(t) for t in types)).replace('__PRODBOXES__', prod_boxes)
        .replace('__ALLROWS__', ''.join(row(f) for f in F))
        .replace('__CONF__', e(', '.join('%s %d' % (k, v) for k, v in conf.most_common())))
        .replace('__NPB__', str(n_pb)).replace('__NPROD__', str(n_prod)).replace('__NPRODF__', str(n_prod_firms)).replace('__NPRODV__', str(n_prod_ver))
        .replace('__PCTRYOPTS__', ''.join('<option>%s</option>' % e(c) for c in pcountries)).replace('__PTYPEBOXES__', ptype_boxes).replace('__PMETALBOXES__', pmetal_boxes)
        .replace('__PTHEAD__', p_thead).replace('__PRODROWS__', ''.join(prow(x) for x in PRODS))
        .replace('__TALK__', TALK or '<p class="mute">Talking points pending (run _pw_talk.py).</p>')
        .replace('__P2N__', str(ST.get('pass2_firms', 0))).replace('__P2NOT__', str(ST.get('pass2_with_notional', 0))).replace('__P2S__', str(ST.get('pass2_searches', 0)))
        .replace('__P2LQ__', e(', '.join('%s %d' % (k, v) for k, v in sorted((ST.get('pass2_liquidity') or {}).items(), key=lambda z: -z[1]))) or 'n/a')
        .replace('__P2SB__', e(', '.join('%s %d' % (k, v) for k, v in sorted((ST.get('pass2_size_bands') or {}).items(), key=lambda z: -z[1]))) or 'n/a'))
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page) // 1024, 'KB;', len(F), 'firms;', n_top, 'targets')
