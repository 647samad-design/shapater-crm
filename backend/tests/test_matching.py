from types import SimpleNamespace as NS

from app.services.matching import score_match
from app.services.units import normalize_phone, to_sqft


def prop(**kw):
    base = dict(purpose="sale", status="available", property_type="house", price=25_000_000, currency="PKR",
                city="Lahore", area_name="DHA Phase 6", bedrooms=4, features=["parking", "garden"])
    return NS(**(base | kw))


def req(**kw):
    base = dict(purpose="sale", property_types=["house"], budget_min=20_000_000, budget_max=30_000_000,
                currency="PKR", city="Lahore", preferred_areas=["DHA Phase 6"], bedrooms_min=3, bedrooms_max=5,
                required_features=["parking"])
    return NS(**(base | kw))


def test_perfect_match_scores_100():
    res = score_match(req(), prop())
    assert res["score"] == 100


def test_purpose_mismatch_is_hard_filter():
    assert score_match(req(purpose="rent"), prop()) is None


def test_sold_property_never_matches():
    assert score_match(req(), prop(status="sold")) is None


def test_over_budget_reduces_score_and_explains():
    res = score_match(req(budget_max=23_000_000), prop())  # ~8.7% over
    assert res["score"] < 100
    assert "over budget" in res["breakdown"]["budget"]["note"]


def test_cross_currency_budget():
    # AED 500k ~ PKR 37.8M at static rates -> far above a 30M PKR budget
    res = score_match(req(), prop(price=500_000, currency="AED"))
    assert res["breakdown"]["budget"]["points"] < 30


def test_missing_feature_is_explained():
    res = score_match(req(required_features=["pool"]), prop())
    assert "pool" in res["breakdown"]["features"]["note"]
    assert res["breakdown"]["features"]["points"] == 0


def test_different_area_same_city_partial():
    res = score_match(req(), prop(area_name="Gulberg"))
    assert res["breakdown"]["location"]["points"] == 10


def test_units_and_phone():
    assert to_sqft(1, "kanal") == 5445.0
    assert to_sqft(5, "marla") == 1361.25
    assert normalize_phone("0300-1234567") == "+923001234567"
    assert normalize_phone("+971 50 123 4567") == "+971501234567"
    assert normalize_phone("00971501234567") == "+971501234567"
