# Research Protocol

This document defines the official research protocol for this cryptocurrency strategy framework. All research, backtesting, and validation must adhere to these rules to ensure consistency, reproducibility, and rigor.

---

## 1. Data Source and Handling

### 1.1. Primary Data Source
- **Source**: Binance API (spot or perpetual futures markets).
- **Primary Loader**: `src/data_loader.py`.

### 1.2. Data Integrity and Gap Handling
- **No Uncontrolled Filling**: The default `ffill()` in the current `data_loader.py` is **prohibited** for formal research.
- **Gap Detection**: All data loading processes must explicitly detect and log missing timestamps (gaps).
- **Gap Policy**:
    - **Tiny Gaps (1-2 bars)**: May be forward-filled, but a `gap_filled` flag must be added to the data for the filled bars.
    - **Medium Gaps (3-10 bars)**: The affected period should be marked as non-tradable or excluded from the backtest.
    - **Large Gaps (>10 bars)**: The entire dataset portion may be considered invalid for that period. A gap report must be generated.
    - **Listing/Delisting Gaps**: No data fabrication is allowed. The tradable universe must be dynamically managed.

### 1.3. Data Storage
- **Format**: CSV.
- **Location**: `data/` directory.
- **Filename Convention**: `{SYMBOL}_{TIMEFRAME}.csv` (e.g., `BTCUSDT_1h.csv`).

---

## 2. Symbol Universe and Timeframe

### 2.1. Symbol Universe
- **Initial Baseline**: `BTCUSDT` (Perpetual Contract).
- **Expansion**: Any high-liquidity pair on Binance is permissible, but the universe for a given experiment must be explicitly defined and held constant.

### 2.2. Timeframe
- **Primary Research Timeframe**: **1 hour (1h)**. This provides a balance between sufficient data points, noise reduction, and sensitivity to transaction costs.
- **Secondary Timeframes**: `4h` and `1d` may be used for robustness checks, but `1h` is the standard for new strategy baselines.

---

## 3. Backtest and Execution Logic

### 3.1. Signal Generation and Timing
- **Strictly Historical Data**: All inputs to a signal (indicators, features, etc.) must only use data available **before** the current bar's close.
- **Signal Timestamp**: A signal is considered generated at the **close** of a bar.

### 3.2. Order Execution Timing
- **Execution Price**: All trades are executed at the **open** of the bar immediately following the signal bar.
- **No Look-ahead**: The backtest engine must **never** use information from the signal bar (e.g., its close, high, or low) to execute the trade. The trade happens at `bar t+1` open, based on a signal from `bar t` close.

---

## 4. Train/Validation/Test and Walk-Forward Rules

### 4.1. Splitting Method
- **Mandatory Method**: **Anchored Walk-Forward Validation**. This reflects a realistic trading scenario where the model is periodically retrained on new data.
- **Simple Train/Test Splits**: A single, fixed train/test split is **not sufficient** for final validation but can be used for initial debugging.

### 4.2. Walk-Forward Configuration
- **Initial Training Window**: Minimum 50% of the available historical data at the start of the experiment.
- **Out-of-Sample (OOS) Window / Step Size**: 10% of the total historical data length.
- **Parameter Search**:
    - Any parameter optimization (e.g., indicator lengths, thresholds) **must** be performed **only** on the current training window.
    - An optional "validation set" can be carved out from the end of the training set for this purpose.
    - The optimal parameters found are then **frozen** and applied to the subsequent out-of-sample window.
- **Result Aggregation**: Final performance metrics must be calculated based on the **concatenated out-of-sample periods only**. In-sample performance should be reported separately for analysis but not as the primary result.

---

## 5. Cost Model

### 5.1. Transaction Costs
- **Baseline Commission**: **0.05% (5 basis points)** per trade (covering typical maker/taker fees).
- **Pair Trading**: Commission is doubled to **0.10%** to account for two legs.

### 5.2. Slippage
- **Baseline Slippage**: **0.01% (1 basis point)** per trade.
- **Implementation**: Slippage should be applied directionally (i.e., buy orders execute at a slightly higher price, sell orders at a slightly lower price).

---

## 6. Performance Reporting

### 6.1. Required Metrics
The following metrics are mandatory for all final reports. See `METRICS_DEFINITION.md` for precise formulas.
- **Primary Metrics**:
    - CAGR (Compound Annual Growth Rate)
    - Max Drawdown (MDD)
    - Sharpe Ratio (annualized)
    - Calmar Ratio (CAGR / |MDD|)
- **Secondary Metrics**:
    - Sortino Ratio
    - Profit Factor
    - Trade Win Rate (%)
    - Average Holding Period
    - Total Number of Trades
    - Exposure (%)
    - Turnover

### 6.2. Report Structure
- Reports must clearly distinguish between **In-Sample (IS)** and **Out-of-Sample (OOS)** performance.
- Walk-forward reports must show performance for each individual OOS period, in addition to the aggregated final result.
- All parameters used in the experiment must be documented in the report.

---

## 7. Anti-Leak Checklist

This is a mandatory checklist to be mentally (or programmatically) verified before committing a research result.

- [ ] **Indicator Calculation**: All rolling calculations use a window ending on or before the current bar (`t`). No future data is included.
- [ ] **Signal Shifting**: Signals are shifted by at least one period (`.shift(1)`) before being used to calculate returns, ensuring execution happens at `t+1`.
- [ ] **Data Normalization**: Any scaling or normalization (e.g., `MinMaxScaler`, `StandardScaler`) is `fit` **only** on the training set and then `transform` is applied to the test set. No `fit_transform` on the full dataset.
- [ ] **Parameter Selection**: Parameters are chosen based **only** on training/validation set performance within a walk-forward loop. No parameters are chosen based on out-of-sample results.
- [ ] **Data Slicing**: There is no overlap between training and testing data within any walk-forward fold.
