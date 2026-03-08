import numpy as np
import yfinance as yf


def get_stock_info(ticker): return yf.Ticker(ticker)

# Following TradingView RSI Divergence Indicator Source Code
def calculate_rsi(df):
    close = df['Close']
    delta = close.diff()
    
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    length = 14
    avg_gain = np.full(len(df), np.nan)
    avg_loss = np.full(len(df), np.nan)
    
    # 1. The first calculation is an SMA (Simple Moving Average)
    # Note: index length represents the 15th element (0-indexed)
    avg_gain[length] = gain.iloc[1:length+1].mean()
    avg_loss[length] = loss.iloc[1:length+1].mean()
    
    # 2. Subsequent values use the RMA recursive formula
    for i in range(length + 1, len(df)):
        avg_gain[i] = (avg_gain[i-1] * (length - 1) + gain.iloc[i]) / length
        avg_loss[i] = (avg_loss[i-1] * (length - 1) + loss.iloc[i]) / length
    
    # 3. Calculate RSI with zero-loss handling
    # Handle division by zero: if avg_loss is 0, RSI is 100
    with np.errstate(divide='ignore', invalid='ignore'):
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = np.where(avg_loss == 0, 100, rsi)
        rsi = np.where(avg_gain == 0, 0, rsi)
    
    return round(rsi[-1], 2)

def get_market_metrics(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y") 
    
    if len(df) < 15:
        return None

    close = df['Close']
    return {
        "Ticker": ticker,
        "Price": close.iloc[-1],
        "RSI": calculate_rsi(df),
        "Prev_Close": close.iloc[-2]
    }