"""Parse raw location strings into structured location data.

Pure functions — no DB access, no side effects. Designed for:
1. Parsing free-text location strings from Greenhouse, HN, etc.
2. Accepting structured data from Ashby/Workable/Lever and normalizing it.
3. Backfilling existing JobListing records.

The goal is 95%+ accuracy on real ATS data. We intentionally err on the side
of INCLUSION — a bare "Remote" with no region qualifier defaults to
"unspecified" so it shows up in US searches (most are US companies).
"""

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ParsedLocation:
    is_remote: bool = False
    workplace_type: str = "unknown"  # remote, hybrid, onsite, unknown
    remote_region: str = "unspecified"  # us_only, us_canada, americas, europe, emea, apac, global, unspecified
    country_codes: list[str] = field(default_factory=list)
    region: str = ""  # state/province
    city: str = ""


# ---------------------------------------------------------------------------
# Remote detection patterns
# ---------------------------------------------------------------------------

REMOTE_PATTERNS = re.compile(
    r"\b(?:remote|distributed|work[ -]?from[ -]?(?:home|anywhere)|telecommute|"
    r"fully[ -]?remote|100%[ -]?remote)\b",
    re.IGNORECASE,
)

HYBRID_PATTERNS = re.compile(
    r"\bhybrid\b",
    re.IGNORECASE,
)

ONSITE_PATTERNS = re.compile(
    r"\b(?:on[ -]?site|in[ -]?office|in[ -]?person|onsite)\b",
    re.IGNORECASE,
)

ANYWHERE_PATTERNS = re.compile(
    r"\b(?:anywhere|worldwide|global(?:ly)?)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Region / country mapping
# ---------------------------------------------------------------------------

# Maps keywords found in location strings to remote_region values
REGION_KEYWORDS = {
    # US only
    "us only": "us_only",
    "usa only": "us_only",
    "u.s. only": "us_only",
    "u.s.": "us_only",
    "united states": "us_only",
    "usa": "us_only",
    # US & Canada
    "us/canada": "us_canada",
    "usa/canada": "us_canada",
    "us & canada": "us_canada",
    "us and canada": "us_canada",
    "north america only": "us_canada",
    # Americas
    "americas": "americas",
    "noram": "americas",
    "north america": "americas",
    "latam": "americas",
    "south america": "americas",
    "amer": "americas",
    # Europe
    "europe only": "europe",
    "europe": "europe",
    "eu": "europe",
    "dach": "europe",
    "iberia": "europe",
    "uk&i": "europe",
    "uk only": "europe",
    # EMEA
    "emea": "emea",
    # APAC
    "apac": "apac",
    "asia": "apac",
    "asia only": "apac",
    # Global
    "worldwide": "global",
    "anywhere in the world": "global",
    "anywhere": "global",
    "global": "global",
    "globally": "global",
}

# Country name -> ISO code
COUNTRY_MAP = {
    "united states": "US",
    "usa": "US",
    "us": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "canada": "CA",
    "united kingdom": "GB",
    "uk": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "germany": "DE",
    "deutschland": "DE",
    "france": "FR",
    "netherlands": "NL",
    "holland": "NL",
    "ireland": "IE",
    "spain": "ES",
    "portugal": "PT",
    "italy": "IT",
    "switzerland": "CH",
    "austria": "AT",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "poland": "PL",
    "czech republic": "CZ",
    "czechia": "CZ",
    "belgium": "BE",
    "australia": "AU",
    "new zealand": "NZ",
    "japan": "JP",
    "south korea": "KR",
    "korea": "KR",
    "singapore": "SG",
    "india": "IN",
    "china": "CN",
    "brazil": "BR",
    "mexico": "MX",
    "argentina": "AR",
    "colombia": "CO",
    "chile": "CL",
    "israel": "IL",
    "turkey": "TR",
    "romania": "RO",
    "ukraine": "UA",
    "hungary": "HU",
    "greece": "GR",
    "taiwan": "TW",
    "thailand": "TH",
    "vietnam": "VN",
    "philippines": "PH",
    "indonesia": "ID",
    "malaysia": "MY",
    "nigeria": "NG",
    "south africa": "ZA",
    "egypt": "EG",
    "kenya": "KE",
    "malta": "MT",
}

# US state abbreviations and names -> abbreviation
US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}

# Reverse: abbreviation -> abbreviation (for matching "CA", "NY" etc.)
US_STATE_ABBREVS = {v: v for v in US_STATES.values()}

# Canadian provinces
CA_PROVINCES = {
    "ontario": "ON", "quebec": "QC", "british columbia": "BC",
    "alberta": "AB", "manitoba": "MB", "saskatchewan": "SK",
    "nova scotia": "NS", "new brunswick": "NB",
    "prince edward island": "PE", "newfoundland": "NL",
}

