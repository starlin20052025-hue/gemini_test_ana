import pandas as pd
import numpy as np

class VectorizedBacktestEngine:
    def __init__(self, initial_capital=10000, commission=0.0005, slippage=0.0001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run_backtest(self, df, signal_column='signal'):
        """
        Expects a DataFrame with 'open', 'high', 'low', 'close' and a 'signal' column.
        Signal values: 1 (long), -1 (short), 0 (flat).
        
        IMPORTANT: Signals are assumed to be generated at the CLOSE of the bar.
        Execution happens at the OPEN of the NEXT bar.
        """
        data = df.copy()
        
        # 1. Shift signals to simulate Next Bar Open execution
        # signal at t means we enter at t+1 open
        data['target_position'] = data[signal_column].shift(1).fillna(0)
        
        # 2. Calculate returns based on Next Open to Next Next Open
        # But a simpler way for vectorized: 
        # position * (close_t / close_t-1 - 1) is common but risky for future leak.
        # Let's use Open-to-Open returns for position holding.
        data['next_open'] = data['open'].shift(-1)
        # If we enter at open_t, and exit at open_t+1:
        data['market_return'] = data['open'].pct_change().shift(-1) 
        
        # 3. Transaction Costs
        # Identify when position changes
        data['pos_diff'] = data['target_position'].diff().abs()
        data['costs'] = data['pos_diff'] * (self.commission + self.slippage)
        
        # 4. Strategy Return
        data['strategy_return'] = (data['target_position'] * data['market_return']) - data['costs']
        
        # 5. Equity Curve
        data['equity_curve'] = (1 + data['strategy_return'].fillna(0)).cumprod()
        data['equity'] = data['equity_curve'] * self.initial_capital
        
        return data

    def calculate_metrics(self, df):
        """
        Calculate key performance indicators.
        """
        equity = df['equity']
        returns = df['strategy_return'].fillna(0)
        
        # Total Return
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        
        # Annualized Return (Assume 1h data -> 24*365 hours/year)
        # Using the actual length of data
        hours_per_year = 24 * 365
        years = len(df) / hours_per_year
        cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        mdd = drawdown.min()
        
        # Sharpe Ratio (Daily-like adjustment)
        # Volatility of hourly returns, then scale to annual
        vol = returns.std() * np.sqrt(hours_per_year)
        sharpe = (cagr / vol) if vol != 0 else 0
        
        # Calmar Ratio
        calmar = (cagr / abs(mdd)) if mdd != 0 else 0
        
        metrics = {
            "Total Return": f"{total_return:.2%}",
            "CAGR": f"{cagr:.2%}",
            "Max Drawdown": f"{mdd:.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Calmar Ratio": f"{calmar:.2f}",
            "Win Rate": f"{(returns > 0).sum() / (returns != 0).sum():.2%}" if (returns != 0).sum() > 0 else "0%"
        }
        
        return metrics

if __name__ == "__main__":
    # Test with dummy data
    dates = pd.date_range(start="2023-01-01", periods=100, freq="H")
    df = pd.DataFrame({
        'open': np.linspace(100, 110, 100) + np.random.randn(100),
        'close': np.linspace(100, 110, 100) + np.random.randn(100),
        'signal': np.random.choice([0, 1], 100)
    }, index=dates)
    
    engine = VectorizedBacktestEngine()
    results = engine.run_backtest(df)
    metrics = engine.calculate_metrics(results)
    print(metrics)
