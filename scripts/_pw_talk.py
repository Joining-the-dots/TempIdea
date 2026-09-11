# -*- coding: utf-8 -*-
"""Wealth talking points — a 45-minute run-sheet built from private_wealth.json + pw_products.json.
Writes pw_talking_points.html (an HTML FRAGMENT with scoped CSS) included by deep_dives_index.py
(tab 'Wealth talking points') and _pw_report.py (section).

v2 (2026-09-11): every claim carries a claim id (data-cid) matching the adversarial fact-check batches
(scratchpad/verify/claims_*.json / verified_*.json). Text below already incorporates every correction
returned by the fact-check; _talk_verify_apply.py stamps the verdict badge onto each line. New lines added
after the check (HSBC / Standard Chartered / ANZ passes) carry cid=0 and are badged "sourced, not re-checked".
"""
import json, os, html, collections, re
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, 'private_wealth.json'), encoding='utf-8')); F = d['firms']
try: P = [x for x in json.load(open(os.path.join(HERE, 'pw_products.json'), encoding='utf-8'))['products'] if x['product_type'] != 'none_found']
except Exception: P = []
e = lambda s: html.escape(str(s if s is not None else ''))
n_pb = sum(1 for f in F if f.get('is_pb', True)); n_prod = len(P); n_prodf = len({x['firm'] for x in P})
n_ver = sum(1 for x in P if x['confidence'] == 'verified')
ptypes = collections.Counter(x['product_type'] for x in P)
searches = int(d['stats'].get('search_count', 0)) + int(d['stats'].get('pass2_searches', 0)) + int((d['stats'].get('pass3') or {}).get('search_count', 0))
GP = d['stats'].get('group_passes') or {}

# --- rows in the country tables that are MARKET CHANNEL, not wealth franchises -------------
# mints, refiners, wholesalers, vaults, exchanges, listed vehicles and market-wide statistics.
# They answer "who do the private banks buy from and custody with", which is why they were
# collected, but they are not wealth competitors and must not be ranked as if they were.
CHANNEL = {
 'The Royal Mint', 'BullionVault', 'Gold Bullion International', 'Xetra-Gold (Deutsche Börse Commodities)',
 'Reisebank (DZ Bank / co-operative banks)', 'BayernLB (Sparkassen wholesaler)', 'Perth Mint depository',
 'Global X GOLD', 'Betashares QAU', 'Loomis FXGS (ex-CPoR Devises)', 'Amundi Physical Gold ETC (CA group)',
 'Absa NewGold (JSE)', 'Sprott physical trusts', 'IIBX (GIFT City)', 'Albilad Gold ETF (Saudi)',
 'Antam Logam Mulia', 'Precious-metal funds, market-wide', 'Bank derivative books (OCC, 31 Mar 2026)',
 'Banking system', 'Royal Canadian Mint', 'Pegadaian',
}

# --- product primer (structures our page-sweep under-captured) -----------------------------
_primer = None
for _p in (os.path.join(HERE, 'pb_product_primer.json'),
           os.path.join(os.path.dirname(HERE), '_pw_primer.json')):
    try:
        _primer = json.load(open(_p, encoding='utf-8')); break
    except Exception:
        pass
PRIMER = (_primer or {}).get('structures') or []


# bullet = (cid, text, url). cid = id in the fact-check batches; 0 = added after the check.
S = []
S.append((2, 'Summary', 'Every large wealth franchise sells gold to its clients in some form. One global franchise\'s client-facing metals shelf is one paper-gold product in one booking centre.', [
 (1, '%d private banks and wealth managers worldwide, %d of them private-bank or wealth arms. %d named client products across %d firms.' % (len(F), n_pb, n_prod, n_prodf), ''),
 (2, 'Citi is an LBMA market maker, became the fifth member of London clearing (LPMCL) on 6 July 2026, appears on the LBMA list of London vaulting custodians, and Citibank N.A. carries the second-largest US precious-metals derivative book: US$236bn notional at 31 March 2026 vs JPMorgan US$509bn (year-end 2025: Citi US$217bn, JPMorgan US$479bn, Bank of America US$121bn).', 'https://www.occ.gov/publications-and-resources/publications/quarterly-report-on-bank-trading-and-derivatives-activities/index-quarterly-report-on-bank-trading-and-derivatives-activities.html')], None))

