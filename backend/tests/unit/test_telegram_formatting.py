import pytest
from app.notifications.telegram_formatter import format_telegram_deal_alert, escape_telegram_html

class DummyAlertEvent:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_telegram_escaping():
    assert escape_telegram_html('SuperYou "Protein" Wafer Bar - Chocolate') == 'SuperYou &quot;Protein&quot; Wafer Bar - Chocolate'
    assert escape_telegram_html('Atta & Jowar') == 'Atta &amp; Jowar'
    assert escape_telegram_html('Protein > 15%') == 'Protein &gt; 15%'
    assert escape_telegram_html('Product < Large >') == 'Product &lt; Large &gt;'

def test_format_telegram_deal_alert_special_chars():
    event = DummyAlertEvent(
        product_name='SuperYou "Protein" Wafer Bar - Chocolate (Made with Atta & Jowar. No Added Sugar. No Trans Fat.) <special>',
        price=100,
        mrp=200,
        discount_percent=50,
        is_historical_low=True,
        previous_price=150,
        price_drop_percent=33.3,
        store_name='My "Special" Store & Co',
        store_id='S123',
        distance_km=1.5,
        trigger_reason='Deal detected & matched criteria',
        product_url='https://example.com/product?id=123&share=true',
        instamart_product_id='123',
        platform='zepto'
    )
    
    formatted = format_telegram_deal_alert(event)
    
    # Asserting that the reserved characters are escaped
    assert '&quot;Protein&quot;' in formatted
    assert 'Atta &amp; Jowar' in formatted
    assert '&lt;special&gt;' in formatted
    assert 'My &quot;Special&quot; Store &amp; Co' in formatted
    assert 'detected &amp; matched' in formatted
    assert 'https://example.com/product?id=123&amp;share=true' in formatted
    
    # Check that intentional html tags are not escaped
    assert '<b>WORTH-IT</b>' in formatted
    assert '<b>SuperYou' in formatted
    assert '<s>₹200</s>' in formatted
    assert '<b>50% OFF</b>' in formatted
    assert '<b>Historical Low Price!</b>' in formatted
    assert '<i>Why: ' in formatted
    assert '<a href="https://example.com/product?id=123&amp;share=true">' in formatted

def test_format_telegram_deal_alert_fallback_store_and_url():
    event = DummyAlertEvent(
        product_name='Normal Product',
        price=50,
        mrp=50,
        discount_percent=0,
        store_id='S456',
        trigger_reason='Test',
        instamart_product_id='999',
        platform='instamart'
    )
    
    formatted = format_telegram_deal_alert(event)
    assert '<code>S456</code>' in formatted
    assert 'https://www.swiggy.com/instamart/item/999' in formatted
    assert 'Swiggy Instamart' in formatted

