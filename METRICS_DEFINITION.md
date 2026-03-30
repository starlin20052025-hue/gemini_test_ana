# Metrics Definition

This document provides precise definitions for all key performance indicators (KPIs) used in this cryptocurrency strategy research framework. Adherence to these definitions ensures consistent and comparable reporting across different strategies and backtest runs.

---

## 1. Core Performance Metrics

### 1.1. Total Return
- **Definition**: The percentage change in equity from the start to the end of the backtest period.
- **Formula**: `(Final Equity / Initial Capital) - 1`
- **Context**: Provides a simple, absolute measure of overall performance.

### 1.2. Compound Annual Growth Rate (CAGR)
- **Definition**: The annualized rate of return of the equity curve over the entire backtest period. It assumes returns are reinvested.
- **Formula**: `((Final Equity / Initial Capital) ^ (1 / Number of Years)) - 1`
- **Number of Years**: Calculated based on the total number of bars in the backtest and the bars per year for the given `time_interval`.
- **Context**: Standard metric for comparing investment performance over different time horizons.

### 1.3. Maximum Drawdown (MDD)
- **Definition**: The largest percentage drop from a peak in equity to a subsequent trough, before a new peak is achieved.
- **Formula**: `Min((Equity - Rolling Max Equity) / Rolling Max Equity)`
- **Context**: Measures the largest loss from a peak, indicating downside risk.

---

## 2. Risk-Adjusted Return Metrics

### 2.1. Sharpe Ratio
- **Definition**: Measures the excess return (over the risk-free rate) per unit of total risk (standard deviation of returns). Assumes normally distributed returns.
- **Formula**: `(Annualized Mean Daily Return - Annualized Risk-Free Rate) / Annualized Standard Deviation of Daily Returns`
  - For simplicity, the risk-free rate is assumed to be 0 for this framework.
  - Daily returns are used for calculation, then annualized by multiplying mean by `sqrt(252)` and std dev by `sqrt(252)` for daily data, or `sqrt(365)` for calendar days. Here we use `sqrt(365)`.
- **Context**: Widely used to evaluate the risk-adjusted performance of an investment. Higher is better.

### 2.2. Sortino Ratio
- **Definition**: Similar to the Sharpe Ratio, but penalizes only downside volatility (standard deviation of negative returns), making it more suitable for non-normally distributed returns or when only downside risk is a concern.
- **Formula**: `(Annualized Mean Daily Return - Annualized Risk-Free Rate) / Annualized Downside Deviation of Daily Returns`
  - Risk-free rate assumed 0.
  - Downside deviation is calculated using only daily returns below 0.
- **Context**: Preferred over Sharpe when differentiating between "good" and "bad" volatility. Higher is better.

### 2.3. Calmar Ratio
- **Definition**: Measures the average annual return relative to the maximum drawdown.
- **Formula**: `CAGR / Absolute(Max Drawdown)`
- **Context**: Focuses on drawdown as the primary measure of risk. Higher is better.

---

## 3. Trade-Level and Supporting Metrics

### 3.1. Number of Trades
- **Definition**: The total count of executed trades (entries and exits combined) during the backtest period.
- **Formula**: `Sum of absolute(position_change) where position_change != 0` (each buy/sell is one "trade" event).
- **Context**: Indicates trading frequency.

### 3.2. Exposure (%)
- **Definition**: The percentage of time the strategy held an open position (long or short) during the backtest period.
- **Formula**: `(Number of bars with actual_position != 0) / Total Number of bars`
- **Context**: Measures how much capital was actively deployed.

### 3.3. Profit Factor
- **Definition**: The ratio of gross profits to gross losses.
- **Formula**: `Sum(Gross Profits) / Sum(Absolute Gross Losses)`
  - Calculated from `net_return` column where `net_return` is positive vs negative.
- **Context**: Indicates how much profit is generated for every dollar lost. A value greater than 1 suggests profitability.

### 3.4. Trade Win Rate (%)
- **Definition**: The percentage of profitable trades out of all closed trades.
- **Formula**: `(Number of profitable trades) / Total Number of trades with PnL`
  - Requires explicit trade extraction (entry to exit events). **(Currently simplified, needs a proper trade log)**
- **Context**: Simple measure of trading success frequency.

### 3.5. Average Holding Period
- **Definition**: The average duration that positions are held open.
- **Formula**: `Sum(Holding periods for each trade) / Total Number of trades`
  - Requires explicit trade extraction. **(Currently not implemented, needs a proper trade log)**
- **Context**: Helps understand the nature of the strategy (e.g., day trading vs. swing trading).

### 3.6. Turnover
- **Definition**: Measures how frequently assets in a portfolio are bought and sold over a period. In this vectorized backtest, it's approximated as the sum of absolute position changes scaled by trade value.
- **Formula**: `Sum(abs(position_change) * execution_price) / Initial Capital` (can be annualized).
- **Context**: Indicates transaction cost sensitivity and trading activity. High turnover often means high transaction costs.

---

## 4. Distinction Between Metrics Levels

- **Bar-Level Metrics**: Calculated directly from bar-by-bar data (e.g., daily returns for Sharpe/Sortino). These are generally more robust in vectorized backtests.
- **Trade-Level Metrics**: Require explicit identification of individual trade entry and exit points (e.g., Trade Win Rate, Average Holding Period). The current `VectorizedBacktestEngine` provides `num_trades` based on `position_change`, but full trade-level analysis (e.g., PnL per trade) is not yet implemented.
- **Portfolio-Level Metrics**: Apply to the overall equity curve (e.g., Total Return, CAGR, MDD, Sharpe, Calmar).

---

## 5. Potential Pitfalls and Misleading Metrics

- **High Sharpe Ratio with Low Trade Count**: A high Sharpe Ratio from very few trades might be statistically insignificant. Always check `Number of Trades`.
- **High CAGR with Extreme MDD**: High returns mean little if the drawdowns are unacceptable for risk tolerance. Always consider CAGR alongside MDD and Calmar Ratio.
- **"Optimized" Metrics**: Metrics from in-sample optimization are often inflated and do not represent true out-of-sample performance. Always prioritize OOS metrics.
- **Ignoring Transaction Costs/Slippage**: Metrics calculated without realistic costs can be highly misleading.
- **Misinterpreting Win Rate**: A high win rate can still lead to losses if losing trades are significantly larger than winning trades (check Profit Factor).

---

By adhering to these definitions and being aware of potential pitfalls, the research framework aims to provide a more transparent and reliable assessment of strategy performance.
