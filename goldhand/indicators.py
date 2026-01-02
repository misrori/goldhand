import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

class Indicators:
    """
    Class containing technical analysis indicators.
    """

    @staticmethod
    def smma(series: pd.Series, window: int) -> pd.Series:
        """
        Calculate Smoothed Simple Moving Average (SMMA).
        
        Parameters:
        - series: pandas Series (e.g., 'hl2' or 'close')
        - window: int, window size
        
        Return: pandas Series
        """
        smma_values = []
        # First value is just the first value of the series (or simple average of first window, 
        # but original code used first value of hl2 as starting point)
        # Original logic:
        # smma_values = [hl2[0]]
        # smma_val = (smma_values[-1] * (window - 1) + hl2[i]) / window
        
        values = series.values
        if len(values) == 0:
            return pd.Series([])
            
        smma_values.append(values[0])
        
        for i in range(1, len(values)):
            prev = smma_values[-1]
            curr = values[i]
            val = (prev * (window - 1) + curr) / window
            smma_values.append(val)
            
        return pd.Series(smma_values, index=series.index)

    @staticmethod
    def rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Parameters:
        - series: pandas Series usually 'close' prices
        - window: int, window size (default 14)
        
        Return: pandas Series
        """
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Use exponential moving average (Wilder's Smoothing) generally used for RSI
        # Note: Original code used simple rolling mean in stocks.py lines 85-86:
        # avg_gain = gain.rolling(window).mean()
        # But helpers.py used ewm (lines 32-33):
        # avg_gain = gain.ewm(alpha=1/win, min_periods=win).mean()
        # We will use EWM as it is more standard for RSI.
        
        avg_gain = gain.ewm(alpha=1/window, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1/window, min_periods=window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def bollinger_bands(series: pd.Series, window: int = 20, std_dev: int = 2):
        """
        Calculate Bollinger Bands.
        
        Returns: tuple of Series (mid, upper, lower)
        """
        mid = series.rolling(window).mean()
        std = series.rolling(window).std()
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        return mid, upper, lower

    @staticmethod
    def get_local_min_max(df: pd.DataFrame, order: int = 30) -> pd.DataFrame:
        """
        Identify local minimums and maximums.
        Adds 'local' column to the DataFrame.
        """
        df = df.copy()
        df['local'] = ''
        
        if 'high' not in df.columns or 'low' not in df.columns:
            return df

        # Find local peaks
        max_ids = list(argrelextrema(df['high'].values, np.greater, order=order)[0])
        min_ids = list(argrelextrema(df['low'].values, np.less, order=order)[0])
        
        df.iloc[min_ids, df.columns.get_loc('local')] = 'minimum'
        df.iloc[max_ids, df.columns.get_loc('local')] = 'maximum'
        
        # Filter alternating min/max logic (from original code)
        states = df[df['local']!='']['local'].index.to_list()
        
        # Simplified clean-up logic to ensure alternating Min/Max
        # Original logic was a bit complex, reusing it for consistency but cleaning structure
        problem = []
        if not states:
            return df
            
        for i in range(0, (len(states)-1)):
            if (df.loc[states[i], 'local'] != df.loc[states[i+1], 'local']):
                if (len(problem) == 0):
                    continue
                else:
                    problem.append(states[i])
                    text = df.loc[states[i], 'local']
                    if(text=='minimum'):
                        real_min = df.loc[problem, 'low'].idxmin()
                        problem.remove(real_min)
                        df.loc[problem, 'local']=''
                    else:
                        real_max = df.loc[problem, 'high'].idxmax()
                        problem.remove(real_max)
                        df.loc[problem, 'local']=''
                    problem = []
            else:
                problem.append(states[i])
                
        return df

    @staticmethod
    def add_local_text(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds 'local_text' column with annotations (rocket, price, etc.)
        Expects 'local' column to be present.
        """
        if 'local' not in df.columns:
            return df
            
        df['local_text'] = ''
        states = df[df['local']!='']['local'].index.to_list()
        
        if not states:
            return df
            
        # First element annotation
        if df.loc[states[0], 'local'] == 'minimum':
            df.loc[states[0],'local_text'] = f"${round(df.loc[states[0], 'low'], 2)}"
        else:
            df.loc[states[0],'local_text'] = f"${round(df.loc[states[0], 'high'], 2)}"

        # Iterate and add calculate changes
        for i in range(1, len(states)):
            prev_idx = states[i-1]
            curr_idx = states[i]
            
            prev_val = df.loc[prev_idx, 'low' if df.loc[prev_idx, 'local']=='minimum' else 'high'] # heuristic
            # Original code logic:
            # prev_high = df.loc[states[i-1], 'high']
            # prev_low = df.loc[states[i-1], 'low']
            
            # If current is maximum -> it was a RISE from prev (minimum)
            current_type = df.loc[curr_idx, 'local']
            
            if current_type == 'maximum':
                prev_low = df.loc[prev_idx, 'low']
                current_high = df.loc[curr_idx, 'high']
                rise = (current_high / prev_low - 1) * 100
                
                if rise > 100:
                    df.loc[curr_idx, 'local_text'] = f'🚀🌌{round(((rise+100)/100), 2)}x<br>${round(current_high, 2)}'
                else:
                    df.loc[curr_idx, 'local_text'] = f'🚀{round(rise, 2)}%<br>${round(current_high, 2)}'
            else:
                # current is minimum -> it was a FALL from prev (maximum)
                prev_high = df.loc[prev_idx, 'high']
                current_low = df.loc[curr_idx, 'low']
                fall = round((1 - (current_low / prev_high)) * 100, 2)
                
                emoji = '💸' # Default
                if fall >= 50:
                    emoji = '😭💔'
                    
                df.loc[curr_idx, 'local_text'] = f'{emoji}{fall}%<br>${round(current_low, 2)}'
                
        return df

    @staticmethod
    def ema(series: pd.Series, span: int) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        """
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def adx(df: pd.DataFrame, window: int = 14):
        """
        Calculate ADX, Plus Directional Indicator (+DI), and Minus Directional Indicator (-DI).
        
        Returns: tuple of Series (adx, plus_di, minus_di)
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window).mean()
        
        plus_di = 100 * (plus_dm.rolling(window).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window).mean()
        
        return adx, plus_di, minus_di
