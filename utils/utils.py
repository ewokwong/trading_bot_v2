from datetime import datetime

def check_exit_conditions(current_price, target_sell, stop_loss):
    if target_sell > 0 and current_price >= target_sell:
        return f"🚨 TARGET REACHED: ${target_sell}"
    if stop_loss > 0 and current_price <= stop_loss:
        return f"📉 STOP LOSS HIT: ${stop_loss}"
    return None

def generate_trading_email(report):
    """
    Converts a trading report dictionary into a formatted HTML email body.
    Expects keys: 'holdings', 'watchlist', 'news', 'final_action', 'conviction', 'reason'
    """
    
    def format_section(title, data, color):
        if not data:
            return ""
        items_html = ""
        for item in data:
            formatted_item = item.replace("\n", "<br>")
            items_html += f"""
            <div style="border-left: 4px solid {color}; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9; border-radius: 4px;">
                <div style="font-size: 14px; color: #333;">{formatted_item}</div>
            </div>
            """
        return f"""
        <h2 style="color: {color}; border-bottom: 2px solid {color}; padding-bottom: 5px; font-size: 20px;">{title}</h2>
        {items_html}
        """

    # --- NEW: Action Box Formatter ---
    def format_action_box(action, conviction, reason):
        if not action: return ""
        # Determine color based on action
        status_color = "#c0392b" if "SELL" in action.upper() else "#27ae60" if "BUY" in action.upper() else "#2c3e50"
        
        return f"""
        <div style="background-color: #ebf5fb; border: 2px solid {status_color}; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h2 style="margin-top: 0; color: {status_color}; text-transform: uppercase; letter-spacing: 1px;">{action}</h2>
            <div style="display: flex; justify-content: center; gap: 20px; margin-bottom: 10px;">
                <span style="font-weight: bold; font-size: 16px;">Conviction: <span style="color: {status_color};">{conviction}</span></span>
            </div>
            <p style="font-style: italic; color: #555; margin: 10px 0 0 0; font-size: 15px;"><strong>Reasoning:</strong> {reason}</p>
        </div>
        """

    # Extract data
    holdings = report.get("holdings", [])
    watchlist = report.get("watchlist", [])
    news_signals = report.get("news", [])
    
    # Extract Action Data
    final_action = report.get("final_action", "NO ACTION")
    conviction = report.get("conviction", "N/A")
    reason = report.get("reason", "No specific catalyst identified.")

    html_start = """
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: auto; padding: 20px;">
        <h1 style="text-align: center; color: #2c3e50; margin-bottom: 5px;">Daily Portfolio & Market Audit</h1>
        <p style="text-align: center; font-size: 14px; color: #7f8c8d; margin-top: 0;">Automated Trading Intelligence Report</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
    """
    
    # Generate Components
    action_box_html = format_action_box(final_action, conviction, reason)
    holdings_html = format_section("Portfolio Holdings", holdings, "#2980b9")
    watchlist_html = format_section("Watchlist Analysis", watchlist, "#27ae60")
    news_html = format_section("Global News Signals", news_signals, "#e67e22")
    
    html_end = """
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #95a5a6; text-align: center;">
            <strong>Disclaimer:</strong> This is an automated algorithmic summary. 
            Verification of RSI and News Catalysts is recommended before execution.
        </footer>
    </body>
    </html>
    """

    return html_start + action_box_html + holdings_html + watchlist_html + news_html + html_end