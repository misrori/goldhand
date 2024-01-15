
# Goldhand
The ultimate python package to work with stock and crypto data

```bash
pip install goldhand
```


# [TradingView]((https://github.com/misrori/goldhand/tw.py))


```python
from goldhand import *

# tradingView data
tw = Tw()

# data frame of the stocks 
tw.stock

# data frame of the top 300 crypto currency
tw.crypto

# data frame of the top 3000 etf
tw.etf

```

```python
# Get a plot of the stock to see the location in the sector 
tw.get_sec_plot('AMD').show()

```
![Sector plot](https://github.com/misrori/goldhand/blob/main/img/sec_plot.png?raw=true "Sector location of FDS")


```python
# Get a plot of the stock to see the location in the industry 
tw.get_sec_plot('AMD').show()

```
![Sector plot](https://github.com/misrori/goldhand/blob/main/img/ind_plot.png?raw=true  "Sector location of FDS")



# [Goldhand class]((https://github.com/misrori/goldhand/stock.py))

The `GoldHand` class is a part of the `goldhand` Python package, which provides functionality for working with stock and crypto data. This class allows users to retrieve detailed information and charts for a specific stock.



```python

# Get a detailed chart of a stock AMD
ticker = "AMD"
t = GoldHand(ticker)
t.df.tail().T
```
![data structure](https://github.com/misrori/goldhand/blob/main/img/df_structure.png?raw=true "data structure")


```python

# Get a detailed chart of a stock AMD
ticker = "TSLA"
t = GoldHand(ticker)
t.plotly_last_year(tw.get_plotly_title(ticker)).show()

## Stock Chart

```
!['Detailed stock chart'](https://github.com/misrori/goldhand/blob/main/img/stock_plot.png?raw=true  "Stock plot")

```python

# Get a detailed chart of a crypto
ticker = "BTC-USD"
t = GoldHand(ticker)
t.plotly_last_year(tw.get_plotly_title(ticker)).show()


```
!['Detailed crypto chart'](https://github.com/misrori/goldhand/blob/main/img/crypto_plot.png?raw=true  "crypto plot")


## [GoldHand Line indicator](https://gist.github.com/misrori/ae77642c31fb1a973c7627cc077a1df2) 
https://gist.github.com/misrori/ae77642c31fb1a973c7627cc077a1df2

```python
ticker = "TSLA"
t = GoldHand(ticker)
t.plot_goldhand_line(tw.get_plotly_title(ticker)).show()

```
!['Detailed crypto chart'](https://github.com/misrori/goldhand/blob/main/img/goldhand_line_plot.png?raw=true  "crypto plot")



# [Backtest](https://github.com/misrori/goldhand/backtest.py)

The Backtest class is a powerful tool for evaluating the performance of trading strategies using historical data. It allows you to simulate trades and calculate various performance metrics to assess the profitability and risk of your strategy.

It takes a data and a function and display the trades. 



```python
ticker= 'TSLA'
data = GoldHand(ticker).df
backtest = Backtest( data, rsi_strategy, plot_title=tw.get_plotly_title(ticker),  buy_threshold=30, sell_threshold=70)
backtest.summarize_strategy()

```
`summarize_strategy`  will  show the trades summary, a plot with trades and the trades in DataFrame.


!['Summary of trades'](https://github.com/misrori/goldhand/blob/main/img/tradesdf.png?raw=true  "summary of trades")

!['Trades plot'](https://github.com/misrori/goldhand/blob/main/img/backtest_plot.png?raw=true  "trades plot")

!['Trades'](https://github.com/misrori/goldhand/blob/main/img/trades_summary.png?raw=true  "trades df")


# Strategys

## [RSI Strategy](https://github.com/misrori/goldhand/strategy_rsi.py)

```python
    """
    RSI strategy for backtesting with Backtest class
    
    Parameters:
    - data: pandas DataFrame with columns: date, open, high, low, close, volume and rsi
    - buy_threshold: int, default 30,  buy when RSI is below this value
    - sell_threshold: int, default 70, sell when RSI is above this value
    """
    backtest = Backtest( data, rsi_strategy, plot_title=tw.get_plotly_title(ticker),  buy_threshold=30, sell_threshold=70)

```


```python
ticker = 'TSLA'
p = show_indicator_rsi_strategy(ticker = ticker, buy_threshold=30, sell_threshold=70, plot_title=tw.get_plotly_title(ticker), add_strategy_summary=True)
```
!['RSI strategy plot'](https://github.com/misrori/goldhand/blob/main/img/rsi_strategy_plot.png?raw=true  "RSI Strategy plot")

## [GoldHand Line indicator](https://github.com/misrori/goldhand/strategy_goldhand_line.py) 

```python
    """
    This function implements the GoldHandLine strategy.
    
    Parameters:
    - data (pandas DataFrame) : The DataFrame containing the data.
    - buy_at (str): The color of the line to buy at. Default is 'gold'.
    - sell_at (str): The color of the line to sell at. Default is 'grey'.
    
    """
    backtest = Backtest( data, goldhand_line_strategy,)

```

```python
ticker = 'BTC-USD'
show_indicator_goldhand_line_strategy(ticker = ticker, plot_title=tw.get_plotly_title(ticker), buy_at='gold', sell_at='blue',  add_strategy_summary=True)
```
!['GoldHand Line strategy plot'](https://github.com/misrori/goldhand/blob/main/img/goldhand_line_strategy_plot.png?raw=true  "GoldHand Line Strategy plot")



