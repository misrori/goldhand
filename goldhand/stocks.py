from datetime import datetime
import pandas as pd
from goldhand.data import Data
from goldhand.indicators import Indicators
from goldhand.plotting import Plotting
import plotly.graph_objects as go

class GoldHand:
    def __init__(self, ticker, ad_ticker=True, range='max', interval='1d'):
        """
        GoldHand class to download and analyze stock data
        
        Parameters:
        - ticker: str, ticker symbol of the stocks or crypto or ETF
        - ad_ticker: bool, add ticker column to the DataFrame
        - range: str, time range to download data for example 5y,1y, 1mo, 1d, 1h
        - interval: str, interval to download data for example 1d, 1h, 5m
        """
        self.ad_ticker = ad_ticker
        self.range = range
        self.interval = interval
        self.ticker = ticker
        self.df = None
        self.download_historical_data()

    def download_historical_data(self):
        """
        Download historical stock, crypto or ETF data and calculate indicators.
        """
        # Download data
        self.df = Data.download(self.ticker, period=self.range, interval=self.interval)
        
        if self.df.empty:
            return

        # HL2
        self.df['hl2'] = (self.df['high'] + self.df['low']) / 2
        
        try:
            # RSI
            self.df['rsi'] = Indicators.rsi(self.df['close'], window=14)
        
            # SMAS
            self.df['sma_50'] = self.df['close'].rolling(50).mean()
            self.df['sma_100'] = self.df['close'].rolling(100).mean()
            self.df['sma_200'] = self.df['close'].rolling(200).mean()

            self.df['diff_sma50'] = (self.df['close'] / self.df['sma_50'] - 1) * 100
            self.df['diff_sma100'] = (self.df['close'] / self.df['sma_100'] - 1) * 100
            self.df['diff_sma200'] = (self.df['close'] / self.df['sma_200'] - 1) * 100

            # Bollinger Bands
            mid, upper, lower = Indicators.bollinger_bands(self.df['close'], window=20)
            self.df['bb_mid'] = mid
            self.df['bb_upper'] = upper
            self.df['bb_lower'] = lower

            self.df['diff_upper_bb'] = (self.df['bb_upper'] / self.df['close'] - 1) * 100
            self.df['diff_lower_bb'] = (self.df['bb_lower'] / self.df['close'] - 1) * 100

            # Local Min/Max
            self.df = Indicators.get_local_min_max(self.df)
            self.df = Indicators.add_local_text(self.df)

        except Exception as e:
            print(f"Error calculating indicators: {e}")

    def plotly_last_year(self, plot_title, plot_height=900, ndays=500, ad_local_min_max=True):
        """
        Plot last year interactive plot of a stock analyzing the local minimums and maximums
        """
        if self.df is None or self.df.empty:
            print("No data to plot")
            return None
            
        tdf = self.df.tail(ndays).copy()
        
        return Plotting.plot_candle_with_locals(
            tdf, 
            title=plot_title, 
            height=plot_height, 
            show_locals=ad_local_min_max
        )

    def plot_goldhand_line(self, plot_title, plot_height=900, ndays=800, ad_local_min_max=True):
        """
        Plot interactive plot using the GoldHandLine indicator
        """
        if self.df is None or self.df.empty:
             print("No data to plot")
             return None

        data = self.df.copy()
        
        # Calculate SMMA using new Indicators module
        data['v1'] = Indicators.smma(data['hl2'], 15)
        data['v2'] = Indicators.smma(data['hl2'], 19)
        data['v3'] = Indicators.smma(data['hl2'], 25)
        data['v4'] = Indicators.smma(data['hl2'], 29)

        data['color'] = 'grey'
        data.loc[(data['v4'] < data['v3']) & (data['v3'] < data['v2']) & (data['v2'] < data['v1']), 'color'] = 'gold'
        data.loc[(data['v1'] < data['v2']) & (data['v2'] < data['v3']) & (data['v3'] < data['v4']), 'color'] = 'blue'

        data['color_change'] = data['color'] != data['color'].shift(1)
        data['group'] = (data['color_change']).cumsum()

        tdf = data.tail(ndays)
        
        # Create base chart
        fig = Plotting.plot_candle_with_locals(
            tdf, 
            title=plot_title, 
            height=plot_height, 
            show_locals=ad_local_min_max,
            show_ma=False 
        )
        
        # Draw GoldHand Ribbons
        color_dict = {'gold': 'rgba(255, 215, 0, 0.4)', 'grey': 'rgba(128, 128 ,128, 0.4)', 'blue': 'rgba(0, 0, 255, 0.4)'}
        
        for group_id in tdf['group'].unique():
             mask = tdf['group'] == group_id
             group_df = tdf.loc[mask]
             
             # Extend with next row if available to connect lines
             if group_df.index[-1] != tdf.index[-1]:
                  next_loc = tdf.index.get_loc(group_df.index[-1]) + 1
                  if next_loc < len(tdf):
                      next_idx = tdf.index[next_loc]
                      # Use .concat instead of append
                      group_df = pd.concat([group_df, tdf.loc[[next_idx]]])

             if group_df.empty:
                 continue

             group_color = group_df['color'].iloc[0]
             c = color_dict.get(group_color, 'grey')
             
             fig.add_trace(go.Scatter(
                 x=group_df['date'], y=group_df['v1'], 
                 mode='lines', line=dict(color=c), showlegend=False
             ))
             fig.add_trace(go.Scatter(
                 x=group_df['date'], y=group_df['v4'], 
                 mode='lines', line=dict(color=c), 
                 fill='tonexty', fillcolor=c, showlegend=False
             ))

        return fig 
