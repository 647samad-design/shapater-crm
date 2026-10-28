"""Rule-based parser: WhatsApp-style text -> property listing or client requirement draft.

Handles Roman-Urdu/English messages like:
  "5 marla house DHA Phase 6 Lahore, 2.5 crore"
  "Need 3 bed apartment in Bahria Town, budget 80 lakh to 1 crore"
  "2 bed flat Dubai Marina AED 1.2M for rent"
Pluggable: an LLM-based parser can implement the same output shape later.
"""
import re

UNIT_MULT = {"crore": 1e7, "cr": 1e7, "lakh": 1e5, "lac": 1e5, "lacs": 1e5, "lakhs": 1e5,
             "million": 1e6, "mn": 1e6, "m": 1e6, "k": 1e3, "thousand": 1e3}
TYPES = {"house": "house", "home": "house", "kothi": "house", "bungalow": "house", "villa": "villa",
         "apartment": "apartment", "flat": "apartment", "studio": "apartment", "plot": "plot", "land": "plot",
         "shop": "shop", "office": "office", "penthouse": "penthouse", "townhouse": "townhouse",
         "portion": "portion", "upper portion": "portion", "lower portion": "portion"}
FEATURES = ["parking", "garden", "pool", "furnished", "balcony", "gym", "lift", "elevator", "basement",
            "corner", "sea view", "servant quarter", "gas", "security"]
CITIES = {"lahore": "PK", "karachi": "PK", "islamabad": "PK", "rawalpindi": "PK", "peshawar": "PK",
          "faisalabad": "PK", "multan": "PK", "dubai": "AE", "abu dhabi": "AE", "sharjah": "AE", "ajman": "AE",
          "riyadh": "SA", "jeddah": "SA", "dammam": "SA", "khobar": "SA", "makkah": "SA", "madinah": "SA"}
COUNTRY_CCY = {"PK": "PKR", "AE": "AED", "SA": "SAR"}
REQ_WORDS = ("need", "required", "requirement", "looking for", "wanted", "want to buy", "chahiye", "chahye",
             "client", "buyer", "tenant", "budget", "searching")
LIST_WORDS = ("available", "for sale", "for rent", "demand", "urgent sale", "listing", "offer", "owner")
CUR = {"aed": "AED", "sar": "SAR", "pkr": "PKR", "usd": "USD", "rs": "PKR", "rs.": "PKR", "$": "USD"}

AREA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(marla|marlay|kanal|sq\.?\s?ft|sqft|square\s?feet|sq\.?\s?yd|sq\.?\s?yards?|gaz|sq\.?\s?m|sqm)\b", re.I)
BED_RANGE = re.compile(r"(\d+)\s*(?:-|to)\s*(\d+)\s*(?:bed(?:room)?s?|bhk|br)\b", re.I)
BED_RE = re.compile(r"(\d+)\s*(?:bed(?:room)?s?|bhk|br)\b", re.I)
PRICE_RE = re.compile(
    r"(?P<c1>aed|sar|pkr|usd|rs\.?|\$)?\s*(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?P<unit>crore|cr|lakhs?|lacs?|million|mn|thousand|m|k)?\b\s*(?P<c2>aed|sar|pkr|usd)?", re.I)
AREA_UNITS = {"marla": "marla", "marlay": "marla", "kanal": "kanal", "gaz": "sqyd", "sqm": "sqm"}


def _area_unit(raw: str) -> str:
    r = re.sub(r"[\s.]", "", raw.lower())
    if r in AREA_UNITS:
        return AREA_UNITS[r]
    if r.startswith(("sqy", "squarey")):
        return "sqyd"
    if r in ("sqm",) or r == "sqm":
        return "sqm"
    return "sqft"


def _prices(text: str) -> list[tuple[float, str | None]]:
    out = []
    for m in PRICE_RE.finditer(text):
        unit, cur = (m.group("unit") or "").lower(), (m.group("c1") or m.group("c2") or "").lower()
        if not (unit or cur):
            continue  # bare numbers (phase 6, 10 marla...) are not prices
        if unit in ("m", "k") and not cur and float(m.group("num").replace(",", "")) > 1000:
            continue
        val = float(m.group("num").replace(",", "")) * UNIT_MULT.get(unit, 1)
        out.append((val, CUR.get(cur)))
    return out


