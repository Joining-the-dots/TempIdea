# Private Wealth Metals Map

A global survey of private banks and wealth managers: **what precious-metals products each one advertises to its clients, and which bullion banks, custodians and refiners sit behind those products.**

Built for a bank precious-metals desk. The question it answers: where can a metals desk supply, custody, finance or clear what a wealth manager is currently buying from someone else.

## What is in here

| Path | What it is |
|---|---|
| `PRIVATE_WEALTH.html` | The report. Open it in any browser, no server needed. Self-contained, ~3.4 MB. |
| `data/private_wealth.json` | 613 firms: product matrix, counterparties, size indicators, liquidity-provider status, scores. |
| `data/pw_products.json` | 564 named client products, one row each, with fees, minimums, custody model and source links. |
| `data/pw_talking_points.html` | The 45-minute run-sheet fragment, embedded in the report and in the desk UI. |
| `scripts/` | The build pipeline (see below). |
| `briefs/` | The three research briefs the agents worked from. Provenance for how each field was collected. |
| `verification/` | Raw output of the adversarial fact-check and the three dedicated bank passes. |

## The report

Six sections:

1. **Talking points** — a timed 45-minute run-sheet: uptake evidence, the nine product families with live fee benchmarks, top three by disclosed volume for 13 markets, competitor designs worth copying, sizing, a proposed shelf, and the questions to expect.
2. **Where the desk can displace** — the 46 firms scoring 7 or more, each expandable to counterparties, evidence and desk angle.
3. **The home bank's own shelf** — what is publicly documented per booking centre.
4. **Who the private banks work with** — counterparty leaderboard by number of wealth firms using them.
5. **Product catalogue** — all 564 products, filterable by type, metal, region, country, segment.
6. **Every firm** — all 613 rows; private-bank and wealth arms shown by default.

## How it was built

Four passes, each run by parallel research agents working from the brief in `briefs/`:

| Pass | Scope | Output |
|---|---|---|
| 1 | 8 regional sweeps: firms, product matrix, counterparties | `private_wealth.json` |
| 2 | The 91 firms scoring 6+: size indicators and liquidity providers | `notional_indicators`, `liquidity` fields |
| 3 | The 236 private-bank arms with a client product: the advertised catalogue | `pw_products.json` |
| 4 | Dedicated passes on HSBC Asia, Standard Chartered and ANZ | `verification/*.json` |

Then an **adversarial fact-check**: every one of the 90 claims in the talk was re-opened against its primary source by independent checkers. Result: 37 confirmed, 34 partly verified, 16 corrected, 3 not independently supportable. Every correction is written into the text, and each line in the report carries its verdict badge.

## Rebuilding

```
python scripts/_pw_merge.py <dir-with-regional-json>     # pass 1 -> private_wealth.json
python scripts/_pw2_apply.py <dir-with-pw2-json>         # pass 2 overlay
python scripts/_pw3_apply.py <dir-with-pw3-json>         # pass 3 -> pw_products.json
python scripts/_hsbc_apply.py verification/scb.json      # a dedicated bank pass (generic)
python scripts/_pw_talk.py                               # regenerate the run-sheet
python scripts/_talk_verify_apply.py <verify-dir>        # stamp fact-check verdicts
python scripts/_pw_report.py PRIVATE_WEALTH.html         # render the report
```

The scripts read and write `private_wealth.json` / `pw_products.json` in the same directory as the scripts, so run them from a working copy with the data files alongside.

## Reading the confidence tags

Nothing here should go on a slide without checking its tag.

- **Product cells**: `Y` verified on the firm's own page or a primary document · `Y?` known but unverified · `N` verified not offered · `?` unknown.
- **Product rows**: `verified` rows carry a URL and a quote; `knowledge` rows carry the intended URL but were not fetched.
- **Size indicators**: every one carries a source URL and a quote. Size *bands* are estimates derived from those and are labelled as such.
- **Counterparties**: `verified` means a source names the relationship. "undisclosed" is a finding in itself: the firm sells the product but names no bank behind it.
- **Talk claims**: each line carries a fact-check badge. Lines marked *not independently supported* are our own findings or figures the checker could not reach.

## Known caveats

- Several firms (Julius Baer, EFG, Kathrein, some Citi and Morgan Stanley pages) block automated fetching; their figures are tagged `knowledge` and need a manual check. The Julius Baer CHF 4.9bn physical-metal figure is the most load-bearing of these.
- The country tables mix units by necessity (balance-sheet metal, account balances, tonnes, fund AUM). Compare within a country, not across.
- 309 of the 613 firm rows are knowledge-level, mostly the small-firm tail. The verified depth is concentrated in the firms that matter.
- Figures are as of the dates stated in each record, largely 2025 annual reports and 2026 interim data.
