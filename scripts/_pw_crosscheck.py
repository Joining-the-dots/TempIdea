# -*- coding: utf-8 -*-
"""Cross-check the private-wealth set against the desk's main book (leads.jsonl) and augment.

For every private-wealth firm — especially the ones with sparse product data — look for a matching
record in leads.jsonl and pull across what the desk already knows: metal exposure, other banks,
our-bank status, hedging posture, gold deposit/leasing, financing archetype, the one-line pitch and
the deep-dive index so the row can link straight to the dive.

Writes back into private_wealth.json as a `book` block per firm. Idempotent.
Usage: python _pw_crosscheck.py [--apply]
"""
import json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
APPLY = '--apply' in sys.argv

STOP = {'the', 'and', 'of', 'group', 'holdings', 'holding', 'plc', 'inc', 'llc', 'ltd', 'limited', 'sa', 'ag', 'nv',
        'bv', 'co', 'corp', 'corporation', 'company', 'gmbh', 'spa', 'as', 'ab', 'oyj', 'asa', 'pte', 'bhd', 'tbk',
        'pjsc', 'psc', 'qsc', 'bsc', 'cjsc', 'ojsc', 'pcl', 'private', 'bank', 'banking', 'banque', 'banca', 'banco',
        'wealth', 'management', 'managers', 'manager', 'asset', 'investments', 'investment', 'financial', 'services',
        'international', 'global', 'sarl', 'scа', 'kgaa', 'se', 'cie', 'et', 'de', 'du', 'la', 'le', 'aktiengesellschaft'}


def toks(s):
    s = str(s or '').lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'[^a-z0-9À-ɏ]+', ' ', s)
    return [t for t in s.split() if t and t not in STOP and len(t) > 1]


def key(s):
    t = toks(s)
    return ' '.join(t[:4])


def firstkey(s):
    t = toks(s)
    return t[0] if t else ''


leads = [json.loads(l) for l in open(os.path.join(HERE, 'leads.jsonl'), encoding='utf-8') if l.strip()]
by_key, by_first = {}, collections.defaultdict(list)
for i, r in enumerate(leads):
    nm = r.get('firm') or ''
    k = key(nm)
    if k and k not in by_key: by_key[k] = i
    f = firstkey(nm)
    if f: by_first[f].append(i)

pw = os.path.join(HERE, 'private_wealth.json')
d = json.load(open(pw, encoding='utf-8')); F = d['firms']

BOOK_FIELDS = ['metal_exposure', 'other_banks', 'our_bank_status', 'our_bank_detail', 'hedging_posture',
               'gold_deposit_leasing', 'financing_archetype', 'one_line_pitch', 'opportunities', 'lead_score',
               'jurisdiction', 'venue', 'basis', 'loco', 'ticker', 'desk_decision', 'mandate', 'blockers']


import math
# document frequency of every token across the book, so common words ("gold", "securities",
# "capital") cannot carry a match on their own
DF = collections.Counter()
for _r in leads:
    DF.update(set(toks(_r.get('firm', ''))))
NDOC = max(1, len(leads))


def idf(t):
    return math.log(NDOC / (1 + DF.get(t, 0)))


# a token is "distinctive" if it is rare enough to identify a firm
DISTINCT_MIN = math.log(NDOC / 60.0)   # appears in fewer than ~60 of 7,972 firm names


def score_match(a, b):
    """IDF-weighted token overlap. Requires at least one distinctive shared token."""
    ta, tb = set(toks(a)), set(toks(b))
    if not ta or not tb: return 0.0
    inter = ta & tb
    if not inter: return 0.0
    if not any(idf(t) >= DISTINCT_MIN for t in inter): return 0.0   # only generic words in common
    num = sum(idf(t) for t in inter)
    den = min(sum(idf(t) for t in ta), sum(idf(t) for t in tb))
    if den <= 0: return 0.0
    sc = num / den
    # a single shared token is only credible when it is genuinely rare
    if len(inter) == 1 and max(idf(t) for t in inter) < math.log(NDOC / 12.0): sc *= 0.55
    return sc


