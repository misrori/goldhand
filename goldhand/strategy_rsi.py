from IPython.display import display
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from goldhand import *



def rsi_strategy(data, buy_threshold = 30, sell_threshold = 70):
    """
    RSI strategy for backtesting with Backtest class
    
    Parameters:
    - data: pandas DataFrame with columns: date, open, high, low, close, volume and rsi
    - buy_threshold: int, default 30,  buy when RSI is below this value
    - sell_threshold: int, default 70, sell when RSI is above this value
    """

    in_trade = False  # Flag to track if already in a trade
    trade_id = 1
    all_trades = []

    temp_trade = {}

    for i in range(1, len(data)):
        # Check if not already in a trade
        if not in_trade:
            # Generate buy signal
            #You have to change olne the buy and sell signal
            if data['rsi'][i] < buy_threshold:

                if i == (len(data) -1): 
                    temp_trade['buy_price'] = data['close'][i]
                    temp_trade.update(dict(data.iloc[i].add_prefix('buy_')))
                else:
                    temp_trade['buy_price'] = data['open'][i+1]
                    temp_trade.update(dict(data.iloc[i+1].add_prefix('buy_')))

                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'open'
                in_trade = True  # Set flag to indicate in a trade
        else:
            # Generate sell signal
            #You have to change olne the buy and sell signal
            if data['rsi'][i] > sell_threshold:
                if i == (len(data) -1): 
                    temp_trade['sell_price'] = data['close'][i]
                    temp_trade.update(dict(data.iloc[i].add_prefix('sell_')))
                else:
                    temp_trade['sell_price'] = data['open'][i+1]
                    temp_trade.update(dict(data.iloc[i+1].add_prefix('sell_')))
                                       
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'closed'

                
                # calculate results
                temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
                temp_trade['days_in_trade'] = (temp_trade['sell_date'] - temp_trade['buy_date']).days

                in_trade = False  # Reset flag to indicate not in a trade
                trade_id +=1
                all_trades.append(temp_trade)
                temp_trade = {}
                
    if temp_trade:
        temp_trade['sell_price'] = data['close'][i]
        temp_trade['trade_id'] = trade_id
        temp_trade['sell_date'] = data['date'][i]

        temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
        temp_trade['days_in_trade'] = (temp_trade['sell_date'] - temp_trade['buy_date']).days
        all_trades.append(temp_trade)

    res_df = pd.DataFrame(all_trades)
    
    # change orders
    all_col = res_df.columns.tolist()
    first = ['result', 'buy_price', 'sell_price', 'buy_date', 'sell_date', 'days_in_trade']
    first.extend([x for x in all_col if x not in first])
    res_df = res_df[first]
    return(res_df)



