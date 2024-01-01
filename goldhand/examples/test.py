from goldhand import *
import pandas as pd
from tqdm import tqdm
tw =Tw()
tw.stock.head(1).T
tw.crypto.head(1).T



all_trades = []
all_trades_summaries=[]

for ticker in tqdm(tw.stock['name'][0:3]):
    try:
        data = GoldHand(ticker).df

        # backtest
        backtest = Backtest( data, rsi_strategy, plot_title=tw.get_plotly_title(ticker))

        # results of backtest
        trades = backtest.trades
        trades_summary= backtest.trades_summary

        # append results
        all_trades.append(trades)
        all_trades_summaries.append(trades_summary)

    except:
        pass


tradesdf = pd.concat(all_trades, ignore_index=True)
trades_summarydf = pd.DataFrame(all_trades_summaries)



print(tradesdf)
print(trades_summarydf)

#ticker = 'TSLA'#

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
