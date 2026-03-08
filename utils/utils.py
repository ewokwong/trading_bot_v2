def check_exit_conditions(current_price, target_sell, stop_loss):
    if target_sell > 0 and current_price >= target_sell:
        return f"🚨 TARGET REACHED: ${target_sell}"
    if stop_loss > 0 and current_price <= stop_loss:
        return f"📉 STOP LOSS HIT: ${stop_loss}"
    return None