S.append((5, 'What clients are buying', 'Volumes disclosed by the firms themselves over the last twelve months: account counts, tonnes and balances.', [
 (4, 'Singapore: UOB\'s total transacted physical gold volume jumped 59% in 2025; Singapore investment demand hit 9.6 t (+48%); UOB moved its gold counters to appointment-only in February 2026.', 'https://e.vnexpress.net/news/business/markets/uob-singapore-s-only-bank-selling-physical-gold-extends-hours-and-shifts-to-appointment-only-service-5039409.html'),
 (5, 'OCBC retail: customers investing in gold and silver 2.5x year on year; two in three first-time investors started with gold or silver; new precious-metals investors tripled month on month in January 2026.', 'https://www.ocbc.com/group/media/release/2026/ocbc-sees-gold-and-silver-emerge-as-first-time-investors-choice.page'),
 (6, 'DBS announced a tokenised 1 g physical gold product held in its own Singapore vault on 11 June 2026, with retail launch in H2 2026 and physical redemption.', 'https://www.dbs.com/newsroom/DBS_expands_gold_offerings_with_market_first_tokenised_physical_gold'),
 (7, 'Korea: the three banks\' gold-banking balances were KRW 1.93 trn at end-2025 (about 331,000 accounts in late December) and peaked at KRW 2.44 trn in January 2026; four banks sold 3,745 kg of bars in 2025.', 'https://www.fnnews.com/news/202606161819598224'),
 (8, 'Taiwan: over 5 million gold passbook accounts nationwide; Bank of Taiwan alone has more than 700,000, and its single-trade volume roughly doubled year on year in January to September 2025.', 'https://www.ctee.com.tw/news/20251020700272-439901'),
 (9, 'Turkey: precious-metal deposits reached US$90.4bn, 56% of individuals\' FX deposits (January 2026); Kuveyt Türk\'s metal accounts went from TL 133bn to TL 322bn in one year.', 'https://www.kuveytturk.com.tr/medium/denetim-raporu-31-aralik-2025-3740.pdf'),
 (10, 'Indonesia: two newly licensed bullion banks (Pegadaian, BSI) manage 153 t, about Rp 360 trn or US$20bn, within about 17 months of licensing; BSI reported 766,742 gold-savings customers by February 2026.', 'https://money.kompas.com/read/2026/08/18/124400826/bullion-bank-ri-kelola-emas-rp-360-triliun'),
 (11, 'Germany: Reisebank\'s precious-metals revenue was about EUR 1.15bn in Q1 2026 alone (+70%); BayernLB\'s gold volume doubled in Q1 2026; Xetra-Gold holds 171 t (EUR 19.4bn).', 'https://www.presseportal.de/pm/116526/6208449'),
 (12, 'UK: gold bullion bought online at the Royal Mint rose 142% in calendar 2025 (silver +253%); BullionVault holds 43 t of client gold and US$9bn of client metal for 130,000 funded clients.', 'https://www.royalmint.com/aboutus/press-centre/royal-mint-reports-record-year-for-precious-metals-investments-as-silver-demand-soars/'),
 (13, 'Canada and Australia: the Royal Canadian Mint\'s precious-metals revenue rose to C$1.84bn (+60%); the Perth Mint depository grew 40% to A$10.4bn.', 'https://www.perthmint.com/news/media-announcements/corporate/annual-report-2024-25/'),
 (14, 'India: ICICI Prudential gold ETF ₹25.8k cr, SBI ₹24.4k cr, HDFC ₹22.3k cr, Kotak ₹12.8k cr (September 2026).', 'https://www.tickertape.in/etfs/icici-prudential-gold-etf-IPEG'),
 (15, 'Switzerland and Liechtenstein: LGT Bank Ltd\'s physical precious metals held for clients rose 73% to CHF 1.73bn in 2025, and Pictet\'s rose 44% to CHF 843m.', 'https://www.pictet.com/ca/en/corporate-news/release-full-year-2025-figures'),
 (0, 'HSBC: the Hong Kong Gold Token passed US$1bn of cumulative trades and 100,000 transactions by November 2025; HSBC\'s 2026 affluent-investor survey found 62% of Asia and Middle East respondents plan to add gold in 2026; group wealth balances are US$2.1trn, over US$1trn in Asia.', 'https://www.caixinglobal.com/2025-11-11/hsbcs-gold-token-tops-1-billion-in-trades-102378000.html')], None))

