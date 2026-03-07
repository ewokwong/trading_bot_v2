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

def get_trading_advice(ticker, buy_price, current_price):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found!")

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # --- COORDINATED UTC LOGIC ---
    now_utc = datetime.now(pytz.utc)
    # Search for news from the last 24 hours
    yesterday_date = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    now_str = now_utc.strftime('%Y-%m-%d %H:%M UTC')

    prompt = f"""
    Current Time: {now_str}
    Ticker: {ticker}
    My Entry Price: {buy_price}
    Current Market Price: {current_price:.2f}
    
    INSTRUCTION: 
    Use Google Search to find news for "{ticker}" published AFTER:{yesterday_date}.
    Specifically search for: "{ticker} stock news after:{yesterday_date}" and "{ticker} earnings updates".
    
    TASK:
    1. Summarize the 3 most impactful news items from the LAST 24 HOURS (relative to {now_str}).
    2. Focus on structural changes, SEC filings, or major product launches.
    3. If no significant news exists in the last 24h, state "No major 24h updates" and check the last 7 days.

    STRATEGY:
    Long-term investor. Bias: HOLD. Sell only if the core thesis is broken.

    RESPONSE FORMAT:
    Buy Price: ${buy_price:.2f}
    Current Price: ${current_price:.2f} (as of {now_str})

    SUMMARY: [3 bullet points with dates]
    ACTION: [BUY MORE / SELL / HOLD]
    REASON: [One sentence justification]
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
        print(f"Error: {HOLDINGS_FILE} not found.")
        return

    with open(HOLDINGS_FILE, 'r') as f:
        holdings = json.load(f)

    for item in holdings:
        ticker_symbol = item['ticker']
        buy_price = float(item['buy_price'])
        
        stock = yf.Ticker(ticker_symbol)
        try:
            # yfinance close prices are typically timestamped in UTC/Exchange time
            current_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception:
            current_price = 0.0
        
        advice = get_trading_advice(ticker_symbol, buy_price, current_price)
        
        print(f"\n{advice}")
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()