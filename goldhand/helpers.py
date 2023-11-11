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

def get_olhc( ticker, scraper = cloudscraper.create_scraper(),  ad_ticker=False, range='18y', interval='1d'):
    response = scraper.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={range}")
    t= response.json()
    df = pd.DataFrame(t['chart']['result'][0]['indicators']['quote'][0])
    df['date'] = pd.to_datetime(t['chart']['result'][0]['timestamp'], unit='s').date
    df = df[['date', 'open', 'low', 'high', 'close', 'volume']]
    if ad_ticker:
        df['ticker'] = ticker
    return(df)


def get_olhc_data(ticker):
    # Download historical stock data for the last year
    df = get_olhc(ticker)
    df.columns = df.columns.str.lower()
    df['date']= [x.date() for x in df['date']]

    # Rsi
    df['rsi'] = ta.rsi(df['close'], 14)

    # SMAS
    df['sma_50']= ta.sma(df['close'], 50)
    df['diff_sma50'] = (df['close']/df['sma_50'] -1)*100
    df['sma_100']= ta.sma(df['close'], 100)
    df['diff_sma100'] = (df['close']/df['sma_100'] -1)*100
    df['sma_200']= ta.sma(df['close'], 200)
    df['diff_sma200'] = (df['close']/df['sma_200'] -1)*100

    #Bolinger bands
    bb = ta.bbands(df['close'])
    bb.columns = ['bb_lower', 'bb_mid', 'bb_upper', 'bandwidth', 'percent']
    df['bb_lower'] = bb['bb_lower']
    df['bb_upper'] = bb['bb_upper']
    df['diff_upper_bb'] = (df['bb_upper']/df['close'] -1)*100
    df['diff_lower_bb'] = (df['bb_lower']/df['close'] -1)*100
    return(df)

def add_locals_to_olhc(df):
    #local min maxs
    df['local'] = ''
    df['local_text'] = ''
    max_ids = list(argrelextrema(df['high'].values, np.greater, order=30)[0])
    min_ids = list(argrelextrema(df['low'].values, np.less, order=30)[0])
    df.loc[min_ids, 'local'] = 'minimum'
    df.loc[max_ids, 'local'] = 'maximum'


    states = df[df['local']!='']['local'].index.to_list()
    problem = []
    problem_list = []
    for i in range(0, (len(states)-1) ):

        if (df.loc[states[i], 'local'] != df.loc[states[i+1], 'local']):
            if (len(problem)==0):
                continue
            else:
                problem.append(states[i])
                text = df.loc[states[i], 'local']
                if(text=='minimum'):
                    real_min = df.loc[problem, 'low'].idxmin()
                    problem.remove(real_min)
                    df.loc[problem, 'local']=''
                else:
                    real_max = df.loc[problem, 'high'].idxmax()
                    problem.remove(real_max)
                    df.loc[problem, 'local']=''

                problem = []
        else:
            problem.append(states[i])

    states = df[df['local']!='']['local'].index.to_list()

    # if first is min ad the price
    if df.loc[states[0], 'local']== 'minimum':
        df.loc[states[0],'local_text'] = f"${round(df.loc[states[0], 'low'], 2)}"
    else:
        df.loc[states[0],'local_text'] = f"${round(df.loc[states[0], 'high'], 2)}"

    # add last fall if last local is max
    if list(df[df['local']!='']['local'])[-1]=='maximum':
        last_min_id = df.loc[df['low']==min(df['low'][-3:] )].index.to_list()[0]
        df.loc[last_min_id , 'local'] = 'minimum'

    states = df[df['local']!='']['local'].index.to_list()


    for i in range(1,len(states)):
        prev = df.loc[states[i-1], 'local']
        current= df.loc[states[i], 'local']
        prev_high = df.loc[states[i-1], 'high']
        prev_low = df.loc[states[i-1], 'low']
        current_high = df.loc[states[i], 'high']
        current_low = df.loc[states[i], 'low']
        if current == 'maximum':
            # rise
            rise = (current_high/ prev_low -1)*100
            if rise>100:
                df.loc[states[i], 'local_text'] = f'🚀🌌{round(((rise+100)/100), 2)}x<br>${round(current_high, 2)}'
            else:
                df.loc[states[i], 'local_text'] = f'🚀{round(rise, 2)}%<br>${round(current_high, 2)}'
        else:
            fall = round((1-(current_low / prev_high))*100, 2)
            df.loc[states[i], 'local_text'] = f'🔻{fall}%<br>${round(current_low, 2)}'
    return(df)

def plotly_with_locals(tdf,plot_title, plot_height=900):
    fig = go.Figure(data=go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'],close=tdf['close']))

    for index, row in tdf[tdf['local']!=''].iterrows():
        direction = row['local']
        tdate = row['date']
        local_text = row['local_text']
        min_price = row['low']
        max_price = row['high']
        if direction == 'maximum':
            fig.add_annotation( x=tdate, y=max_price, text=local_text, showarrow=True,
            align="center", bordercolor="#c7c7c7",
            font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2,
            borderpad=4,
            bgcolor="#f4fdff",
            opacity=0.8,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            ax=-45,ay=-45)

        if direction == 'minimum':
            fig.add_annotation( x=tdate, y=min_price, text=local_text, showarrow=True,
            align="center", bordercolor="#c7c7c7",
            font=dict(family="Courier New, monospace", size=16, color="red" ), borderwidth=2,
            borderpad=4,
            bgcolor="#f4fdff",
            opacity=0.8,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            ax=45,ay=45)

        fig.update_layout(showlegend=False, plot_bgcolor='white', height=plot_height, title= plot_title)

    fig.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig.update(layout_xaxis_rangeslider_visible=False)
    return(fig)