fam = [
 (16, 'Gold account, unallocated', 'gold_account_unallocated', 'A claim on the bank for X grams or ounces, no specific bars; priced off LBMA or the bank\'s own two-way price; the bank hedges in the interbank market. Cheapest to run, highest margin, usually no delivery right.', 'Swiss Metallkonto fees in the catalogue run from 0.20% p.a. (Luzerner KB) through 0.30% (Basler KB gold) to 0.80% (ex-CS/UBS); UOB Gold Savings 0.25% p.a.; Emirates NBD gram gold: 2.1% arrangement under USD 250k, a one-off 0.315% custody-and-insurance charge if redeemed within 5 years (1.05% after); HSBC Wayfoong Statement Gold: spread capped at 4%; Citi HK Gold Manager: spread only.'),
 (17, 'Metal account, allocated', 'gold_account_allocated', 'Client owns identified bars (or a pro-rata share of a pool) in a named vault; the bank earns a custody fee and the spread. JPMorgan Private Bank offers claims on gold in its own vault: CNBC reports unallocated claims from about US$250k and allocated 400 oz bars from about US$1m with storage and insurance fees.', 'UBS key4 gold 0.35% p.a. storage from 0.1 g; Intesa Deposito Oro 0.75% p.a.; Royal Canadian Mint ETRs 0.35% gold / 0.45% silver; BMO Gold Deposit Program at the Mint.'),
 (18, 'Physical bars and coins', 'physical_bullion', 'Sold over the counter, in the app or delivered; stored by the bank or taken away. Volume driver in Asia and Germany; the buy-back policy is the product (OCBC Hong Kong withdrew bar buy-back from 1 February 2026).', 'Reisebank, ZKB, UOB, Shinhan, Emirates NBD branded bars, Canadian bank online stores; Fidelity/FideliTrade buy commissions 2.90% down to 0.99% and sell 2.00% down to 0.75%, storage 0.125% per quarter.'),
 (19, 'Savings / accumulation plan', 'gold_savings_plan', 'Monthly gram or coin accumulation from a small ticket; the entry product for the mass-affluent and the feeder for the account business.', 'Reisebank Goldsparplan from EUR 25/month; Austrian Sparkassen coin plans from EUR 50; Bank of Taiwan regular plan +40%; Garanti\'s plan funded from a credit-card limit; BSI from 0.02 g.'),
 (20, 'Digital gold / token', 'digital_gold_token', 'Tokenised claim on vaulted gold, 24/7 dealing, fractional; the retail growth product of 2025 to 2026 in Hong Kong and Singapore.', 'HSBC Gold Token: 0.001 oz units, no dealing or storage fee but a bank margin of up to 2% (5% off-hours), no delivery, over US$1bn traded by November 2025, bullion vaulted in London; DBS Physical Gold Token (1 g in a DBS vault, announced June 2026 for H2); AMINA Gold Token with credit lines.'),
 (21, 'Gold deposit / DCI', 'gold_deposit_dci', 'Term product where the client\'s gold earns a yield (lent by the bank) or a deposit converts into gold at maturity. Rare outside Turkey, China and Malaysia, and a natural desk product.', 'CMB 金生利 pays the yield in grams; Kuveyt Türk gold-to-gold participation account; CIMB Gold Convertible (gold as the second currency); HSBC China gold-linked structured deposits; Citi HK Gold Premium Investment.'),
 (22, 'Structured notes on gold', 'structured_note', 'Autocalls, reverse convertibles and capital-protected notes on XAU; distributed through the PB advisory channel; hedged by the issuing desk.', 'Vontobel carried CHF 1.33bn of physical metal at end-2025 to hedge its metal-linked structured products; Citi issues market-linked notes on SPDR Gold Trust for the Wells Fargo Advisors shelf (SEC 424B2).'),
 (23, 'Lombard against metal', 'lombard_vs_metal', 'Borrowing against bullion, metal accounts or ETFs. Rare among UK and US banks, which is where the opening is.', 'Swiss houses lend against metal accounts and bullion (LTV not published per asset); Money Metals lends up to 65% against bullion in the US; AMINA extends credit lines against its gold token; ANZ Investment Lending accepts the ASX gold ETPs.'),
 (24, 'Own fund / ETF and advisory allocation', 'own_fund_etf', 'The house implements its gold view through its own vehicle: cleanest for discretionary mandates and the fastest way to move client assets.', 'ANZ Private seeded a State Street gold fund (0.14%) in July 2024 for its strategic allocation and maintains an overweight; JPMorgan Private Bank recommends about 5%; HSBC Global Private Banking is overweight gold; Coutts and ABN AMRO have added gold sleeves to model portfolios.'),
]
fam_rows = ''.join('<tr data-cid="%d"><td><b>%s</b><div class="pwt-m">%d in catalogue</div></td><td>%s</td><td>%s</td></tr>' % (cid, e(n), ptypes.get(k, 0), e(w), e(b)) for cid, n, k, w, b in fam)
S.append((8, 'The products, explained', 'Nine families cover the whole shelf. For each: what the client actually holds, how the bank earns, and the benchmark fees a client can find online today.', [], ('<table class="pwt-t"><thead><tr><th style="width:18%%">Family</th><th style="width:44%%">What the client holds, and how the bank earns</th><th>Published fees</th></tr></thead><tbody>%s</tbody></table>' % fam_rows)))

