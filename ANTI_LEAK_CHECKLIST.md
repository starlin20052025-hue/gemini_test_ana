# Anti-Leak Checklist

This checklist serves as a mandatory verification guide to prevent future leakage (look-ahead bias) in all research and backtesting activities. Adherence to this protocol ensures that all strategy signals and decisions are based solely on information available at the time of execution, mimicking real-world trading conditions.

---

## I. Data Preprocessing and Feature Engineering

- [ ] **Indicator Calculation**: All technical indicators (e.g., SMAs, EMAs, ATR, RSI) must be calculated using a window that ends *on or before* the current bar (`t`). No data from `t+1` or beyond should ever be used in the calculation of an indicator for bar `t`.
  - **Specific Check**: Ensure all `.rolling()` or similar functions use `closed='left'` or `closed='right'` appropriately such that future data is excluded.
- [ ] **Data Normalization / Scaling**:
  - [ ] If using any form of normalization (e.g., `MinMaxScaler`, `StandardScaler`, Z-score normalization) across the dataset, the `fit()` operation **must only** be performed on the training data *within the current walk-forward window*.
  - [ ] The `transform()` operation can then be applied to both the training and subsequent test/validation data.
  - [ ] **Prohibited**: Fitting the scaler on the entire dataset and then transforming.
- [ ] **Rolling Statistics Boundaries**: For any rolling statistics (mean, std dev, min, max) used as features or thresholds, explicitly verify that their calculation windows do not inadvertently extend into future data relative to the decision point.

---

## II. Signal Generation and Execution

- [ ] **Signal Generation Timestamp**: A trading signal for bar `t` must be generated using data available only up to the *close* of bar `t`.
- [ ] **Execution Timing**:
  - [ ] All trades resulting from a signal generated at the close of bar `t` **must be executed at the open of bar `t+1`**.
  - [ ] **Prohibited**: Assuming execution at the close price of bar `t`, or any price within bar `t+1` other than its open (unless explicitly modeled as market/limit orders with realistic latency/slippage).
- [ ] **Order Book / Market Depth**: If using order book data, ensure that the depth information used for a decision at time `t` is strictly from time `t` or earlier. No implied future liquidity.

---

## III. Walk-Forward Validation and Parameter Optimization

- [ ] **Parameter Search Isolation**: Any parameter optimization or selection process **must** be performed solely on the training/validation data *within the current walk-forward fold*.
  - [ ] **Prohibited**: Searching for optimal parameters across the entire historical dataset and then backtesting with those fixed parameters.
- [ ] **Out-of-Sample (OOS) Integrity**: The out-of-sample (test) period for each walk-forward step must be kept strictly separate from the in-sample (training/validation) period. No information from the OOS period should influence decisions made in the IS period.
- [ ] **Parameter Freezing**: Once parameters are selected from an in-sample period, they **must be frozen** for the subsequent out-of-sample test period.
- [ ] **Adaptive Parameters**: If parameters are designed to adapt, the adaptation logic itself must be based purely on historical data available *at the time of adaptation*.

---

## IV. Reporting and Analysis

- [ ] **IS vs. OOS Separation**: All performance reports **must clearly distinguish** between In-Sample and Out-of-Sample results. Avoid presenting aggregated results that mask potential overfitting on IS data.
- [ ] **Reporting Metrics**: Ensure that metrics derived for OOS periods are calculated purely from OOS data.
- [ ] **Avoid Data Snooping (Post-Analysis)**: When analyzing results, avoid subconsciously adjusting strategy rules or parameters based on observations from the OOS performance. All modifications should stem from hypothesis generation on IS data or prior domain knowledge.

---

## V. Code-Level Enforcement

- [ ] **Explicit Shift**: For any signal or feature that relies on future information for execution, ensure a `.shift(1)` (or equivalent) operation is applied to properly align the data for next-bar-open execution.
- [ ] **Time-Series Splitters**: Utilize `sklearn.model_selection.TimeSeriesSplit` or custom time-based splitting functions that enforce chronological order and prevent data leakage.
- [ ] **Assertions/Comments**: Add comments in the code to highlight critical time-dependency points and ensure anti-leakage. Consider adding assertions in development/testing to check for data order or unexpected future values.
- [ ] **Module Boundaries**: Ensure that data passed between modules (e.g., feature generation to backtest engine) adheres to the anti-leak principles.

---

## VI. Pair Trading Specific Checks (if applicable)

- [ ] **Spread/Ratio Construction**: If forming a synthetic instrument (e.g., spread or ratio), ensure its calculation for time `t` only uses prices available at time `t` or earlier for its constituent assets.
- [ ] **Hedge Ratio**: If dynamically calculating a hedge ratio (e.g., via cointegration), the estimation **must** be performed *only* on past data within the training window.
- [ ] **Stationarity Tests**: If using statistical tests (e.g., ADF, KPSS) for cointegration or stationarity, ensure the test window does not include future data relative to the decision point.

---

By rigorously following this checklist, we aim to build a research framework that yields reliable and robust strategy performance estimates.
