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

class ResearchFramework:
    def __init__(self, symbol="BTCUSDT", interval="1h"):
        self.symbol = symbol
        self.interval = interval
        self.loader = BinanceDataLoader()
        # Initialize backtest engine with protocol-defined costs
        self.engine = VectorizedBacktestEngine(commission_bps=5, slippage_bps=1)

        # Reproducible Output Structure
        self.run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.output_base_dir = "outputs/single_asset_research"
        self.output_dir = os.path.join(self.output_base_dir, self.run_id)
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Results for this run will be saved in: {self.output_dir}")

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

    def run_walk_forward(self, start_str="2020-01-01", initial_train_pct=0.5, walk_forward_step_pct=0.1):
        """
        Anchored Walk-Forward Validation.
        Ensures strict anti-leakage during indicator calculation.

        :param start_str: Start date for historical data.
        :param initial_train_pct: Percentage of total data for initial training window (e.g., 0.5 for 50%).
        :param walk_forward_step_pct: Percentage of total data to step forward for each OOS period (e.g., 0.1 for 10%).
        """
        raw_df = self.loader.get_full_history(self.symbol, self.interval, start_str=start_str)
        df_processed, self.data_gap_stats = self.loader.clean_and_check_gaps(raw_df, self.interval)

        # Anti-Leak Control: Remove rows with gaps as per RESEARCH_PROTOCOL.md
        if df_processed['has_gap'].any():
            print(f"Removing {df_processed['has_gap'].sum()} rows with gaps from {self.symbol} data.")
            df_processed = df_processed[~df_processed['has_gap']].copy()
            df_processed.drop(columns=['has_gap'], inplace=True)
        else:
            df_processed.drop(columns=['has_gap'], inplace=True)

        # Set index for backtesting
        df_processed.set_index(pd.to_datetime(df_processed['timestamp'], unit='ms'), inplace=True)
        df_processed.drop(columns=['timestamp'], inplace=True) # Drop the timestamp column itself

        n = len(df_processed)
        if n == 0:
            print("No data available after processing. Cannot run walk-forward.")
            return pd.DataFrame(), pd.DataFrame() # Return empty for both results and full_oos_results

        # Minimum lookback for indicators (e.g., max window for SMA, ATR).
        # This should be dynamically determined from add_indicators, for now, use a conservative value.
        # Max lookback for current strategy: median_atr window (500)
        min_lookback_bars = 500

        # Determine initial training window size and step size in terms of bars
        initial_train_size = max(int(n * initial_train_pct), min_lookback_bars)
        step_size = max(int(n * walk_forward_step_pct), 1) # Ensure step is at least 1 bar

        if initial_train_size >= n:
            print("Initial training window covers entire dataset. No out-of-sample period for walk-forward.")
            return pd.DataFrame()

        results = []
        full_oos_results = pd.DataFrame() # To store all OOS trade results

        current_train_end_idx = initial_train_size

        while current_train_end_idx < n:
            # Define the current training data slice (in-sample for indicator calculation and param fitting)
            train_slice = df_processed.iloc[:current_train_end_idx].copy()

            # --- Placeholder for Parameter Optimization (Future Work) ---
            # If strategy involved parameters to be optimized, this is where it would happen.
            # E.g., optimal_params = self.optimize_parameters(train_slice)
            # For this baseline, parameters are fixed.

            # Define the Out-of-Sample (OOS) test slice
            test_start_idx = current_train_end_idx
            test_end_idx = min(current_train_end_idx + step_size, n)

            # If no actual test data remaining, break
            if test_start_idx >= test_end_idx:
                break

            test_slice_raw = df_processed.iloc[test_start_idx:test_end_idx].copy()

            # --- Anti-Leakage for Indicator Calculation ---
            # To calculate indicators for test_slice_raw, we need lookback data from train_slice.
            indicator_lookback_slice = df_processed.iloc[max(0, current_train_end_idx - min_lookback_bars) : current_train_end_idx].copy()

            # Combine lookback data + current test slice for indicator calculation
            combined_slice_for_indicators = pd.concat([indicator_lookback_slice, test_slice_raw])

            # Calculate indicators on the combined slice
            combined_slice_with_signals = self.add_indicators(combined_slice_for_indicators)

            # Extract only the test_slice portion with signals
            test_slice_with_signals = combined_slice_with_signals.loc[test_slice_raw.index]

            # Run backtest on the OOS test slice
            backtest_res = self.engine.run_backtest(test_slice_with_signals, signal_column='signal')
            metrics = self.engine.calculate_metrics(backtest_res, time_interval=self.interval)

            period_str = f"{test_slice_with_signals.index[0].date()} to {test_slice_with_signals.index[-1].date()}"
            metrics['Period'] = period_str
            results.append(metrics)

            # Append OOS results for overall aggregation
            if not backtest_res.empty:
                full_oos_results = pd.concat([full_oos_results, backtest_res])

            current_train_end_idx += step_size

        if not full_oos_results.empty:
            overall_metrics = self.engine.calculate_metrics(full_oos_results, time_interval=self.interval)
            overall_metrics['Period'] = "Overall OOS"
            results.append(overall_metrics) # Add overall OOS metrics

        return pd.DataFrame(results), full_oos_results

    def generate_final_report(self, wf_results, full_oos_results):
        # Save run metadata
        metadata = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "interval": self.interval,
            "initial_capital": self.engine.initial_capital,
            "commission_bps": self.engine.commission_rate * 10000,
            "slippage_bps": self.engine.slippage_rate * 10000,
            "status": "Completed" if not wf_results.empty else "No_Data",
            "data_gap_stats": self.data_gap_stats, # Add gap statistics
            # Add more relevant parameters as needed
        }
        with open(os.path.join(self.output_dir, "run_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4, cls=NumpyEncoder)

        if wf_results.empty:
            report = f"# Anchored Walk-Forward Research Report: {self.symbol}\n\n"
            report += "## No Walk-Forward Stages were generated due to insufficient data or errors.\n"
            report_filepath = os.path.join(self.output_dir, f"strategy_report_{self.symbol}_{self.interval}.md")
            with open(report_filepath, "w") as f:
                f.write(report)
            print(f"No walk-forward stages were generated. Report updated in {report_filepath}.")
            return

        report = f"# Anchored Walk-Forward Research Report: {self.symbol}\n\n"
        report += "## Walk-Forward Stages (Out-of-Sample Performance)\n"
        report += wf_results.to_markdown(index=False)
        
        # Save wf_results DataFrame
        wf_results.to_csv(os.path.join(self.output_dir, "wf_metrics_summary.csv"), index=False)

        # Summary for overall OOS performance
        overall_oos_row = wf_results[wf_results['Period'] == "Overall OOS"]
        if not overall_oos_row.empty:
            report += f"\n\n## Overall Out-of-Sample Performance Summary\n"
            report += f"- **Total Return**: {overall_oos_row['Total Return'].iloc[0]}\n"
            report += f"- **CAGR**: {overall_oos_row['CAGR'].iloc[0]}\n"
            report += f"- **Max Drawdown**: {overall_oos_row['Max Drawdown'].iloc[0]}\n"
            report += f"- **Sharpe Ratio**: {overall_oos_row['Sharpe Ratio'].iloc[0]}\n"
            report += f"- **Calmar Ratio**: {overall_oos_row['Calmar Ratio'].iloc[0]}\n"
            report += f"- **Number of Trades**: {overall_oos_row['Number of Trades'].iloc[0]}\n"
            report += f"- **Exposure (%)**: {overall_oos_row['Exposure (%)'].iloc[0]}\n"
        else:
            report += f"\n\n## Overall Out-of-Sample Performance Summary: Not Available\n"
            report += f"   (No 'Overall OOS' period found in results, possibly due to insufficient data for any OOS stages.)\n"

        # Clean numeric columns for calculation for other summary
        wf_results_summary = wf_results[wf_results['Period'] != "Overall OOS"].copy()

        if not wf_results_summary.empty:
            for col in ['CAGR', 'Max Drawdown', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']:
                if col in wf_results_summary.columns:
                    # Handle cases where value is 'inf' or '-inf' from metrics calculation
                    wf_results_summary[col + '_num'] = wf_results_summary[col].astype(str).str.replace('%', '').replace('inf', str(np.nan)).astype(float)

            avg_cagr = wf_results_summary['CAGR_num'].mean()
            avg_mdd = wf_results_summary['Max Drawdown_num'].mean()

            report += f"\n\n## Per-Stage Average Performance (Excluding Overall OOS)\n"
            report += f"- **Average OOS CAGR**: {avg_cagr:.2f}%\n"
            report += f"- **Average OOS Max Drawdown**: {avg_mdd:.2f}%\n"
            # More sophisticated stability metrics can be added here
            report += f"- **Strategy Stability (Positive CAGR Stages)**: {len(wf_results_summary[wf_results_summary['CAGR_num'] > 0])} out of {len(wf_results_summary)} stages were profitable.\n"
        else:
            report += f"\n\n## No Walk-Forward Stages to Summarize (Excluding Overall OOS)\n"
        
        # Save full_oos_results DataFrame if available
        if not full_oos_results.empty:
            full_oos_results.to_csv(os.path.join(self.output_dir, "full_oos_backtest_results.csv"))
            print(f"Full OOS backtest results saved to {os.path.join(self.output_dir, 'full_oos_backtest_results.csv')}")

        report_filepath = os.path.join(self.output_dir, f"strategy_report_{self.symbol}_{self.interval}.md")
        with open(report_filepath, "w") as f:
            f.write(report)
        print(f"Advanced Research complete. Report updated in {report_filepath}.")

if __name__ == "__main__":
    research = ResearchFramework()
    wf_results, full_oos_results = research.run_walk_forward()
    research.generate_final_report(wf_results, full_oos_results)
