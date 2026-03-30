import pandas as pd
import numpy as np

class VectorizedBacktestEngine:
    def __init__(self, initial_capital=100000, commission_bps=5, slippage_bps=1):
        """
        Initializes the backtest engine.
        :param initial_capital: Starting capital.
        :param commission_bps: Commission fee in basis points (1 bps = 0.01%).
        :param slippage_bps: Slippage in basis points.
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_bps / 10000
        self.slippage_rate = slippage_bps / 10000

    def run_backtest(self, df, signal_column='signal'):
        """
        Runs a vectorized backtest on the given data.

        The core principle is "Signal at Close, Execute at Next Open".

        :param df: DataFrame with 'open', 'high', 'low', 'close' columns.
        :param signal_column: The name of the column containing the target position signal (1, -1, 0).
        :return: A DataFrame containing the detailed backtest results.
        """
        data = df.copy().sort_index()

        # --- 1. Define Execution Price ---
        # The execution price for a signal at bar 't' is the open of bar 't+1'.
        data['execution_price'] = data['open'].shift(-1)

        # --- 2. Define Target Position ---
        # The signal at time 't' determines our desired position for the period from 't+1' to 't+2'.
        # We shift the signal to align it with the time it becomes active.
        data['target_position'] = data[signal_column].shift(1).fillna(0)

        # --- 3. Calculate Position Changes and Costs ---
        # 'actual_position' is the position held *during* the bar, from its open to close.
        data['actual_position'] = data['target_position'].shift(1).fillna(0)
        
        # 'position_change' is the amount traded at the 'execution_price' (this bar's open).
        data['position_change'] = data['target_position'] - data['actual_position']

        # --- 4. Calculate Transaction Costs ---
        # Turnover is the absolute value of the change in position.
        turnover = data['position_change'].abs()
        
        # Slippage: apply to the execution price based on trade direction
        slippage_cost = turnover * data['execution_price'] * self.slippage_rate
        
        # Commission: apply to the value of the traded amount
        commission_cost = turnover * data['execution_price'] * self.commission_rate
        
        data['transaction_costs'] = slippage_cost + commission_cost

        # --- 5. Calculate Returns ---
        # Gross return is based on the position held *during* the previous bar,
        # and the price change from the previous execution price to the current one.
        # This represents the PnL from holding the asset.
        data['gross_return'] = data['actual_position'] * (data['execution_price'] - data['execution_price'].shift(1))
        
        # Net return is the gross return minus costs for this bar's trades.
        data['net_return'] = data['gross_return'] - data['transaction_costs']

        # --- 6. Calculate Equity Curve ---
        data['equity_curve'] = self.initial_capital + data['net_return'].fillna(0).cumsum()
        
        # Fill remaining NaN values (e.g., from shifted execution_price at the end)
        # Note: equity_curve should not be filled with 0 if it starts with initial_capital.
        # This fillna is for other columns like execution_price at the very end.
        data.fillna(0, inplace=True)

        return data

    def calculate_metrics(self, results_df, time_interval='1h'):
        """
        Calculates key performance indicators from the backtest results.
        """
        equity = results_df['equity_curve']
        if equity.iloc[0] == 0: equity.iloc[0] = self.initial_capital # Ensure start is not 0
        
        # --- Total Return & CAGR ---
        total_return = (equity.iloc[-1] / self.initial_capital) - 1
        
        interval_map = {'1h': 24*365, '4h': 6*365, '1d': 365, '15m': 96*365}
        bars_per_year = interval_map.get(time_interval, 24*365)
        
        num_years = len(results_df) / bars_per_year
        cagr = ((1 + total_return) ** (1 / num_years)) - 1 if num_years > 0 else 0

        # --- Drawdown ---
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        mdd = drawdown.min()

        # --- Sharpe & Sortino ---
        # Use pct_change on equity curve for returns series
        daily_returns = equity.resample('D').last().pct_change().dropna()
        
        if len(daily_returns) > 1:
            sharpe_ratio = (daily_returns.mean() * np.sqrt(365)) / daily_returns.std() if daily_returns.std() != 0 else 0
            
            negative_returns = daily_returns[daily_returns < 0]
            downside_deviation = negative_returns.std() if len(negative_returns) > 1 else 0
            sortino_ratio = (daily_returns.mean() * np.sqrt(365)) / downside_deviation if downside_deviation != 0 else 0
        else:
            sharpe_ratio = sortino_ratio = 0

        # --- Calmar Ratio ---
        calmar_ratio = cagr / abs(mdd) if mdd != 0 else 0
        
        # --- Trade-level stats ---
        trades = results_df[results_df['position_change'] != 0]
        num_trades = len(trades)
        
        # --- Profit Factor ---
        gross_profits = results_df['net_return'][results_df['net_return'] > 0].sum()
        gross_losses = results_df['net_return'][results_df['net_return'] < 0].sum()
        profit_factor = abs(gross_profits / gross_losses) if gross_losses != 0 else np.inf
        
        # --- Trade Win Rate (Simplified - bar-level) ---
        # Note: A proper trade win rate requires a trade log (entry-exit pairs).
        # This is a simplified bar-level win rate, showing profitable bars.
        profitable_bars = (results_df['net_return'] > 0).sum()
        losing_bars = (results_df['net_return'] < 0).sum()
        total_non_zero_bars = profitable_bars + losing_bars
        win_rate = profitable_bars / total_non_zero_bars if total_non_zero_bars > 0 else 0

        # --- Turnover (Annualized Approximation) ---
        # Sum of absolute traded value / initial capital, then annualized
        total_traded_value = (results_df['position_change'].abs() * results_df['execution_price']).sum()
        turnover = (total_traded_value / self.initial_capital) / num_years if num_years > 0 else 0
        
        # --- Average Holding Period (Requires Trade Log - Placeholder) ---
        avg_holding_period = "N/A (Requires Trade Log)" # Placeholder for now, needs trade-level extraction
        
        metrics = {
            "Start Date": pd.to_datetime(results_df.index[0]).date(),
            "End Date": pd.to_datetime(results_df.index[-1]).date(),
            "Total Return": f"{total_return:.2%}",
            "CAGR": f"{cagr:.2%}",
            "Max Drawdown": f"{mdd:.2%}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Sortino Ratio": f"{sortino_ratio:.2f}",
            "Calmar Ratio": f"{calmar_ratio:.2f}",
            "Number of Trades": num_trades,
            "Exposure (%)": f"{(results_df['actual_position'] != 0).mean():.2%}",
            "Profit Factor": f"{profit_factor:.2f}",
            "Trade Win Rate (%)": f"{win_rate:.2%}",
            "Turnover (Annualized)": f"{turnover:.2f}",
            "Average Holding Period": avg_holding_period,
        }
        return metrics

def create_test_data():
    """Creates a simple, predictable data series for testing."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=10, freq="D"))
    data = {
        'open':  [100, 102, 103, 101, 105, 106, 108, 107, 109, 110],
        'close': [101, 102.5, 100, 104, 105.5, 107, 106.5, 108, 110, 111],
        'high':  [102, 103, 104, 105, 106, 108, 109, 109, 111, 112],
        'low':   [99,  101, 100, 100, 104, 105, 106, 106, 108, 109],
    }
    df = pd.DataFrame(data, index=dates)
    # Signal: Go long on day 2, flat on day 5, short on day 7
    df['signal'] = 0
    df.iloc[1, df.columns.get_loc('signal')] = 1  # Signal at close of day 2
    df.iloc[4, df.columns.get_loc('signal')] = 0  # Signal at close of day 5
    df.iloc[6, df.columns.get_loc('signal')] = -1 # Signal at close of day 7
    return df

