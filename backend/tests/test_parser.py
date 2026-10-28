from app.services.parser import parse_message


def test_listing_roman_style():
    r = parse_message("5 marla house DHA Phase 6 Lahore, 2.5 crore")
    d = r["data"]
    assert r["kind"] == "property" and d["property_type"] == "house" and d["purpose"] == "sale"
    assert d["area_value"] == 5 and d["area_unit"] == "marla"
    assert d["price"] == 25_000_000 and d["currency"] == "PKR" and d["city"] == "Lahore"
    assert d["area_name"] == "DHA Phase 6"


def test_requirement_with_range():
    r = parse_message("Need 3 bed apartment in Bahria Town Lahore, budget 80 lakh to 1 crore")
    d = r["data"]
    assert r["kind"] == "requirement" and d["property_types"] == ["apartment"]
    assert d["bedrooms_min"] == 3 and d["preferred_areas"] == ["Bahria Town"]
    assert d["budget_min"] == 8_000_000 and d["budget_max"] == 10_000_000


def test_gulf_rent_aed():
    r = parse_message("2 bed flat Dubai Marina AED 1.2M for rent, parking, furnished")
    d = r["data"]
    assert d["purpose"] == "rent" and d["currency"] == "AED" and d["price"] == 1_200_000
    assert d["bedrooms"] == 2 and d["city"] == "Dubai" and "parking" in d["features"]


def test_rent_in_k_and_missing_info_warns():
    r = parse_message("Flat available for rent 75k")
    assert r["data"]["price"] == 75_000 and r["data"]["purpose"] == "rent"
    assert any("location" in w.lower() for w in r["warnings"])
