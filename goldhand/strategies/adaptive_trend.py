from IPython.display import display
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from goldhand.stocks import GoldHand
from goldhand.backtest import Backtest
from goldhand.indicators import Indicators
from goldhand.plotting import Plotting

def adaptive_trend_strategy(data, is_crypto=False):
    """
    Adaptive Trend Strategy V3.
    """
    df = data.copy()

    # Settings
    if is_crypto:
        ema_fast = 12
        ema_slow = 26
        rsi_min = 55
        rsi_max = 70
        adx_min = 50
        di_min = 40
        di_ratio = 2.0
        initial_stop_pct = 0.02
        trail_activate_pct = 0.03
        trail_distance_pct = 0.08
        cooldown_bars = 8
    else:
        ema_fast = 20
        ema_slow = 50
        rsi_min = 51
        rsi_max = 73
        adx_min = 40
        di_min = 30
        di_ratio = 1.5
        initial_stop_pct = 0.035
        trail_activate_pct = 0.03
        trail_distance_pct = 0.13
        cooldown_bars = 5

    # Indicators
    df['rsi'] = Indicators.rsi(df['close'], 14)
    df['ema_fast'] = Indicators.ema(df['close'], ema_fast)
    df['ema_slow'] = Indicators.ema(df['close'], ema_slow)
    df['adx'], df['plus_di'], df['minus_di'] = Indicators.adx(df, 14)

    in_position = False
    entry_price = None
    highest_since_entry = None
    last_exit_bar = -cooldown_bars
    
    trade_id = 1
    all_trades = []
    temp_trade = {}

    lookback = 60
    # Start loop
    for i in range(lookback, len(df)):
        current_date = df['date'].iloc[i]
        close = df['close'].iloc[i]
        high_price = df['high'].iloc[i]
        low_price = df['low'].iloc[i]
        
        # Next open price (approximate execution for backtest unless using close)
        # Using next open for entry/exit is more realistic if signal is on close
        if i < len(df) - 1:
            next_open = df['open'].iloc[i+1]
            next_date = df['date'].iloc[i+1]
        else:
            next_open = close # fallback
            next_date = current_date

        if in_position and entry_price is not None:
            highest_since_entry = max(highest_since_entry, high_price)
            max_profit_pct = (highest_since_entry - entry_price) / entry_price

            initial_stop = entry_price * (1 - initial_stop_pct)

            if max_profit_pct >= trail_activate_pct:
                trailing_stop = highest_since_entry * (1 - trail_distance_pct)
                stop_price = max(initial_stop, trailing_stop)
            else:
                stop_price = initial_stop

            # Check for stop hit
            if low_price <= stop_price:
                # Sell execution
                exit_price = max(stop_price, low_price) # Realistic approximation
                # Ideally, if gap down, exit is open, but stop_price logic implies intra-bar touch
                
                temp_trade['sell_price'] = exit_price
                temp_trade['sell_date'] = current_date # Exited on this bar
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'closed'
                temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
                
                d1 = pd.to_datetime(temp_trade['buy_date'])
                d2 = pd.to_datetime(temp_trade['sell_date'])
                temp_trade['days_in_trade'] = (d2 - d1).days

                in_position = False
                entry_price = None
                highest_since_entry = None
                last_exit_bar = i
                
                trade_id += 1
                all_trades.append(temp_trade)
                temp_trade = {}
                continue

        # Check for Entry
        if not in_position and (i - last_exit_bar) >= cooldown_bars:
            rsi = df['rsi'].iloc[i]
            # ema_f = df['ema_fast'].iloc[i] 
            # ema_s = df['ema_slow'].iloc[i]
            # adx = df['adx'].iloc[i]
            # using direct iloc access for speed if needed, but pandas overhead dominates here anyway
            
            # Using i-3 needs check
            if i < 3: continue
            
            ema_f = df['ema_fast'].iloc[i]
            ema_s = df['ema_slow'].iloc[i]
            adx = df['adx'].iloc[i]
            plus_di = df['plus_di'].iloc[i]
            minus_di = df['minus_di'].iloc[i]

            if pd.isna(adx) or pd.isna(ema_s):
                continue

            above_emas = close > ema_f > ema_s
            rsi_ok = rsi > rsi_min and rsi < rsi_max
            power_trend = adx > adx_min
            dominant_bullish = plus_di > di_min and plus_di > minus_di * di_ratio
            ema_rising = ema_f > df['ema_fast'].iloc[i-3]

            if above_emas and rsi_ok and power_trend and dominant_bullish and ema_rising:
                # BUY Signal
                temp_trade['buy_price'] = next_open # Buy next open
                temp_trade['buy_date'] = next_date
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'open'
                
                in_position = True
                entry_price = next_open
                highest_since_entry = entry_price # Reset high watermark
                
    # Close open trade at end
    if temp_trade:
        temp_trade['sell_price'] = df['close'].iloc[-1]
        temp_trade['trade_id'] = trade_id
        temp_trade['sell_date'] = df['date'].iloc[-1]
        temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
        
        d1 = pd.to_datetime(temp_trade['buy_date'])
        d2 = pd.to_datetime(temp_trade['sell_date'])
        temp_trade['days_in_trade'] = (d2 - d1).days
        
        all_trades.append(temp_trade)

    return pd.DataFrame(all_trades)