# ---- country top-3 (cid, firm, figure, url) — text already corrected per verified_B.json
C = [
 ('Switzerland & Liechtenstein', 'Physical precious metals carried on the bank\'s own balance sheet to back client metal accounts (31 Dec 2025 annual reports).', [
   (25, 'Julius Baer', 'CHF 4.89bn physical precious metals (+53%), 2025 accounts', 'https://www.juliusbaer.com/en/media/news-portal/presentation-of-the-2025-full-year-results'),
   (26, 'LGT Bank Ltd (Vaduz)', 'CHF 1.73bn physical PM (+73%)', 'https://vpr.hkma.gov.hk/statics/assets/doc/100305/ar_25/ar_25_eng.pdf'),
   (27, 'Vontobel', 'CHF 1.33bn physical PM hedging its metal-linked structured products; CHF 873m PM swaps, CHF 3.16bn PM derivatives in total', 'https://www.vontobel.com/'),
   (28, 'Pictet', 'CHF 843m physical PM (+44%); CHF 3.6bn PM derivatives volume; own physical gold fund', 'https://www.pictet.com/ca/en/corporate-news/release-full-year-2025-figures')]),
 ('United Kingdom', 'No UK bank publishes a client metals book; the disclosed volumes sit with the Mint, the platforms and the trusts.', [
   (29, 'The Royal Mint', '£1.18bn precious-metals revenue; RMAU ETC about US$1.4bn; £838m of metal held under consignment arrangements, counterparty not named', 'https://assets.publishing.service.gov.uk/media/68c7dbc753f33f9d46e2067f/RMTF_2024-25_FINAL.pdf'),
   (30, 'BullionVault', 'US$9bn client metal: 43 t gold, 1,134 t silver, 130,000 clients', 'https://www.bullionvault.com/about-us/in-the-press'),
   (31, 'Personal Assets Trust (Troy)', '£156m direct bullion, 9.2% of NAV, custodian JPMorgan', 'https://www.patplc.co.uk/wp-content/uploads/sites/5/2026/06/PAT-Annual-Report-2026.pdf')]),
 ('United States', 'Wealth physical programmes run through white-label plumbing; the disclosed numbers are the trusts and the OCC derivative table.', [
   (32, 'Sprott physical trusts', 'PHYS US$14.7bn (114 t) + PSLV US$12.6bn (215 Moz)', 'https://www.sec.gov/Archives/edgar/data/0001477049/000199937126017864/ex99-1.htm'),
   (33, 'Gold Bullion International', 'US$8bn under administration, 200,000 accounts (self-reported); the platform behind Merrill and Oppenheimer physical programmes', 'https://gbi.co/'),
   (34, 'Bank derivative books (OCC, 31 Mar 2026)', 'JPMorgan US$509bn, Citibank US$236bn PM notional; year-end 2025: JPMorgan US$479bn, Citi US$217bn, Bank of America US$121bn', 'https://www.occ.gov/publications-and-resources/publications/quarterly-report-on-bank-trading-and-derivatives-activities/index-quarterly-report-on-bank-trading-and-derivatives-activities.html')]),
 ('Germany & Austria', 'Retail and private-bank gold moves through two wholesale channels plus the exchange-traded bar.', [
   (35, 'Xetra-Gold (Deutsche Börse Commodities)', '171 t, EUR 19.4bn under custody (Jun 2026)', 'https://www.deutsche-boerse.com/'),
   (36, 'BayernLB (Sparkassen wholesaler)', '46 t gold (2024) and 248 t silver (2025); Q1 2026 gold volume doubled', 'https://de.finance.yahoo.com/nachrichten/bayernlb-steigt-gold-handel-1-053000432.html'),
   (37, 'Reisebank (DZ Bank / co-operative banks)', '~EUR 1.15bn PM revenue in Q1 2026 (+70%); FY2025 +55%', 'https://www.presseportal.de/pm/116526/6208449'),
   (38, 'Flossbach von Storch', 'about 9.2% of the Multiple Opportunities fund in precious metals, roughly EUR 1.9bn (Aug 2026 factsheet)', 'https://www.flossbachvonstorch.de/')]),
 ('Turkey', 'The largest gold-banking market in the set: gram accounts, gold time deposits and physical delivery at every bank.', [
   (39, 'Banking system', 'US$90.4bn precious-metal deposits = 56.4% of individuals\' FX deposits (Jan 2026)', 'https://www.nefes.com.tr/turkiyede-altinda-bir-ilk-dolar-ve-euroyu-gecti-98995'),
   (40, 'Kuveyt Türk', 'TL 322bn (~US$7.5bn) PM participation accounts; TL 172bn forward gold purchases', 'https://www.kuveytturk.com.tr/medium/denetim-raporu-31-aralik-2025-3740.pdf'),
   (41, 'Precious-metal funds, market-wide', 'TL 1.3trn across all Turkish precious-metal mutual and pension funds (Nov 2025)', 'https://www.kuveytturkportfoy.com.tr/blog/finans/kiymetli-maden-fonlarinin-toplam-buyuklugu')]),
 ('Singapore & Hong Kong', 'The Asian wealth hubs: growth rates rather than balances are disclosed, plus the token and ETF launches.', [
   (42, 'UOB', 'total transacted physical gold volume +59% in 2025; only local bank buying back metal', 'https://e.vnexpress.net/news/business/markets/uob-singapore-s-only-bank-selling-physical-gold-extends-hours-and-shifts-to-appointment-only-service-5039409.html'),
   (43, 'OCBC (retail)', 'PM investors 2.5x y/y; new PM investors tripled in Jan 2026', 'https://www.ocbc.com/group/media/release/2026/ocbc-sees-gold-and-silver-emerge-as-first-time-investors-choice.page'),
   (44, 'HSBC (Hong Kong)', 'Gold Token over US$1bn traded and 100,000+ transactions by Nov 2025; Hang Seng Gold ETF about HK$1.28bn, HSBC gold custodian and dealer', 'https://www.caixinglobal.com/2025-11-11/hsbcs-gold-token-tops-1-billion-in-trades-102378000.html'),
   (45, 'DBS', 'tokenised 1 g gold in its own vault announced June 2026 for H2 retail launch', 'https://www.dbs.com/newsroom/DBS_expands_gold_offerings_with_market_first_tokenised_physical_gold')]),
 ('South Korea & Taiwan', 'Bank gold accounts at mass scale, none with a bullion-bank parent.', [
   (46, 'Shinhan (Gold Riche)', 'KRW 1.30trn, 187,859 accounts; 3,000 kg of bars sold in 2025; silver banking KRW 241bn (Dec 2025)', 'https://www.newsis.com/view/NISX20251226_0003455435'),
   (47, 'KB + Woori', '~KRW 678bn combined (derived from the three-bank total); four-bank bar sales 3,745 kg in 2025', 'https://v.daum.net/v/20251229150904544'),
   (48, 'Bank of Taiwan', '>700,000 passbook accounts of >5 million nationwide; trade volume roughly doubled Jan to Sep 2025', 'https://www.setn.com/News.aspx?NewsID=1787681')]),
 ('India', 'Banks cannot hold client gold accounts; the volume is in the group ETFs and the import channel.', [
   (49, 'ICICI Prudential Gold ETF', '₹25,822 cr (~US$2.9bn)', 'https://www.tickertape.in/etfs/icici-prudential-gold-etf-IPEG'),
   (50, 'SBI Gold ETF', '₹24,425 cr; SBI had also mobilised 13.2 t cumulatively under the Gold Monetisation Scheme by FY2020', 'https://www.tickertape.in/etfs/sbi-gold-etf-SBIG'),
   (51, 'HDFC Gold ETF', '₹22,285 cr (11 Sep 2026)', 'https://stackwealth.in/mutual-funds/hdfc-gold-etf'),
   (52, 'IIBX (GIFT City)', '93 t of gold traded in FY2024-25; 1,137 t of silver cumulatively since the Dec 2023 launch', 'https://www.iibx.co.in/')]),
 ('Indonesia', 'Two licensed bullion banks and one state refiner; entirely domestic supply chain.', [
   (53, 'Pegadaian', '155 t under management (H1 2026)', 'https://keuangan.kontan.co.id/'),
   (54, 'Bank Syariah Indonesia', '~24 t; 8.06 t traded in H1 2026; 766,742 gold-savings customers (Feb 2026)', 'https://www.krusial.com/'),
   (55, 'Antam Logam Mulia', '37.4 t sold in 2025 (down from the 43.8 t record in 2024), 18.1 t in H1 2026', 'https://www.kabarbursa.com/')]),
 ('Gulf', 'Product launches are public, volumes mostly not; the balance-sheet notes give the size signal.', [
   (56, 'Emirates NBD', 'commodity-options notional AED 7.6bn (+44%); branded bars in the app; gold loans, leasing and repo in its bullion-service FAQ', 'https://cdn.emiratesnbd.com/en/assets/file/ir/annual_report_2025.pdf'),
   (57, 'National Bank of Fujairah', 'AED 245m of gold borrowings matched against client gold loans', 'https://ent.news/2025/10/1678.pdf'),
   (58, 'Albilad Gold ETF (Saudi)', '470 kg of gold (Sep 2026)', 'https://www.saudiexchange.sa/')]),
 ('Canada', 'All bank programmes custody at the Royal Canadian Mint; the bank balance sheets show the scale.', [
   (59, 'TD', 'C$35.0bn trading commodities incl. C$2.1bn of repos collateralised by physical PM', 'https://www.td.com/'),
   (60, 'RBC', 'C$9.1bn precious metals (+51%); PM liabilities C$3.2bn (4x)', 'https://www.rbc.com/investor-relations/_assets-custom/pdf/ar_2025_e.pdf'),
   (61, 'CIBC', 'C$6.5bn precious metals (+55%)', 'https://www.cibc.com/'),
   (62, 'BMO', 'ZGLD gold ETF C$1.72bn (Aug 2026); C$6.4bn precious metals in other assets (down from C$9.5bn)', 'https://www.bmo.com/ir/archive/en/bmo_ar2025.pdf')]),
 ('Australia', 'Private banks distribute; the physical franchise sits with the Mint and the ETPs.', [
   (63, 'Perth Mint depository', 'A$10.4bn client metal (+40%); PMGOLD about 11.9 t (Jun 2026)', 'https://www.perthmint.com/news/media-announcements/corporate/annual-report-2024-25/'),
   (64, 'Global X GOLD', 'about A$5.4bn (Jun 2026), JPMorgan London custody', 'https://www.globalxetfs.com.au/funds/gold/'),
   (65, 'Betashares QAU', 'A$1.23bn; JPMorgan London holds the bullion; Citigroup Pty is fund-level custodian per the PDS on file', 'https://www.betashares.com.au/fund/gold-etf-currency-hedged/'),
   (0, 'ANZ Private / State Street Gold Fund', 'A$128m (Aug 2026), seeded with about A$50m in July 2024; ANZ Private\'s only metals product', 'https://www.ssga.com/au/en_gb/institutional/mf/state-street-gold-fund-sst4481au')]),
 ('France, Luxembourg & South Africa', '', [
   (66, 'Amundi Physical Gold ETC (CA group)', 'US$10.8bn, HSBC metal counterparty and custodian', 'https://www.amundietf.lu/'),
   (67, 'Absa NewGold (JSE)', 'ZAR 40.3bn, 13.6 t, ICBC Standard custodian', 'https://etfsa.co.za/wp-content/uploads/2024/05/absa-newgold-mar2026.pdf'),
   (68, 'Loomis FXGS (ex-CPoR Devises)', 'SEK 689m revenue line (FY2025); CPoR is the French banks\' historical gold wholesaler', 'https://www.loomis.com/')]),
]
def _ctry_block(n, lede, rows):
    wealth = [r for r in rows if r[1] not in CHANNEL]
    chan = [r for r in rows if r[1] in CHANNEL]
    def _li(rs):
        return ''.join('<li data-cid="%d"><b>%s</b> — %s%s</li>' % (cid, e(a), e(b), (' <a href="%s" target="_blank" rel="noopener">src</a>' % e(u)) if u else '') for cid, a, b, u in rs)
    out = ['<div class="pwt-c"><h4>%s</h4>' % e(n)]
    if lede: out.append('<p class="pwt-m">%s</p>' % e(lede))
    if wealth: out.append('<ol>%s</ol>' % _li(wealth))
    if chan:
        out.append('<div class="pwt-chan"><span class="pwt-chan-h">Market channel, not a wealth competitor</span><ol>%s</ol></div>' % _li(chan))
    out.append('</div>')
    return ''.join(out)


