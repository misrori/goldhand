from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import plotly.express as px
from scipy.signal import argrelextrema
import numpy as np
import requests
import json
import cloudscraper

class GoldHand:
    def __init__(self, ticker, ad_ticker=True, range='18y', interval='1d'):
        self.scraper = cloudscraper.create_scraper()
        self.ad_ticker = ad_ticker
        self.range = range
        self.interval = interval
        self.ticker = ticker
        self.df = None
        self.download_historical_data()


    def get_olhc(self):
        #scraper = cloudscraper.create_scraper()
        response = self.scraper.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}?interval={self.interval}&range={self.range}")
        t= response.json()
        df = pd.DataFrame(t['chart']['result'][0]['indicators']['quote'][0])
        df['date'] = pd.to_datetime(t['chart']['result'][0]['timestamp'], unit='s').date
        df = df[['date', 'open', 'low', 'high', 'close', 'volume']]
        if self.ad_ticker:
            df['ticker'] = self.ticker
        return(df)



    def download_historical_data(self):
        # Download historical stock data for the last year
        self.df = self.get_olhc()
        self.df.columns = self.df.columns.str.lower()

        # Rsi
        self.df['rsi'] = ta.rsi(self.df['close'], 14)

        # SMAS
        self.df['sma_50']= ta.sma(self.df['close'], 50)
        self.df['diff_sma50'] = (self.df['close']/self.df['sma_50'] -1)*100
        self.df['sma_100']= ta.sma(self.df['close'], 100)
        self.df['diff_sma100'] = (self.df['close']/self.df['sma_100'] -1)*100
        self.df['sma_200']= ta.sma(self.df['close'], 200)
        self.df['diff_sma200'] = (self.df['close']/self.df['sma_200'] -1)*100

        #Bolinger bands
        bb = ta.bbands(self.df['close'])
        bb.columns = ['bb_lower', 'bb_mid', 'bb_upper', 'bandwidth', 'percent']
        self.df['bb_lower'] = bb['bb_lower']
        self.df['bb_upper'] = bb['bb_upper']
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
        problem_list = []
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

        # add last fall if last local is max
        if list(self.df[self.df['local']!='']['local'])[-1]=='maximum':
            last_min_id = self.df.loc[self.df['low']==min(self.df['low'][-3:] )].index.to_list()[0]
            self.df.loc[last_min_id , 'local'] = 'minimum'

        states = self.df[self.df['local']!='']['local'].index.to_list()
        
        
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


    def plotly_last_year(self, plot_title, plot_height=900):
        tdf = self.df.tail(500)

        fig = go.Figure(data=go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'],close=tdf['close']))

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


# https://stackoverflow.com/questions/71411995/pandas-plotly-secondary-graph-needs-to-be-to-rsi

#https://wire.insiderfinance.io/plot-candlestick-rsi-bollinger-bands-and-macd-charts-using-yfinance-python-api-1c2cb182d147

