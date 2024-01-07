from goldhand import *
import pandas as pd
from tqdm import tqdm
tw =Tw()



ticker = 'TSLA'

data = GoldHand(ticker).df

backtest = Backtest( data, goldhand_line_strategy, buy_at='gold', sell_at='grey')

backtest.show_trades().show()

p = show_indicator_goldhand_line_strategy(ticker, plot_title=tw.get_plotly_title(ticker), ndays=700, plot_height=1000,  buy_at='gold', sell_at='grey', add_strategy_summary=True)
p.show()



#show_indicator_rsi_strategy(ticker = 'TSLA', buy_threshold = 30, sell_threshold= 80, plot_title=tw.get_plotly_title('TSLA'), ndays=800).show()




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

#backtest.show_trades()

#p = show_indicator_rsi_strategy(ticker, plot_title=tw.get_plotly_title(ticker), ndays=700, plot_height=1000, buy_threshold=25, sell_threshold=80, add_strategy_summary=True)
#p.show()



#stock_ticker = "AMD"
#t = GoldHand(stock_ticker)
#p = t.plot_goldhand_line(tw.get_plotly_title(stock_ticker))
#p.update_layout(height=1080, width=1920)
#p.write_image("fig2.png")
