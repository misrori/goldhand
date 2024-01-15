
from re import A
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json


class Tw:
    def __init__(self):
        """ 
        Get all stock, crypto and ETF data from TradingView
        """
        self.stock = pd.DataFrame()
        self.crypto = pd.DataFrame()
        self.etf = pd.DataFrame()
        
        self.get_all_stock()
        self.get_all_crypto()
        self.get_all_etf()

    def get_all_stock(self):
        """ 
        Get all stocks data from TradingView
        """
        
        data_query = '{"filter":[{"left":"type","operation":"in_range","right":["stock","dr","fund"]},{"left":"subtype","operation":"in_range","right":["common","foreign-issuer","","etf","etf,odd","etf,otc","etf,cfd"]},{"left":"exchange","operation":"in_range","right":["AMEX","NASDAQ","NYSE"]},{"left":"is_primary","operation":"equal","right":true},{"left":"active_symbol","operation":"equal","right":true}],"options":{"lang":"en"},"markets":["america"],"symbols":{"query":{"types":[]},"tickers":[]},"columns":["logoid","name","close","change","change_abs","Recommend.All","volume","Value.Traded","market_cap_basic","price_earnings_ttm","earnings_per_share_basic_ttm","number_of_employees","sector","High.3M","Low.3M","Perf.3M","Perf.5Y","High.1M","Low.1M","High.6M","Low.6M","Perf.6M","beta_1_year","price_52_week_high","price_52_week_low","High.All","Low.All","BB.lower","BB.upper","change|1M","change_abs|1M","change|1W","change_abs|1W","change|240","country","EMA50","EMA100","EMA200","MACD.macd","MACD.signal","Mom","Perf.1M","RSI7","SMA50","SMA100","SMA200","Stoch.RSI.K","Stoch.RSI.D","Perf.W","Perf.Y","Perf.YTD","industry","Perf.All","description","type","subtype","update_mode","pricescale","minmov","fractional","minmove2","Mom[1]","RSI7[1]","Rec.Stoch.RSI","currency","fundamental_currency_code"],"sort":{"sortBy":"market_cap_basic","sortOrder":"desc"},"range":[0,8000]}'
        response = requests.post('https://scanner.tradingview.com/america/scan', data=data_query)
        data = response.json()
        list_elements = list(map(lambda x:x['d'], data['data'] ))
        self.stock = pd.DataFrame(list_elements)
        self.stock.columns = json.loads(data_query)['columns']
        self.stock = self.stock[self.stock['name'].str.contains('\\.')!=True]


    def get_all_crypto(self):
        """
        Get all crypto data from TradingView       
        """

        data_query = '{"columns":["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","close","pricescale","minmov","fractional","minmove2","currency","24h_close_change|5","market_cap_calc","fundamental_currency_code","24h_vol_cmc","circulating_supply","crypto_common_categories","crypto_blockchain_ecosystems"],"ignore_unknown_fields":false,"options":{"lang":"en"},"range":[0,300],"sort":{"sortBy":"crypto_total_rank","sortOrder":"asc"},"markets":["coin"]}'
        response = requests.post('https://scanner.tradingview.com/coin/scan', data=data_query)
        data = response.json()
        list_elements = list(map(lambda x:x['d'], data['data'] ))
        self.crypto = pd.DataFrame(list_elements)
        self.crypto.columns = json.loads(data_query)['columns']
        filter = list(map(lambda x: 'stablecoins' not in x, self.crypto['crypto_common_categories'].fillna('-') ))
        self.crypto = self.crypto.loc[filter, ]
        self.crypto['ticker'] = self.crypto['base_currency'] + '-USD'

    def get_all_etf(self):
        """
        Get all ETFs from TradingView
        """
        data_query = '{"columns":["name","description","logoid","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","Value.Traded","relative_volume_10d_calc","aum","fundamental_currency_code","nav_total_return.5Y","expense_ratio","asset_class.tr","focus.tr","nav_discount_premium","category.tr","brand.tr","niche.tr"],"ignore_unknown_fields":false,"options":{"lang":"en"},"price_conversion":{"to_symbol":true},"range":[0,3000],"sort":{"sortBy":"aum","sortOrder":"desc"},"markets":["america"],"filter2":{"operator":"and","operands":[{"operation":{"operator":"or","operands":[{"operation":{"operator":"and","operands":[{"expression":{"left":"typespecs","operation":"has","right":["etn"]}}]}},{"operation":{"operator":"and","operands":[{"expression":{"left":"typespecs","operation":"has","right":["etf"]}}]}}]}}]}}'
        response = requests.post('https://scanner.tradingview.com/america/scan', data=data_query)
        data = response.json()
        list_elements = list(map(lambda x:x['d'], data['data'] ))
        self.etf = pd.DataFrame(list_elements)
        self.etf.columns = json.loads(data_query)['columns']
        self.etf = self.etf[self.etf['name'].str.contains('\\.')!=True]
    
    
    def moneystring( self, money):
        """
        Convert money to string with unit
        Parameters:
        - money: money to convert
        Return: string with unit
        """

        if money > 1_000_000_000_000:
            money_str = f"{round(money / 1_000_000_000_000, 2)} Trillion" 
        elif money>1_000_000_000:
            money_str = f"{round(money / 1_000_000_000, 2)} Billion"
        else:
            money_str = f"{round(money / 1_000_000, 2)} Million"
        return money_str


    def get_one_stock_info(self, ticker):
        """
        Get info about one stock
        Parameters: 
        - ticker: ticker of the stock
        Return: type dictioanry
        """

        ticker = ticker.upper()
        one_row = self.stock.loc[self.stock['name']==ticker,].iloc[0]
        tsec = self.stock.loc[self.stock['sector']==one_row['sector']].reset_index(drop=True)
        tind = self.stock.loc[self.stock['industry']== one_row['industry']].reset_index(drop=True)
        return({'ticker': one_row['name'],
                'price': one_row['close'],
                'market_cap': one_row['market_cap_basic'] ,
                'n_emp': one_row['number_of_employees'],
                'market_cap_text': self.moneystring(one_row['market_cap_basic']),
                'name': one_row['description'],
                'sector': one_row['sector'],
                'industry': one_row['industry'],
                'sec_loc': f"{tsec.index[tsec['name']==ticker].to_list()[0] +1  }/{tsec.shape[0]}",
                'ind_loc': f"{tind.index[tind['name']==ticker].to_list()[0] +1 }/{tind.shape[0]}",
                'performance': f"Performance|week:{round(one_row['Perf.W'], 2)}% | month:{round(one_row['Perf.1M'], 2)}% | 6 months:{round(one_row['Perf.6M'], 2)}% | year:{round(one_row['Perf.Y'], 2)}% |"
                })
        
        
    def get_top_n_stocks_by_sector(self,percent=10):
        """
        Get top n % stocks by sector
        Parameters: 
        - percent: percent of stocks to return
        Return: Pandas DataFrame
        """

        return ( 
                self.stock.groupby('sector')
                 .apply(lambda x: x.nlargest(int(len(x) * round((percent/100),2) ), 'market_cap_basic'))
                 .reset_index(drop=True)
                
            )
        

    def get_plotly_title(self, ticker):
        """
        Get plotly title for stock or crypto
        Parameters: 
        - ticker: ticker of the stock
        Return: Summary of the stock or crypto to be used as plotly title
        """

        if '-USD' in ticker:
            # crypto
            coin = self.crypto.loc[self.crypto['ticker']==ticker].iloc[0]
            plotly_title = f"{coin['base_currency_desc']} ({coin['base_currency']})<br>💲{self.moneystring(coin['market_cap_calc'])} | {', '.join(coin['crypto_common_categories'])}"
        
        elif ticker in self.etf['name'].tolist() :
            # ETF
            t = self.etf.loc[self.etf['name']==ticker].iloc[0]
            plotly_title = f"{t['description']} ({t['name']}) | 💲{round(t['close'], 2)} <br>AUM:💲{self.moneystring(t['aum'])} | {t['focus.tr']}  | Expense ratio {t['expense_ratio']}"
        else:
            # stock
            t = self.get_one_stock_info(ticker)
            plotly_title = f"{t['name']} ({t['ticker']}) | 💲{round(t['price'], 2)} | {t['sector']} | {t['industry']} <br>💲{t['market_cap_text']} | 👨‍💼 {round(t['n_emp']):,} <br>Sector location: {t['sec_loc']} | Industry location: {t['ind_loc']}"
        return(plotly_title)


    def get_sec_plot(self, ticker):
        """
        Get plotly figure for a ticker showing the sector location of the stock 
        Parameters: 
        - ticker: ticker of the stock
        Return: plotly figure showing the sector location of the stock
        """

        if ticker in self.etf['name'].tolist():
            return f"{ticker} is ETF use get_etf_plot"
        row_df = self.stock.loc[self.stock['name']==ticker]
        row_df.rename(columns = {'description': 'Company'}, inplace=True)
        secdf = self.stock.loc[ (self.stock['sector'] ==row_df['sector'].iloc[0] ) ].reset_index(drop=True)
        secdf.rename(columns = {'description': 'Company'}, inplace=True)
        fig = px.bar(secdf, x='name', y='market_cap_basic', title = f"{row_df['Company'].iloc[0]} ({row_df['name'].iloc[0]})<br>{row_df['sector'].iloc[0]} | {row_df['industry'].iloc[0]}", labels={'market_cap_basic':'Market kapitalization'}, text='Company')
        fig = px.bar(secdf, x='name', y='market_cap_basic', title = self.get_plotly_title(ticker), labels={'market_cap_basic':'Market Capitalization'}, text='Company')
        fig.add_annotation( x=row_df['name'].iloc[0], y=row_df['market_cap_basic'].iloc[0], text= f"{self.moneystring(row_df['market_cap_basic'].iloc[0])}",  showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=65,ay=-45)
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=600)
        return (fig)


    def get_ind_plot(self, ticker):
        """
        Get plotly figure for a ticker showing the industry location of the stock
        Parameters: 
        - ticker: ticker of the stock
        Return: plotly figure showing the industry location of the stock
        """

        if ticker in self.etf['name'].tolist():
            return f"{ticker} is ETF use get_etf_plot"
        row_df = self.stock.loc[self.stock['name']==ticker]
        inddf = self.stock.loc[ (self.stock['industry'] ==row_df['industry'].iloc[0] ) ].reset_index(drop=True)
        row_df.rename(columns = {'description': 'Company'}, inplace=True)
        inddf.rename(columns = {'description': 'Company'}, inplace=True)
        fig = px.bar(inddf, x='name', y='market_cap_basic', title = self.get_plotly_title(ticker), labels={'market_cap_basic':'Market Capitalization'}, text='Company')
        fig.add_annotation( x=row_df['name'].iloc[0], y=row_df['market_cap_basic'].iloc[0], text= f"{self.moneystring(row_df['market_cap_basic'].iloc[0])}",  showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=65,ay=-45)
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=600)
        return (fig)


    def get_etf_plot(self, ticker):
        """
        Get plotly figure for a ETF showing the ETF location with the same focus
        Parameters:
        - ticker: ticker of the ETF
        Return: plotly figure showing the ETF location with the same focus
        
        """
        row_df = self.etf.loc[self.etf['name']==ticker]
        focdf = self.etf.loc[ (self.etf['focus.tr'] ==row_df['focus.tr'].iloc[0] ) ].reset_index(drop=True)
        fig = px.bar(focdf, x='name', y='aum', title = self.get_plotly_title(ticker), labels={'aum':'Assets Under Management'}, text='description')
        fig.add_annotation( x=row_df['name'].iloc[0], y=row_df['aum'].iloc[0], text= f"{self.moneystring(row_df['aum'].iloc[0])}",  showarrow=True, align="center", bordercolor="#c7c7c7", font=dict(family="Courier New, monospace", size=16, color="#214e34" ), borderwidth=2, borderpad=4, bgcolor="#f4fdff", opacity=0.8, arrowhead=2, arrowsize=1, arrowwidth=1, ax=65,ay=-45)
        fig.update_layout(showlegend=False, plot_bgcolor='white', height=600)
        return (fig)
        



#tw = Tw()
#print(tw.stock.head(1).T)
#print(tw.crypto.head(1).T)
