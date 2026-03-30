# TODO_FIXES.md

# TODO Fixes for Gemini Prototype

This file tracks the hardening work required to transform the current Gemini-generated prototype into a research-grade cryptocurrency strategy framework.

---

# Priority Legend

- **P0** = must fix before trusting any result
- **P1** = high priority, needed for serious research use
- **P2** = important but can follow after the core engine is corrected
- **P3** = enhancement / extension

---

# P0 - Critical: Do not trust results before these are fixed

## 1. Define the research protocol formally

### Goal
Stop implicit assumptions and make the framework auditable.

### Tasks
- [ ] Create `RESEARCH_PROTOCOL.md`
- [ ] Define:
  - [ ] data source assumptions
  - [ ] symbol universe
  - [ ] timeframe handling
  - [ ] signal generation timing
  - [ ] order execution timing
  - [ ] train / validation / test definitions
  - [ ] walk-forward rules
  - [ ] parameter search rules
  - [ ] cost model rules
  - [ ] reporting standards
- [ ] Make sure all scripts follow the documented protocol

### Deliverable
A written protocol that defines exactly how research is performed.

---

## 2. Rebuild the backtest engine into an auditable model

### Goal
Replace the current simplified engine with one that can be trusted.

### Tasks
- [ ] Refactor the engine so position transitions are explicit
- [ ] Define exact handling for:
  - [ ] `0 -> 1`
  - [ ] `1 -> 0`
  - [ ] `0 -> -1`
  - [ ] `-1 -> 0`
  - [ ] `1 -> -1`
  - [ ] `-1 -> 1`
- [ ] Add explicit columns for:
  - [ ] signal time
  - [ ] target position
  - [ ] actual executed position
  - [ ] entry event
  - [ ] exit event
  - [ ] turnover
  - [ ] transaction cost
  - [ ] gross return
  - [ ] net return
- [ ] Ensure next-bar-open execution is applied consistently
- [ ] Add unit-style test cases for simple synthetic price series
- [ ] Validate that PnL attribution matches expected hand-calculated cases

### Deliverable
A backtest engine whose logic can be manually audited row by row.

---

## 3. Formalize anti-leak controls

### Goal
Move from "we used shift(1)" to a real anti-future-leak framework.

### Tasks
- [ ] Create `ANTI_LEAK_CHECKLIST.md`
- [ ] Audit every strategy module for:
  - [ ] rolling-window boundary correctness
  - [ ] no current-bar-close execution
  - [ ] no full-sample statistics inside OOS logic
  - [ ] no test-period-derived parameter fitting
  - [ ] no leakage from combined preprocessing
- [ ] Add code comments wherever time dependency matters
- [ ] Add assertions or validation checks in code where possible
- [ ] Separate fitting logic from inference logic

### Deliverable
A documented and testable anti-leak policy.

---

## 4. Rebuild walk-forward validation properly

### Goal
Upgrade from segmented backtest to true research-grade walk-forward.

### Tasks
- [ ] Define explicit walk-forward workflow:
  - [ ] train window
  - [ ] optional validation window
  - [ ] parameter search
  - [ ] parameter freeze
  - [ ] OOS run
  - [ ] step forward
- [ ] Define:
  - [ ] initial train size
  - [ ] step size
  - [ ] test window size
  - [ ] minimum data requirement
  - [ ] fallback behavior
- [ ] Implement a reusable walk-forward runner
- [ ] Log the selected parameters for each step
- [ ] Aggregate OOS-only results separately from IS results
- [ ] Save step-by-step outputs to disk for inspection

### Deliverable
A walk-forward process that can be inspected and repeated consistently.

---

## 5. Re-validate metrics

### Goal
Ensure all reported numbers mean exactly what they claim to mean.

### Tasks
- [ ] Create `METRICS_DEFINITION.md`
- [ ] Re-check formulas for:
  - [ ] Total Return
  - [ ] CAGR
  - [ ] Max Drawdown
  - [ ] Sharpe Ratio
  - [ ] Calmar Ratio
  - [ ] Sortino Ratio
  - [ ] Exposure
  - [ ] Turnover
  - [ ] Trade Count
  - [ ] Avg Holding Period
  - [ ] Profit Factor
  - [ ] Trade Win Rate
- [ ] Distinguish between:
  - [ ] bar win rate
  - [ ] trade win rate
  - [ ] gross metrics
  - [ ] net metrics
- [ ] Validate annualization factors by timeframe
- [ ] Ensure metrics are computed on clean OOS-only outputs when required

### Deliverable
A clear metrics definition doc plus corrected implementation.

---

# P1 - High Priority: Needed for serious research use

## 6. Replace unsafe gap handling

### Goal
Stop masking missing-data issues with unconditional forward fill.

### Tasks
- [ ] Detect all missing timestamp gaps
- [ ] Create a gap report with:
  - [ ] start timestamp
  - [ ] end timestamp
  - [ ] missing bar count
  - [ ] symbol
  - [ ] timeframe
- [ ] Define handling rules by severity:
  - [ ] tiny gap
  - [ ] medium gap
  - [ ] large gap
  - [ ] listing-era gap
- [ ] Add metadata columns such as:
  - [ ] `gap_flag`
  - [ ] `gap_size`
- [ ] Ensure research reports mention how gaps were handled
- [ ] Remove blanket `ffill` unless explicitly justified and flagged

### Deliverable
A controlled and transparent gap-handling pipeline.

---

## 7. Separate prototype code paths from validated code paths

### Goal
Prevent exploratory modules from being mistaken for trustworthy research modules.

