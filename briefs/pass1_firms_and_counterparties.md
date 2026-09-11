# Private-bank / private-wealth METALS shelf sweep — agent brief

You are researching for a bank precious-metals desk (Citi). Goal: for every private bank / private-wealth manager in your region, establish
(1) WHAT METALS PRODUCTS it offers its clients, and (2) WHICH BANKS / COUNTERPARTIES it works with to deliver them
(bullion supplier, liquidity provider for OTC/structured trades, custodian/vault, ETF/ETC custodian, refiner, structured-note issuer, gold-account partner).

Metals = gold, silver, platinum, palladium first; copper/other base metals only if the firm has a specific product.

## Method (knowledge-first, then verify)
1. Start from the seed list below AND add any material private bank / wealth manager in the region you know of that I missed (target: complete coverage of firms with > ~US$10bn client assets, plus any smaller firm notable for metals).
2. For each firm, write what you already know, then VERIFY the load-bearing claims with web search / fetch of the firm's own product pages, factsheets, prospectuses (own gold ETFs/ETCs name the custodian), annual reports, LBMA/LPPM membership lists, press releases. Budget: ~2–4 searches for a large firm, 1 for a small one. Stop after ~45 searches total; if searches start failing (rate-limit / empty), back off, pause, and fall back to knowledge with confidence="knowledge".
3. Every counterparty claim MUST carry an evidence string (short verbatim quote or precise paraphrase) and a URL where possible. Do not guess a counterparty. "unknown" is a valid and useful answer.
4. Tag each product cell: "Y" (verified), "Y?" (from knowledge, unverified), "N" (verified not offered), "?" (unknown).

## Product taxonomy (use these exact keys)
- physical_bullion — bars/coins sold to clients, delivered or stored
- metal_account_allocated — allocated / segregated storage account
- metal_account_unallocated — unallocated / pool / "Metallkonto" / paper-gold account (gold passbook, gold savings)
- gold_savings_plan — regular-purchase plan / gram accumulation / digital gold (incl. tokenised gold e.g. HSBC Gold Token)
- gold_deposit_dci — gold-linked deposits, dual-currency-style deposits in XAU, gold yield-enhancement deposits
- structured_notes — gold/silver-linked structured notes, reverse convertibles, capital-protected notes, autocalls
- otc_derivatives — OTC forwards / options / accumulators on metal for HNW/UHNW clients
- lombard_vs_metal — Lombard / margin lending secured on physical bullion, metal accounts or metal ETFs (state LTV if known)
- own_etf_etc — the firm or its asset-management arm sponsors a physical-metal ETF/ETC (name it + its custodian)
- third_party_etf — distributes third-party metal ETFs/ETCs (name the ones promoted if disclosed)
- metal_funds — actively managed precious-metal / mining funds of its own
- metals_covered — list from [Au, Ag, Pt, Pd, other]
- advisory_view — publishes a house view / strategic allocation to gold (yes/no, % if stated)

## Counterparty roles (use these exact keys)
bullion_supplier | liquidity_provider | custodian_vault | etf_custodian | refiner | note_issuer | account_partner | clearing_lpmcl | other

## Output — write ONE JSON file to the path given in your task, shape:
{
 "region": "...", "generated": "2026-09-09", "search_count": N, "notes": "anything the desk should know about the region (regulation, gold-import rules, market structure)",
 "firms": [
  {
   "firm": "Bank Julius Baer & Co. Ltd", "group": "Julius Baer Group", "country": "Switzerland", "booking_centres": ["CH","SG","HK","...".],
   "type": "pure-play private bank | universal-bank PB arm | independent wealth manager | broker-dealer wealth | digital/neo wealth | trust bank | cantonal/regional bank PB",
   "client_assets_usd_bn": 500, "assets_year": 2025,
   "products": { "physical_bullion": "Y", "metal_account_allocated": "Y", ... , "metals_covered": ["Au","Ag","Pt","Pd"], "advisory_view": "yes — 5% strategic" },
   "product_evidence": [ {"claim": "...", "quote": "...", "url": "..."} ],
   "counterparties": [ {"name": "UBS", "role": "bullion_supplier", "evidence": "...", "url": "...", "confidence": "verified|knowledge"} ],
   "lbma_lppm_membership": "LBMA full member / associate / none",
   "in_house_trading_desk": "yes/no/? — does it run its own bullion desk (market-maker) or buy in from others",
   "citi_status": "Citi is the firm | Citi named as counterparty | Citi not named | unknown",
   "desk_angle": "one line: what Citi could sell/displace here (e.g. wholesale bullion supply, loco-London allocated custody, wholesale lombard funding vs bullion, structured-note hedging, ETF custody)",
   "score": 1-10 (desk value: size of metals franchise × displaceability × absence of in-house bullion bank),
   "confidence": "verified | mixed | knowledge",
   "sources": ["url", ...]
  }
 ]
}

Be exhaustive on NAMES (breadth), but honest on evidence (depth where it matters). Big metals franchises (UBS, Julius Baer, Pictet, HSBC PB, Emirates NBD, BOCHK, ICBC PB, Kotak, DBS…) deserve the deep verification; tail names get a quick knowledge-based row with "?" cells.
When done, reply with: the file path, the firm count, the search count, and the 5 most desk-relevant findings (in 5 bullets).