CTRY_ALIAS = {'uk': 'united kingdom', 'usa': 'united states', 'us': 'united states', 'uae': 'united arab emirates',
              'korea': 'south korea', 'türkiye': 'turkey', 'czechia': 'czech republic', 'hk': 'hong kong'}


def ctry_set(s):
    s = str(s or '').lower()
    out = set()
    for part in re.split(r'[/,;&()]| and ', s):
        p = part.strip()
        p = CTRY_ALIAS.get(p, p)
        if p and len(p) > 2: out.add(p)
    return out


def ctry_compatible(pw_country, lead_juris):
    """False only when both sides name places and none of them overlap."""
    a, b = ctry_set(pw_country), ctry_set(lead_juris)
    if not a or not b: return True            # unknown on either side -> do not block
    for x in a:
        for y in b:
            if x in y or y in x: return True
    return False


def is_grouped(nm):
    """a tail row that bundles several firms, e.g. 'A / B / C'"""
    return len(re.split(r'\s*/\s*', re.sub(r'\(.*?\)', '', str(nm)))) >= 3


hits, checked, rejected_ctry = 0, 0, 0
sparse_hits = 0
report = []
for f in F:
    nm = f['firm']
    # candidate pool: same first meaningful token
    cands = set()
    for t in toks(nm)[:3]:
        cands.update(by_first.get(t, [])[:400])
    best, bestsc, best_parent = None, 0.0, False
    for i in cands:
        sc = score_match(nm, leads[i].get('firm', ''))
        if sc <= bestsc: continue
        same_ctry = ctry_compatible(f.get('country'), leads[i].get('jurisdiction'))
        if not same_ctry:
            # a very strong name match in another jurisdiction is the PARENT/GROUP record,
            # which is still useful desk intel — keep it, but label it as group-level
            if sc >= 0.90:
                best, bestsc, best_parent = i, sc, True
            else:
                rejected_ctry += 1
            continue
        best, bestsc, best_parent = i, sc, False
    checked += 1
    n_unknown = sum(1 for v in f['products'].values() if v == '?')
    if best is None or bestsc < 0.80:
        f.pop('book', None); continue
    L = leads[best]
    book = {k: L[k] for k in BOOK_FIELDS if L.get(k) not in (None, '', [], {})}
    if not book: continue
    book['_match_name'] = L.get('firm', '')
    if is_grouped(nm): book['_grouped'] = True
    if best_parent: book['_parent_record'] = True
    book['_match_score'] = round(bestsc, 2)
    book['_leads_idx'] = best
    f['book'] = book
    hits += 1
    if n_unknown >= 5: sparse_hits += 1
    report.append((round(bestsc, 2), nm[:46], L.get('firm', '')[:46], n_unknown, sorted(set(book) - {'_match_name', '_match_score', '_leads_idx'})[:6]))

_par = sum(1 for x in F if (x.get('book') or {}).get('_parent_record'))
d.setdefault('stats', {})['book_crosscheck'] = {'firms_matched': hits, 'of': checked,
                                               'sparse_firms_matched': sparse_hits,
                                               'parent_records': _par, 'fields': BOOK_FIELDS}
print('  of which %d are group/parent records (different jurisdiction, labelled)' % _par)
print('matched %d of %d private-wealth firms to the book (%d of them product-sparse); %d candidates rejected on jurisdiction' % (hits, checked, sparse_hits, rejected_ctry))
report.sort(reverse=True)
print('\ntop matches:')
for sc, a, b, unk, flds in report[:22]:
    print('  %.2f  %-46s <- %-46s  ?cells=%-2d  %s' % (sc, a, b, unk, ','.join(flds[:5])))
if APPLY:
    json.dump(d, open(pw, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nwritten to private_wealth.json')
else:
    print('\n(dry run — pass --apply to write)')
