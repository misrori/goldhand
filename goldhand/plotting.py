import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class Plotting:
    """
    Class to handle all visualization logic using Plotly.
    Style: GoldHand default style.
    """
    
    @staticmethod
    def _create_base_ohlc(df: pd.DataFrame):
        """Helper to create base candlestick chart"""
        return go.Ohlc(
            x=df['date'], 
            open=df['open'], 
            high=df['high'], 
            low=df['low'], 
            close=df['close'],
            name='OHLC'
        )

    @staticmethod
    def plot_candle_with_locals(df: pd.DataFrame, title: str = "GoldHand Chart", height: int = 900, 
                                show_ma: bool = True, show_locals: bool = True):
        """
        Plot interactive candlestick chart with local min/max annotations and SMA lines.
        """
        fig = go.Figure(data=Plotting._create_base_ohlc(df))
        
        # Add SMAs
        if show_ma:
            if 'sma_50' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['sma_50'], opacity=0.5, 
                                       line=dict(color='lightblue', width=2), name='SMA 50'))
            if 'sma_200' in df.columns:
                fig.add_trace(go.Scatter(x=df['date'], y=df['sma_200'], opacity=0.7, 
                                       line=dict(color='red', width=2.5), name='SMA 200'))

        # Add Locals
        if show_locals and 'local' in df.columns and 'local_text' in df.columns:
            # Filter non-empty locals
            locals_df = df[df['local'] != ""]
            
            for _, row in locals_df.iterrows():
                direction = row['local']
                tdate = row['date']
                local_text = row['local_text']
                
                # Determine color and offset based on direction
                if direction == 'maximum':
                    y_val = row['high']
                    color = "#214e34" # dark green
                    ay = -45
                else: # minimum
                    y_val = row['low']
                    color = "red"
                    ay = 45
                    
                fig.add_annotation(
                    x=tdate, y=y_val, text=local_text, showarrow=True, align="center",
                    bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color=color),
                    borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8,
                    arrowhead=2, arrowsize=1, arrowwidth=1, ax=(ay * -1 if direction == 'maximum' else ay), ay=ay
                )

        # Style
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=height, title=title)
        fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update(layout_xaxis_rangeslider_visible=False)
        
        return fig
    
    @staticmethod
    def add_trades_to_figure(fig, trades: pd.DataFrame, df: pd.DataFrame = None, row: int = None, col: int = None):
        """
        Add trade markers and rectangles to an existing figure.
        """
        if trades.empty:
            return

        for index, row_data in trades.iterrows():
            buy_date = row_data['buy_date']
            sell_date = row_data.get('sell_date', None)
            # Ensure we work with clean date objects if strict typing needed, 
            # but plotly usually handles pandas Timestamp/strings fine.
            
            buy_price = row_data['buy_price']
            
            # Default values for open trades
            sell_price = row_data.get('sell_price')
            if sell_price is None or pd.isna(sell_price):
                 if df is not None:
                    sell_price = df.iloc[-1]['close']
                 else:
                    sell_price = buy_price

            result_val = row_data.get('result', 1.0)
            
            triangle_color = 'green' if result_val >= 1 else 'red'
            
            # Helper for kwargs
            trace_kwargs = {}
            shape_kwargs = {}
            if row is not None and col is not None:
                trace_kwargs = {'row': row, 'col': col}
                shape_kwargs = {'row': row, 'col': col}

            # Buy Marker
            fig.add_trace(go.Scatter(
                x=[buy_date], y=[buy_price], mode='markers',
                marker=dict(symbol='triangle-up', size=16, color=triangle_color),
                showlegend=False
            ), **trace_kwargs)
            
            # Sell Marker (if exists)
            # We draw sell marker even if it's the current close for visualizing the "potential" exit or current state
            fig.add_trace(go.Scatter(
                    x=[sell_date] if sell_date else [df.iloc[-1]['date'] if df is not None else buy_date], 
                    y=[sell_price], mode='markers',
                    marker=dict(symbol='triangle-down', size=16, color=triangle_color),
                    showlegend=False
            ), **trace_kwargs)

            # Draw Box
            if sell_date:
                rise_pct = (result_val - 1) * 100
                label_text = f"{round(rise_pct, 2)}%"
                
                # Ensure we use the correct arguments for add_shape
                # row/col are handled by the figure method if passed in **shape_kwargs
                
                fig.add_shape(
                    type="rect", 
                    x0=buy_date, y0=buy_price, 
                    x1=sell_date, y1=sell_price,
                    line=dict(color=triangle_color, width=2),
                    fillcolor="LightSkyBlue", opacity=0.3,
                    label=dict(text=label_text, textposition="bottom center", font=dict(color=triangle_color)),
                    layer="above", 
                    **shape_kwargs
                )

    @staticmethod
    def plot_strategy_trades(df: pd.DataFrame, trades: pd.DataFrame, title: str, 
                             height: int = 900, summary_text: str = None):
        """
        Plot trades on the chart.
        """
        fig = go.Figure(data=Plotting._create_base_ohlc(df))
        
        # Add basic SMAs context
        if 'sma_50' in df.columns:
            fig.add_trace(go.Scatter(x=df['date'], y=df['sma_50'], opacity=0.5, 
                                   line=dict(color='lightblue', width=2), name='SMA 50'))

        # Reuse helper
        Plotting.add_trades_to_figure(fig, trades, df=df)

        # Add Summary Box
        if summary_text:
             fig.add_annotation(
                 xref='paper', yref='paper',
                 x=0.02, y=0.98,
                 text=summary_text,
                 showarrow=False,
                 bordercolor='black',
                 borderwidth=1,
                 bgcolor='white',
                 align='left',
                 font=dict(size=12, color='black')
             )

        # Style
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=height, title=title)
        fig.update_xaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update_yaxes(mirror=True, ticks='outside', showline=True, linecolor='black', gridcolor='lightgrey')
        fig.update(layout_xaxis_rangeslider_visible=False)
        
        return fig
