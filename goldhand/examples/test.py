from goldhand import *
import pandas as pd
from tqdm import tqdm
tw =Tw()
tw.stock.head(1).T
tw.crypto.head(1).T


#show_indicator_rsi_strategy(ticker = 'TSLA', buy_threshold = 30, sell_threshold= 80, plot_title=tw.get_plotly_title('TSLA'), ndays=800).show()


ticker = 'TSLA'
tw.get_sec_plot(ticker)

#t = GoldHand(ticker)
#p = t.plot_goldhand_line(plot_title=tw.get_plotly_title(ticker), ndays=800, plot_height=1000, ad_local_min_max=False)
#p.show()#

#p = t.plotly_last_year(plot_title=tw.get_plotly_title(ticker), ndays=800, plot_height=1000, ad_local_min_max=False)
#p.show()#
#
#
#

#ticker = 'GE'#

#t = GoldHand(ticker)
#p = t.plot_goldhand_line(plot_title=tw.get_plotly_title(ticker), ndays=800, plot_height=1000, ad_local_min_max=True)
#p.show()#

#p = t.plotly_last_year(plot_title=tw.get_plotly_title(ticker), ndays=800, plot_height=1000, ad_local_min_max=True)
#p.show()



#backtest = Backtest( data, rsi_strategy, buy_threshold=29, sell_threshold=70)

#backtest.show_trades().show()


#ticker= 'COIN'
#p = show_indicator_goldhand_line_strategy(ticker, plot_title=tw.get_plotly_title(ticker), ndays=700, plot_height=1000)
#p.show()

#stock_ticker = "AMD"
#t = GoldHand(stock_ticker)
#p = t.plot_goldhand_line(tw.get_plotly_title(stock_ticker))
#p.update_layout(height=1080, width=1920)
#p.write_image("fig2.png")