if __name__ == "__main__":
    # --- Run Unit Test ---
    test_df = create_test_data()
    
    # Use 0 commission/slippage for easy manual verification
    engine = VectorizedBacktestEngine(initial_capital=10000, commission_bps=0, slippage_bps=0)
    results = engine.run_backtest(test_df)

    print("--- Backtest Results on Test Data ---")
    print("Columns: index, open, execution_price, signal, target_position, actual_position, position_change, gross_return, net_return, equity_curve")
    print(results[['open', 'execution_price', 'signal', 'target_position', 'actual_position', 'position_change', 'gross_return', 'net_return', 'equity_curve']].round(2))
    
    # --- Manual Verification Logic ---
    # 1. Signal at day 2 (close=102.5) is 1.
    #    - Trade on day 3 open: Buy 1 share at 103.
    #    - position_change = 1. gross_return = 0. net_return = 0 (cost is 0). equity = 10000.
    # 2. Hold 1 share.
    #    - Day 4 open is 101.
    #    - gross_return = 1 * (101 - 103) = -2. equity = 10000 - 2 = 9998.
    # 3. Hold 1 share.
    #    - Day 5 open is 105. Signal at day 5 is 0.
    #    - gross_return = 1 * (105 - 101) = 4. equity = 9998 + 4 = 10002.
    # 4. Signal at day 5 (close=105.5) is 0.
    #    - Trade on day 6 open: Sell 1 share at 106.
    #    - position_change = -1. gross_return = 1 * (106 - 105) = 1. equity = 10002 + 1 = 10003.
    # 5. Hold 0 shares. Signal at day 7 is -1.
    #    - Day 7 open is 108.
    #    - gross_return = 0. equity = 10003.
    # 6. Signal at day 7 (close=106.5) is -1.
    #    - Trade on day 8 open: Sell 1 share at 107.
    #    - position_change = -1. gross_return = 0. equity = 10003.
    # 7. Hold -1 share.
    #    - Day 9 open is 109.
    #    - gross_return = -1 * (109 - 107) = -2. equity = 10003 - 2 = 10001.
    # 8. Hold -1 share. No more signals.
    #    - Day 10 open is 110.
    #    - gross_return = -1 * (110 - 109) = -1. equity = 10001 - 1 = 10000.
    
    print("\n--- Metrics ---")
    metrics = engine.calculate_metrics(results, time_interval='1d')
    print(metrics)
    
    final_equity = results['equity_curve'].iloc[-1]
    print(f"\nFinal Equity from test: {final_equity:.2f}")
    print("Expected final equity (manual calc): 10003.00")
    assert abs(final_equity - 10003) < 0.01, "Test Failed!"
    print("\nUnit Test Passed!")

