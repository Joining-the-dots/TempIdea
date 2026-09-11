# Private-wealth metals sweep — PASS 3: the ADVERTISED PRODUCT SHELF (private-bank / wealth arms only)

Audience: a bank precious-metals desk (Citi). Earlier passes built a firm-level matrix (does firm X offer physical / metal account / structured notes … Y/N). This pass turns that into a PRODUCT CATALOGUE: one record per named metals product that the PRIVATE-BANKING / WEALTH / AFFLUENT arm of each firm ADVERTISES to its clients — the way a client would see it on the firm's own website, brochure, factsheet, T&Cs or fee schedule.

## Scope rules
- ONLY client-facing products of the private-bank / wealth / premier / priority / affluent / retail-investor arm. IGNORE the institutional bullion desk, market-making, interbank, refinery, vaulting-for-institutions and corporate hedging services. (If the same bank has both, record only the client products.)
- A "product" = something with a name or a clear product page: e.g. "UBS Gold Account", "Metallkonto", "Gold Passbook (黃金存摺)", "Gold Savings Account", "Emirates NBD Gold bars", "Precious Metals Account", "Gold Investment Account (GIA-i)", "Physical Gold – delivery & storage", "Gold-linked structured note (autocall on XAU)", "Lombard loan against precious metals", "Gold DCI / Gold-linked deposit", "Gold Accumulation Plan", "Digital gold / gold token", "in-house gold fund/ETF distributed to clients", "Advisory: strategic gold allocation X%".
- One record per product per firm. If a bank has a gold account AND physical bars AND structured notes → 3 records. Retail and private-banking versions of the same product → one record, note the segment range.
- Do NOT invent. If the firm advertises nothing, write one record with product_type "none_found" and say what pages you checked. If a product is known but the page could not be fetched, confidence = "knowledge".

## Per product capture (use these exact keys)
- product_name — as marketed (original language + English in brackets if not English)
- product_type — one of: gold_account_unallocated | gold_account_allocated | physical_bullion | gold_savings_plan | digital_gold_token | gold_deposit_dci | structured_note | otc_derivative | lombard_vs_metal | own_fund_etf | third_party_fund_etf | advisory_allocation | other
- segment — retail | affluent/premier | private-banking/HNW | UHNW/family-office | all (state what the page says)
- metals — list from [Au, Ag, Pt, Pd, other]
- description — 1–3 sentences in the firm's own framing (what the client gets)
- unit_and_minimum — e.g. "1 gram units, min 1g", "min 100 oz", "min USD 250k for structured notes", "?" if not stated
- fees — spread / storage / custody / transaction / management fee as stated (e.g. "storage 0.15% p.a. + VAT; buy/sell spread ~1%"), "?" if not stated
- custody — where/how metal is held: "unallocated, bank's own book", "allocated, bank vault Zurich", "third-party vault (Brink's Singapore)", "no physical (cash-settled)", "?"
- physical_delivery — Y | N | ?
- currency — pricing/settlement currency(ies)
- pricing_basis — e.g. "LBMA PM fix + spread", "bank's own two-way price", "loco-London spot", "Shanghai Gold Exchange", "?"
- shariah — Y | N | n/a
- url — the product page / factsheet / T&C (REQUIRED where confidence = verified)
- quote — ≤ 40-word verbatim snippet from the page proving the product exists
- confidence — verified | knowledge
- notes — anything else relevant (launch date, partner named on the page, restrictions, tax)

## Also capture per firm (once)
- pb_arm_name — the exact name of the wealth/private arm (e.g. "Citi Private Bank", "Julius Baer", "DBS Treasures Private Client", "HSBC Global Private Banking")
- shelf_summary — one sentence: what the shelf looks like to a HNW client
- gold_view — the house view / strategic allocation to gold if published (%, date, url) else ""
- partner_named — any partner named on the client pages (refiner, custodian, digital-gold provider) with url

## Budget & method
Knowledge-first, then verify on the firm's OWN pages: search "<firm> gold account / precious metals / Edelmetall / métaux précieux / 黃金 / 골드 / oro" + fetch the product page(s). ~1–2 fetches per firm; stop at ~45 web calls total; back off on failures and fall back to knowledge. Multi-firm rows (names joined with " / ") are grouped tails: do a quick single search per group and record any product found under the specific bank name in `firm_actual`.

## Output — ONE JSON file at the path in your task, saved INCREMENTALLY (every ~8 firms):
{"group": "...", "generated": "2026-09-10", "search_count": N,
 "firms": [
   {"firm": "<EXACT firm string from the task file>", "firm_actual": "<specific bank if the row was a grouped tail, else same>",
    "pb_arm_name": "...", "shelf_summary": "...", "gold_view": "...", "partner_named": [{"name": "...", "role": "...", "url": "..."}],
    "products": [ { ...product record... }, ... ],
    "sources": ["..."]}
 ]}
When done, reply with: file path, firm count, product count, search count, and the 5 most interesting product designs you found (name + one line).
