from IPython.display import display
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from goldhand.stocks import GoldHand
from goldhand.backtest import Backtest
from goldhand.indicators import Indicators
from goldhand.plotting import Plotting

def rsi_strategy(data, buy_threshold=30, sell_threshold=70):
    """
    RSI strategy for backtesting.
    """
    data = data.copy()
    
    # Ensure RSI is present
    if 'rsi' not in data.columns:
        data['rsi'] = Indicators.rsi(data['close'])

    in_trade = False
    trade_id = 1
    all_trades = []
    temp_trade = {}

    for i in range(1, len(data)):
        if not in_trade:
            # Buy Signal
            if data['rsi'].iloc[i] < buy_threshold:
                if i == (len(data) - 1): 
                    temp_trade['buy_price'] = data['close'].iloc[i]
                    temp_trade['buy_date'] = data['date'].iloc[i]
                else:
                    temp_trade['buy_price'] = data['open'].iloc[i+1]
                    temp_trade['buy_date'] = data['date'].iloc[i+1]

                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'open'
                in_trade = True
        else:
            # Sell Signal
            if data['rsi'].iloc[i] > sell_threshold:
                if i == (len(data) - 1): 
                    temp_trade['sell_price'] = data['close'].iloc[i]
                    temp_trade['sell_date'] = data['date'].iloc[i]
                else:
                    temp_trade['sell_price'] = data['open'].iloc[i+1]
                    temp_trade['sell_date'] = data['date'].iloc[i+1]
                                       
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'closed'
                temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
                
                d1 = pd.to_datetime(temp_trade['buy_date'])
                d2 = pd.to_datetime(temp_trade['sell_date'])
                temp_trade['days_in_trade'] = (d2 - d1).days

                in_trade = False
                trade_id += 1
                all_trades.append(temp_trade)
                temp_trade = {}
                
    if temp_trade:
        temp_trade['sell_price'] = data['close'].iloc[-1]
        temp_trade['trade_id'] = trade_id
        temp_trade['sell_date'] = data['date'].iloc[-1]
        temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
        
        d1 = pd.to_datetime(temp_trade['buy_date'])
        d2 = pd.to_datetime(temp_trade['sell_date'])
        temp_trade['days_in_trade'] = (d2 - d1).days
        
        all_trades.append(temp_trade)

    return pd.DataFrame(all_trades)


def show_indicator_rsi_strategy(ticker, buy_threshold=30, sell_threshold=70, plot_title='', ndays=0, plot_height=1000, add_strategy_summary=True):
    """
    Show RSI strategy result in one plot: candlestick chart, SMA lines, trades, RSI indicator.
    """
    gh = GoldHand(ticker)
    if gh.df is None or gh.df.empty:
        print(f"No data for {ticker}")
        return

    data = gh.df.copy()
    backtest = Backtest(data, rsi_strategy, buy_threshold=buy_threshold, sell_threshold=sell_threshold, plot_title=plot_title)
    trades = backtest.trades
    
    if ndays > 0:
        data = data.tail(ndays)
        
    # Custom Plot with Subplot for RSI
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=['Price', "RSI"], row_heights=[0.7, 0.3])

    # 1. Price Chart
    fig.add_trace(go.Ohlc(x=data['date'], open=data['open'], high=data['high'], low=data['low'], close=data['close'], name='OHLC'), row=1, col=1)
    
    # SMAs
    if 'sma_50' in data.columns:
        fig.add_trace(go.Scatter(x=data['date'], y=data['sma_50'], line=dict(color='lightblue', width=2), name='SMA 50'), row=1, col=1)
    if 'sma_200' in data.columns:
        fig.add_trace(go.Scatter(x=data['date'], y=data['sma_200'], line=dict(color='red', width=2), name='SMA 200'), row=1, col=1)
        
    # Trades using helper
    Plotting.add_trades_to_figure(fig, trades, df=data, row=1, col=1)

    # 2. RSI Chart
    if 'rsi' in data.columns:
        fig.add_trace(go.Scatter(x=data['date'], y=data['rsi'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
        
    # Threshold lines
    fig.add_shape(type="line", x0=data['date'].min(), x1=data['date'].max(), y0=buy_threshold, y1=buy_threshold, line=dict(color="grey", width=1, dash="dash"), layer='above', row=2, col=1)
    fig.add_shape(type="line", x0=data['date'].min(), x1=data['date'].max(), y0=sell_threshold, y1=sell_threshold, line=dict(color="grey", width=1, dash="dash"), layer='above', row=2, col=1)

    # Style (consistent with Plotting class)
    fig.update_layout(template='plotly_white', height=plot_height, title=plot_title, showlegend=False)
    
    # Apply style to all axes explicitly
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update(layout_xaxis_rangeslider_visible=False)

    
    if add_strategy_summary:
        # Add annotation with summary
        fig.add_annotation(
             xref='paper', yref='paper',
             x=0.02, y=0.98,
             text=backtest.trade_summary_plot_text,
             showarrow=False,
             bordercolor='black',
             borderwidth=1,
             bgcolor='white',
             align='left',
             font=dict(size=12, color='black')
         )
         
    return fig