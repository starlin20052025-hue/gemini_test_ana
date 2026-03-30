import pandas as pd
import requests
import os
from datetime import datetime
import time
import numpy as np

class BinanceDataLoader:
    def __init__(self, base_url="https://api.binance.com", data_dir="data"):
        self.base_url = base_url
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def fetch_klines(self, symbol, interval, start_time=None, end_time=None, limit=1000):
        """
        Fetch historical klines from Binance API.
        :param start_time: int (ms timestamp)
        :param end_time: int (ms timestamp)
        """
        endpoint = "/api/v3/klines"
        url = self.base_url + endpoint
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def get_full_history(self, symbol, interval, start_str="2017-01-01"):
        """
        Fetch all available history for a symbol and interval.
        """
        filename = f"{symbol}_{interval}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        existing_df = None
        if os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            # Ensure timestamp is int for comparison
            existing_df['timestamp'] = existing_df['timestamp'].astype(int)
            start_ts = int(existing_df['timestamp'].iloc[-1]) + 1
            print(f"Updating {symbol} {interval} from {datetime.fromtimestamp(start_ts/1000)}")
        else:
            start_ts = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
            print(f"Fetching full history for {symbol} {interval} starting from {start_str}")

        all_data = []
        current_ts = start_ts
        now_ts = int(time.time() * 1000)

        while current_ts < now_ts:
            klines = self.fetch_klines(symbol, interval, start_time=current_ts)
            if not klines:
                break
            
            all_data.extend(klines)
            # The next start time is the close time of the last candle + 1ms
            current_ts = klines[-1][6] + 1
            
            # Prevent rate limiting
            time.sleep(0.1)
            
            if len(klines) < 500: # Usually means we reached the end
                break
        
        new_df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        if new_df.empty:
            if existing_df is not None:
                print("No new data found. Returning existing data.")
                return existing_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            else:
                print("No new data found and no existing file. Returning empty DataFrame.")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Basic cleaning for new data
        new_df['timestamp'] = new_df['timestamp'].astype(int)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            new_df[col] = new_df[col].astype(float)
        new_df = new_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        final_df = new_df
        if existing_df is not None:
            final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp']).reset_index(drop=True)
            
        final_df.to_csv(filepath, index=False)
        print(f"Successfully saved {len(final_df)} rows to {filepath}")
        return final_df

    def clean_and_check_gaps(self, df, interval):
        """
        Check for missing timestamps based on interval.
        Adds a 'has_gap' column to indicate if any OHLCV data was missing.
        Returns the processed DataFrame and a dictionary of gap statistics.
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns.tolist() + ['has_gap']), {'gap_count': 0, 'max_gap_length': 0, 'avg_gap_length': 0}

        # Convert interval to ms
        interval_map = {'1h': 3600000, '4h': 14400000, '1d': 86400000, '15m': 900000}
        step = interval_map.get(interval)
        if not step:
            # If interval not mapped, no gap checking is performed, return as is.
            df['has_gap'] = False
            return df, {'gap_count': 0, 'max_gap_length': 0, 'avg_gap_length': 0}
            
        # Ensure 'timestamp' is sorted before creating full_range
        df = df.sort_values('timestamp').reset_index(drop=True)

        full_range = pd.to_datetime(np.arange(df['timestamp'].iloc[0], df['timestamp'].iloc[-1] + step, step), unit='ms')
        # Create a temporary DataFrame with the full range of timestamps for merging
        full_ts_df = pd.DataFrame({'timestamp_ms': full_range.astype(np.int64)})
        full_ts_df.set_index(pd.to_datetime(full_ts_df['timestamp_ms'], unit='ms'), inplace=True)
        
        # Set original df index to datetime for merging
        df_indexed = df.set_index(pd.to_datetime(df['timestamp'], unit='ms'))

        # Merge with original data
        merged_df = pd.merge(full_ts_df, df_indexed, left_index=True, right_index=True, how='left')
        
        # Identify rows where original data columns are NaN (indicating a gap)
        merged_df['has_gap'] = merged_df['open'].isna()
        missing_count = merged_df['has_gap'].sum()
        
        # Calculate gap statistics
        gap_lengths = []
        if missing_count > 0:
            # Find consecutive NaNs
            nan_groups = (merged_df['open'].isna() != merged_df['open'].isna().shift()).cumsum()
            nan_group_sizes = merged_df[merged_df['open'].isna()].groupby(nan_groups).size()
            gap_lengths = nan_group_sizes.tolist()
            
            print(f"Warning: Found {missing_count} missing rows in {interval} data. These are NOT filled and remain as NaN.")
            print(f"Gap details: {gap_lengths} (lengths of consecutive missing bars).")
            
        gap_stats = {
            'gap_count': missing_count,
            'max_gap_length': max(gap_lengths) if gap_lengths else 0,
            'avg_gap_length': np.mean(gap_lengths) if gap_lengths else 0
        }
            
        # The index is already the correct datetime.
        merged_df['timestamp'] = merged_df.index.astype(np.int64) // 10**6 # Convert datetime index back to ms timestamp

        # Drop the redundant timestamp_ms column from full_ts_df if it exists, before returning.
        if 'timestamp_ms' in merged_df.columns:
            merged_df = merged_df.drop(columns=['timestamp_ms'])

        # Reset index to make 'timestamp' a regular column again, and drop original index
        return merged_df.reset_index(drop=True), gap_stats


    def get_batch_data(self, symbols, interval, start_str="2020-01-01"):
        """
        Fetch and align multiple symbols.
        Returns the combined DataFrame and a dictionary of gap statistics per symbol.
        """
        dfs = {}
        all_gap_stats = {}
        for symbol in symbols:
            df = self.get_full_history(symbol, interval, start_str=start_str)
            df, gap_stats = self.clean_and_check_gaps(df, interval)
            all_gap_stats[symbol] = gap_stats
            # After clean_and_check_gaps, 'timestamp' is a regular column, and 'has_gap' is added.
            # We need to set the index to datetime for concat operation.
            df_for_batch = df.set_index(pd.to_datetime(df['timestamp'], unit='ms'))
            # Drop the redundant timestamp column that is now the index
            df_for_batch = df_for_batch.drop(columns=['timestamp'])
            dfs[symbol] = df_for_batch
            
        # Align all dataframes by index (timestamp)
        combined_df = pd.concat(dfs.values(), axis=1, keys=symbols, join='inner')
        return combined_df, all_gap_stats

if __name__ == "__main__":
    loader = BinanceDataLoader()
    # Pre-fetch BTC and ETH for Pair Trade research
    combined_df, gap_stats = loader.get_batch_data(["BTCUSDT", "ETHUSDT"], "1h")
    print("\nCombined DataFrame Head:")
    print(combined_df.head())
    print("\nGap Statistics:")
    for symbol, stats in gap_stats.items():
        print(f"  {symbol}: {stats}")
