import json
import os
import pytz
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HOLDINGS_FILE = "holdings.json"

def check_exit_conditions(current_price, target_sell, stop_loss):
    """Returns a specific instruction if price targets are met."""
    if target_sell > 0 and current_price >= target_sell:
        return f"CRITICAL: Target Sell Price of ${target_sell} reached/exceeded."
    if stop_loss > 0 and current_price <= stop_loss:
        return f"CRITICAL: Stop Loss of ${stop_loss} triggered."
    return None

def get_trading_advice(ticker, buy_price, current_price, exit_alert):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    now_utc = datetime.now(pytz.utc)
    yesterday_date = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    now_str = now_utc.strftime('%Y-%m-%d %H:%M UTC')

    # If an alert exists, we force the AI to prioritize the SELL action
    exit_instruction = f"\nALERT: {exit_alert}. EVALUATE FOR IMMEDIATE SELL." if exit_alert else ""

    prompt = f"""
    Current Time: {now_str}
    Ticker: {ticker}
    My Entry Price: {buy_price}
    Current Market Price: {current_price:.2f}
    {exit_instruction}
    
    INSTRUCTION: 
    Use Google Search to find news for "{ticker}" published AFTER:{yesterday_date}.
    
    TASK:
    1. Summarize 3 impactful news items from the LAST 24 HOURS.
    2. If "{exit_alert}" is present, your ACTION should likely be SELL unless news suggests further massive upside.

    RESPONSE FORMAT:
    Buy Price: ${buy_price:.2f}
    Current Price: ${current_price:.2f} (as of {now_str})
    SUMMARY: [3 bullet points]
    ACTION: [BUY MORE / SELL / HOLD]
    REASON: [Justification]
    """
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0 
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt,
        config=config
    )
    return response.text

def main():
    if not os.path.exists(HOLDINGS_FILE):
        return

    with open(HOLDINGS_FILE, 'r') as f:
        holdings = json.load(f)

    for item in holdings:
        ticker = item['ticker']
        buy_price = float(item['buy_price'])
        target_sell = float(item.get('target_sell_price', 0))
        stop_loss = float(item.get('stop_loss_price', 0))
        
        stock = yf.Ticker(ticker)
        try:
            current_price = stock.history(period="1d")['Close'].iloc[-1]
        except:
            continue
        
        exit_alert = check_exit_conditions(current_price, target_sell, stop_loss)
        advice = get_trading_advice(ticker, buy_price, current_price, exit_alert)
        
        print(f"\n{advice}\n{'='*60}")

if __name__ == "__main__":
    main()