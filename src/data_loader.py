import pandas as pd
import requests
import os
from datetime import datetime
import time

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
        
        # Determine start time
        if os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            last_ts = existing_df['timestamp'].iloc[-1]
            start_ts = int(last_ts) + 1
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
        
        if not all_data:
            print("No new data found.")
            return pd.read_csv(filepath) if os.path.exists(filepath) else None

        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Basic cleaning
        df['timestamp'] = df['timestamp'].astype(int)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        if os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['timestamp']).reset_index(drop=True)
            
        df.to_csv(filepath, index=False)
        print(f"Successfully saved {len(df)} rows to {filepath}")
        return df

    def clean_and_check_gaps(self, df, interval):
        """
        Check for missing timestamps based on interval.
        """
        # Convert interval to ms
        interval_map = {'1h': 3600000, '4h': 14400000, '1d': 86400000, '15m': 900000}
        step = interval_map.get(interval)
        if not step:
            return df
            
        full_range = range(df['timestamp'].iloc[0], df['timestamp'].iloc[-1] + step, step)
        full_df = pd.DataFrame({'timestamp': list(full_range)})
        
        merged_df = pd.merge(full_df, df, on='timestamp', how='left')
        missing_count = merged_df['close'].isna().sum()
        
        if missing_count > 0:
            print(f"Warning: Found {missing_count} missing rows. Filling with ffill.")
            merged_df = merged_df.ffill()
            
        return merged_df

    def get_batch_data(self, symbols, interval, start_str="2020-01-01"):
        """
        Fetch and align multiple symbols.
        """
        dfs = {}
        for symbol in symbols:
            df = self.get_full_history(symbol, interval, start_str=start_str)
            df = self.clean_and_check_gaps(df, interval)
            df = df.set_index('timestamp')
            dfs[symbol] = df
            
        # Align all dataframes by index (timestamp)
        combined_df = pd.concat(dfs.values(), axis=1, keys=symbols, join='inner')
        return combined_df

if __name__ == "__main__":
    loader = BinanceDataLoader()
    # Pre-fetch BTC and ETH for Pair Trade research
    loader.get_batch_data(["BTCUSDT", "ETHUSDT"], "1h")
