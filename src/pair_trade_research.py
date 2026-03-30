from data_loader import BinanceDataLoader
from backtest_engine import VectorizedBacktestEngine
import pandas as pd
import numpy as np
import os
import uuid
import json # For saving metadata
from datetime import datetime # For timestamp in run_id

# Custom JSON encoder for NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class PairTradeResearch:
    def __init__(self, symbol_a="BTCUSDT", symbol_b="ETHUSDT", interval="1h"):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.interval = interval
        self.loader = BinanceDataLoader()
        # Initialize backtest engine with protocol-defined costs for pair trading (double commission)
        self.engine = VectorizedBacktestEngine(commission_bps=10, slippage_bps=1)

        # Reproducible Output Structure
        self.run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.output_base_dir = "outputs/pair_trade_research"
        self.output_dir = os.path.join(self.output_base_dir, self.run_id)
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Results for this run will be saved in: {self.output_dir}")

    def run_pair_research(self, start_str="2022-01-01"):
        """
        Research on Statistical Arbitrage (Mean Reversion) between two assets.
        """
        print(f"Loading aligned data for {self.symbol_a} and {self.symbol_b}...")
        combined_df, all_gap_stats = self.loader.get_batch_data([self.symbol_a, self.symbol_b], self.interval, start_str=start_str)
        
        # Anti-Leak Control: Remove rows where any symbol had a gap
        gap_cols = [col for col in combined_df.columns if 'has_gap' in col]
        if combined_df[gap_cols].any(axis=1).any():
            initial_rows = len(combined_df)
            combined_df = combined_df[~combined_df[gap_cols].any(axis=1)]
            print(f"Removed {initial_rows - len(combined_df)} rows due to gaps.")
        combined_df = combined_df.drop(columns=gap_cols) # Drop the has_gap columns
        
        # Set index for backtesting
        combined_df.index = pd.to_datetime(combined_df.index.get_level_values(0), unit='ms') # Assuming timestamp is the first level of index from get_batch_data
        # Note: combined_df.columns.droplevel('timestamp') is no longer needed as 'timestamp' is not a column level anymore.

        # Extract individual close prices
        price_a = combined_df[self.symbol_a]['close']
        price_b = combined_df[self.symbol_b]['close']
        
        # Calculate Ratio
        ratio = price_a / price_b
        
        # Calculate Z-Score of the Ratio
        # Window of 100 hours for mean reversion
        window = 100
        # Anti-Leak Control: Ensure rolling mean/std are calculated only on past data
        mean = ratio.rolling(window, closed='left').mean()
        std = ratio.rolling(window, closed='left').std()
        zscore = (ratio - mean) / std
        
        # Signal Generation: Mean Reversion
        # Long the ratio (Long A, Short B) when zscore < -1.5
        # Short the ratio (Short A, Long B) when zscore > 1.5
        # Exit when zscore returns to 0
        
        # Prepare DataFrame for backtest engine
        # Note: This is still a simplified model treating the ratio as a single tradable asset.
        # As per REVIEW_NOTES.md, a real pair-trade engine is required for robust analysis.
        df_for_backtest = pd.DataFrame({
            'open': combined_df[self.symbol_a]['open'], # Using Symbol A's open for the 'synthetic' asset
            'close': ratio,  # The "asset" we trade is the ratio itself
            'zscore': zscore
        }, index=combined_df.index) # Ensure index alignment
        
        df_for_backtest['signal'] = 0
        # Simple signal logic: enter when Z-score crosses threshold
        df_for_backtest.loc[df_for_backtest['zscore'] < -1.5, 'signal'] = 1  # Buy Ratio (Long A, Short B)
        df_for_backtest.loc[df_for_backtest['zscore'] > 1.5, 'signal'] = -1 # Sell Ratio (Short A, Long B)
        
        # Logic for exit at mean (zscore crosses 0) - This requires careful handling in vectorized backtest.
        # For now, positions are held until a new entry signal (in opposite direction) or explicit flat signal.
        # This is a simplification and not truly robust mean-reversion exit.
        
        print("Running backtest on Pair Ratio (simplified model)...")
        backtest_res = self.engine.run_backtest(df_for_backtest)
        metrics = self.engine.calculate_metrics(backtest_res, time_interval=self.interval) # Pass interval for correct annualization
        
        # Save run metadata
        metadata = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "symbol_a": self.symbol_a,
            "symbol_b": self.symbol_b,
            "interval": self.interval,
            "initial_capital": self.engine.initial_capital,
            "commission_bps": self.engine.commission_rate * 10000,
            "slippage_bps": self.engine.slippage_rate * 10000,
            "status": "Completed" if not backtest_res.empty else "No_Data",
            "entry_threshold": 1.5, # Example parameter
            "zscore_window": window, # Example parameter
            "data_gap_stats": all_gap_stats, # Add gap statistics for each symbol
            # Add more relevant parameters as needed
        }
        with open(os.path.join(self.output_dir, "run_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4, cls=NumpyEncoder)

        # Save detailed backtest results
        if not backtest_res.empty:
            backtest_res.to_csv(os.path.join(self.output_dir, "pair_trade_backtest_results.csv"))
            print(f"Detailed backtest results saved to {os.path.join(self.output_dir, 'pair_trade_backtest_results.csv')}")

        # Output Pair Trade Report
        report = f"""
# Pair Trade (Stat Arb) Research: {self.symbol_a} / {self.symbol_b} (Simplified Model)

## WARNING: This is a simplified prototype.
As per `REVIEW_NOTES.md` and `RESEARCH_PROTOCOL.md`, this pair trade implementation
treats the ratio as a synthetic single asset and does not account for true
two-leg accounting, hedge ratio modeling, or separate costs per leg.
Results from this section should be treated as **exploratory only** and
**not as meaningful performance evidence**.

## Strategy: Z-Score Mean Reversion
- Period: {start_str} to Present
- Window: {window} hours
- Entry Threshold: +/- 1.5 Std Dev
- Rolling Z-Score `closed='left'` used for anti-leakage.

| Metric | Value |
|:-------|:------|
| Total Return | {metrics['Total Return']} |
| CAGR | {metrics['CAGR']} |
| Max Drawdown | {metrics['Max Drawdown']} |
| Sharpe Ratio | {metrics['Sharpe Ratio']} |
| Calmar Ratio | {metrics['Calmar Ratio']} |
| Number of Trades | {metrics['Number of Trades']} |
| Exposure (%) | {metrics['Exposure (%)']} |
| Profit Factor | {metrics['Profit Factor']} |
| Trade Win Rate (%) | {metrics['Trade Win Rate (%)']} |
| Turnover (Annualized) | {metrics['Turnover (Annualized)']} |
| Average Holding Period | {metrics['Average Holding Period']} |

## Observations
- Pair trading typically has lower CAGR but higher stability (Market Neutral).
- Commission drag is significant in pair trading due to double-leg execution.
- The current model is a placeholder; a full two-leg engine is required for proper validation.
"""
        report_filepath = os.path.join(self.output_dir, f"pair_trade_report_{self.symbol_a}_{self.symbol_b}_{self.interval}.md")
        with open(report_filepath, "w") as f:
            f.write(report)
        print(f"Pair Trade Research complete. Report saved to {report_filepath}")

if __name__ == "__main__":
    research = PairTradeResearch()
    research.run_pair_research()