### Tasks
- [ ] Label current modules by maturity:
  - [ ] draft
  - [ ] prototype
  - [ ] validated
- [ ] Update README with repository status warning
- [ ] Mark `pair_trade_research.py` as experimental
- [ ] Mark current baseline outputs as exploratory only
- [ ] Avoid mixing trusted and untrusted reports in the same folder

### Deliverable
A clearer repository structure and reduced risk of self-misleading conclusions.

---

## 8. Create reproducible output structure

### Goal
Make every run inspectable and repeatable.

### Tasks
- [ ] Standardize output folders, e.g.:
  - [ ] `outputs/`
  - [ ] `reports/`
  - [ ] `artifacts/`
- [ ] Save per-run metadata:
  - [ ] timestamp
  - [ ] git commit hash
  - [ ] symbol
  - [ ] timeframe
  - [ ] parameter set
  - [ ] cost settings
  - [ ] split settings
- [ ] Save:
  - [ ] raw signals
  - [ ] executed positions
  - [ ] trade log
  - [ ] equity curve
  - [ ] metrics summary
  - [ ] configuration snapshot

### Deliverable
A reproducible research output system.

---

# P2 - Important: Research quality and robustness

## 9. Add parameter robustness testing

### Goal
Avoid trusting a narrow lucky parameter choice.

### Tasks
- [ ] Define parameter grids for baseline strategies
- [ ] Add local perturbation tests around selected parameters
- [ ] Compare neighboring parameter performance stability
- [ ] Flag fragile solutions
- [ ] Summarize stable vs unstable regions

### Deliverable
A robustness layer showing whether selected parameters are structurally stable.

---

## 10. Add cost stress testing

### Goal
Check whether strategy edge survives under more realistic friction.

### Tasks
- [ ] Test multiple fee assumptions
- [ ] Test multiple slippage assumptions
- [ ] Test adverse execution cases
- [ ] Produce cost sensitivity summary

### Deliverable
A cost sensitivity report.

---

## 11. Add regime segmentation analysis

### Goal
Understand where the strategy actually works.

### Tasks
- [ ] Define historical subperiods
- [ ] Compare performance by regime:
  - [ ] bull
  - [ ] bear
  - [ ] sideways
  - [ ] high-volatility
  - [ ] low-volatility
- [ ] Report OOS results by regime
- [ ] Avoid relying only on aggregate full-period metrics

### Deliverable
A regime-based evaluation report.

---

## 12. Add trade-level reporting

### Goal
Move from bar-level equity analysis to real trading behavior analysis.

### Tasks
- [ ] Build trade extraction logic
- [ ] Save trade-level table with:
  - [ ] entry time
  - [ ] exit time
  - [ ] side
  - [ ] holding period
  - [ ] gross PnL
  - [ ] net PnL
  - [ ] MAE
  - [ ] MFE
- [ ] Use trade-level table for:
  - [ ] trade win rate
  - [ ] profit factor
  - [ ] average hold time
  - [ ] expectancy

### Deliverable
A proper trade log and trade analytics layer.

---

# P3 - Extension: Only after single-asset framework is solid

## 13. Rebuild pair trade as a true two-leg framework

### Goal
Replace the current ratio-placeholder approach with a real pair-trading engine.

### Tasks
- [ ] Define spread construction methodology
- [ ] Add hedge ratio handling
- [ ] Add two-leg capital accounting
- [ ] Add per-leg transaction cost accounting
- [ ] Add entry / exit logic at spread level
- [ ] Add trade log for both legs
- [ ] Add risk checks for imbalance and drift

### Deliverable
A real pair-trading research engine.

---

## 14. Add statistical validation for pair trade

### Goal
Ensure pairs are statistically meaningful before trading.

### Tasks
- [ ] Add stationarity checks
- [ ] Add cointegration testing
- [ ] Add rolling stability checks
- [ ] Add pair selection workflow
- [ ] Log statistical diagnostics into reports

### Deliverable
A statistically defendable pair-selection process.

---

## 15. Add portfolio / multi-strategy support

### Goal
Enable future combination of trend, mean-reversion, and pair-trade modules.

### Tasks
- [ ] Define strategy interface
- [ ] Add multi-strategy run manager
- [ ] Add combined equity curve generation
- [ ] Add strategy-level allocation controls
- [ ] Add portfolio-level metrics

### Deliverable
A modular multi-strategy research framework.

---

# Immediate Suggested Order of Execution

Recommended implementation order:

1. [ ] `RESEARCH_PROTOCOL.md`
2. [ ] `ANTI_LEAK_CHECKLIST.md`
3. [ ] refactor `backtest_engine.py`
4. [ ] rebuild walk-forward logic
5. [ ] `METRICS_DEFINITION.md`
6. [ ] fix gap handling
7. [ ] rerun single-asset baseline
8. [ ] add trade log
9. [ ] add robustness and cost stress tests
10. [ ] only then revisit pair trade

---

# Success Criteria

The prototype can be considered upgraded only when:

- [ ] results are reproducible
- [ ] no-leak assumptions are explicitly documented
- [ ] walk-forward is truly past-only
- [ ] metrics are clearly defined and validated
- [ ] backtest rows are auditable
- [ ] outputs separate IS and OOS cleanly
- [ ] pair trade is no longer a synthetic ratio shortcut
- [ ] conclusions are based on validated evidence, not narrative interpretation

---

# Final Note

Until the P0 items are complete:

- do not trust performance claims
- do not treat reports as final evidence
- do not use current pair-trade outputs for decision-making

This repository is promising as a prototype, but it still requires disciplined hardening before it becomes a trustworthy research platform.