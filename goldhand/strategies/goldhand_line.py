from IPython.display import display
import pandas as pd
from goldhand.stocks import GoldHand
from goldhand.backtest import Backtest
from goldhand.indicators import Indicators
from goldhand.plotting import Plotting

def goldhand_line_strategy(data, buy_at='gold', sell_at='grey'):
    """
    This function implements the GoldHandLine strategy.
    
    Parameters:
    - data (pandas DataFrame) : The DataFrame containing the data.
    - buy_at (str): The color of the line to buy at. Default is 'gold'.
    - sell_at (str): The color of the line to sell at. Default is 'grey'.
    
    Returns: The trades of the GoldHandLine strategy. 
    """
    data = data.copy()
    
    # Ensure HL2 exists
    if 'hl2' not in data.columns:
         data['hl2'] = (data['high'] + data['low'])/2

    # Apply SMMA using Indicators module
    data['v1'] = Indicators.smma(data['hl2'], 15)
    data['v2'] = Indicators.smma(data['hl2'], 19)
    data['v3'] = Indicators.smma(data['hl2'], 25)
    data['v4'] = Indicators.smma(data['hl2'], 29)

    data['color'] = 'grey'
    
    # Update color based on conditions
    data.loc[(data['v4'] < data['v3']) & (data['v3'] < data['v2']) & (data['v2'] < data['v1']), 'color'] = 'gold'
    data.loc[(data['v1'] < data['v2']) & (data['v2'] < data['v3']) & (data['v3'] < data['v4']), 'color'] = 'blue'

    in_trade = False
    trade_id = 1
    all_trades = []
    temp_trade = {}

    for i in range(1, len(data)):
        # Buy Signal
        if not in_trade:
            if data['color'].iloc[i] == buy_at:
                if i == (len(data) - 1): 
                    temp_trade['buy_price'] = data['close'].iloc[i]
                    temp_trade['buy_date'] = data['date'].iloc[i]
                else:
                    temp_trade['buy_price'] = data['open'].iloc[i+1]
                    temp_trade['buy_date'] = data['date'].iloc[i+1]
                
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'open'
                in_trade = True
        
        # Sell Signal
        else:
            if data['color'].iloc[i] == sell_at:
                if i == (len(data) - 1): 
                    temp_trade['sell_price'] = data['close'].iloc[i]
                    temp_trade['sell_date'] = data['date'].iloc[i]
                else:
                    temp_trade['sell_price'] = data['open'].iloc[i+1]
                    temp_trade['sell_date'] = data['date'].iloc[i+1]
                
                temp_trade['trade_id'] = trade_id
                temp_trade['status'] = 'closed'
                temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
                
                # Check if dates are actual dates or strings/timestamps, calculate days
                d1 = pd.to_datetime(temp_trade['buy_date'])
                d2 = pd.to_datetime(temp_trade['sell_date'])
                temp_trade['days_in_trade'] = (d2 - d1).days

                in_trade = False
                trade_id += 1
                all_trades.append(temp_trade)
                temp_trade = {}

    # Close open trade at the end
    if temp_trade:
        temp_trade['sell_price'] = data['close'].iloc[-1]
        temp_trade['trade_id'] = trade_id
        temp_trade['sell_date'] = data['date'].iloc[-1]
        temp_trade['result'] = temp_trade['sell_price'] / temp_trade['buy_price']
        
        d1 = pd.to_datetime(temp_trade['buy_date'])
        d2 = pd.to_datetime(temp_trade['sell_date'])
        temp_trade['days_in_trade'] = (d2 - d1).days
        
        all_trades.append(temp_trade)

    res_df = pd.DataFrame(all_trades)
    return res_df


def show_indicator_goldhand_line_strategy(ticker, plot_title='', buy_at='gold', sell_at='grey', ndays=0, plot_height=1000, add_strategy_summary=True):
    """
    Show the GoldHandLine strategy on a plotly chart.
    """
    gh = GoldHand(ticker)
    if gh.df is None or gh.df.empty:
        print(f"No data for {ticker}")
        return

    data = gh.df.copy()
    
    # Run backtest
    backtest = Backtest(data, goldhand_line_strategy, plot_title=plot_title, buy_at=buy_at, sell_at=sell_at)
    
    # Filter data for display if ndays is set
    if ndays != 0:
        data = data.tail(ndays)
        # We might want to filter trades as well in visual, 
        # but Backtest calculates on full data. 
        # For visualization we can't easily filter the backtest internal trades without re-running or filtering output.
        # But 'show_trades' uses the stored trades.
        
    # Since Backtest controls visualization now, we rely on it.
    # However, standard Backtest.show_trades() uses the data passed to it. 
    # If we want to show subset, we might need to adjust.
    # For now, let's just return what backtest produces.
    
    if add_strategy_summary:
        backtest.summarize_strategy()
    else:
        return backtest.show_trades()