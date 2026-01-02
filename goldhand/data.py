import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class Data:
    """
    Class to handle data downloading from Yahoo Finance.
    """
    
    @staticmethod
    def download(ticker: str, period: str = 'max', interval: str = '1d', auto_adjust: bool = True) -> pd.DataFrame:
        """
        Download historical data for a single ticker.
        
        Parameters:
        - ticker: str, symbol (e.g., 'AAPL', 'BTC-USD')
        - period: str, data period to download (e.g. '1y', '2y', 'max')
        - interval: str, data interval (e.g. '1d', '1h')
        
        Returns:
        - pd.DataFrame with lowercase columns ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
        """
        try:
            # Using yfinance to download data
            # auto_adjust=True fixes the Close price for splits and dividends
            df = yf.download(ticker, period=period, interval=interval, auto_adjust=auto_adjust, progress=False, multi_level_index=False)
            
            if df.empty:
                print(f"Warning: No data found for ticker {ticker}")
                return pd.DataFrame()

            # Clean up DataFrame
            df.reset_index(inplace=True)
            df.columns = df.columns.str.lower()
            
            # Rename 'Date'/'Datetime' to 'date' consistently
            if 'date' not in df.columns:
                if 'datetime' in df.columns:
                    df.rename(columns={'datetime': 'date'}, inplace=True)
            
            # Ensure 'date' column is datetime.date objects for compatibility with existing logic
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date

            # Add ticker column
            df['ticker'] = ticker
            
            # Select relevant columns
            cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
            df = df[[c for c in cols if c in df.columns]]
            
            return df
            
        except Exception as e:
            print(f"Error downloading data for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_ticker_info(ticker: str) -> dict:
        """
        Get fundamental info about the ticker.
        """
        try:
            t = yf.Ticker(ticker)
            return t.info
        except Exception as e:
            print(f"Error getting info for {ticker}: {e}")
            return {}
