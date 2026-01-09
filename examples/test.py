import pandas as pd
import numpy as np
from goldhand import GoldHand, Backtest, Tw
from goldhand.strategies import (
    goldhand_line_strategy,
    rsi_strategy,
    adaptive_trend_strategy
)



# check folder

# Initialize TradingView data
tw = Tw()