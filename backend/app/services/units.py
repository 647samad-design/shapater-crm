"""Area, currency and phone normalisation helpers (Pakistan + Gulf)."""
import re

from app.core.config import settings

# 1 marla = 272.25 sq ft (standard), 1 kanal = 20 marla
SQFT_PER_UNIT = {
    "sqft": 1.0,
    "sqm": 10.7639,
    "sqyd": 9.0,
    "marla": 272.25,
    "kanal": 5445.0,
}

# Static approximate rates to USD. TODO: replace with a daily exchange-rate job.
USD_RATES = {"USD": 1.0, "AED": 0.2723, "SAR": 0.2667, "PKR": 0.0036, "EUR": 1.08, "GBP": 1.27}


def to_sqft(value: float | None, unit: str | None) -> float | None:
    if value is None or not unit:
        return None
    return round(value * SQFT_PER_UNIT[unit.lower()], 2)


def to_usd(amount: float, currency: str) -> float:
    return float(amount) * USD_RATES.get(currency.upper(), 1.0)


def normalize_phone(raw: str, default_cc: str | None = None) -> str:
    """'0300-1234567' -> '+923001234567'; '+971 50 123 4567' -> '+971501234567'."""
    cc = default_cc or settings.default_phone_country_code
    digits = re.sub(r"\D", "", raw)
    if raw.strip().startswith("+"):
        return "+" + digits
    if digits.startswith("00"):
        return "+" + digits[2:]
    if digits.startswith("0"):
        return "+" + cc + digits[1:]
    return "+" + digits
