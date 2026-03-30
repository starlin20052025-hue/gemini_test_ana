# REVIEW_NOTES.md

# Gemini Prototype Review Notes

## Repository Positioning

This repository currently stores a **Gemini-generated prototype research framework** for cryptocurrency strategy research.

It should **not** yet be treated as a production-grade or research-grade trading framework.

Current status:

- good as an exploration draft
- useful for preserving Gemini’s ideas and generated code
- not yet reliable enough for formal strategy validation
- requires substantial hardening before becoming the main research baseline

---

## Overall Assessment

### What is useful

The prototype has value in the following areas:

1. It captures the intended research direction reasonably well:
   - full-history mindset
   - train / test separation
   - anchored walk-forward as a target direction
   - anti-future-leak awareness
   - baseline metrics such as CAGR / MDD / Sharpe / Calmar
   - future extension toward pair trade / stat arb

2. It provides an initial project skeleton:
   - `data_loader.py`
   - `backtest_engine.py`
   - `research_script.py`
   - `pair_trade_research.py`

3. It is useful as a **discussion artifact** and **refactoring starting point**

### What is not yet acceptable

The repository currently has major weaknesses in:

- backtest correctness
- walk-forward rigor
- anti-leak guarantees
- cost modeling realism
- gap handling
- pair trade implementation realism
- metrics correctness
- research workflow discipline

---

## High Priority Problems

## 1. Research workflow drifted from spec

The original task was mainly:

- research review
- framework design
- validation design
- anti-leak design
- baseline proposal

But the generated output quickly jumped into implementation.

### Why this is a problem

This causes the project to skip the most important phase:

- defining exact research protocol before coding

### Required fix

Before more coding is added, define:

- exact research protocol
- data assumptions
- signal timing assumptions
- train / validation / test rules
- walk-forward rules
- cost model rules
- output definitions

---

## 2. Walk-forward implementation is not rigorous enough

The repo claims anchored walk-forward, but the implementation does not yet satisfy strict research-grade walk-forward standards.

### Current issues

- training slices are cut, but not used for real parameter selection in a controlled pipeline
- validation logic is not explicitly separated from test logic
- fixed rules are mostly applied directly rather than selected from past-only data
- no clear distinction between:
  - in-sample parameter search
  - out-of-sample evaluation
  - final aggregation

### Why this matters

A weak walk-forward implementation can easily give false confidence while still leaking selection bias.

### Required fix

Implement explicit workflow such as:

1. training window
2. optional validation window
3. parameter search using only past data
4. freeze selected parameters
5. run next out-of-sample segment
6. append results
7. roll forward and repeat

Must document:

- initial window length
- step length
- parameter universe
- selection metric
- tie-breaking rules
- fallback rules if data is insufficient

---

## 3. Anti-future-leak protection is incomplete

The prototype strongly emphasizes `shift(1)` and next-bar-open logic. That is good, but not sufficient.

### Current issues

Potential leak sources still remain:

- indicator construction may still rely on data boundaries not fully controlled by split logic
- walk-forward parameter selection is not fully isolated
- rolling statistics may accidentally span across train/test incorrectly
- pair-trade signal construction does not prove strict historical-only dependency
- no formal anti-leak checklist is enforced in code

### Required fix

Create a strict anti-leak policy document and code checks.

Minimum checklist:

- all tradable signals generated only from information available before execution
- execution occurs at next bar open, never current close
- all parameter fitting occurs only on training data
- all normalization or scaling fit only on training data
- no full-sample statistics allowed in OOS generation
- all rolling windows verified at boundaries
- all reporting clearly separates IS and OOS

---

## 4. Backtest engine is too simplified

The current vectorized backtest engine is a prototype, not a trustworthy research engine.

### Current issues

- return generation is overly simplified
- position transitions are too coarse
- flip handling needs explicit treatment
- cost application is too naive
- long / short / flat transitions are not modeled in a sufficiently explicit way
- execution assumptions are not fully auditable

### Example concerns

Need to explicitly verify handling of:

- `0 -> 1`
- `1 -> 0`
- `0 -> -1`
- `-1 -> 0`
- `1 -> -1`
- `-1 -> 1`

For each case, define:

- entry price
- exit price
- whether one or two cost events occur
- when PnL starts accruing
- when PnL stops accruing

### Required fix

Refactor backtest engine into a more explicit transaction-aware model, even if still vectorized.

At minimum:

- explicit position state transition table
- explicit cost event model
- explicit return attribution logic
- auditable intermediate columns

---

## 5. Metrics need re-validation

The metrics implementation should not be trusted yet without formal review.

### Current issues

- Sharpe formula may not follow standard return-series definition
- annualization assumptions are hardcoded and need validation by timeframe
- total return to CAGR conversion should be verified carefully
- drawdown computation needs explicit edge-case checks
- win-rate based on bar return is not the same as trade win-rate

### Required fix

Re-define metrics clearly.

Must distinguish between:

- bar-level metrics
- trade-level metrics
- portfolio-level metrics

Minimum recommended metrics:

