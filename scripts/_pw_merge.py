"""Merge the regional private-wealth sweep files (pw_*.json, written by the research agents)
into private_wealth.json — the dataset behind the "Private wealth" DEEP_DIVES tab.

Usage:  python _pw_merge.py <dir-with-pw_*.json>
Dedups firms case-insensitively on a normalised firm name (first file wins, later files
only fill blanks), normalises product cells to Y / Y? / N / ?, and computes stats.
"""
import glob, json, os, re, sys, datetime

SRC = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'private_wealth.json')

PRODUCT_KEYS = ['physical_bullion', 'metal_account_allocated', 'metal_account_unallocated', 'gold_savings_plan',
                'gold_deposit_dci', 'structured_notes', 'otc_derivatives', 'lombard_vs_metal', 'own_etf_etc',
                'third_party_etf', 'metal_funds']
ROLES = ['bullion_supplier', 'liquidity_provider', 'custodian_vault', 'etf_custodian', 'refiner', 'note_issuer',
         'account_partner', 'clearing_lpmcl', 'other']

REGION_OF = {  # country -> desk region
    'Switzerland': 'EMEA', 'Liechtenstein': 'EMEA', 'United Kingdom': 'EMEA', 'UK': 'EMEA', 'Ireland': 'EMEA',
    'Jersey': 'EMEA', 'Guernsey': 'EMEA', 'Isle of Man': 'EMEA', 'Germany': 'EMEA', 'Austria': 'EMEA', 'France': 'EMEA',
    'Belgium': 'EMEA', 'Netherlands': 'EMEA', 'Luxembourg': 'EMEA', 'Italy': 'EMEA', 'Spain': 'EMEA', 'Portugal': 'EMEA',
    'Monaco': 'EMEA', 'Sweden': 'EMEA', 'Norway': 'EMEA', 'Denmark': 'EMEA', 'Finland': 'EMEA', 'Poland': 'EMEA',
    'Czech Republic': 'EMEA', 'Czechia': 'EMEA', 'Greece': 'EMEA', 'Turkey': 'EMEA', 'Türkiye': 'EMEA', 'Cyprus': 'EMEA',
    'Malta': 'EMEA', 'Israel': 'EMEA', 'UAE': 'EMEA', 'United Arab Emirates': 'EMEA', 'Saudi Arabia': 'EMEA',
    'Qatar': 'EMEA', 'Kuwait': 'EMEA', 'Bahrain': 'EMEA', 'Oman': 'EMEA', 'Jordan': 'EMEA', 'Lebanon': 'EMEA',
    'Egypt': 'EMEA', 'South Africa': 'EMEA', 'Nigeria': 'EMEA', 'Kenya': 'EMEA', 'Mauritius': 'EMEA', 'Morocco': 'EMEA',
    'United States': 'NAM', 'USA': 'NAM', 'US': 'NAM', 'Canada': 'NAM', 'Bermuda': 'NAM', 'Cayman Islands': 'NAM',
    'Bahamas': 'NAM', 'Panama': 'LATAM', 'Mexico': 'LATAM', 'Brazil': 'LATAM', 'Chile': 'LATAM', 'Peru': 'LATAM',
    'Colombia': 'LATAM', 'Argentina': 'LATAM', 'Uruguay': 'LATAM',
    'Hong Kong': 'APAC', 'Singapore': 'APAC', 'China': 'APAC', 'Taiwan': 'APAC', 'Japan': 'APAC', 'South Korea': 'APAC',
    'Korea': 'APAC', 'India': 'APAC', 'Malaysia': 'APAC', 'Indonesia': 'APAC', 'Thailand': 'APAC', 'Philippines': 'APAC',
    'Vietnam': 'APAC', 'Australia': 'APAC', 'New Zealand': 'APAC', 'Macau': 'APAC', 'Sri Lanka': 'APAC', 'Pakistan': 'APAC',
    'Bangladesh': 'APAC',
}


