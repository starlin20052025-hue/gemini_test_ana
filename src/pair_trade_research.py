from data_loader import BinanceDataLoader
from backtest_engine import VectorizedBacktestEngine
import pandas as pd
import numpy as np
import os

class PairTradeResearch:
    def __init__(self, symbol_a="BTCUSDT", symbol_b="ETHUSDT", interval="1h"):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.interval = interval
        self.loader = BinanceDataLoader()
        self.engine = VectorizedBacktestEngine(commission=0.001) # Pair trade has double commission

    def run_pair_research(self, start_str="2022-01-01"):
        """
        Research on Statistical Arbitrage (Mean Reversion) between two assets.
        """
        print(f"Loading aligned data for {self.symbol_a} and {self.symbol_b}...")
        combined_df = self.loader.get_batch_data([self.symbol_a, self.symbol_b], self.interval, start_str=start_str)
        
        # Extract individual close prices
        price_a = combined_df[(self.symbol_a, 'close')]
        price_b = combined_df[(self.symbol_b, 'close')]
        
        # Calculate Ratio
        ratio = price_a / price_b
        
        # Calculate Z-Score of the Ratio
        # Window of 100 hours for mean reversion
        window = 100
        mean = ratio.rolling(window).mean()
        std = ratio.rolling(window).std()
        zscore = (ratio - mean) / std
        
        # Signal Generation: Mean Reversion
        # Long the ratio (Long A, Short B) when zscore < -2
        # Short the ratio (Short A, Long B) when zscore > 2
        # Exit when zscore returns to 0
        
        df = pd.DataFrame({
            'open': price_a, # Using Symbol A for dummy open price to satisfy engine
            'close': ratio,  # The "asset" we trade is the ratio
            'zscore': zscore
        })
        
        df['signal'] = 0
        # Simple signal logic
        df.loc[zscore < -1.5, 'signal'] = 1  # Buy Ratio
        df.loc[zscore > 1.5, 'signal'] = -1  # Sell Ratio
        
        # Logic for exit at mean (zscore crosses 0)
        # For vectorized, we keep the position until it flips or hits exit
        # A more complex signal logic would be needed for precise exit at 0
        
        print("Running backtest on Pair Ratio...")
        # Note: VectorizedBacktestEngine needs to be aware this is a spread
        # Here we simulate trading the ratio as a synthetic asset
        results = self.engine.run_backtest(df)
        metrics = self.engine.calculate_metrics(results)
        
        # Output Pair Trade Report
        report = f"""
# Pair Trade (Stat Arb) Research: {self.symbol_a} / {self.symbol_b}

## Strategy: Z-Score Mean Reversion
- Period: {start_str} to Present
- Window: {window} hours
- Entry Threshold: +/- 1.5 Std Dev

| Metric | Value |
|:-------|:------|
| Total Return | {metrics['Total Return']} |
| CAGR | {metrics['CAGR']} |
| Max Drawdown | {metrics['Max Drawdown']} |
| Sharpe Ratio | {metrics['Sharpe Ratio']} |
| Calmar Ratio | {metrics['Calmar Ratio']} |

## Observations
- Pair trading typically has lower CAGR but higher stability (Market Neutral).
- Commission drag is significant in pair trading due to double-leg execution.
"""
        with open("pair_trade_report.md", "w") as f:
            f.write(report)
        print("Pair Trade Research complete. Report saved to pair_trade_report.md")

if __name__ == "__main__":
    research = PairTradeResearch()
    research.run_pair_research()
