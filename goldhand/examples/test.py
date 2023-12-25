from goldhand import *
import pandas as pd
tw =Tw()
tw.stock.head(1).T
tw.crypto.head(1).T



ticker = 'BA'

data = GoldHand(ticker).df

#backtest = Backtest( data, rsi_strategy, buy_threshold=29, sell_threshold=70)

#backtest.show_trades().show()


show_indicator_rsi_strategy('TSLA', 30,80)

#stock_ticker = "AMD"
#t = GoldHand(stock_ticker)
#p = t.plot_goldhand_line(tw.get_plotly_title(stock_ticker))
#p.update_layout(height=1080, width=1920)
#p.write_image("fig2.png")