def show_indicator_adaptive_trend_strategy(ticker, is_crypto=False, plot_title='', ndays=0, plot_height=1000, add_strategy_summary=True):
    """
    Show Adaptive Trend Strategy V3 result.
    """
    gh = GoldHand(ticker)
    if gh.df is None or gh.df.empty:
        print(f"No data for {ticker}")
        return

    data = gh.df.copy()
    
    # We need to wrap the strategy because Backtest expects (data, buy_threshold, sell_threshold) signature
    # or **kwargs. We will pass is_crypto via wrapper or lambda if needed, but Backtest handles **kwargs
    
    backtest = Backtest(data, adaptive_trend_strategy, is_crypto=is_crypto, plot_title=plot_title)
    trades = backtest.trades
    
    if ndays > 0:
        data = data.tail(ndays)
        
    # Custom Plot
    # Row 1: Price + EMA
    # Row 2: RSI
    # Row 3: ADX
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        subplot_titles=['Price', "RSI", "ADX"], row_heights=[0.6, 0.2, 0.2])

    # 1. Price Chart
    fig.add_trace(go.Ohlc(x=data['date'], open=data['open'], high=data['high'], low=data['low'], close=data['close'], name='OHLC'), row=1, col=1)
    
    # Calculate indicators for plot if not present (Backtest does it internally on copy)
    if 'ema_fast' not in data.columns:
         ema_fast = 12 if is_crypto else 20
         ema_slow = 26 if is_crypto else 50
         data['ema_fast'] = Indicators.ema(data['close'], ema_fast)
         data['ema_slow'] = Indicators.ema(data['close'], ema_slow)
         data['rsi'] = Indicators.rsi(data['close'], 14)
         data['adx'], data['plus_di'], data['minus_di'] = Indicators.adx(data, 14)

    fig.add_trace(go.Scatter(x=data['date'], y=data['ema_fast'], line=dict(color='orange', width=1.5), name='EMA Fast'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data['date'], y=data['ema_slow'], line=dict(color='blue', width=1.5), name='EMA Slow'), row=1, col=1)
        
    # Trades using helper
    Plotting.add_trades_to_figure(fig, trades, df=data, row=1, col=1)

    # 2. RSI Chart
    fig.add_trace(go.Scatter(x=data['date'], y=data['rsi'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
    # Thresholds (default visual reference)
    fig.add_shape(type="line", x0=data['date'].min(), x1=data['date'].max(), y0=30, y1=30, line=dict(color="grey", width=1, dash="dash"), layer='above', row=2, col=1)
    fig.add_shape(type="line", x0=data['date'].min(), x1=data['date'].max(), y0=70, y1=70, line=dict(color="grey", width=1, dash="dash"), layer='above', row=2, col=1)

    # 3. ADX Chart
    fig.add_trace(go.Scatter(x=data['date'], y=data['adx'], line=dict(color='black', width=2), name='ADX'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data['date'], y=data['plus_di'], line=dict(color='green', width=1), name='+DI'), row=3, col=1)
    fig.add_trace(go.Scatter(x=data['date'], y=data['minus_di'], line=dict(color='red', width=1), name='-DI'), row=3, col=1)
    
    # Style
    fig.update_layout(template='plotly_white', height=plot_height, title=plot_title, showlegend=True) # Legend useful here
    
    # Apply style to all axes
    fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
    fig.update(layout_xaxis_rangeslider_visible=False)

    if add_strategy_summary:
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
