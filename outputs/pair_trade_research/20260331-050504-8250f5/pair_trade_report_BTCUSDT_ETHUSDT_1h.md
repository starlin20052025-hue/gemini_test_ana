
# Pair Trade (Stat Arb) Research: BTCUSDT / ETHUSDT (Simplified Model)

## WARNING: This is a simplified prototype.
As per `REVIEW_NOTES.md` and `RESEARCH_PROTOCOL.md`, this pair trade implementation
treats the ratio as a synthetic single asset and does not account for true
two-leg accounting, hedge ratio modeling, or separate costs per leg.
Results from this section should be treated as **exploratory only** and
**not as meaningful performance evidence**.

## Strategy: Z-Score Mean Reversion
- Period: 2022-01-01 to Present
- Window: 100 hours
- Entry Threshold: +/- 1.5 Std Dev
- Rolling Z-Score `closed='left'` used for anti-leakage.

| Metric | Value |
|:-------|:------|
| Total Return | -244.21% |
| CAGR | nan% |
| Max Drawdown | -240.54% |
| Sharpe Ratio | 0.00 |
| Calmar Ratio | nan |
| Number of Trades | 3085 |
| Exposure (%) | 31.17% |
| Profit Factor | 0.82 |
| Trade Win Rate (%) | 41.57% |
| Turnover (Annualized) | 410.88 |
| Average Holding Period | N/A (Requires Trade Log) |

## Observations
- Pair trading typically has lower CAGR but higher stability (Market Neutral).
- Commission drag is significant in pair trading due to double-leg execution.
- The current model is a placeholder; a full two-leg engine is required for proper validation.
