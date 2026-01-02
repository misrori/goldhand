from IPython.display import display
import pandas as pd
import numpy as np
from goldhand.plotting import Plotting

class Backtest:
    """
    Backtest class for running trading strategies.
    """
    
    def __init__(self, data, strategy_func, plot_title='Backtest', **kwargs):
        """
        Initialize backtest.
        
        Parameters:
        - data: DataFrame with OHLCV data
        - strategy_func: Function that takes data and returns trades DataFrame
        - plot_title: Title for plots
        - **kwargs: Additional parameters to pass to strategy function
        """
        self.data = data.copy()
        self.strategy_func = strategy_func
        self.plot_title = plot_title
        self.additional_params = kwargs
        
        # Run strategy
        self.trades = self.strategy_func(self.data, **kwargs)
        
        # Ensure trades is a DataFrame
        if not isinstance(self.trades, pd.DataFrame):
            self.trades = pd.DataFrame()
            
        # Reorder columns for better readability
        if not self.trades.empty:
            first = ['ticker', 'buy_price', 'buy_date', 'trade_id', 'status', 'sell_price', 'sell_date', 'result', 'days_in_trade']
            all_col = list(self.trades.columns)
            first = [x for x in first if x in all_col]
            first.extend([x for x in all_col if x not in first])
            self.trades = self.trades[first]
            
        self.calculate_summary()

    def calculate_summary(self):
        """
        Calculate comprehensive performance metrics.
        """
        if self.trades.empty:
            self.trades_summary = {'number_of_trades': 0}
            self.trade_summary_plot_text = "No trades executed."
            return

        # Explicit type conversion to numeric to avoid errors
        results = pd.to_numeric(self.trades['result'], errors='coerce').fillna(1.0)
        days = pd.to_numeric(self.trades['days_in_trade'], errors='coerce').fillna(0)
        
        n_trades = len(self.trades)
        win_trades = results[results > 1]
        loss_trades = results[results < 1]
        
        # Calculate profit percentages
        profit_pcts = (results - 1) * 100
        win_profit_pcts = profit_pcts[results > 1]
        loss_profit_pcts = profit_pcts[results < 1]
        
        # Basic metrics
        win_ratio = (len(win_trades) / n_trades) * 100 if n_trades > 0 else 0
        avg_res = profit_pcts.mean()
        median_res = profit_pcts.median()
        cum_res = results.prod()
        
        # Detailed profit/loss metrics
        profitable_trades_mean = win_profit_pcts.mean() if len(win_profit_pcts) > 0 else 0
        profitable_trades_median = win_profit_pcts.median() if len(win_profit_pcts) > 0 else 0
        looser_trades_mean = loss_profit_pcts.mean() if len(loss_profit_pcts) > 0 else 0
        looser_trades_median = loss_profit_pcts.median() if len(loss_profit_pcts) > 0 else 0
        
        # Trade results lists
        trade_results_str = " # ".join([f"{x:.2f}" for x in profit_pcts.values[:10]])  # First 10
        if len(profit_pcts) > 10:
            trade_results_str += " # ..."
            
        profitable_results_str = " # ".join([f"{x:.2f}" for x in win_profit_pcts.values[:10]])
        if len(win_profit_pcts) > 10:
            profitable_results_str += " # ..."
            
        looser_results_str = " # ".join([f"{x:.2f}" for x in loss_profit_pcts.values[:10]])
        if len(loss_profit_pcts) > 10:
            looser_results_str += " # ..."
        
        # Date and price info
        first_trade_date = self.trades['buy_date'].iloc[0] if 'buy_date' in self.trades.columns else None
        last_trade_date = self.trades['sell_date'].iloc[-1] if 'sell_date' in self.trades.columns else None
        first_data_date = self.data['date'].iloc[0]
        last_data_date = self.data['date'].iloc[-1]
        first_open_price = self.data['open'].iloc[0]
        last_close_price = self.data['close'].iloc[-1]
        
        # Hold result
        hold_result = last_close_price / first_open_price
        
        # Buy/Sell colors (from original strategy if available)
        buy_color = self.additional_params.get('buy_at', 'gold')
        sell_color = self.additional_params.get('sell_at', 'grey')
        
        self.trades_summary = {
            'ticker': self.data['ticker'].iloc[0] if 'ticker' in self.data.columns else 'Unknown',
            'number_of_trades': n_trades,
            'win_ratio(%)': round(win_ratio, 2),
            'average_res(%)': round(avg_res, 2),
            'average_trade_len(days)': round(days.mean(), 1),
            'median_res(%)': round(median_res, 2),
            'cumulative_result': round(cum_res, 6),
            'trade_results': trade_results_str,
            'profitable_trade_results': profitable_results_str,
            'profitable_trades_mean': round(profitable_trades_mean, 2),
            'profitable_trades_median': round(profitable_trades_median, 2),
            'looser_trade_results': looser_results_str,
            'looser_trades_mean': round(looser_trades_mean, 2),
            'looser_trades_median': round(looser_trades_median, 2),
            'median_trade_len(days)': round(days.median(), 1),
            'number_of_win_trades': len(win_trades),
            'number_of_lost_trades': len(loss_trades),
            'max_gain(%)': round((results.max() - 1) * 100, 2),
            'max_lost(%)': round((results.min() - 1) * 100, 2),
            'first_trade_buy': str(first_trade_date) if first_trade_date else 'N/A',
            'first_data_date': str(first_data_date),
            'first_open_price': round(first_open_price, 6),
            'last_data_date': str(last_data_date),
            'last_close_price': round(last_close_price, 6),
            'hold_result': f"{round(hold_result, 2)} x",
            'buy_at': buy_color,
            'sell_at': sell_color
        }
        
        # Add additional params to summary for context
        self.trades_summary.update(self.additional_params)
        
        # Format text for plot
        self.trade_summary_plot_text = (
            f"Trades: {self.trades_summary['number_of_trades']}<br>"
            f"Win ratio: {self.trades_summary['win_ratio(%)']}%<br>"
            f"Avg Result: {self.trades_summary['average_res(%)']}%<br>"
            f"Cum Result: {self.trades_summary['cumulative_result']}<br>"
            f"Hold Result: {self.trades_summary['hold_result']}"
        )

    def show_trades(self):
        """
        Return the plotly figure with trades.
        """
        if self.trades.empty:
            print("No trades to show.")
            return Plotting._create_base_ohlc(self.data)
            
        return Plotting.plot_strategy_trades(
            self.data, 
            self.trades, 
            title=self.plot_title,
            summary_text=self.trade_summary_plot_text
        )

    def summarize_strategy(self):
        """
        Display summary table and plot.
        """
        display(pd.DataFrame(self.trades_summary, index=['Strategy summary']).T)
        self.show_trades().show()
        display(self.trades)