CP_ALIAS = [  # regex -> canonical counterparty label (order matters)
    (r'^unknown|^undisclosed|^not disclosed|^n/?a$|^none$|^\?', 'undisclosed'),
    (r'julius baer', 'Julius Baer'), (r'\bubs\b', 'UBS'), (r'credit suisse', 'Credit Suisse (UBS)'),
    (r'j\.?\s?p\.?\s?morgan|jpm\b|jpmorgan', 'JPMorgan'), (r'\bhsbc\b', 'HSBC'), (r'icbc standard', 'ICBC Standard'),
    (r'\bicbc\b', 'ICBC'), (r'standard chartered|\bscb\b|stanchart', 'Standard Chartered'), (r'\bciti', 'Citi'),
    (r'goldman', 'Goldman Sachs'), (r'morgan stanley', 'Morgan Stanley'), (r'bank of america|merrill|bofa', 'Bank of America'),
    (r'wells fargo', 'Wells Fargo'), (r'\bbnp\b', 'BNP Paribas'), (r'soci[eé]t[eé] g[eé]n[eé]rale|socgen|\bsg\b', 'Société Générale'),
    (r'natixis', 'Natixis'), (r'deutsche bank|\bdb\b', 'Deutsche Bank'), (r'commerzbank', 'Commerzbank'),
    (r'\bzkb\b|z[üu]rcher kantonalbank|swisscanto', 'ZKB'), (r'raiffeisen', 'Raiffeisen'), (r'\bpictet', 'Pictet'),
    (r'lombard odier', 'Lombard Odier'), (r'vontobel', 'Vontobel'), (r'mks\s?pamp|\bpamp\b|\bmks\b', 'MKS PAMP'),
    (r'argor', 'Argor-Heraeus'), (r'heraeus', 'Heraeus'), (r'valcambi', 'Valcambi'), (r'metalor', 'Metalor'),
    (r'umicore', 'Umicore'), (r'perth mint', 'Perth Mint'), (r'royal canadian mint|\brcm\b', 'Royal Canadian Mint'),
    (r'royal mint', 'The Royal Mint'), (r'rand refinery', 'Rand Refinery'), (r'stonex|\binte?l\b fcstone', 'StoneX'),
    (r'brink', "Brink's"), (r'loomis', 'Loomis'), (r'malca', 'Malca-Amit'), (r'\bg4s\b', 'G4S'),
    (r'freeport|le freeport', 'Le Freeport'), (r'delaware depository', 'Delaware Depository'), (r'\bids\b', 'IDS'),
    (r'\bbank of china\b|\bboc\b|bochk', 'Bank of China'), (r'\bdbs\b', 'DBS'), (r'\bocbc\b|bank of singapore', 'OCBC'),
    (r'\buob\b', 'UOB'), (r'scotia', 'Scotiabank'), (r'\btd\b|toronto.dominion', 'TD'), (r'\brbc\b|royal bank of canada', 'RBC'),
    (r'\bbmo\b|bank of montreal', 'BMO'), (r'\bcibc\b', 'CIBC'), (r'\banz\b', 'ANZ'), (r'macquarie', 'Macquarie'),
    (r'westpac', 'Westpac'), (r'\bnab\b|national australia', 'NAB'), (r'sumitomo|\bsmbc\b', 'SMBC'), (r'mitsubishi ufj|\bmufg\b', 'MUFG'),
    (r'mizuho', 'Mizuho'), (r'nomura', 'Nomura'), (r'tanaka', 'Tanaka Kikinzoku'), (r'komsco', 'KOMSCO'),
    (r'\bsge\b|shanghai gold exchange', 'SGE'), (r'\bsgx\b', 'SGX'), (r'\bcme\b|comex', 'CME/COMEX'), (r'\blme\b', 'LME'),
    (r'\blbma\b', 'LBMA'), (r'lpmcl', 'LPMCL'), (r'hkpmcc|hong kong precious metals clearing', 'HKPMCC'), (r'cgse|chinese gold.*silver exchange', 'CGSE'),
    (r'emirates nbd', 'Emirates NBD'), (r'first abu dhabi|\bfab\b', 'FAB'), (r'kuveyt', 'Kuveyt Türk'), (r'istanbul gold', 'Istanbul Gold Refinery'),
    (r'degussa', 'Degussa'), (r'pro aurum', 'pro aurum'), (r'reisebank', 'Reisebank'), (r'm[üu]nze [öo]sterreich|austrian mint', 'Münze Österreich'),
    (r'clearstream', 'Clearstream'), (r'xetra.gold|deutsche b[öo]rse commodities', 'Xetra-Gold'), (r'sharps pixley', 'Sharps Pixley'),
    (r'baird', 'Baird & Co'), (r'bullionvault', 'BullionVault'), (r'goldmoney', 'Goldmoney'), (r'kitco', 'Kitco'), (r'apmex', 'APMEX'),
    (r'sprott', 'Sprott'), (r'state street|spdr', 'State Street/SPDR'), (r'ishares|blackrock', 'iShares/BlackRock'), (r'invesco', 'Invesco'),
    (r'wisdomtree', 'WisdomTree'), (r'xtrackers|dws', 'DWS/Xtrackers'), (r'amundi', 'Amundi'), (r'graniteshares', 'GraniteShares'),
    (r'abrdn|aberdeen', 'abrdn'), (r'van ?eck', 'VanEck'), (r'phillip', 'PhillipCapital'), (r'interactive brokers|ibkr', 'Interactive Brokers'),
    (r'\bbny\b|bank of new york|mellon', 'BNY'), (r'northern trust', 'Northern Trust'), (r'barclays', 'Barclays'), (r'natwest|coutts', 'NatWest/Coutts'),
    (r'lloyds', 'Lloyds'), (r'santander', 'Santander'), (r'\bbbva\b', 'BBVA'), (r'unicredit', 'UniCredit'), (r'intesa', 'Intesa Sanpaolo'),
    (r'\bing\b', 'ING'), (r'abn amro', 'ABN AMRO'), (r'\bkbc\b', 'KBC'), (r'nordea', 'Nordea'), (r'\bseb\b', 'SEB'), (r'danske', 'Danske'),
    (r'erste', 'Erste'), (r'\blgt\b', 'LGT'), (r'\bvp bank\b', 'VP Bank'), (r'\bllb\b|liechtensteinische landesbank', 'LLB'),
    (r'\bpsbc\b|postal savings', 'PSBC'), (r'\bccb\b|china construction', 'CCB'), (r'\babc\b|agricultural bank', 'ABC'), (r'\bcmb\b|china merchants', 'CMB'),
    (r'bank of communications|bocom', 'BoCom'), (r'ping an', 'Ping An'), (r'hang seng', 'Hang Seng'), (r'bank of taiwan', 'Bank of Taiwan'),
    (r'\bmmtc\b|mmtc.pamp', 'MMTC-PAMP'), (r'\bkotak\b', 'Kotak'), (r'\bhdfc\b', 'HDFC'), (r'\bicici\b', 'ICICI'), (r'state bank of india|\bsbi\b', 'SBI'),
    (r'safegold|augmont|digital gold', 'Digital-gold platform'), (r'itaú|itau', 'Itaú'), (r'btg', 'BTG Pactual'), (r'bradesco', 'Bradesco'),
    (r'banorte', 'Banorte'), (r'investec', 'Investec'), (r'standard bank', 'Standard Bank'), (r'\bfnb\b|firstrand', 'FirstRand/FNB'), (r'absa', 'Absa'), (r'nedbank', 'Nedbank'),
]
_CP_RX = [(re.compile(p, re.I), c) for p, c in CP_ALIAS]


