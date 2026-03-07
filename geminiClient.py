import os
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_trading_advice(ticker, buy_price, current_price, exit_alert):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    now_utc = datetime.now(pytz.utc)
    yesterday_date = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    now_str = now_utc.strftime('%Y-%m-%d %H:%M UTC')

    # Formatting the alert for the prompt
    exit_instruction = f"\nCRITICAL ALERT: {exit_alert}. RECOMMEND SELL." if exit_alert else ""

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
    2. If an ALERT is present, your ACTION should be SELL.

    RESPONSE FORMAT (STRICT HTML):
    <b>Ticker:</b> {ticker}
    <b>Buy Price:</b> ${buy_price:.2f}
    <b>Current Price:</b> ${current_price:.2f} (as of {now_str})

    <b>SUMMARY:</b>
    • News item 1
    • News item 2
    • News item 3

    <b>ACTION:</b> [BUY MORE / SELL / HOLD]
    <b>REASON:</b> [One sentence justification]
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