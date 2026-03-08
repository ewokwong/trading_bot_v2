import json
import os
import pytz
import time

from clients.geminiClient import get_trading_advice_holdings, get_trading_advice_watchlist
from clients.telegramClient import send_telegram_message
from datetime import datetime
from dotenv import load_dotenv
from utils.utils import check_exit_conditions
from utils.yfinanceUtils import get_stock_info, get_market_metrics

# Load env variables
load_dotenv()
HOLDINGS_FILE = "data/holdings.json"
WATCHLIST = "data/watchlist.json"

def main():
    # # ------- HOLDINGS ------- #
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
        buy_datetime = datetime.fromisoformat(item["buy_datetime"]).astimezone(pytz.utc)
        
        stock = get_stock_info(ticker)
        
        try:
            current_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            continue
        
        exit_alert = check_exit_conditions(current_price, target_sell, stop_loss)
        advice = get_trading_advice_holdings(ticker, buy_price, current_price, buy_datetime, exit_alert)
        
        # Build final message with a header
        header = f"🚀 <b>TRADING UPDATE: {ticker}</b>\n"
        if exit_alert:
            header = f"⚠️ <b>EXIT SIGNAL: {ticker}</b>\n"
            
        full_message = f"{header}\n{advice}"
        send_telegram_message(full_message)
    
    # ------- WATCHLIST ------- #
    if not os.path.exists(WATCHLIST):
        print(f"File {WATCHLIST} not found.")
        return

    with open(WATCHLIST, 'r') as f:
        watchlist = json.load(f)

    for i, item in enumerate(watchlist):
        if i > 0:
            time.sleep(10) 

        ticker = item['ticker']
        print(f"Checking Watchlist: {ticker}...")
        
        metrics = get_market_metrics(ticker)
        advice = get_trading_advice_watchlist(ticker, metrics, item)
        
        full_report = f"🎯 <b>WATCHLIST ENTRY SIGNAL: {ticker}</b>\n{advice}"
        send_telegram_message(full_report)

if __name__ == "__main__":
    main()