import html
from typing import Any

def escape_telegram_html(text: str) -> str:
    """
    Escapes characters for Telegram HTML parse mode.
    Only <, >, and & are strictly required to be escaped in Telegram HTML,
    but we use html.escape which also escapes quotes.
    """
    if text is None:
        return ""
    return html.escape(str(text))

def format_telegram_deal_alert(event: Any, mode: str = "detailed") -> str:
    """
    Formats an AlertEvent into a Telegram HTML message.
    """
    product_name = escape_telegram_html(getattr(event, "product_name", None) or getattr(event, "instamart_product_id", ""))
    
    price = getattr(event, "price", 0)
    mrp = getattr(event, "mrp", 0)
    discount_percent = getattr(event, "discount_percent", 0)
    store_name = getattr(event, "store_name", None)
    store_id = getattr(event, "store_id", "")
    distance_km = getattr(event, "distance_km", None)
    trigger_reason = getattr(event, "trigger_reason", "")
    
    product_url = getattr(event, "product_url", None)
    instamart_product_id = getattr(event, "instamart_product_id", "")
    platform = getattr(event, "platform", "instamart")
    
    if not product_url:
        if platform == 'zepto':
            product_url = f"https://www.zeptonow.com/pvid/{instamart_product_id}"
        elif platform == 'blinkit':
            product_url = f"https://blinkit.com/prn/item/prid/{instamart_product_id}"
        else:
            product_url = f"https://www.swiggy.com/instamart/item/{instamart_product_id}"
            
    platform_name_display = platform.title()
    if platform_name_display.lower() == 'instamart':
        platform_name_display = "Swiggy Instamart"
        
    escaped_url = escape_telegram_html(product_url)
    pincode_display = ""
    resolved_pincode = getattr(event, "store_pincode", None) or getattr(event, "search_pincode", None)
    if resolved_pincode:
        pincode_display = f" (PIN: {escape_telegram_html(resolved_pincode)})"

    if store_name:
        escaped_store_simple = f"📍 {escape_telegram_html(store_name)}{pincode_display}"
        escaped_store_detailed = f"📍 {escape_telegram_html(store_name)}{pincode_display}"
    else:
        escaped_store_simple = f"📍 Store {escape_telegram_html(store_id)}{pincode_display}"
        escaped_store_detailed = f"🏪 Store: <code>{escape_telegram_html(store_id)}</code>{pincode_display}"

    if mode == "simple":
        lines = [
            f"🎯 <b>{product_name}</b>",
            f"💰 ₹{price:.0f} (<b>{discount_percent:.0f}% OFF</b>)",
            escaped_store_simple,
            f"<a href=\"{escaped_url}\">🛒 Open on {escape_telegram_html(platform_name_display)}</a>"
        ]
        return "\n".join(lines)

    lines = [
        "🔍 <b>WORTH-IT</b>",
        "",
        f"<b>{product_name}</b>",
        "",
    ]

    # Pricing
    if mrp and mrp > price:
        lines.append(f"💰 ₹{price:.0f}  <s>₹{mrp:.0f}</s>")
    else:
        lines.append(f"💰 ₹{price:.0f}")

    lines.append(f"🔥 <b>{discount_percent:.0f}% OFF</b>")

    if getattr(event, "is_historical_low", False):
        lines.append("📉 <b>Historical Low Price!</b>")

    previous_price = getattr(event, "previous_price", None)
    price_drop_percent = getattr(event, "price_drop_percent", None)
    if previous_price and price_drop_percent:
        lines.append(f"📊 Dropped {price_drop_percent:.1f}% from ₹{previous_price:.0f}")

    lines.append("")

    # Location
    lines.append(escaped_store_detailed)

    if distance_km is not None:
        lines.append(f"📏 {distance_km:.1f} km away")

    lines.append("")
    lines.append(f"<i>Why: {escape_telegram_html(trigger_reason)}</i>")
    lines.append("")
    lines.append(f"<a href=\"{escaped_url}\">🛒 Open on {escape_telegram_html(platform_name_display)}</a>")

    return "\n".join(lines)

def format_telegram_test_message() -> str:
    """
    Formats the test message for Telegram HTML parse mode.
    """
    lines = [
        "🎯 <b>Worth-It — Test Message</b>",
        "",
        "✅ Your Telegram integration is working correctly.",
        "",
        "You'll receive deal alerts here when qualifying prices are found."
    ]
    return "\n".join(lines)
