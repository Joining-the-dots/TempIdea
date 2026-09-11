# Private-wealth metals sweep — PASS 2: notionals + liquidity providers

You are enriching an existing dataset for a bank precious-metals desk (Citi). Pass 1 already established, for each private bank / wealth manager, the metals products it offers and some of the banks it works with. Your task file (path given in your task) lists your firms with everything already known (products, known counterparties, evidence snippets, sources already used). DO NOT redo pass 1. Answer two things per firm, with sources:

## Q-A. How big is the metals business? (`notional_indicators`)
Find any public quantitative indicator of the firm's precious-metals activity. Notionals are rarely disclosed for private banks, so hunt PROXIES, in this priority order:
1. Stated metals volumes: tonnes/oz traded or held, metal-account balances, number of gold accounts, gold-savings AUM, bullion sales revenue, import volumes (nominated-bank import data, customs), gold deposits held with the central bank.
2. Own physical-metal ETF/ETC/fund AUM (factsheet, latest available) and any stated bar counts.
3. Regulatory / annual-report disclosures: "precious metals" line in trading assets, commodity derivative notionals in the derivatives note, "gold" in balance-sheet notes, Pillar 3 commodity risk, Turkish/Korean/Taiwanese/Indian/Indonesian regulator statistics on gold accounts by bank.
4. Market-structure signals: LBMA/LPPM membership tier (full member / market maker / associate), LPMCL/SGX/HKPMCC/SGE/BIST/IIBX membership, number of vaults or branches selling metal, client counts of the metals product.
5. Press quotes: "we sold X tonnes", "gold accounts grew Y%", "Z customers".
Record each indicator as {metric, value, unit, as_of, source_url, quote}. If nothing at all is public, say so explicitly with `"none_found": true` and one line on what you looked at. Then give a `size_band` estimate: one of "very large (>US$5bn metals AUM or >50t/yr)", "large (US$1–5bn or 10–50t)", "mid (US$100m–1bn or 1–10t)", "small (<US$100m)", "unknown" — and mark it ESTIMATE if inferred.

## Q-B. Who provides liquidity / physical? (`liquidity`)
For the firm's metals book, identify the wholesale liquidity provider (the bank or dealer it hedges with or buys physical from), separately from the custodian. Sources: ETF prospectuses (the "gold counterparty"/"metal counterparty"/"authorised participants" are often named), fund annual reports (counterparty lists in derivatives notes), product T&Cs / FAQs ("we source metal from…"), press releases on partnerships, LBMA/LPPM member lists, central-bank or regulator disclosures, trade press (Metals Focus, Bullion Vault, MetalsDaily, Reuters, Bloomberg), Pillar 3 counterparty disclosures, tender/award notices. Output:
- `status`: "named-verified" (a source names it) | "named-knowledge" (you know it but found no source) | "in-house" (the firm is itself a bullion bank / market maker — say which desk) | "undisclosed" (product exists, provider not public) | "n/a" (no metals book)
- `providers`: [{name, role: "liquidity_provider|bullion_supplier|hedge_counterparty|authorised_participant|custodian|refiner", evidence, source_url, confidence}]
- `notes`: one line — e.g. "hedges via group treasury with LBMA banks, unnamed"; "buys kilobars from Argor-Heraeus, hedges XAU/USD with UBS per 2024 fund AR p.31".

## Budget & method
Knowledge first, then verify. ~2–3 searches/fetches per firm; stop at ~45 total; if searches start failing, back off and fall back to knowledge with confidence "knowledge". Prefer primary documents (prospectus, annual report, regulator statistics, the firm's own pages). Every value needs a URL. Do not repeat sources already listed in the task file unless you need a specific figure from them.

## Output — write ONE JSON file to the path given in your task, INCREMENTALLY (save after every ~5 firms):
{
 "group": "...", "generated": "2026-09-10", "search_count": N,
 "firms": [
  {"firm": "<exact firm string from the task file>",
   "notional_indicators": [{"metric": "...", "value": "...", "unit": "...", "as_of": "...", "source_url": "...", "quote": "..."}],
   "none_found": false,
   "size_band": "large (US$1–5bn or 10–50t)", "size_band_basis": "ESTIMATE — from ETF AUM US$2.1bn + Metallkonto book unknown",
   "liquidity": {"status": "named-verified", "providers": [{"name": "...", "role": "...", "evidence": "...", "source_url": "...", "confidence": "verified|knowledge"}], "notes": "..."},
   "trades_pm": "yes-in-house-desk | yes-price-taker | distributes-only | no",
   "new_products_found": ["any product not already in the pass-1 matrix, with a source"],
   "sources": ["..."]}
 ]
}
Use the firm string EXACTLY as given so the merge can join. When done, reply with: file path, firm count, search count, and the 5 most useful numbers or provider names you found.
