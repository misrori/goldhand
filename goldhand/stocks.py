from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.signal import argrelextrema
import numpy as np
import yfinance as yf
import requests
import json

class GoldHand:
    def __init__(self, ticker, ad_ticker=True, range='18y', interval='1d'):
        """
        GoldHand class to download and analyze stock data

        Paramseters:
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


    
    def smma(self, data, window, colname):
        """
        Calculate Smoothed Simple Moving Average (SMMA)
        Parameters:
        - data: Pandas DataFrame
        - window: int, window size
        - colname: str, name of the column to add to the DataFrame
        
        Return: DataFrame with added column
        """
        hl2 = data['hl2'].values
        smma_values = [hl2[0]]

        for i in range(1, len(hl2)):
            smma_val = (smma_values[-1] * (window - 1) + hl2[i]) / window
            smma_values.append(smma_val)

        data[colname] = smma_values
        return data



    def download_historical_data(self):
        """
        Download historical stock, crypto or ETF data 
        """
        # Download historical stock data for the last year
        self.df = self.download(self.ticker, period=self.range, interval=self.interval)
        self.df.columns = self.df.columns.str.lower()
        self.df['hl2'] = (self.df['high'] + self.df['low'])/2
        
        try:
            # Rsi
            window = 14
            delta = self.df['close'].diff()

            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(window).mean()
            avg_loss = loss.rolling(window).mean()

            rs = avg_gain / avg_loss
            self.df['rsi'] = 100 - (100 / (1 + rs))
        

            # SMAS
            self.df['sma_50']  = self.df['close'].rolling(50).mean()
            self.df['sma_100'] = self.df['close'].rolling(100).mean()
            self.df['sma_200'] = self.df['close'].rolling(200).mean()

            self.df['diff_sma50'] = (self.df['close']/self.df['sma_50'] -1)*100
            self.df['diff_sma100'] = (self.df['close']/self.df['sma_100'] -1)*100
            self.df['diff_sma200'] = (self.df['close']/self.df['sma_200'] -1)*100

            #Bolinger bands
            bb_window = 20

            mid = self.df['close'].rolling(bb_window).mean()
            std = self.df['close'].rolling(bb_window).std()

            self.df['bb_mid']   = mid
            self.df['bb_upper'] = mid + 2*std
            self.df['bb_lower'] = mid - 2*std

            self.df['diff_upper_bb'] = (self.df['bb_upper']/self.df['close'] -1)*100
            self.df['diff_lower_bb'] = (self.df['bb_lower']/self.df['close'] -1)*100


            #local min maxs
            self.df['local'] = ''
            self.df['local_text'] = ''
            max_ids = list(argrelextrema(self.df['high'].values, np.greater, order=30)[0])
            min_ids = list(argrelextrema(self.df['low'].values, np.less, order=30)[0])
            self.df.loc[min_ids, 'local'] = 'minimum'
            self.df.loc[max_ids, 'local'] = 'maximum'


            states = self.df[self.df['local']!='']['local'].index.to_list()
            problem = []
            for i in range(0, (len(states)-1) ):

                if (self.df.loc[states[i], 'local'] != self.df.loc[states[i+1], 'local']):
                    if (len(problem)==0):
                        continue
                    else:
                        problem.append(states[i])
                        text = self.df.loc[states[i], 'local']
                        if(text=='minimum'):
                            real_min = self.df.loc[problem, 'low'].idxmin()
                            problem.remove(real_min)
                            self.df.loc[problem, 'local']=''
                        else:
                            real_max = self.df.loc[problem, 'high'].idxmax()
                            problem.remove(real_max)
                            self.df.loc[problem, 'local']=''

                        problem = []
                else:
                    problem.append(states[i])

            states = self.df[self.df['local']!='']['local'].index.to_list()

            # if first is min ad the price
            if self.df.loc[states[0], 'local']== 'minimum':
                self.df.loc[states[0],'local_text'] = f"${round(self.df.loc[states[0], 'low'], 2)}"
            else:
                self.df.loc[states[0],'local_text'] = f"${round(self.df.loc[states[0], 'high'], 2)}"

            
            # add one local min max after the last one
            if self.df.loc[states[-1], 'local']== 'maximum':
                lowest_index_after_last_max = self.df['low'][states[-1]+1:].idxmin()
                self.df.loc[lowest_index_after_last_max, 'local'] = 'minimum'
            else:
                high_index_after_last_min = self.df['high'][states[-1]+1:].idxmax()
                self.df.loc[high_index_after_last_min, 'local'] = 'maximum'

            states = self.df[self.df['local']!='']['local'].index.to_list()

        except:
            pass
        
        try:
                
            for i in range(1,len(states)):
                prev = self.df.loc[states[i-1], 'local']
                current= self.df.loc[states[i], 'local']
                prev_high = self.df.loc[states[i-1], 'high']
                prev_low = self.df.loc[states[i-1], 'low']
                current_high = self.df.loc[states[i], 'high']
                current_low = self.df.loc[states[i], 'low']
                if current == 'maximum':
                    # rise
                    rise = (current_high/ prev_low -1)*100
                    if rise>100:
                        self.df.loc[states[i], 'local_text'] = f'🚀🌌{round(((rise+100)/100), 2)}x<br>${round(current_high, 2)}'
                    else:
                        self.df.loc[states[i], 'local_text'] = f'🚀{round(rise, 2)}%<br>${round(current_high, 2)}'
                else:
                    fall = round((1-(current_low / prev_high))*100, 2)
                    if fall < 30:
                        temj = '💸'
                    elif fall < 50:
                        temj = '💸'
                    else:
                        temj = '😭💔' 
                    self.df.loc[states[i], 'local_text'] = f'{temj}{fall}%<br>${round(current_low, 2)}'
            self.df.reset_index(inplace=True, drop=True)
        except:
            pass

    def plotly_last_year(self, plot_title, plot_height=900, ndays=500, ad_local_min_max=True):
        """
        Plot last year interactive plot of a stock analyzing the local minimums and maximums
        Parameters:
        - plot_title: str, title of the plot
        - plot_height: int, height of the plot
        - ndays: int, number of days to plot
        - ad_local_min_max: bool, add local min max to the plot
        Return: plotly figure
        """
        tdf = self.df.tail(ndays)

        fig = go.Figure(data=go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'],close=tdf['close']))
        if ad_local_min_max:
            for index, row in tdf[tdf['local']!=''].iterrows():
                direction = row['local']
                tdate = row['date']
                local_text = row['local_text']
                min_price = row['low']
                max_price = row['high']
                if direction == 'maximum':
                    fig.add_annotation( x=tdate, y=max_price, text=local_text, showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=-45,ay=-45)

                if direction == 'minimum':
                    fig.add_annotation( x=tdate, y=min_price, text=local_text, showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="red" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=45,ay=45)

        fig.update_layout(showlegend=False, plot_bgcolor='white', height=plot_height, title= plot_title)

        fig.update_xaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey' )
        fig.update_yaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.add_trace( go.Scatter(x=tdf['date'], y=tdf['sma_50'], opacity =0.5, line=dict(color='lightblue', width = 2) , name = 'SMA 50') )
        fig.add_trace( go.Scatter(x=tdf['date'], y=tdf['sma_200'], opacity =0.7, line=dict(color='red', width = 2.5) ,  name = 'SMA 200') )
        return(fig)

    def plot_goldhand_line(self, plot_title, plot_height=900, ndays=800,  ad_local_min_max=True):
        """
        Plot last year interactive plot of a stock analyzing the local minimums and maximums using the GoldHandLine indicator
        Parameters:
        - plot_title: str, title of the plot
        - plot_height: int, height of the plot
        - ndays: int, number of days to plot
        - ad_local_min_max: bool, add local min max to the plot
        Return: plotly figure
        """
        
        data = self.df.copy()
        # Apply SMMA to the dataframe
        data = self.smma(data, 15, 'v1')
        data = self.smma(data, 19, 'v2')
        data = self.smma(data, 25, 'v3')
        data = self.smma(data, 29, 'v4')

        data['color'] = 'grey'  # Set default color to grey

        # Update color based on conditions
        data.loc[(data['v4'] < data['v3']) & (data['v3'] < data['v2']) & (data['v2'] < data['v1']), 'color'] = 'gold'
        data.loc[(data['v1'] < data['v2']) & (data['v2'] < data['v3']) & (data['v3'] < data['v4']), 'color'] = 'blue'

        # Identify rows where color changes compared to the previous row
        data['color_change'] = data['color'] != data['color'].shift(1)

        # Create a 'group' column and increase the value only when there's a color change
        data['group'] = (data['color_change']).cumsum()

        tdf = data.tail(ndays)

        fig = go.Figure(data=go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'],close=tdf['close']))
        if ad_local_min_max:
            for index, row in tdf[tdf['local']!=''].iterrows():
                direction = row['local']
                tdate = row['date']
                local_text = row['local_text']
                min_price = row['low']
                max_price = row['high']
                if direction == 'maximum':
                    fig.add_annotation( x=tdate, y=max_price, text=local_text, showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=-45,ay=-45)

                if direction == 'minimum':
                    fig.add_annotation( x=tdate, y=min_price, text=local_text, showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="red" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=45,ay=45)


        fig.update_xaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey' )
        fig.update_yaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update(layout_xaxis_rangeslider_visible=False)

        for group_id in tdf['group'].unique():
            if group_id ==tdf['group'].unique().max():
                indices = tdf[tdf['group'] == group_id].index.to_list()
            else:
                indices = tdf[tdf['group'] == group_id].index.to_list()
                indices.append(indices[-1]+1)


            group_df = tdf.loc[indices]

            group_color = group_df['color'].iloc[0]
            color_dict = {'gold' : 'rgba(255, 215, 0, 0.4)' , 'grey' : 'rgba(128, 128 ,128, 0.4)' , 'blue' : 'rgba(0, 0, 255, 0.4)' }

            # Create v1 and v4 traces
            trace_v1 = go.Scatter(x=group_df['date'], y=group_df['v1'], mode='lines', name='v1', line=dict(color=color_dict[group_color]) )
            trace_v4 = go.Scatter(x=group_df['date'], y=group_df['v4'], mode='lines', name='v4', line=dict(color=color_dict[group_color]), fill='tonexty', fillcolor =color_dict[group_color])

            # Add candlestick trace and additional lines to the figure
            fig.add_trace(trace_v1)
            fig.add_trace(trace_v4)

        fig.update_layout(showlegend=False, plot_bgcolor='white', height=plot_height, title= plot_title)
        return(fig)

        
        
        
# https://stackoverflow.com/questions/71411995/pandas-plotly-secondary-graph-needs-to-be-to-rsi

#https://wire.insiderfinance.io/plot-candlestick-rsi-bollinger-bands-and-macd-charts-using-yfinance-python-api-1c2cb182d147

