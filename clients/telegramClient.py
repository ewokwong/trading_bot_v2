import os
import requests

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram credentials missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    MAX_LENGTH = 4000
    
    # Split message into chunks
    chunks = [message[i:i + MAX_LENGTH] for i in range(0, len(message), MAX_LENGTH)]
    
    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML" 
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Telegram Sent: {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to send Telegram: {e}")