# Known city -> (country_code, state/region) for common tech hubs
KNOWN_CITIES = {
    "san francisco": ("US", "CA"),
    "sf": ("US", "CA"),
    "new york": ("US", "NY"),
    "new york city": ("US", "NY"),
    "nyc": ("US", "NY"),
    "los angeles": ("US", "CA"),
    "la": ("US", "CA"),
    "seattle": ("US", "WA"),
    "austin": ("US", "TX"),
    "boston": ("US", "MA"),
    "chicago": ("US", "IL"),
    "denver": ("US", "CO"),
    "portland": ("US", "OR"),
    "atlanta": ("US", "GA"),
    "miami": ("US", "FL"),
    "dallas": ("US", "TX"),
    "houston": ("US", "TX"),
    "phoenix": ("US", "AZ"),
    "philadelphia": ("US", "PA"),
    "san diego": ("US", "CA"),
    "san jose": ("US", "CA"),
    "washington": ("US", "DC"),
    "washington dc": ("US", "DC"),
    "dc": ("US", "DC"),
    "raleigh": ("US", "NC"),
    "nashville": ("US", "TN"),
    "salt lake city": ("US", "UT"),
    "minneapolis": ("US", "MN"),
    "pittsburgh": ("US", "PA"),
    "detroit": ("US", "MI"),
    "charlotte": ("US", "NC"),
    "san antonio": ("US", "TX"),
    "columbus": ("US", "OH"),
    "indianapolis": ("US", "IN"),
    "las vegas": ("US", "NV"),
    "south san francisco": ("US", "CA"),
    "palo alto": ("US", "CA"),
    "mountain view": ("US", "CA"),
    "sunnyvale": ("US", "CA"),
    "menlo park": ("US", "CA"),
    "redwood city": ("US", "CA"),
    "cupertino": ("US", "CA"),
    "san mateo": ("US", "CA"),
    "santa clara": ("US", "CA"),
    "oakland": ("US", "CA"),
    "berkeley": ("US", "CA"),
    "boulder": ("US", "CO"),
    "cambridge": ("US", "MA"),
    "toronto": ("CA", "ON"),
    "vancouver": ("CA", "BC"),
    "montreal": ("CA", "QC"),
    "ottawa": ("CA", "ON"),
    "calgary": ("CA", "AB"),
    "london": ("GB", ""),
    "manchester": ("GB", ""),
    "edinburgh": ("GB", ""),
    "bristol": ("GB", ""),
    "dublin": ("IE", ""),
    "berlin": ("DE", ""),
    "munich": ("DE", ""),
    "hamburg": ("DE", ""),
    "amsterdam": ("NL", ""),
    "paris": ("FR", ""),
    "stockholm": ("SE", ""),
    "copenhagen": ("DK", ""),
    "oslo": ("NO", ""),
    "helsinki": ("FI", ""),
    "zurich": ("CH", ""),
    "barcelona": ("ES", ""),
    "madrid": ("ES", ""),
    "lisbon": ("PT", ""),
    "milan": ("IT", ""),
    "rome": ("IT", ""),
    "vienna": ("AT", ""),
    "warsaw": ("PL", ""),
    "prague": ("CZ", ""),
    "budapest": ("HU", ""),
    "bucharest": ("RO", ""),
    "istanbul": ("TR", ""),
    "tel aviv": ("IL", ""),
    "tokyo": ("JP", ""),
    "singapore": ("SG", ""),
    "sydney": ("AU", ""),
    "melbourne": ("AU", ""),
    "bangalore": ("IN", ""),
    "bengaluru": ("IN", ""),
    "mumbai": ("IN", ""),
    "hyderabad": ("IN", ""),
    "pune": ("IN", ""),
    "delhi": ("IN", ""),
    "new delhi": ("IN", ""),
    "sao paulo": ("BR", ""),
    "mexico city": ("MX", ""),
    "bogota": ("CO", ""),
    "buenos aires": ("AR", ""),
    "santiago": ("CL", ""),
    "cape town": ("ZA", ""),
    "nairobi": ("KE", ""),
    "lagos": ("NG", ""),
    "cairo": ("EG", ""),
    "athens": ("GR", ""),
    "seoul": ("KR", ""),
    "taipei": ("TW", ""),
    "bangkok": ("TH", ""),
    "ho chi minh city": ("VN", ""),
    "manila": ("PH", ""),
    "jakarta": ("ID", ""),
    "kuala lumpur": ("MY", ""),
    "valletta": ("MT", ""),
    "valetta": ("MT", ""),
}

