import json
import os
import pytz
from datetime import datetime, timedelta
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview" # While on free tier... 500 Req per day limit

def prepare_telegram_summary(report_text):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    formatted_date = datetime.now().strftime('%d %b %Y')

    prompt = f"""
    CONTEXT: High-frequency trading desk dispatcher.
    INPUT: {report_text}
    
    TASK: Generate a concise, high-density Telegram alert in HTML. 
    
    STARTING HEADER:
    <b>Morning Trading Brief: {formatted_date}</b>
    — — — — — — — — — —

    ORGANIZATION:
    Organize the output into three distinct sections (after the header): 
    1. 📂 <b>PORTFOLIO STATUS</b>
    2. 🎯 <b>WATCHLIST SIGNALS</b>
    3. 🚨 <b>NEWS SIGNALS</b>
    STRUCTURE FOR EACH TICKER:
    <b>$TICKER</b> | EMOJI <b>ACTION</b>
    <code>Context:</code> [Price/RSI/PL%]
    <code>Strategy:</code> [Key catalyst/risk fragment]
    — — — — — — — — — —

    GUIDELINES:
    1. EMOJIS: 📈 BUY | 🛑 AVOID | ⏳ WAIT/HOLD.
    2. SECTIONING: If a section is empty in the input, omit the header entirely.
    3. BREVITY: Use technical fragments. No filler text or conversational intros.
    4. NO SUMMARY: Start immediately with the first header.
    
    LIMIT: Strictly under 4000 characters.
    """

    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=2048 
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config
    )
    
    if not response or not response.text:
        print("⚠️ Warning: AI returned an empty response or was blocked by filters.")
        return []
    
    return response.text.strip()

def get_trading_advice_news(ticker, metrics, news_item):
    client = genai.Client(api_key=GEMINI_API_KEY)
    now_str = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    prompt = f"""
    Current Time: {now_str}
    Ticker: {ticker}
    Incoming News: {news_item}
    
    CURRENT METRICS:
    - Price: ${metrics['Price']:.2f}
    - RSI: {metrics['RSI']:.1f}
    - Previous Close: ${metrics['Prev_Close']:.2f}

    TASK:
    1. NEWS AUDIT: Analyze the incoming news for "{ticker}". Is this a "Material Catalyst" (Earnings, Guidance, M&A) or "Noise" (Analyst price target tweaks, general macro sentiment)?
    2. CONTEXTUAL ENRICHMENT: Check if the broader sector for {ticker} is currently under pressure. Is this ticker moving in isolation?
    3. THE RED-TEAM AUDIT: Identify the strongest "Counter-Thesis"—the reason a professional would NOT trade this news.
    4. CLASSIFICATION: Define if this is a "Technical Dip" (Healthy pullback) or a "Fundamental Break" (Structural change).

    RESPONSE FORMAT (STRICT HTML):
    <b>🗞️ News Analysis: {ticker}</b>
    <b>Current Price:</b> ${metrics['Price']:.2f} (RSI: {metrics['RSI']:.1f})
    
    <b>1. CATALYST EVALUATION:</b>
    [Classify as MATERIAL or NOISE and explain why in one sentence.]

    <b>2. SECTOR SENTIMENT:</b>
    [Briefly describe if the sector is helping or hurting the ticker.]

    <b>3. RED-TEAM AUDIT (Counter-Thesis):</b>
    [Identify one major risk that makes this news/trade dangerous.]

    <b>4. CLASSIFICATION:</b> [Technical Dip / Fundamental Break]

    <b>FINAL ACTION:</b> [BUY / WAIT / AVOID]
    <b>REASON:</b> [One sentence justification.]
    """
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0 
    )

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
    return response.text

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

def identify_anxious_selloffs(lookback_hours=48):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    now_utc = datetime.now(pytz.utc)
    start_time = (now_utc - timedelta(hours=lookback_hours)).strftime('%Y-%m-%d %H:%M')
    
    prompt = f"""
    Current Time: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC
    Analysis Window: {lookback_hours}h 
    SCOPE: Global Large-Cap ($10B+) | All Industries

    TASK:
    1. IDENTIFY OUTLIERS: Scan for Blue Chip stocks with the most extreme 5-day drawdowns (e.g., >10%) or deeply oversold RSI levels (RSI < 30). Prioritize the "Biggest Losers" in the current window.

    2. QUANTIFY THE OVERREACTION: For each identified stock, determine if the sell-off is an "Anxious Overreaction." 
    - Is the drop caused by macro noise (interest rates, geopolitical rumors, or sector-wide contagion)?
    - Is there a "Dislocation" where the stock price has fallen significantly further than its peers or its actual earnings impact?

    3. MOAT & STRUCTURAL NECESSITY: Filter for "Economic Linchpins." 
    - Could the economy function normally without them? (e.g., ASML for lithography, CBA for AU liquidity, UNH for US healthcare).
    - High Priority: If the company is an "Economic Necessity" but is being sold off like a speculative asset.

    4. SECTOR DIVERSITY: Provide 5 stocks across different industries to ensure a diversified "Recovery" watchlist.

    FORMATTING RULES:
    - ASX: Append '.AX' | Global: Use standard Tickers.
    - Format: Return a raw JSON array of objects such that the response can be returned via json.loads(response.text) 
    - No Prose: Do not include introductory text, markdown formatting (no ```json), or follow-up commentary.Make sure the response can be returned via return json.loads(response.text)
    
    RESPONSE FORMAT (JSON ARRAY ONLY):
    [
    {{
        "ticker": "TKR",
        "industry": "Industry Name",
        "rsi_level": "XX",
        "drawdown_5d": "X%",
        "overreaction_evidence": "Specific reason why the market has 'punished' this stock too severely relative to its moat.",
        "moat_logic": "Explain why this firm is a structural necessity for the economy.",
        "recovery_catalyst": "What event (e.g., upcoming CPI data, earnings correction) will trigger the reversal?"
    }}
    ]
    """


    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0,
        response_mime_type="application/json"
    )

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
    return json.loads(response.text)