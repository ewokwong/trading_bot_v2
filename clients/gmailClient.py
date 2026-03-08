import os
import smtplib

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_report_email(html_content):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"📊 Morning Trading Brief: {datetime.now().strftime('%d %b %Y')}"

    full_body = f"""
    <html>
        <body style="background-color: #f4f7f6; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 20px; margin: 0;">
            <div style="max-width: 650px; margin: auto; background-color: transparent;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px;">Market Strategy Report</h2>
                {html_content}
            </div>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(full_body, 'html'))

    try:
        with smtplib.SMTP(os.getenv("EMAIL_SMTP_SERVER"), int(os.getenv("EMAIL_SMTP_PORT"))) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print("✅ Success: Formatted email sent.")
    except Exception as e:
        print(f"❌ SMTP Error: {e}")