def show_indicator_rsi_strategy(ticker, buy_threshold = 30, sell_threshold = 70, plot_title = '', ndays=0, plot_height=1000, add_strategy_summary = True):
    """
    Show RSI strategy result in one plot: candlestick chart, SMA lines, trades, RSI indicator, summary of the strategy on the left side of the plot
    Parameters:
    - ticker: str, ticker symbol
    - buy_threshold: int, default 30,  buy when RSI is below this value
    - sell_threshold: int, default 70, sell when RSI is above this value
    - plot_title: str, default '', title of the plot
    - ndays: int, default 0, number of days to show, if 0, show all data
    - plot_height: int, default 1000, height of the plot
    - add_strategy_summary: bool, default True, add strategy summary to the plot
    """

    tdf = GoldHand(ticker).df
    backtest = Backtest( tdf, rsi_strategy, buy_threshold=buy_threshold, sell_threshold=sell_threshold)
    trades =backtest.trades
    
    if ndays > 0:
        tdf = tdf.tail(ndays)
        trades = trades.loc[trades['buy_date']>tdf.date.min()]
        
    if tdf['high'].max() == max(tdf['high'][0:50]):
        tex_loc = [0.1, 0.2]
    else:
        tex_loc = [0.1, 0.85]

    

    # Create subplots with shared x-axis and custom heights
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=['', "RSI"], row_heights=[0.7, 0.3])

    # Add OHLC candlestick chart
    fig.add_trace(go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'], close=tdf['close']), row=1, col=1)

    # Add SMA lines
    fig.add_trace(go.Scatter(x=tdf['date'], y=tdf['sma_50'], opacity=0.5, line=dict(color='lightblue', width=2), name='SMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=tdf['date'], y=tdf['sma_200'], opacity=0.7, line=dict(color='red', width=2.5), name='SMA 200'), row=1, col=1)

    # Add trade points and annotations
    for index, row in trades.iterrows():
        buy_date = row['buy_date']
        sell_date = row['sell_date']
        buy_price = row['buy_price']
        sell_price = row['sell_price']
        trade_id = row['trade_id']
        status = row['status']
        triangle_color = 'green' if row['result'] > 1 else 'red'

        rise = (row['result'] - 1) * 100

        if rise > 100:
            if status == 'closed':
                result = f'Up:{round(((rise + 100) / 100), 2)}x'
            else:
                result = f'Up:{round(((rise + 100) / 100), 2)}x <br> Still open'
        else:
            if status == 'closed':
                result = f"{round(((row['result'] - 1) * 100), 2)}%"
            else:
                result = f"{round(((row['result'] - 1) * 100), 2)}% <br> Still open"

        # add buy
        buy_point = (buy_date, buy_price)
        triangle_trace = go.Scatter(x=[buy_point[0]], y=[buy_point[1]], mode='markers',
                                  marker=dict(symbol='triangle-up', size=16, color=triangle_color))
        fig.add_trace(triangle_trace)
        fig.add_annotation(x=buy_date, y=buy_price, text=f"Buy: ${round(buy_price, 2)}<br>#{trade_id}",
                          showarrow=True, align="center", bordercolor="#c7c7c7",
                          font=dict(family="Courier New, monospace", size=12, color=triangle_color),
                          borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8,
                          arrowhead=2, arrowsize=1, arrowwidth=1, ax=30, ay=30,
                          hovertext= f"Buy: ${round(buy_price, 2)}")

        # add sell
        sell_point = (sell_date, sell_price)
        triangle_trace = go.Scatter(x=[sell_point[0]], y=[sell_point[1]], mode='markers',
                                  marker=dict(symbol='triangle-down', size=16, color=triangle_color))
        fig.add_trace(triangle_trace)
        fig.add_annotation(x=sell_date, y=sell_price,
                          text=f"Sell: ${round(sell_price, 2)}<br>#{trade_id}, {result}",
                          showarrow=True, align="center", bordercolor="#c7c7c7",
                          font=dict(family="Courier New, monospace", size=12, color=triangle_color),
                          borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8,
                          arrowhead=2, arrowsize=1, arrowwidth=1, ax=-30, ay=-30,
                          hovertext = f"Sell: ${round(sell_price, 2)}<br>#{trade_id}, {result}")

        # add rectangle
        fig.add_shape(type="rect", x0=buy_point[0], y0=buy_point[1], x1=sell_point[0], y1=sell_point[1],
                      line=dict(color=triangle_color, width=2,), fillcolor="LightSkyBlue", opacity=0.3,
                      label=dict(text=f"{result}<br>{row['days_in_trade']} days",
                                textposition="bottom center",
                                font=dict(size=13, color=triangle_color, family="Times New Roman")))

    # Update layout
    fig.update_layout(showlegend=False, plot_bgcolor='white', height=plot_height, title=plot_title)
    fig.update(layout_xaxis_rangeslider_visible=False)

    # Update x-axes and y-axes for the main chart
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey', row=1, col=1)
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey', row=1, col=1)

    # Update x-axes and y-axes for the RSI subplot
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey', row=2, col=1)
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey', row=2, col=1)

    if add_strategy_summary:
        t= backtest.trades_summary
        trade_text = f"Trades: {t['number_of_trades']}<br>"\
        f"Win ratio: {t['win_ratio(%)']}%<br>"\
        f"Average result: {t['average_res(%)']}%<br>"\
        f"Median result: {t['median_res(%)']}%<br>"\
        f"Average trade length: {round(t['average_trade_len(days)'], 0)} days<br>"\
        f"Cumulative result: {round(t['cumulative_result'], 2)}x<br>"\
        f"Profitable trades mean: {t['profitable_trades_mean']}%<br>"\
        f"Profitable trades median: {t['profitable_trades_median']}%<br>"\
        f"Looser trades mean: {t['looser_trades_mean']}%<br>"\
        f"Looser trades median: {t['looser_trades_median']}%<br>"

        # Add a larger textbox using annotations
        fig.add_annotation( go.layout.Annotation( x=tex_loc[0], y=tex_loc[1], xref='paper', yref='paper', text=trade_text, showarrow=True, arrowhead=4, ax=0, ay=0, bordercolor='black', borderwidth=2, bgcolor='white', align='left', font=dict(size=14, color='black')))


    # Add RSI line
    fig.add_trace(go.Scatter(x=tdf['date'], y=tdf['rsi'], line=dict(color='green', width=2), name='RSI'), row=2, col=1)
    fig.add_shape(type="line", x0=tdf['date'].min(), x1=tdf['date'].max(), y0=buy_threshold, y1=buy_threshold, line=dict(color="black", width=2, dash="dash"), row=2, col=1)
    fig.add_shape(type="line", x0=tdf['date'].min(), x1=tdf['date'].max(), y0=sell_threshold, y1=sell_threshold, line=dict(color="black", width=2, dash="dash"), row=2, col=1)


    # Show the plot
    return (fig)


# Test
# show_indicator_rsi_strategy('TSLA', 30,80)