def cp_short(name):
    n = str(name or '').strip()
    if not n: return 'undisclosed'
    for rx, c in _CP_RX:
        if rx.search(n): return c
    s = re.split(r'\s+[—–-]\s+|\s*\(|;|\s+/\s+|\s+\bvia\b', n)[0].strip()
    return s[:40] if s else n[:40]


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'\b(ag|sa|ltd|limited|plc|inc|llc|co|cie|group|holdings?|bank|banque|banca|private|wealth|management)\b', ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def cell(v):
    v = str(v or '?').strip()
    u = v.upper()
    if u in ('Y', 'YES', 'TRUE'): return 'Y'
    if u in ('Y?', 'YES?', 'LIKELY', 'PROBABLE'): return 'Y?'
    if u in ('N', 'NO', 'FALSE'): return 'N'
    if u in ('?', 'UNKNOWN', 'UNK', '', 'NONE'): return '?'
    if u.startswith('Y'): return 'Y' if '?' not in u else 'Y?'
    if u.startswith('N'): return 'N'
    return '?'


def region_of(country, default=''):
    c = str(country or '')
    if c in REGION_OF: return REGION_OF[c]
    for part in re.split(r'[/,;&]| and ', c):
        p = part.strip()
        if p in REGION_OF: return REGION_OF[p]
    cl = c.lower()
    for kw, reg in (('nordic', 'EMEA'), ('baltic', 'EMEA'), ('estonia', 'EMEA'), ('latvia', 'EMEA'), ('lithuania', 'EMEA'),
                    ('andorra', 'EMEA'), ('hungary', 'EMEA'), ('romania', 'EMEA'), ('croatia', 'EMEA'), ('slovenia', 'EMEA'),
                    ('bulgaria', 'EMEA'), ('slovakia', 'EMEA'), ('serbia', 'EMEA'), ('ghana', 'EMEA'), ('tanzania', 'EMEA'),
                    ('uganda', 'EMEA'), ('zambia', 'EMEA'), ('botswana', 'EMEA'), ('namibia', 'EMEA'), ('europe', 'EMEA'),
                    ('gulf', 'EMEA'), ('gcc', 'EMEA'), ('africa', 'EMEA'), ('caribbean', 'NAM'), ('latam', 'LATAM'),
                    ('latin', 'LATAM'), ('asia', 'APAC'), ('global', 'EMEA')):
        if kw in cl: return reg
    return default



