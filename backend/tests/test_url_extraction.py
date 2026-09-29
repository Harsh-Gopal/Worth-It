import pytest
from app.links import extract_canonical_url

def test_url_extraction():
    uid = "7851f4a9-cab6-4b75-bae2-bcbc43bf0bdb"
    
    # Valid
    assert extract_canonical_url(f"https://www.zepto.com/pn/foo/pvid/{uid}")[1] == f"https://www.zeptonow.com/pn/product/pvid/{uid}"
    assert extract_canonical_url(f"Check out this product on Zepto!\nhttps://www.zepto.com/pn/foo/pvid/{uid}")[1] == f"https://www.zeptonow.com/pn/product/pvid/{uid}"
    assert extract_canonical_url(f"https://www.zepto.com/pn/foo/pvid/{uid}\nCheck out this product on Zepto!")[1] == f"https://www.zeptonow.com/pn/product/pvid/{uid}"
    assert extract_canonical_url("Check this out: https://www.blinkit.com/prn/foo/prid/123")[1] == "https://blinkit.com/prn/product/prid/123"
    assert extract_canonical_url("Check this out:\nhttps://www.swiggy.com/instamart/item/123456")[1] == "https://www.swiggy.com/instamart/item/123456"
    assert extract_canonical_url(f"   https://www.zepto.com/pn/foo/pvid/{uid}   ")[1] == f"https://www.zeptonow.com/pn/product/pvid/{uid}"
    assert extract_canonical_url(f"https://www.zepto.com/pn/foo/pvid/{uid}.")[1] == f"https://www.zeptonow.com/pn/product/pvid/{uid}"
    
    # Invalid
    assert extract_canonical_url("random text") == (None, None, "URL_EXTRACTION_FAILED")
    assert extract_canonical_url("https://amazon.in/foo") == (None, None, "UNSUPPORTED_PLATFORM")
    
    # Ambiguity
    assert extract_canonical_url(f"https://www.zepto.com/pn/foo/pvid/{uid} \n https://www.swiggy.com/instamart/item/123456")[2] == "AMBIGUOUS_URLS"