ctry_html = ''.join(_ctry_block(n, lede, rows) for n, lede, rows in C)
S.append((8, 'The largest positions, by country', 'The best disclosed volume in each key market. Wealth franchises are listed first; mints, refiners, wholesalers, vaults and listed vehicles are shown separately underneath, because they are the supply and custody channel rather than competitors for a client relationship. Units differ by market (balance-sheet metal, account balances, tonnes, fund AUM), so compare within a country, not across.', [], '<div class="pwt-grid">%s</div>' % ctry_html))

# ---- HSBC / Standard Chartered / ANZ head-to-head (from the dedicated passes)
scb = GP.get('standard') or {}
h2h = [
 (0, 'HSBC (US$2.1trn wealth balances, over US$1trn in Asia): the client gold shelf is concentrated in Hong Kong. Hong Kong has Wayfoong Statement Gold (1 mace units, spread capped at 4%, no delivery, available to Global Private Banking accounts) and the SFC-authorised Gold Token (0.001 oz, no fees, bank margin up to 2%, bullion vaulted by HSBC Bank plc in London), plus custody and dealing for the Hang Seng Gold ETF. Singapore, Taiwan and Australia carry no gold product; India is served by the HSBC AMC gold ETF; Malaysia has a counter-only gold account (conventional bank, not Amanah); China gold-linked structured deposits. HSBC is not on India\'s 2026 to 2029 list of authorised bullion importers. Global Private Banking is overweight gold and reaches HK products through the local bank.', 'https://www.hsbc.com.hk/investments/products/gold-token/'),
 (0, 'ANZ (Private >A$9bn): a liquidity competitor, not a shelf competitor. ANZ Private\'s only metals product is the State Street Gold Fund it seeded in July 2024 (feeder into SPDR Gold MiniShares, 0.14%, A$128m by Aug 2026, mostly price appreciation), backed by a maintained overweight. No allocated metal, physical, Lombard or gold-linked notes; retail broking went to CMC, Asian wealth to DBS in 2018, the Singapore vault closed in 2019. ANZ is an LBMA full member, not a market maker, and its institutional commodities trading assets rose 42% to A$9.1bn in FY2025.', 'https://www.anz.com.au/personal/private-banking/insights/global-market-outlook-2026/'),
]
if scb.get('citi_angle'):
    h2h.append((0, 'Standard Chartered: ' + scb['citi_angle'][:900], ''))
