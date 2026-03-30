from data_loader import BinanceDataLoader
from backtest_engine import VectorizedBacktestEngine
import pandas as pd
import numpy as np
import os

class ResearchFramework:
    def __init__(self, symbol="BTCUSDT", interval="1h"):
        self.symbol = symbol
        self.interval = interval
        self.loader = BinanceDataLoader()
        self.engine = VectorizedBacktestEngine()

    def add_indicators(self, df):
        """
        Strategy Logic: SMA Cross + ATR Volatility Filter
        """
        df = df.copy()
        # SMA
        df['sma_short'] = df['close'].rolling(window=20).mean()
        df['sma_long'] = df['close'].rolling(window=50).mean()
        
        # ATR (Average True Range) for Volatility Filter
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Trend Strength: Only trade if price is above a longer term SMA
        df['trend_ma'] = df['close'].rolling(200).mean()
        
        # Signal Generation
        # 1. SMA Cross
        # 2. Price > 200 SMA (Trend Filter)
        # 3. ATR > Median ATR (Volatility Filter - avoid flat markets)
        median_atr = df['atr'].rolling(500).median()
        
        condition = (df['sma_short'] > df['sma_long']) & \
                    (df['close'] > df['trend_ma']) & \
                    (df['atr'] > median_atr)
        
        df['signal'] = np.where(condition, 1, 0)
        return df

    def run_walk_forward(self, start_str="2020-01-01", window_size_pct=0.5, step_pct=0.1):
        """
        Anchored Walk-Forward Validation
        """
        raw_df = self.loader.get_full_history(self.symbol, self.interval, start_str=start_str)
        df = self.loader.clean_and_check_gaps(raw_df, self.interval)
        
        n = len(df)
        window_size = int(n * window_size_pct)
        step = int(n * step_pct)
        
        results = []
        current_end = window_size
        
        while current_end + step <= n:
            train_data = df.iloc[:current_end].copy()
            test_data = df.iloc[current_end : current_end + step].copy()
            
            # Generate signals on test data (using parameters if we had them)
            # For baseline, we just use fixed params but only on the OOS slice
            full_test_slice = df.iloc[max(0, current_end - 200) : current_end + step].copy() 
            test_with_signals = self.add_indicators(full_test_slice).iloc[200:]
            
            backtest_res = self.engine.run_backtest(test_with_signals)
            metrics = self.engine.calculate_metrics(backtest_res)
            
            period_str = f"{pd.to_datetime(test_data['timestamp'].iloc[0], unit='ms').date()} to {pd.to_datetime(test_data['timestamp'].iloc[-1], unit='ms').date()}"
            metrics['Period'] = period_str
            results.append(metrics)
            
            current_end += step
            
        return pd.DataFrame(results)

    def generate_final_report(self, wf_results):
        report = f"# Anchored Walk-Forward Research Report: {self.symbol}\n\n"
        report += "## Walk-Forward Stages (Out-of-Sample Performance)\n"
        report += wf_results.to_markdown(index=False)
        
        # Summary
        # Clean numeric columns for calculation
        for col in ['CAGR', 'Max Drawdown', 'Sharpe Ratio']:
            wf_results[col + '_num'] = wf_results[col].str.replace('%', '').str.replace('Ratio', '').astype(float)
        
        avg_cagr = wf_results['CAGR_num'].mean()
        avg_mdd = wf_results['Max Drawdown_num'].mean()
        
        report += f"\n\n## Overall Research Conclusion\n"
        report += f"- **Average OOS CAGR**: {avg_cagr:.2f}%\n"
        report += f"- **Average OOS Max Drawdown**: {avg_mdd:.2f}%\n"
        report += f"- **Strategy Stability**: {'High' if avg_cagr > 0 and len(wf_results[wf_results['CAGR_num'] > 0]) > len(wf_results)/2 else 'Low'}\n"
        
        with open("strategy_report.md", "w") as f:
            f.write(report)
        print("Advanced Research complete. Report updated.")

if __name__ == "__main__":
    research = ResearchFramework()
    wf_results = research.run_walk_forward()
    research.generate_final_report(wf_results)
