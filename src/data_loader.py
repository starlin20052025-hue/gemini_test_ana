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
        Fetch all available history for a symbol and interval, saving with string timestamps.
        """
        filename = f"{symbol}_{interval}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        existing_df = None
        if os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            # Convert string timestamp to datetime to find the last timestamp
            last_ts_str = existing_df['timestamp'].iloc[-1]
            start_ts = int(pd.to_datetime(last_ts_str).timestamp() * 1000) + 1
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
            current_ts = klines[-1][6] + 1
            time.sleep(0.1)
            if len(klines) < 500:
                break
        
        if not all_data:
            print("No new data found.")
            return existing_df if existing_df is not None else pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        new_df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert timestamp to string format
        new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            new_df[col] = new_df[col].astype(float)
        new_df = new_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['timestamp']).reset_index(drop=True) if existing_df is not None else new_df
            
        final_df.to_csv(filepath, index=False)
        print(f"Successfully saved {len(final_df)} rows to {filepath}")
        return final_df

    def clean_and_check_gaps(self, df, interval):
        """
        Check for missing timestamps based on interval, assuming 'timestamp' is a string column.
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns.tolist() + ['has_gap']), {'gap_count': 0, 'max_gap_length': 0, 'avg_gap_length': 0}

        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp_dt').reset_index(drop=True)
        
        interval_map = {'1h': 'h', '4h': '4h', '1d': 'D', '15m': '15T'}
        freq = interval_map.get(interval)
        if not freq:
            df['has_gap'] = False
            return df.drop(columns=['timestamp_dt']), {'gap_count': 0, 'max_gap_length': 0, 'avg_gap_length': 0}

        full_range = pd.date_range(start=df['timestamp_dt'].iloc[0], end=df['timestamp_dt'].iloc[-1], freq=freq)
        full_df = pd.DataFrame({'timestamp_dt': full_range})
        
        merged_df = pd.merge(full_df, df, on='timestamp_dt', how='left')
        
        merged_df['has_gap'] = merged_df['open'].isna()
        missing_count = merged_df['has_gap'].sum()
        
        gap_lengths = []
        if missing_count > 0:
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
        
        # Restore the original string timestamp format for the final DataFrame
        merged_df['timestamp'] = merged_df['timestamp_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return merged_df.drop(columns=['timestamp_dt']), gap_stats

    def get_batch_data(self, symbols, interval, start_str="2020-01-01"):
        """
        Fetch and align multiple symbols.
        """
        dfs = {}
        all_gap_stats = {}
        for symbol in symbols:
            df = self.get_full_history(symbol, interval, start_str=start_str)
            df, gap_stats = self.clean_and_check_gaps(df, interval)
            all_gap_stats[symbol] = gap_stats
            
            df_for_batch = df.set_index(pd.to_datetime(df['timestamp']))
            df_for_batch = df_for_batch.drop(columns=['timestamp'])
            dfs[symbol] = df_for_batch
            
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