else:
    h2h.append((0, 'Standard Chartered: dedicated pass in progress; this line is replaced automatically when it lands.', ''))
S.append((2, 'HSBC, Standard Chartered and ANZ', 'The three banks most often encountered in Asia.', h2h, None))

S.append((5, 'Five competitor product designs', 'Each of these is live today.', [
 (69, 'JPMorgan Private Bank: gold claims in its own vault, reported by CNBC as unallocated claims from about US$250k and allocated 400 oz bars from about US$1m with storage and insurance fees, alongside a ~5% strategic-allocation view. The desk-and-vault product; Citi now has the London vault to match it.', 'https://www.cnbc.com/'),
 (70, 'UBS key4 gold: allocated gold in the app from 0.1 g, 0.35% p.a. storage, 1.4% to 0.9% dealing, home delivery by registered post. The mass-affluent version of the same thing.', 'https://www.ubs.com/'),
 (71, 'DBS Physical Gold Token: 1 g per token in a DBS Singapore vault, 24/7 dealing, physical redemption, retail and accredited tiers, announced June 2026 for H2 launch. The tokenised wrapper on allocated custody.', 'https://www.dbs.com/newsroom/DBS_expands_gold_offerings_with_market_first_tokenised_physical_gold'),
 (72, 'Emirates NBD: a fully priced gram-gold account (2.1% arrangement under USD 250k, one-off 0.315% custody charge on early redemption) plus ENBD-branded bars in the app, with gold loans, leasing and repo listed in its bullion-service FAQ. The most complete shelf built by one bank in 18 months.', 'https://www.emiratesnbd.com/'),
 (73, 'China Merchants Bank 金生利 and Kuveyt Türk gold-to-gold accounts: the client\'s gold earns a yield paid in grams. The desk\'s lease book turned into a client product.', 'https://www.cmbchina.com/')], None))

S.append((4, 'One global franchise today, as the client sees it', 'What is on Citi\'s client pages across booking centres.', [
 (74, 'Citi\'s only advertised client gold product found anywhere is the Hong Kong "Gold Manager": cash-settled, loco-London-referenced paper gold, HKD 5,000 minimum, no delivery, plus a Gold Premium Investment deposit.', 'https://www.citibank.com.hk/'),
 (75, 'No comparable product is marketed on Citi\'s US, Singapore, UAE or UK client sites. Structured notes, OTC hedging and securities-backed lending exist but are not presented as metals products.', ''),
 (76, 'Peers in the same booking centres: HSBC HK (paper gold, token, ETF custody), DBS/UOB/OCBC SG (accounts, bars, token), Emirates NBD/FAB UAE (accounts, bars), JPMorgan/Morgan Stanley US (allocated and unallocated programmes), UBS/JB/Pictet CH (accounts, physical, Lombard).', ''),
 (77, 'The gap is not in the wholesale capability: LBMA market maker, fifth LPMCL member since 6 July 2026, a London vault on the LBMA custodian list run with Malca-Amit, and a US$236bn precious-metals derivative book at March 2026.', 'https://www.citigroup.com/global/news/press-release/2026/citi-clearing-member-london-precious-metals-clearing-limited')], None))

S.append((3, 'How big could it be', 'Peers disclose the physical metal they carry to back client accounts. Against client assets:', [
 (78, 'LGT Bank Ltd CHF 1.73bn of client-backing metal on CHF 142bn of client assets is about 1.2%; Pictet CHF 843m on CHF 757bn under management or custody is about 0.1%; Julius Baer\'s reported CHF 4.9bn on CHF 521bn AUM would be about 0.9% if confirmed. (ESTIMATE, derived from the annual reports.)', 'https://www.pictet.com/ca/en/corporate-news/release-full-year-2025-figures'),
 (79, 'Applied to a wealth franchise in the hundreds of billions of client assets, a mature metal-account shelf is a low-single-digit-billion physical book, earning custody fees, dealing spread and a lease or funding margin on unallocated balances. (ESTIMATE.)', ''),
 (80, 'The retail signal in Asia is faster: Korean bank gold balances more than tripled from KRW 0.78trn at end-2024 to a KRW 2.44trn peak in January 2026, then fell 29% to KRW 1.73trn by July; Taiwan passbook volumes roughly doubled; Indonesia\'s bullion banks reached 153 t in about 17 months.', 'https://www.fnnews.com/news/202606161819598224')], None))

