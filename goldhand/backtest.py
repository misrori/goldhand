from IPython.display import display
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

class Backtest:
    def __init__(self, data, strategy_function, plot_title='', **kwargs):
        """
        Backtest class to test strategies on historical data to see how they would have performed.
        
        Parameters:
        - data: pandas DataFrame with historical data
        - strategy_function: function that takes in the data and returns a DataFrame of trades
        - plot_title: title for the plot
        - kwargs: additional parameters to be passed to the strategy function
        """
        self.data = data
        self.plot_title = plot_title
        self.strategy_function = strategy_function
        self.additional_params = kwargs
        self.add_trades()
        self.summary_of_trades()


    def add_trades(self):
        """
        Calculate the trades using the strategy function and the data provided
        """
        self.trades = self.strategy_function(self.data, **self.additional_params)
        self.trades['ticker'] = self.data['ticker'].iloc[0]
        
        # order columns
        all_col = self.trades.columns.tolist()
        first = ['ticker']
        first.extend([x for x in all_col if x not in first])
        self.trades = self.trades[first]


    def summary_of_trades(self):
        """
        Calculate the summary of the trades
        """
        self.trades_summary = {
          'ticker' : self.data['ticker'].iloc[0],
          'number_of_trades' : self.trades.shape[0],
          'win_ratio(%)' : round(((sum(self.trades['result'] >1) / self.trades.shape[0])*100),2),
          'average_res(%)' : round(((self.trades['result'].mean()-1)*100),2),
          'average_trade_len(days)' :  round(self.trades['days_in_trade'].mean(), 0),
          
          
          'median_res(%)': round(((self.trades['result'].median()-1)*100),2),
          'cumulative_result': list(np.cumprod(self.trades['result'], axis=0))[-1],
          'trade_results': ' # '.join([ str(round(((x-1)*100),2)) for x in self.trades['result']]),

          'profitable_trade_results': ' # '.join([ str(round(((x-1)*100),2)) for x in self.trades['result'] if x>=1]),

          'profitable_trades_mean' : round((( np.mean([x for x in self.trades['result'] if x>=1]) -1)*100),2),
          'profitable_trades_median' : round((( np.median([x for x in self.trades['result'] if x>=1])-1)*100),2),

          'looser_trade_results': ' # '.join([ str(round(((x-1)*100),2)) for x in self.trades['result'] if x<1]),

          'looser_trades_mean' : round((( np.mean([x for x in self.trades['result'] if x<1])-1)*100),2),
          'looser_trades_median' : round((( np.median([x for x in self.trades['result'] if x<1])-1)*100),2),

          'median_trade_len(days)' :  self.trades['days_in_trade'].median(),


          'number_of_win_trades': sum(self.trades['result'] >1),
          'number_of_lost_trades': (self.trades.shape[0] - sum(self.trades['result'] >1)),

          'max_gain(%)' : round(((self.trades['result'].max()-1)*100),2),
          'max_lost(%)' : round(((self.trades['result'].min()-1)*100),2),

          'first_trade_buy' : min(self.trades['buy_date']),
          
          
          'first_data_date' : self.data['date'].iloc[0],
          'first_open_price' : self.data['open'].iloc[0],
          
          'last_data_date' : self.data['date'].iloc[-1],
          'last_close_price' : self.data['close'].iloc[-1],
          
          'hold_result' : f"{round(t.df['close'].iloc[-1] / t.df['open'].iloc[0],2)} x",
          

        }
        self.trades_summary.update(self.additional_params)

    def show_trades(self):
        """
        Plot the trades of the strategy on the data provided
        """
        tdf = self.data
        fig = go.Figure(data=go.Ohlc(x=tdf['date'], open=tdf['open'], high=tdf['high'], low=tdf['low'],close=tdf['close']))
        fig.add_trace( go.Scatter(x=tdf['date'], y=tdf['sma_50'], opacity =0.5, line=dict(color='lightblue', width = 2) , name = 'SMA 50') )
        fig.add_trace( go.Scatter(x=tdf['date'], y=tdf['sma_200'], opacity =0.7, line=dict(color='red', width = 2.5) ,  name = 'SMA 200') )
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update_xaxes( mirror=True,  ticks='outside',  showline=True,  linecolor='black', gridcolor='lightgrey')
        fig.update_yaxes( mirror=True,  ticks='outside',  showline=True, linecolor='black',  gridcolor='lightgrey')

        for index, row in self.trades.iterrows():
            buy_date= row['buy_date']
            sell_date= row['sell_date']
            buy_price = row['buy_price']
            sell_price = row['sell_price']
            trade_id  = row['trade_id']
            status = row['status']
            triangle_color = 'green' if row['result'] >1 else 'red'

            rise = (row['result'] -1)*100

            if rise>100:
                if status =='closed':
                    result = f'Up:{round(((rise+100)/100), 2)}x'
                else:
                    result = f'Up:{round(((rise+100)/100), 2)}x <br> Still open'
            else:
                if status =='closed':
                    result = f"{round(((row['result']-1)*100),2) }%"
                else:
                    result = f"{round(((row['result']-1)*100),2) }% <br> Still open"


            # add buy
            buy_point=(buy_date, buy_price)
            triangle_trace = go.Scatter(x=[buy_point[0]],  y=[buy_point[1]],  mode='markers', marker=dict(symbol='triangle-up', size=16, color=triangle_color))
            fig.add_trace(triangle_trace)
            fig.add_annotation( x=buy_date, y=buy_price, text=f"Buy: ${round(buy_price, 2)}<br>#{trade_id}",  hovertext = f"Buy: ${round(buy_price, 2)}<br>#{trade_id}", showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=12, color= triangle_color ), borderwidth=2, borderpad=4, bgcolor="#f4fdff",  opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=30,ay=30)

            # add sell
            sell_point=(sell_date, sell_price)
            triangle_trace = go.Scatter(x=[sell_point[0]],  y=[sell_point[1]],  mode='markers', marker=dict(symbol='triangle-down', size=16, color=triangle_color))
            fig.add_trace(triangle_trace)
            fig.add_annotation( x=sell_date, y=sell_price, text=f"Sell: ${round(sell_price, 2)}<br>#{trade_id}, {result}", hovertext = f"Sell: ${round(sell_price, 2)}<br>#{trade_id}, {result}"  ,showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=12, color= triangle_color ), borderwidth=2, borderpad=4, bgcolor="#f4fdff",  opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=-30,ay=-30)

            # add reactangle
            fig.add_shape(type="rect", x0=buy_point[0], y0=buy_point[1], x1=sell_point[0], y1=sell_point[1],line=dict(color= triangle_color ,width=2,),fillcolor="LightSkyBlue", opacity=0.3, label=dict( text=f"{result}<br>{row['days_in_trade']} days",   textposition="bottom center", font=dict(size=13, color =triangle_color, family="Times New Roman")))

            # set size
            fig.update_layout(showlegend=False, plot_bgcolor='white',title=self.plot_title  ,height=900)

        return(fig)


    def summarize_strategy(self):
        """
        Display the summary of the strategy:
        - Summary of trades
        - Trades in interactive plot
        - Trades in DataFrame
        """
        display(pd.DataFrame(self.trades_summary, index=['Strategy summary']).T )
        self.show_trades().show()
        display(self.trades)