- Total Return
- CAGR
- Max Drawdown
- Sharpe Ratio
- Calmar Ratio
- Sortino Ratio
- Exposure
- Turnover
- Trade Count
- Avg Holding Period
- Profit Factor
- Trade Win Rate

Also define exactly:

- whether Sharpe uses mean excess return
- whether risk-free rate is assumed zero
- how annualization factor is chosen by timeframe
- whether trade win rate and bar win rate are both reported

---

## 6. Gap handling is unsafe

The current approach uses forward fill for missing candles.

### Why this is dangerous

Forward-filling missing market data can distort:

- volatility
- ATR
- moving averages
- return series
- signal timing

It also hides whether the missing bars are caused by:

- exchange outage
- API issue
- download failure
- symbol listing gap
- delisting / trading halt behavior

### Required fix

Gap handling must be rule-based.

Recommended policy:

1. detect and log every gap
2. classify gap size
3. decide handling by severity

Example:

- tiny isolated gap: allow controlled fill with flag
- medium gap: mark segment invalid
- large gap: exclude period from research
- listing-era gap: do not fabricate bars

Also add:

- `gap_flag`
- `gap_size`
- research report section describing missing-data handling

---

## 7. Pair trade implementation is not yet a real pair-trade engine

The current pair trade logic is best treated as a conceptual placeholder.

### Current issues

- ratio treated like a synthetic single asset
- no true two-leg accounting
- no hedge ratio modeling
- no capital allocation per leg
- no borrow / financing assumptions
- no separate cost per leg
- no cointegration validation
- no stationarity validation
- no spread construction discipline

### Why this matters

A real pair-trade strategy is not equivalent to backtesting a ratio as if it were one tradable asset.

### Required fix

Do not treat current pair trade result as meaningful performance evidence.

Before pair-trade research continues, implement:

- aligned dual-leg market data structure
- hedge ratio definition
- entry/exit based on spread, not just naive ratio
- double-leg cost accounting
- capital allocation rules
- optional cointegration / stationarity tests
- pair-specific reporting

Until then, label pair trade module as:

- experimental
- placeholder
- not validated

---

## 8. Result interpretation is too narrative-driven

Some generated conclusions sound plausible, but are not yet backed by strong enough evidence.

### Examples of risk

- claiming regime shift from one limited result set
- claiming ATR filter solved OOS issues without deeper robustness checks
- attributing pair-trade failure mainly to commission drag when implementation itself is incomplete

### Required fix

All conclusions should be downgraded from strong claims to testable hypotheses.

Use wording like:

- "suggests"
- "may indicate"
- "requires robustness validation"
- "not yet sufficient evidence"

Do not present prototype outputs as established findings.

---

## Required Repository Changes

## 1. README rewrite

Current README should be revised so the project is not mistaken for a validated framework.

### Recommended README positioning

This repo should explicitly say:

- this is a Gemini-generated prototype
- current outputs are exploratory
- framework is under review
- performance results are not yet research-grade conclusions
- multiple modules require validation and refactoring

---

## 2. Add status labels

Recommended module status:

- `data_loader.py` -> draft
- `backtest_engine.py` -> prototype, not validated
- `research_script.py` -> exploratory baseline
- `pair_trade_research.py` -> conceptual placeholder

---

## 3. Add architecture / protocol docs

Add these files:

- `RESEARCH_PROTOCOL.md`
- `ANTI_LEAK_CHECKLIST.md`
- `METRICS_DEFINITION.md`
- `TODO_FIXES.md`

---

## 4. Freeze prototype results as non-final

If keeping current output files or reports, label them clearly:

- prototype results
- exploratory only
- not production validated
- not final strategy evidence

---

## Recommended Next Steps

## Phase 1: Hardening the single-asset framework

Priority order:

1. define research protocol
2. refactor backtest engine
3. formalize anti-leak controls
4. formalize metrics
5. formalize walk-forward
6. re-run single-asset baseline
7. validate output consistency

## Phase 2: Add robustness testing

After the engine is trustworthy:

- parameter sensitivity testing
- transaction cost stress testing
- regime segmentation
- subperiod comparison
- train / validation / test discipline checks

## Phase 3: Rebuild pair trade properly

Only after single-asset framework is correct:

- real two-leg engine
- spread construction
- hedge ratio handling
- cost realism
- cointegration / stationarity validation

---

## Suggested Repo Warning Text

Recommended short warning to place near the top of README:

> This repository currently contains a Gemini-generated prototype for cryptocurrency strategy research.  
> It is useful as a draft framework and discussion artifact, but it has not yet passed research-grade validation.  
> Backtest correctness, walk-forward rigor, anti-leak guarantees, metrics, and pair-trade implementation all require further review and refactoring.

---

## Final Judgment

This repository is worth keeping.

But it should currently be treated as:

- an AI-generated draft
- a prototype research scaffold
- a refactoring target

It should **not** yet be treated as:

- a validated strategy framework
- a trusted backtest engine
- a reliable pair-trading research platform
- a source of final performance conclusions