# Region names that aren't cities (don't put in city field)
REGION_NAMES = {
    "san francisco bay area", "bay area", "silicon valley",
    "greater london", "greater manchester",
    "orange county", "tri-state area",
}


# ---------------------------------------------------------------------------
# Main parsing function
# ---------------------------------------------------------------------------


def parse_location(raw: str) -> ParsedLocation:
    """Parse a raw location string into structured location data.

    This is the main entry point for free-text parsing (Greenhouse, HN, etc.).
    For platforms with structured data (Ashby, Workable, Lever), use
    parse_structured_location() instead.
    """
    result = ParsedLocation()

    if not raw or not raw.strip():
        return result

    text = raw.strip()
    text_lower = text.lower()

    # Step 1: Detect remote/hybrid/onsite
    has_remote = bool(REMOTE_PATTERNS.search(text_lower))
    has_hybrid = bool(HYBRID_PATTERNS.search(text_lower))
    has_onsite = bool(ONSITE_PATTERNS.search(text_lower))
    has_anywhere = bool(ANYWHERE_PATTERNS.search(text_lower))

    if has_remote or has_anywhere:
        result.is_remote = True
        result.workplace_type = "remote"
    if has_hybrid:
        # Hybrid implies some remote capability
        result.is_remote = True
        result.workplace_type = "hybrid"
    if has_onsite and not has_remote and not has_hybrid:
        result.workplace_type = "onsite"

    # Step 2: Detect remote region from keywords
    for keyword, region in REGION_KEYWORDS.items():
        if keyword in text_lower:
            result.remote_region = region
            # If we found a region keyword, this is definitely remote
            if region in ("global", "us_only", "us_canada", "americas", "europe", "emea", "apac"):
                result.is_remote = True
                if result.workplace_type == "unknown":
                    result.workplace_type = "remote"
            break

    # Step 3: Extract country codes and city/state from the location parts
    # Split on common separators: ;  •  |  " or "  /
    # But NOT commas (they separate city, state)
    parts = re.split(r"\s*[;•|]\s*|\s+or\s+|\s*/\s*", text)

    countries_found = set()
    cities_found = []
    states_found = []

    for part in parts:
        part = part.strip().rstrip(";,. ")
        if not part:
            continue

        part_lower = part.lower()

        # Remove remote/hybrid/onsite prefixes/suffixes for location extraction
        cleaned = re.sub(
            r"\b(?:remote|hybrid|on-?site|in-?office|distributed)\b\s*[-–—]?\s*",
            "", part, flags=re.IGNORECASE,
        ).strip().strip("-–— ,")
        cleaned_lower = cleaned.lower().strip()

        if not cleaned_lower:
            continue

        # Skip if it's just a work type annotation
        if cleaned_lower in ("remote", "hybrid", "onsite", "on-site", "in-office",
                             "full time", "full-time", "part time", "part-time",
                             "contract", "internship"):
            continue

        # Remove parenthetical qualifiers for matching, but check them too
        paren_match = re.search(r"\(([^)]+)\)", cleaned)
        paren_content = ""
        if paren_match:
            paren_content = paren_match.group(1).strip().lower()
            cleaned_no_paren = re.sub(r"\s*\([^)]*\)", "", cleaned).strip()
        else:
            cleaned_no_paren = cleaned
        cleaned_no_paren_lower = cleaned_no_paren.lower()

        # Check parenthetical content for country/region (e.g. "Remote (U.S.)")
        if paren_content:
            _extract_geo(paren_content, countries_found, cities_found, states_found)

        # Check the main text
        _extract_geo(cleaned_no_paren_lower, countries_found, cities_found, states_found)

    result.country_codes = sorted(countries_found)

    if cities_found:
        result.city = cities_found[0]  # primary city
    if states_found:
        result.region = states_found[0]  # primary state/region

    # Step 4: Infer remote region from country codes if not already set
    if result.is_remote and result.remote_region == "unspecified" and result.country_codes:
        codes = set(result.country_codes)
        if codes == {"US"}:
            result.remote_region = "us_only"
        elif codes <= {"US", "CA"}:
            result.remote_region = "us_canada"
        elif all(c in _AMERICAS_CODES for c in codes):
            result.remote_region = "americas"
        elif all(c in _EUROPE_CODES for c in codes):
            result.remote_region = "europe"

    # Step 5: If we found locations but no remote signal, mark as onsite
    if result.workplace_type == "unknown" and (result.city or result.country_codes):
        result.workplace_type = "onsite"

    return result