def parse_message(text: str, default_currency: str | None = None) -> dict:
    raw = text.strip()
    low = raw.lower()
    warnings: list[str] = []

    req_hits = sum(w in low for w in REQ_WORDS)
    list_hits = sum(w in low for w in LIST_WORDS)
    kind = "requirement" if req_hits > list_hits else "property"

    purpose = "rent" if re.search(r"\b(rent|kiraya|kiraye|lease|per month|pm)\b", low) else "sale"

    ptype = None
    for word in sorted(TYPES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(word)}s?\b", low):
            ptype = TYPES[word]
            break

    work = raw
    area = AREA_RE.search(work)
    area_value = area_unit = None
    if area:
        area_value, area_unit = float(area.group(1)), _area_unit(area.group(2))
        work = work.replace(area.group(0), " ")

    bmin = bmax = None
    br = BED_RANGE.search(work)
    if br:
        bmin, bmax = int(br.group(1)), int(br.group(2))
        work = work.replace(br.group(0), " ")
    else:
        b = BED_RE.search(work)
        if b:
            bmin = bmax = int(b.group(1))
            work = work.replace(b.group(0), " ")
        elif "studio" in low:
            bmin = bmax = 0

    prices = _prices(work)
    ccy = next((c for _, c in prices if c), None)

    city = country = None
    for name, ctry in CITIES.items():
        if re.search(rf"\b{name}\b", low):
            city, country = name.title(), ctry
            break
    ccy = ccy or (COUNTRY_CCY.get(country) if country else None) or default_currency

    loc = None
    stop = (r"(?=,|\n|$|\s(?:budget|price|demand|rent|for|with|rs\.?|aed|sar|pkr|usd|\$)\b"
            r"|\s\d+(?:\.\d+)?\s*(?:crore|cr|lakhs?|lacs?|million|mn|m|k)\b)")
    m = re.search(rf"\b(?:in|at|near)\s+([A-Za-z0-9][A-Za-z0-9 .'\-]*?){stop}", work, re.I)
    if not m and ptype:
        m = re.search(rf"\b{ptype}s?\s+(?:in\s+)?([A-Za-z][A-Za-z0-9 .'\-]*?){stop}", work, re.I)
    if m:
        loc = m.group(1).strip(" .-")
        if city:  # strip the city out of the locality text
            loc = re.sub(rf"\b{city}\b", "", loc, flags=re.I).strip(" ,.-") or None

    features = [f for f in FEATURES if re.search(rf"\b{f}\b", low)]

    data: dict = {"purpose": purpose, "property_type": ptype, "currency": ccy, "city": city,
                  "country": country, "features": features}
    if kind == "property":
        data.update(area_name=loc, bedrooms=bmin, area_value=area_value, area_unit=area_unit,
                    price=prices[0][0] if prices else None)
        found = [data["property_type"], data["price"], data["area_name"] or data["city"],
                 data["bedrooms"] is not None or area_value is not None]
    else:
        data.update(property_types=[ptype] if ptype else [], preferred_areas=[loc] if loc else [],
                    bedrooms_min=bmin, bedrooms_max=bmax, required_features=features)
        if len(prices) >= 2:
            data["budget_min"], data["budget_max"] = sorted(p for p, _ in prices[:2])
        elif prices:
            data["budget_max"] = prices[0][0]
        found = [ptype, prices, loc or city, bmin is not None]
    if kind == "requirement":
        data.pop("features")
    if not prices:
        warnings.append("No price/budget detected")
    if not (loc or city):
        warnings.append("No location detected")
    if not ptype:
        warnings.append("No property type detected")
    return {"kind": kind, "data": data, "confidence": round(sum(bool(f) for f in found) / len(found), 2),
            "warnings": warnings}
