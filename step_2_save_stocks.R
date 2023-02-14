library(rtsdata)
library(TTR)
source('step_1_tradingview.R')
stock_get_one_ticker  <- function(ticker, start_date = "1900-01-01", end_date = Sys.Date(),  mas=c(50, 100, 200)) {
  
  tryCatch({
    # get OLHC data
    df <- data.frame(ds.getSymbol.yahoo(ticker, from = (as.Date(start_date)-250), to =end_date ))
    names(df) <- tolower(sapply(strsplit(names(df), '.', fixed = T), '[[', 2))
    df$date <- as.Date(row.names(df))
    row.names(df) <- 1:nrow(df)
    df <- data.table(df)
    
    # check columns
    if( !identical(names(df) , c("open","high","low", "close","volume",  "adjusted","date"))) {
      text<- paste0('Error: ', ticker, ' # problem: names of dataframe is bad ', ' time: ', Sys.time())
      stop(text)
    }
  }, error=function(x) {
    stop('No ticker')
  })
  
  # ticker symbol
  df$ticker <- ticker
  
  # calculate SMA
  for (simple_mas in mas) {
    df[[paste0('ma_', simple_mas, '_value')]] <- SMA( df[['close']], simple_mas )
    df[[paste0('diff_',simple_mas,'_ma_value')]] <-  (( df[["close"]]  /df[[paste0('ma_', simple_mas, '_value')]] )-1)*100
  }
  # calculate RSI
  df$rsi <- RSI(as.numeric(df$high),n = 14)
  
  #calcualte MACD 
  mdf <- data.frame(MACD(df$close, nFast = 12, nSlow = 26, nSig = 9, maType="EMA" ))
  names(mdf) <- c('macd_fast', 'macd_slow') 
  df <- cbind(df,mdf)
  
  #calculate MACD bullish and bearish cross 
  df$macd_bulish_cross <- FALSE
  df$macd_bearish_cross <- FALSE
  df$macd_bullish <- ifelse(df$macd_fast>df$macd_slow, TRUE, FALSE)
  for (i in 35:nrow(df)) {
    if (df$macd_fast[i]>df$macd_slow[i] & df$macd_fast[(i-1)]< df$macd_slow[(i-1)]) {
      df$macd_bulish_cross[i] <- TRUE
    }
    if (df$macd_fast[i]<df$macd_slow[i] & df$macd_fast[(i-1)]> df$macd_slow[(i-1)]) {
      df$macd_bearish_cross[i] <- TRUE
    }
  }
  # calculate the number of days after bullish and bearish cross
  df$days_after_macd_bullish_cross <- 0
  t_counter <- 0
  for (i in which(df$macd_bulish_cross)[1]:nrow(df)) {
    if (df$macd_bulish_cross[i]) {
      t_counter<- 0    
    }else{
      t_counter  <- t_counter+1
      df$days_after_macd_bullish_cross[i] <- t_counter
      
    }  
  }
  df$days_after_macd_bullish_cross<- ifelse(df$macd_bullish, df$days_after_macd_bullish_cross, 0)
  df$days_after_macd_bearish_cross <- 0
  t_counter <- 0
  for (i in which(df$macd_bearish_cross)[1]:nrow(df)) {
    if (df$macd_bearish_cross[i]) {
      t_counter<- 0    
    }else{
      t_counter  <- t_counter+1
      df$days_after_macd_bearish_cross[i] <- t_counter
      
    }  
  }
  df$days_after_macd_bearish_cross<- ifelse(!df$macd_bullish, df$days_after_macd_bearish_cross, 0)
  
  # calculate Boilinger band low and high values 
  bb <-data.frame(BBands( df[,c("high","low","close")] ,n=20,sd=2))
  bb<- bb[,c('dn', 'up')]
  names(bb) <- c('bband_low', 'bband_high')
  bb$bband_diff <- bb$bband_high/bb$bband_low
  df <- cbind(df, bb)
  
  return(df)
}

# params
STOCK_FOLDER <- '/home/mihaly/R_codes/goldhand/stocks_data/'

# get all stocks
df <- get_stocks()
df <- df[!grepl(pattern = '.', x = df$name, fixed = T),]

# work with the top 10% 
topstocks <- df[1:1000,]
for (i in topstocks$name) {
  tryCatch({
    df <- stock_get_one_ticker(i)
    saveRDS(df, paste0(STOCK_FOLDER, i, '.rds'))
  },error= function(x){
    print(x)
  })
}


