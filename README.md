# Private Wealth Metals Map

A global survey of private banks and wealth managers: **what precious-metals products each one advertises to its clients, and which bullion banks, custodians and refiners sit behind those products.**

The question it answers: where could a bullion desk supply, custody, finance or clear what a wealth manager is currently buying from someone else.

The prescriptive sections — the run-sheet's proposed shelf, and the per-firm `strategic_idea` field — are **illustrative strategic ideas**, not anyone's plan or recommendation. They exist to show what the research implies. Everything else is market observation, collected identically for every firm in the set.

## What is in here

| Path | What it is |
|---|---|
| `index.html` | The report, and the site root. Open it in any browser, no server needed. Self-contained, ~3.4 MB, with a download button in its header. |
| `data/private_wealth.json` | 613 firms: product matrix, counterparties, size indicators, liquidity-provider status, scores. |
| `data/pw_products.json` | 564 named client products, one row each, with fees, minimums, custody model and source links. |
| `data/pw_talking_points.html` | The run-sheet fragment, embedded in the report and in the desk UI. |
| `scripts/` | The build pipeline (see below). |
| `briefs/` | The three research briefs the agents worked from. Provenance for how each field was collected. |
| `verification/` | Raw output of the adversarial fact-check and the three dedicated bank passes. |

## The report

An index at the top jumps to any section.

1. **Talking points** — a ten-section run-sheet. It opens with the proven product shelf in one section: the nine families a client can find on a public page with their fee benchmarks, then beneath them the yield-enhancement and financing structures sold through relationship managers and under-counted by a page sweep (dual-currency deposits, lending against metal, put-selling, covered calls, accumulators, gold-linked notes). Then five competitor designs worth copying. Then the uptake evidence, who is winning by country, an HSBC / Standard Chartered / ANZ comparison, sizing, a potential shelf and the questions to expect.
2. **Product catalogue** — all 564 named client products, filterable by type, metal, region, country and segment.
3. **Where the gaps are** — the 46 firms scoring 7 or more, each expandable to counterparties, evidence and the strategic idea.
4. **One global franchise, as the web sees it** — what is publicly documented for one large group per booking centre, shown against the peer shelves.
5. **Who the private banks work with** — counterparty leaderboard by number of wealth firms using them.
6. **Regional read**, then **every firm** — all 613 rows, private banks and wealth managers shown by default.

### Private banks vs the market channel

540 of the 613 rows are private banks and wealth managers. The other 73 are the market channel: mints, refiners, wholesalers, vaults, exchanges and ETF issuers. They are in the set because they answer the second half of the question — who the wealth firms buy metal from and custody with — not because they compete for a client relationship. They are hidden by default in the firm table and shown separately in the country tables, so nothing ranks a refinery against a bank's client book.

## How it was built

Four passes, each run by parallel research agents working from the brief in `briefs/`:

| Pass | Scope | Output |
|---|---|---|
| 1 | 8 regional sweeps: firms, product matrix, counterparties | `private_wealth.json` |
| 2 | The 91 firms scoring 6+: size indicators and liquidity providers | `notional_indicators`, `liquidity` fields |
| 3 | The 236 private-bank arms with a client product: the advertised catalogue | `pw_products.json` |
| 4 | Dedicated passes on HSBC Asia, Standard Chartered and ANZ | `verification/*.json` |
| 5 | Product primer: the structures sold by relationship managers rather than advertised | `data/pb_product_primer.json` |

Every claim in the run-sheet was then re-opened against its primary source by independent checkers, and the corrections were written into the text. The raw verdicts are kept in `verification/` as provenance; the page itself states the facts and links the source.

## Rebuilding

```
python scripts/_pw_merge.py <dir-with-regional-json>     # pass 1 -> private_wealth.json
python scripts/_pw2_apply.py <dir-with-pw2-json>         # pass 2 overlay
python scripts/_pw3_apply.py <dir-with-pw3-json>         # pass 3 -> pw_products.json
python scripts/_hsbc_apply.py verification/scb.json      # a dedicated bank pass (generic)
python scripts/_pw_talk.py                               # regenerate the run-sheet
python scripts/_talk_verify_apply.py <verify-dir>        # stamp fact-check verdicts
python scripts/_pw_report.py index.html                  # render the report
```

The scripts read and write `private_wealth.json` / `pw_products.json` in the same directory as the scripts, so run them from a working copy with the data files alongside.

## Reading the confidence tags

Nothing here should go on a slide without checking its tag.

- **Product cells**: `Y` verified on the firm's own page or a primary document · `Y?` known but unverified · `N` verified not offered · `?` unknown.
- **Product rows**: `verified` rows carry a URL and a quote; `knowledge` rows carry the intended URL but were not fetched.
- **Size indicators**: every one carries a source URL and a quote. Size *bands* are estimates derived from those and are labelled as such.
- **Counterparties**: `verified` means a source names the relationship. "undisclosed" is a finding in itself: the firm sells the product but names no bank behind it.
- **Run-sheet claims**: each carries a source link. The checkers' raw verdicts are in `verification/`.

## Known caveats

- Several firms (Julius Baer, EFG, Kathrein, some Citi and Morgan Stanley pages) block automated fetching; their figures are tagged `knowledge` and need a manual check. The Julius Baer CHF 4.9bn physical-metal figure is the most load-bearing of these.
- The country tables mix units by necessity (balance-sheet metal, account balances, tonnes, fund AUM). Compare within a country, not across.
- 309 of the 613 firm rows are knowledge-level, mostly the small-firm tail. The verified depth is concentrated in the firms that matter.
- Figures are as of the dates stated in each record, largely 2025 annual reports and 2026 interim data.
