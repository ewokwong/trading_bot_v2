import os
import requests

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram credentials missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" 
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"✅ Telegram Sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send Telegram: {e}")
        if 'response' in locals():
            print(f"Error Details: {response.text}")