S.append((4, 'A potential shelf', 'Three tiers. Each maps to a competitor product that already exists.', [
 (81, 'Tier 1 (private bank, all booking centres): an allocated precious-metals account in the group\'s own London vault with physical delivery via a secure-logistics partner, plus Lombard lending against it. Template: JPMorgan PB vault claims; Julius Baer / LGT metal accounts.', ''),
 (82, 'Tier 2 (affluent and private-client tiers in SG, HK, UAE, UK): an unallocated gram-gold account with physical redemption in kilobars or 100 g, priced off loco-London and desk-hedged. Template: UOB Gold Savings, Emirates NBD gram gold, HSBC Wayfoong Statement Gold; an existing paper-gold product could be extended beyond one booking centre and given a delivery right.', ''),
 (83, 'Tier 3 (yield and structured): gold-linked deposits and a gold DCI where a lease book funds the client yield; a standing gold autocall/reverse-convertible programme; a house strategic-allocation view implemented via a physically backed vehicle. Templates: CMB, Kuveyt Türk, CIMB Gold Convertible, HSBC China structured deposits, ANZ Private gold fund.', ''),
 (84, 'KPIs to set now: metal-account balances and account count by booking centre, physical delivered (kg), Lombard drawn against metal, structured-note issuance on XAU, share of PB clients holding any metal product.', '')], None))

S.append((4, 'Risks and constraints', '', [
 (85, 'US tax: physical gold and grantor-trust ETFs are taxed as collectibles at 28%; IRA metal must sit at an approved depository. Design the US product around that (allocated at a depository, IRA-eligible).', ''),
 (86, 'Conduct: unallocated accounts are a claim on the bank, not metal; say so in the T&Cs (BEA\'s Gold Account brochure and HSBC\'s Wayfoong Statement Gold key facts do). Buy-back terms are worth setting deliberately, since they can change: OCBC Hong Kong withdrew bar buy-back in February 2026.', 'https://www.hkbea.com/pdf/en/pdf/account-services/Gold_Account_Principal_Brochure.pdf'),
 (87, 'Regulation: mainland China has restricted new paper-gold positions since 2022 and the restrictions have continued; Shariah products need an immediate-ownership structure such as the bai\' as-sarf contract Maybank\'s MIGA-i describes.', ''),
 (88, 'Operations: UOB moved its gold counters to appointment-only in February 2026 under demand; logistics and vault capacity are part of the product.', 'https://e.vnexpress.net/news/business/markets/uob-singapore-s-only-bank-selling-physical-gold-extends-hours-and-shifts-to-appointment-only-service-5039409.html'),
 (89, 'Conflicts: a large bank is often already fund-level custodian or note issuer for a peer\'s products (Citigroup Pty is fund custodian of Betashares QAU per its PDS, where JPMorgan holds the bullion; Citi issues gold-linked notes on the Wells Fargo shelf). Map those before any launch.', ''),
 (90, '45 of the 91 largest metals books name no liquidity provider.', '')], None))





# ---- structures the public-page sweep under-captures (sold by RMs, not advertised) ----
if PRIMER:
    _pr_rows = []
    for _x in PRIMER:
        _ex = '; '.join('%s %s' % (str(_v.get('firm', ''))[:34], str(_v.get('product', ''))[:44]) for _v in (_x.get('examples') or [])[:3])
        _pr_rows.append('<tr data-cid="0"><td><b>%s</b><div class="pwt-m">%s</div></td><td>%s<div class="pwt-m" style="margin-top:.3rem"><b>What the client takes on.</b> %s</div></td><td>%s<div class="pwt-m" style="margin-top:.3rem"><b>Desk supplies.</b> %s</div></td></tr>' % (
            e(_x.get('name', '')), e(str(_x.get('typical_terms', ''))[:150]), e(str(_x.get('how_it_works', ''))[:420]),
            e(str(_x.get('client_risk', ''))[:200]), e(_ex or 'no named example verified'), e(str(_x.get('desk_hook', ''))[:180])))
    S.append((6, 'The structures a product sweep misses', 'Sold through relationship managers rather than advertised on a product page.', [],
              '<table class="pwt-t"><thead><tr><th style="width:17%%">Structure</th><th style="width:45%%">How it works / what the client is really taking</th><th>In the market / what the desk prices</th></tr></thead><tbody>%s</tbody></table>' % ''.join(_pr_rows)))
else:
    S.append((6, 'The structures a product sweep misses', 'Primer pending: run the product-primer pass, then regenerate. These are the yield-enhancement and financing structures (dual-currency deposits, lending against metal, put-selling, accumulators, gold-linked notes) that private banks sell through relationship managers rather than advertise.', [], None))


# both title variants: the desk copy keeps the original wording, the published copy is genericised

# --- fold the RM-sold structures into the single products section ---------------------------
_prod_i = next((i for i, x in enumerate(S) if x[1] == 'The products, explained'), None)
_miss_i = next((i for i, x in enumerate(S) if x[1] == 'The structures a product sweep misses'), None)
if _prod_i is not None and _miss_i is not None:
    _pm, _pt, _pl, _pb, _ptab = S[_prod_i]
    _mm, _mt, _ml, _mb, _mtab = S[_miss_i]
    _combined = (
        '<h4 class="pwt-sub">On the shelf &mdash; what the bank advertises</h4>'
        + (_ptab or '')
        + '<h4 class="pwt-sub">Sold by the relationship manager, not advertised</h4>'
        + '<p class="pwt-lede">%s</p>' % _ml
        + (_mtab or ''))
    _lede = ('The families a client can find on a public page, with their published fees, followed by the '
             'yield-enhancement and financing structures sold through relationship managers.')
    S[_prod_i] = (_pm, _pt, _lede, _pb, _combined)
    S.pop(_miss_i)