if __name__ == '__main__':
    firms, seen, regions, searches = [], {}, [], 0
    files = sorted(f for f in glob.glob(os.path.join(SRC, 'pw_*.json')) if not re.search(r'part|meta|tail', os.path.basename(f), re.I))
    for fn in files:
        try:
            d = json.load(open(fn, encoding='utf-8'))
        except Exception as ex:
            print('SKIP', fn, ex); continue
        if not isinstance(d, dict) or not d.get('firms'):  # agents' part-files / meta scratch
            continue
        regions.append(d.get('region', os.path.basename(fn)))
        searches += int(d.get('search_count') or 0)
        for f in d.get('firms') or []:
            if not f.get('firm'): continue
            k = norm(f['firm'])
            prods = f.get('products') or {}
            rec = {
                'firm': f['firm'].strip(), 'group': f.get('group') or '', 'country': f.get('country') or '',
                'region': region_of(f.get('country'), d.get('desk_region') or ''),
                'booking_centres': f.get('booking_centres') or [], 'type': f.get('type') or '',
                'client_assets_usd_bn': f.get('client_assets_usd_bn'), 'assets_year': f.get('assets_year'),
                'products': {k2: cell(prods.get(k2)) for k2 in PRODUCT_KEYS},
                'metals_covered': prods.get('metals_covered') or [], 'advisory_view': prods.get('advisory_view') or '',
                'own_etf_detail': prods.get('own_etf_detail') or '', 'lombard_ltv': prods.get('lombard_ltv') or '',
                'product_evidence': f.get('product_evidence') or [],
                'counterparties': [c for c in (f.get('counterparties') or []) if c.get('name')],
                'lbma_lppm_membership': f.get('lbma_lppm_membership') or '',
                'in_house_trading_desk': f.get('in_house_trading_desk') or '',
                'citi_status': f.get('citi_status') or 'unknown', 'desk_angle': f.get('desk_angle') or '',
                'score': f.get('score'), 'confidence': f.get('confidence') or 'knowledge',
                'sources': f.get('sources') or [], 'src_file': os.path.basename(fn),
            }
            for c in rec['counterparties']:
                c['role'] = c.get('role') if c.get('role') in ROLES else 'other'
                c['name_full'] = str(c['name']); c['name'] = cp_short(c['name'])
            if k in seen:  # merge: fill blanks only
                old = firms[seen[k]]
                for pk in PRODUCT_KEYS:
                    if old['products'][pk] == '?' and rec['products'][pk] != '?': old['products'][pk] = rec['products'][pk]
                names = {(c['name'].lower(), c['role']) for c in old['counterparties']}
                old['counterparties'] += [c for c in rec['counterparties'] if (c['name'].lower(), c['role']) not in names]
                old['product_evidence'] += rec['product_evidence']
                old['sources'] = sorted(set(old['sources']) | set(rec['sources']))
                for fld in ('desk_angle', 'lbma_lppm_membership', 'in_house_trading_desk', 'advisory_view', 'lombard_ltv', 'own_etf_detail'):
                    if not old[fld] and rec[fld]: old[fld] = rec[fld]
                if (old['score'] or 0) < (rec['score'] or 0): old['score'] = rec['score']
                old['src_file'] += ',' + rec['src_file']
                continue
            seen[k] = len(firms); firms.append(rec)

    firms.sort(key=lambda r: (-(r['score'] or 0), r['country'], r['firm']))
    cp_tally, undisclosed = {}, 0
    for r in firms:
        for c in r['counterparties']:
            if c['name'] == 'undisclosed': undisclosed += 1; continue
            cp_tally.setdefault(c['name'], set()).add(r['firm'])
    stats = {
        'total': len(firms), 'regions': regions, 'search_count': searches,
        'by_region': {}, 'by_product': {pk: sum(1 for r in firms if r['products'][pk] == 'Y') for pk in PRODUCT_KEYS},
        'by_product_incl_unverified': {pk: sum(1 for r in firms if r['products'][pk] in ('Y', 'Y?')) for pk in PRODUCT_KEYS},
        'citi_named': sum(1 for r in firms if 'named as counterparty' in r['citi_status'].lower()),
        'undisclosed_counterparty_rows': undisclosed,
        'top_counterparties': sorted(((k, len(v)) for k, v in cp_tally.items()), key=lambda x: -x[1])[:40],
    }
    for r in firms: stats['by_region'][r['region'] or '?'] = stats['by_region'].get(r['region'] or '?', 0) + 1
    out = {'generated': datetime.date.today().isoformat(), 'method': 'Knowledge-first regional sweep by research agents, load-bearing claims web-verified against issuer pages / factsheets / prospectuses; product cells Y = verified, Y? = knowledge (unverified), N = verified not offered, ? = unknown. Counterparty rows carry evidence + URL; confidence=knowledge rows are unverified.',
           'stats': stats, 'firms': firms}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('wrote', OUT, stats['total'], 'firms from', len(files), 'files;', searches, 'searches')
    print(json.dumps(stats['by_region']), json.dumps(stats['by_product']))
    print('top counterparties:', stats['top_counterparties'][:15])
