import json
import os
import yfinance as yf

from dotenv import load_dotenv
from geminiClient import get_trading_advice
from telegramClient import send_telegram_message

# Load env variables
load_dotenv()
HOLDINGS_FILE = "holdings.json"

def check_exit_conditions(current_price, target_sell, stop_loss):
    if target_sell > 0 and current_price >= target_sell:
        return f"🚨 TARGET REACHED: ${target_sell}"
    if stop_loss > 0 and current_price <= stop_loss:
        return f"📉 STOP LOSS HIT: ${stop_loss}"
    return None


def main():
    if not os.path.exists(HOLDINGS_FILE):
        print(f"File {HOLDINGS_FILE} not found.")
        return

    with open(HOLDINGS_FILE, 'r') as f:
        holdings = json.load(f)

    for item in holdings:
        ticker = item['ticker']
        buy_price = float(item['buy_price'])
        target_sell = float(item.get('target_sell_price', 0))
        stop_loss = float(item.get('stop_loss_price', 0))
        
        print(f"Processing {ticker}...")
        stock = yf.Ticker(ticker)
        try:
            current_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            continue
        
        exit_alert = check_exit_conditions(current_price, target_sell, stop_loss)
        advice = get_trading_advice(ticker, buy_price, current_price, exit_alert)
        
        # Build final message with a header
        header = f"🚀 <b>TRADING UPDATE: {ticker}</b>\n"
        if exit_alert:
            header = f"⚠️ <b>EXIT SIGNAL: {ticker}</b>\n"
            
        full_message = f"{header}\n{advice}"
        send_telegram_message(full_message)

if __name__ == "__main__":
    main()