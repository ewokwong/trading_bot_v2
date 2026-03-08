import json
import os
import pytz
from datetime import datetime, timedelta
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview" # While on free tier... 500 Req per day limit

def get_trading_advice_watchlist(ticker, metrics, watchlist_item):
    client = genai.Client(api_key=GEMINI_API_KEY)
    now_str = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M UTC')
    yesterday = (datetime.now(pytz.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    rules_json = json.dumps(watchlist_item['rules'], indent=2)

    prompt = f"""
    Current Time: {now_str}
    Ticker: {ticker} (Watchlist Triggered)
    
    MY STRATEGY CONDITIONS:
    {rules_json}

    CURRENT DATA POINTS:
    - Price: ${metrics['Price']:.2f}
    - RSI: {metrics['RSI']:.1f}
    - Previous Close: ${metrics['Prev_Close']:.2f}

    TASK:
    1. NEWS AUDIT: Find news for "{ticker}" from the last 24h. Categorize findings into "Material Catalysts" (Earnings, Guidance, C-Suite changes) vs. "Noise" (Routine buy-backs, generic analyst updates).
    2. CONTEXTUAL ENRICHMENT: Look at the broader sector for {ticker} (e.g., ASX Healthcare or US Software). Is the ticker moving in isolation or is the whole sector under pressure?
    3. THE RED-TEAM AUDIT: Even if my rules are MET, identify the strongest "Counter-Thesis" (the reason a professional trader would AVOID this trade right now).
    4. CLASSIFICATION: Define if this is a "Technical Dip" (Healthy pullback) or a "Fundamental Break" (Structural change in the business model).

    RESPONSE FORMAT (STRICT HTML):
    <b>🎯 Watchlist Signal: {ticker}</b>
    <b>Current Price:</b> ${metrics['Price']:.2f} (RSI: {metrics['RSI']:.1f})
    
    <b>1. STRATEGY COMPLIANCE:</b>
    [State clearly if technical rules are MET or NOT MET based on rules_json]

    <b>2. FUNDAMENTAL CONTEXT:</b>
    • <b>Key News:</b> [Most material news item from last 24h]
    • <b>Sector Sentiment:</b> [Is the sector helping or hurting this ticker right now?]

    <b>3. CRITICAL AUDIT (The "Why"):</b>
    [Explain the price action. Is it an overreaction to noise, or is there a valid reason for the RSI to be this low/high? Be specific about "Falling Knives" or "Structural Shifts".]

    <b>4. THE COUNTER-THESIS:</b>
    [One sentence on why this trade might FAIL even if the technicals look good.]

    <b>FINAL ACTION:</b> [BUY / WAIT / AVOID]
    <b>CONVICTION SCORE:</b> [1-10]
    <b>REASON:</b> [One sentence justification that balances your technical rules with the fundamental reality discovered.]
    """
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0 
    )

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
    return response.text

def get_trading_advice_holdings(ticker, buy_price, current_price, buy_datetime, exit_alert):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    now_utc = datetime.now(pytz.utc)
    yesterday_date = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')
    now_str = now_utc.strftime('%Y-%m-%d %H:%M UTC')

    # Formatting the alert for the prompt
    exit_instruction = f"\nCRITICAL ALERT: {exit_alert}. RECOMMEND SELL." if exit_alert else ""

    prompt = f"""
    Current Time: {now_str}
    Ticker: {ticker}
    My Entry Price: ${buy_price:.2f}
    Holding Duration: [Calculate days since {buy_datetime}]
    Current Market Price: ${current_price:.2f}
    Performance: [Calculate % Gain/Loss]
    {exit_instruction}
    
    INSTRUCTION: 
    1. Search for "{ticker}" news published AFTER: {yesterday_date}.
    2. Focus on "Risk Signals": Dividend cuts, CEO departures, regulatory probes, or "Structural Breaks" in the business model.
    3. Audit against the "Buy Thesis": If this is a high-growth tech stock, is growth slowing? If it's a value play, is the dividend safe?

    TASK:
    1. THESIS CHECK: Identify if any news from the last 24h directly contradicts the reason for holding this stock.
    2. PROFIT/LOSS PROTECTION: Given the current price of ${current_price:.2f} vs the Buy Price of ${buy_price:.2f}, should a "Trailing Stop" or "Take Profit" be considered based on recent volatility?
    3. THE "SLEEP TEST": Based on news sentiment, is there a reason to be anxious about holding this overnight?

    RESPONSE FORMAT (STRICT HTML):
    <b>Portfolio Status: {ticker}</b>
    <b>Entry:</b> ${buy_price:.2f} | <b>Current:</b> ${current_price:.2f} | <b>P/L:</b> [Calculated %]

    <b>🚨 CRITICAL NEWS & RISK AUDIT:</b>
    • [Material news item 1 - focus on impact]
    • [Material news item 2 - focus on impact]
    • [Market/Sector sentiment affecting this holding]

    <b>THESIS MONITOR:</b>
    [Analysis: Is the core reason for owning this stock still intact?]

    <b>FINAL ACTION:</b> [HOLD / TRIM / SELL / BUY MORE]
    <b>REASON:</b> [One sentence justification linking the news impact to your specific entry price.]
    """
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0 
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL, 
        contents=prompt,
        config=config
    )
    return response.text