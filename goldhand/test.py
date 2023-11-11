from tw import *
from stocks import *

tw =Tw()
stock_ticker = "AMD"
t = GoldHand(stock_ticker)
p = t.plotly_last_year(tw.get_plotly_title(stock_ticker))
p.update_layout(height=1080, width=1920)
p.write_image("fig2.png", )

