from IPython.display import display
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from goldhand import *



def goldhand_line_strategy(data):

    data['hl2'] = (data['high'] + data['low'])/2

    def smma(data, window, colname):
        hl2 = data['hl2'].values
        smma_values = [hl2[0]]

        for i in range(1, len(hl2)):
            smma_val = (smma_values[-1] * (window - 1) + hl2[i]) / window
            smma_values.append(smma_val)

        data[colname] = smma_values
        return data

    # Apply SMMA to the dataframe
    data = smma(data, 15, 'v1')
    data = smma(data, 19, 'v2')
    data = smma(data, 25, 'v3')
    data = smma(data, 29, 'v4')

    data['color'] = 'grey'  # Set default color to grey

    # Update color based on conditions
    data.loc[(data['v4'] < data['v3']) & (data['v3'] < data['v2']) & (data['v2'] < data['v1']), 'color'] = 'gold'
    data.loc[(data['v1'] < data['v2']) & (data['v2'] < data['v3']) & (data['v3'] < data['v4']), 'color'] = 'blue'

    in_trade = False  # Flag to track if already in a trade
    trade_id = 1
    all_trades = []

    temp_trade = {}

    for i in range(1, len(data)):
        # Check if not already in a trade
        if not in_trade:
            # Generate buy signal
            if (data['color'][i] =='gold') :

                temp_trade['buy_price'] = data['close'][i]
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'open'
                temp_trade.update(dict(data.iloc[i].add_prefix('buy_')))
                in_trade = True  # Set flag to indicate in a trade
        else:
            # Generate sell signal
            if (data['color'][i] =='grey') :

                temp_trade['sell_price'] = data['close'][i]
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'closed'

                temp_trade.update(dict(data.iloc[i].add_prefix('sell_')))

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



def show_indicator_goldhand_line_strategy(ticker, plot_title = 'Goldhand line Strategy'):

    data = GoldHand(ticker).df

    #### data prepar
    data['hl2'] = (data['high'] + data['low'])/2

    def smma(data, window, colname):
        hl2 = data['hl2'].values
        smma_values = [hl2[0]]

        for i in range(1, len(hl2)):
            smma_val = (smma_values[-1] * (window - 1) + hl2[i]) / window
            smma_values.append(smma_val)

        data[colname] = smma_values
        return data

    # Apply SMMA to the dataframe
    data = smma(data, 15, 'v1')
    data = smma(data, 19, 'v2')
    data = smma(data, 25, 'v3')
    data = smma(data, 29, 'v4')

    data['color'] = 'grey'  # Set default color to grey

    # Update color based on conditions
    data.loc[(data['v4'] < data['v3']) & (data['v3'] < data['v2']) & (data['v2'] < data['v1']), 'color'] = 'gold'
    data.loc[(data['v1'] < data['v2']) & (data['v2'] < data['v3']) & (data['v3'] < data['v4']), 'color'] = 'blue'



    # Identify rows where color changes compared to the previous row
    data['color_change'] = data['color'] != data['color'].shift(1)

    # Create a 'group' column and increase the value only when there's a color change
    data['group'] = (data['color_change']).cumsum()


    ##### data prepar end

    ##### backtest
    backtest = Backtest( data, goldhand_line_strategy, plot_title = 'Goldhand line Strategy' )
    trades =backtest.trades


    # base plot
    fig = go.Figure(data=go.Ohlc(x=data['date'], open=data['open'], high=data['high'], low=data['low'],close=data['close']))
    fig.update_xaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey' )
    fig.update_yaxes( mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update(layout_xaxis_rangeslider_visible=False)


    for group_id in data['group'].unique():
        if group_id ==data['group'].unique().max():

            indices = data[data['group'] == group_id].index.to_list()
        else:
            indices = data[data['group'] == group_id].index.to_list()
            indices.append(indices[-1]+1)


        group_df = data.loc[indices]

        group_color = group_df['color'].iloc[0]
        color_dict = {'gold' : 'rgba(255, 215, 0, 0.4)' , 'grey' : 'rgba(128, 128 ,128, 0.4)' , 'blue' : 'rgba(0, 0, 255, 0.4)' }



        # Create v1 and v4 traces
        trace_v1 = go.Scatter(x=group_df['date'], y=group_df['v1'], mode='lines', name='v1', line=dict(color=color_dict[group_color]) )
        trace_v4 = go.Scatter(x=group_df['date'], y=group_df['v4'], mode='lines', name='v4', line=dict(color=color_dict[group_color]), fill='tonexty', fillcolor =color_dict[group_color])


        # Add candlestick trace and additional lines to the figure
        fig.add_trace(trace_v1)
        fig.add_trace(trace_v4)


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
    fig.update_layout(showlegend=False, plot_bgcolor='white', height=800, title=plot_title)
    fig.update(layout_xaxis_rangeslider_visible=False)

    # Update x-axes and y-axes for the main chart
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')

    # Update x-axes and y-axes for the RSI subplot
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')




    # Show the plot
    fig.show()


#show_indicator_goldhand_line_strategy('TSLA', plot_title='sdgfsdg')