ORDER = [
 ('Summary',),
 ('The products, explained',),
 ('Five competitor product designs',),
 ('What clients are buying',),
 ('The largest positions, by country',),
 ('HSBC, Standard Chartered and ANZ',),
 ('One global franchise today, as the client sees it', 'One global franchise today, as the client sees it'),
 ('How big could it be',),
 ('A potential shelf', 'A potential shelf — strategic idea'),
 ('Risks and constraints',),
]
_rank = {t: i for i, grp in enumerate(ORDER) for t in grp}
S.sort(key=lambda x: _rank.get(x[1], 99))


def _slug(t):
    return 'pwt-' + re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')[:40]

total = sum(m for m, *_ in S)
css = '''<style>
.pwt{max-width:1100px;font-size:15px;line-height:1.5}
.pwt h3{font-size:1.25rem;margin:1.6rem 0 .2rem;display:flex;align-items:baseline;gap:10px}
.pwt .pwt-lede{color:#43536b;margin:.2rem 0 .6rem;max-width:80ch}
.pwt ul{margin:.2rem 0 0 1.2rem;padding:0}.pwt li{margin:.3rem 0}
.pwt a{font-size:.8em}
.pwt .pwt-m{color:#7a8696;font-size:.86em}
.pwt .pwt-sub{font-family:inherit;font-size:.95rem;font-weight:600;margin:1.1rem 0 .15rem;
 padding-bottom:.22rem;border-bottom:1px solid #c6d2de;color:#1f5b8d;letter-spacing:.01em}
.pwt .pwt-sub:first-child{margin-top:.3rem}
.pwt-t{border-collapse:collapse;width:100%;font-size:.93em;margin:.4rem 0}.pwt-t th{text-align:left;font-size:.78em;text-transform:uppercase;letter-spacing:.05em;color:#7a8696;border-bottom:2px solid #1f5b8d;padding:6px 8px}.pwt-t td{vertical-align:top;padding:7px 8px;border-bottom:1px solid #e4e9ef}
.pwt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px 26px}
.pwt-c h4{margin:.4rem 0 .1rem;font-size:1rem}.pwt-c ol{margin:.2rem 0 0 1.2rem;padding:0;font-size:.93em}.pwt-c li{margin:.2rem 0}
.pwt .pwt-idx{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:2px 18px;margin:.7rem 0 .3rem;padding:.7rem .9rem;background:#f4f7fa;border:1px solid #dbe3ec;border-radius:4px}
.pwt .pwt-idx-h{grid-column:1/-1;font:600 11px/1 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.09em;color:#5a708a;margin-bottom:.3rem}
.pwt .pwt-idx a{display:flex;gap:8px;align-items:baseline;font-size:.93em;text-decoration:none;color:#1f5b8d;padding:3px 0;font-weight:600}
.pwt .pwt-idx a:hover{text-decoration:underline}
.pwt .pwt-n{display:inline-block;min-width:1.35em;text-align:right;color:#8a97a8;font-weight:500;font-variant-numeric:tabular-nums}
.pwt h3{scroll-margin-top:12px}
.pwt .pwt-top{margin-left:auto;font-size:.7em;color:#b4bdc8;text-decoration:none;font-weight:400}
.pwt .pwt-top:hover{color:#1f5b8d}
.pwt .pwt-chan{margin-top:.45rem;padding-top:.35rem;border-top:1px dashed #cfd8e2}
.pwt .pwt-chan-h{display:block;font:600 10px/1.3 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.07em;color:#8a97a8;margin-bottom:.15rem}
.pwt .pwt-chan ol{color:#6b7686}
.pwt .pwt-b{display:inline-block;font:600 10.5px/1 system-ui,sans-serif;letter-spacing:.03em;border-radius:3px;padding:3px 6px;white-space:nowrap;vertical-align:middle}
@media (prefers-color-scheme:dark){.pwt .pwt-lede{color:#c3bdb0}.pwt-t td{border-color:#2f3441}
 .pwt .pwt-sub{color:#8fb0ea;border-bottom-color:#39424f}
 .pwt .pwt-idx{background:#1c2331;border-color:#2f3a4b}.pwt .pwt-idx a{color:#8fb0ea}.pwt .pwt-idx-h{color:#8d9bb0}
 .pwt .pwt-chan{border-top-color:#39424f}.pwt .pwt-chan ol{color:#98a3b4}}
</style>'''
idx = ''.join('<a href="#%s"><span class="pwt-n">%d</span>%s</a>' % (_slug(t), i + 1, e(t)) for i, (m, t, *_) in enumerate(S))
parts = [css, '<div class="pwt">',
         '<p class="pwt-lede">%s private banks and wealth managers worldwide, and the %s metals products they advertise to clients. Figures marked ESTIMATE are derived.</p>' % (len(F), n_prod),
         '<nav class="pwt-idx" aria-label="Contents"><span class="pwt-idx-h">Contents</span>%s</nav>' % idx]
for m, t, lede, bullets, table in S:
    parts.append('<h3 id="%s">%s<a class="pwt-top" href="#" title="Back to contents">&uarr;</a></h3>' % (_slug(t), e(t)))
    if lede: parts.append('<p class="pwt-lede">%s</p>' % e(lede))
    if bullets: parts.append('<ul>' + ''.join('<li data-cid="%d">%s%s</li>' % (cid, e(b), (' <a href="%s" target="_blank" rel="noopener">src</a>' % e(u)) if u else '') for cid, b, u in bullets) + '</ul>')
    if table: parts.append(table)
parts.append('</div>')
out = os.path.join(HERE, 'pw_talking_points.html')
open(out, 'w', encoding='utf-8').write('\n'.join(parts))
print('wrote', out, '|', len(S), 'sections,', sum(len(b) for *_, b, _ in S), 'bullets,', len(C), 'country tables; SCB pass loaded:', bool(scb))