def _extract_geo(text: str, countries: set, cities: list, states: list):
    """Extract country codes, cities, and states from a text fragment."""
    text = text.strip().rstrip(".,;: ")

    # Check known cities first (most specific)
    for city_name, (cc, state) in KNOWN_CITIES.items():
        # Short names (<=3 chars like "sf", "nyc", "dc", "la") need word boundary match
        if len(city_name) <= 3:
            if not re.search(rf"\b{re.escape(city_name)}\b", text, re.IGNORECASE):
                continue
        elif city_name not in text:
            continue
        countries.add(cc)
        if city_name not in [c.lower() for c in cities]:
            # Capitalize properly
            cities.append(city_name.title())
        if state and state not in states:
            states.append(state)
        return

    # Check region names (Bay Area, etc.) — don't add to cities
    for region_name in REGION_NAMES:
        if region_name in text:
            # Try to infer country from region
            if "bay area" in text or "silicon valley" in text:
                countries.add("US")
                if "CA" not in states:
                    states.append("CA")
            elif "london" in text:
                countries.add("GB")
            return

    # Check countries
    for country_name, cc in COUNTRY_MAP.items():
        if country_name in text:
            countries.add(cc)
            return

    # Check US states (full name)
    for state_name, abbrev in US_STATES.items():
        if state_name in text:
            countries.add("US")
            if abbrev not in states:
                states.append(abbrev)
            return

    # Check US state abbreviations (2-letter, must be word boundary)
    # Pattern: "City, XX" or standalone "XX"
    state_match = re.search(r"\b([A-Z]{2})\b", text.upper())
    if state_match:
        abbrev = state_match.group(1)
        if abbrev in US_STATE_ABBREVS:
            countries.add("US")
            if abbrev not in states:
                states.append(abbrev)
            # Try to extract city before the state abbreviation
            city_part = text[:state_match.start()].strip().rstrip(", ")
            if city_part and len(city_part) > 1:
                # Don't add if it looks like a country or region keyword
                if city_part.lower() not in COUNTRY_MAP and city_part.lower() not in REGION_KEYWORDS:
                    if city_part.title() not in cities:
                        cities.append(city_part.title())
            return

    # Check Canadian provinces
    for prov_name, abbrev in CA_PROVINCES.items():
        if prov_name in text:
            countries.add("CA")
            if abbrev not in states:
                states.append(abbrev)
            return


def parse_structured_location(
    *,
    location_str: str = "",
    is_remote: bool | None = None,
    workplace_type: str | None = None,
    country: str = "",
    country_code: str = "",
    region: str = "",
    city: str = "",
) -> ParsedLocation:
    """Parse structured location data from platforms that provide it (Ashby, Workable, Lever).

    Accepts structured fields directly and merges with free-text parsing as fallback.
    """
    # Start with free-text parse of the location string
    result = parse_location(location_str)

    # Override with structured data when available
    if is_remote is not None:
        result.is_remote = is_remote
        if is_remote and result.workplace_type == "unknown":
            result.workplace_type = "remote"

    if workplace_type:
        wt = workplace_type.lower().replace("-", "").replace("_", "").replace(" ", "")
        if wt in ("remote",):
            result.workplace_type = "remote"
            result.is_remote = True
        elif wt in ("hybrid",):
            result.workplace_type = "hybrid"
            result.is_remote = True
        elif wt in ("onsite", "on site"):
            result.workplace_type = "onsite"

    if country_code:
        cc = country_code.upper()
        if cc not in result.country_codes:
            result.country_codes = sorted(set(result.country_codes) | {cc})
    elif country:
        cc = COUNTRY_MAP.get(country.lower().strip())
        if cc and cc not in result.country_codes:
            result.country_codes = sorted(set(result.country_codes) | {cc})

    if city and not result.city:
        result.city = city.strip()
    if region and not result.region:
        # Check if it's a US state name
        abbrev = US_STATES.get(region.lower().strip())
        if abbrev:
            result.region = abbrev
        else:
            result.region = region.strip()

    # Re-infer remote_region from country codes if structured data changed them
    if result.is_remote and result.remote_region == "unspecified" and result.country_codes:
        codes = set(result.country_codes)
        if codes == {"US"}:
            result.remote_region = "us_only"
        elif codes <= {"US", "CA"}:
            result.remote_region = "us_canada"

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AMERICAS_CODES = {"US", "CA", "MX", "BR", "AR", "CO", "CL"}
_EUROPE_CODES = {
    "GB", "DE", "FR", "NL", "IE", "ES", "PT", "IT", "CH", "AT",
    "SE", "NO", "DK", "FI", "PL", "CZ", "BE", "RO", "HU", "GR",
    "UA", "MT",
}
