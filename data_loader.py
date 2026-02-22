import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

class DataLoader:
    def __init__(self, symbols=['AAPL', 'MSFT', 'NVDA', 'SPY'], cache_dir='market_data'):
        self.symbols = symbols
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_data(self, period='60d', interval='5m'):
        """
        Retrieves intraday data if possible, otherwise falls back to daily.
        5-minute intervals provide enough granularity for TWAP/VWAP simulation.
        """
        data_map = {}
        
        for symbol in self.symbols:
            file_path = os.path.join(self.cache_dir, f"{symbol}_{interval}.csv")
            
            try:
                # Try loading from local cache first to save API hits
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                    if not df.empty:
                        data_map[symbol] = df
                        continue

                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if df.empty:
                    # Fallback for symbols that might not support 5m for 60d
                    df = ticker.history(period='1mo', interval='2m')
                
                if not df.empty:
                    # Standardizing column names for the rest of the system
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                    df.to_csv(file_path)
                    data_map[symbol] = df
                else:
                    print(f"Warning: No data found for {symbol}")
            
            except Exception as e:
                print(f"Failed to fetch {symbol}: {e}")
        
        return data_map

    def get_combined_market_stats(self, data_map):
        """Calculates baseline volatility and avg volume for impact models."""
        stats = {}
        for symbol, df in data_map.items():
            returns = df['Close'].pct_change().dropna()
            stats[symbol] = {
                'avg_volume': df['Volume'].mean(),
                'volatility': returns.std(),
                'avg_price': df['Close'].mean()
            }
        return stats

if __name__ == "__main__":
    # Self-test block
    loader = DataLoader(symbols=['AAPL', 'MSFT'])
    market_data = loader.fetch_data(period='5d', interval='1h')
    
    for sym, data in market_data.items():
        print(f"Symbol: {sym} | Rows: {len(data)}")
        print(data.head(3))
        
    stats = loader.get_combined_market_stats(market_data)
    print("\nMarket Stats:", stats)