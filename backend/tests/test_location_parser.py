"""Tests for the location parser — the core of location filtering.

Tests real-world location strings from ATS platforms and job boards.
"""

import pytest

from apps.jobs.location_parser import parse_location, parse_structured_location


# ---------------------------------------------------------------------------
# Remote detection
# ---------------------------------------------------------------------------


class TestRemoteDetection:
    def test_bare_remote(self):
        r = parse_location("Remote")
        assert r.is_remote is True
        assert r.workplace_type == "remote"
        assert r.remote_region == "unspecified"

    def test_remote_case_insensitive(self):
        r = parse_location("REMOTE")
        assert r.is_remote is True

    def test_distributed(self):
        r = parse_location("Distributed")
        assert r.is_remote is True

    def test_work_from_anywhere(self):
        r = parse_location("Work from Anywhere")
        assert r.is_remote is True
        assert r.remote_region == "global"

    def test_hybrid(self):
        r = parse_location("Hybrid")
        assert r.is_remote is True
        assert r.workplace_type == "hybrid"

    def test_onsite(self):
        r = parse_location("On-site")
        assert r.is_remote is False
        assert r.workplace_type == "onsite"

    def test_onsite_city(self):
        r = parse_location("San Francisco, CA")
        assert r.is_remote is False
        assert r.workplace_type == "onsite"

    def test_empty(self):
        r = parse_location("")
        assert r.is_remote is False
        assert r.workplace_type == "unknown"

    def test_fully_remote(self):
        r = parse_location("100% Remote")
        assert r.is_remote is True


# ---------------------------------------------------------------------------
# Remote + region
# ---------------------------------------------------------------------------


class TestRemoteRegion:
    def test_remote_us(self):
        r = parse_location("Remote, US")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_dash_usa(self):
        r = parse_location("Remote - USA")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_no_space_usa(self):
        """Airbnb-style: Remote-USA"""
        r = parse_location("Remote-USA")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_united_states(self):
        r = parse_location("Remote, United States")
        assert r.is_remote is True
        assert r.remote_region == "us_only"
        assert "US" in r.country_codes

    def test_remote_paren_us(self):
        """Discord-style: Remote (U.S.)"""
        r = parse_location("Remote (U.S.)")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_paren_us_only(self):
        r = parse_location("Remote (US Only)")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_emea(self):
        r = parse_location("Remote-EMEA")
        assert r.is_remote is True
        assert r.remote_region == "emea"

    def test_remote_apac(self):
        r = parse_location("Remote - APAC")
        assert r.is_remote is True
        assert r.remote_region == "apac"

    def test_remote_north_america(self):
        r = parse_location("Remote, North America")
        assert r.is_remote is True
        assert r.remote_region == "americas"

    def test_worldwide(self):
        r = parse_location("Worldwide")
        assert r.is_remote is True
        assert r.remote_region == "global"

    def test_anywhere_in_the_world(self):
        r = parse_location("Anywhere in the World")
        assert r.is_remote is True
        assert r.remote_region == "global"

    def test_remote_canada(self):
        r = parse_location("Remote, Canada")
        assert r.is_remote is True
        assert "CA" in r.country_codes

    def test_remote_germany(self):
        r = parse_location("Remote, Germany")
        assert r.is_remote is True
        assert "DE" in r.country_codes

    def test_usa_only(self):
        """Remotive-style: 'USA Only'"""
        r = parse_location("USA Only")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_remote_dach(self):
        r = parse_location("Remote-DACH")
        assert r.is_remote is True
        assert r.remote_region == "europe"


# ---------------------------------------------------------------------------
# City / state / country extraction
# ---------------------------------------------------------------------------


class TestCityExtraction:
    def test_sf_ca(self):
        r = parse_location("San Francisco, CA")
        assert r.city == "San Francisco"
        assert r.region == "CA"
        assert "US" in r.country_codes

    def test_nyc(self):
        r = parse_location("New York, NY")
        assert "US" in r.country_codes
        assert r.region == "NY"

    def test_austin_tx(self):
        r = parse_location("Austin, TX")
        assert r.city == "Austin"
        assert r.region == "TX"
        assert "US" in r.country_codes

    def test_london(self):
        r = parse_location("London")
        assert "GB" in r.country_codes
        assert r.city == "London"

    def test_berlin(self):
        r = parse_location("Berlin")
        assert "DE" in r.country_codes

    def test_toronto_ontario(self):
        r = parse_location("Toronto, Ontario, CAN")
        assert "CA" in r.country_codes

    def test_country_only(self):
        r = parse_location("Germany")
        assert "DE" in r.country_codes
        assert r.workplace_type == "onsite"

    def test_state_only(self):
        r = parse_location("California, USA")
        assert "US" in r.country_codes


# ---------------------------------------------------------------------------
# Multi-location / complex strings (Greenhouse nightmares)
# ---------------------------------------------------------------------------


class TestComplexPatterns:
    def test_semicolon_separated(self):
        """Gusto-style multi-location"""
        r = parse_location("Denver, CO;San Francisco, CA;New York, NY")
        assert "US" in r.country_codes
        assert r.is_remote is False

    def test_city_or_remote(self):
        """Discord-style: city or Remote"""
        r = parse_location("San Francisco Bay Area or Remote")
        assert r.is_remote is True

    def test_city_or_remote_us(self):
        r = parse_location("San Francisco, CA or Remote (U.S.)")
        assert r.is_remote is True
        assert "US" in r.country_codes

    def test_reversed_remote(self):
        """Airbnb-style: country - Remote"""
        r = parse_location("Brazil - Remote")
        assert r.is_remote is True
        assert "BR" in r.country_codes

    def test_hybrid_per_city(self):
        """Gusto-style per-city work type"""
        r = parse_location("Denver, CO - Hybrid; Phoenix, AZ - Remote")
        assert r.is_remote is True  # has a remote option

    def test_bullet_separator(self):
        """Figma-style bullet separator"""
        r = parse_location("San Francisco, CA \u2022 New York, NY \u2022 United States")
        assert "US" in r.country_codes

    def test_trailing_whitespace(self):
        r = parse_location("Remote, United States ")
        assert r.is_remote is True
        assert r.remote_region == "us_only"

    def test_trailing_semicolon(self):
        r = parse_location("San Francisco, CA;")
        assert "US" in r.country_codes

    def test_bay_area(self):
        r = parse_location("San Francisco Bay Area")
        assert "US" in r.country_codes


# ---------------------------------------------------------------------------
# Structured location (Ashby, Workable, Lever)
# ---------------------------------------------------------------------------


class TestStructuredLocation:
    def test_ashby_remote_with_address(self):
        r = parse_structured_location(
            location_str="Houston, TX",
            is_remote=True,
            workplace_type="Remote",
            country="USA",
            region="Texas",
            city="Houston",
        )
        assert r.is_remote is True
        assert r.workplace_type == "remote"
        assert "US" in r.country_codes
        assert r.city == "Houston"
        assert r.region == "TX"

    def test_workable_structured(self):
        r = parse_structured_location(
            location_str="London, UK",
            is_remote=False,
            workplace_type="on_site",
            country="United Kingdom",
            country_code="GB",
            city="London",
        )
        assert r.is_remote is False
        assert r.workplace_type == "onsite"
        assert "GB" in r.country_codes
        assert r.city == "London"

    def test_lever_remote_workplace_type(self):
        r = parse_structured_location(
            location_str="Mountain View",
            workplace_type="remote",
        )
        assert r.is_remote is True
        assert r.workplace_type == "remote"

    def test_lever_hybrid(self):
        r = parse_structured_location(
            location_str="New York, NY",
            workplace_type="hybrid",
        )
        assert r.is_remote is True
        assert r.workplace_type == "hybrid"

    def test_structured_overrides_text(self):
        """Structured is_remote=False overrides 'Remote' in location string."""
        r = parse_structured_location(
            location_str="Remote",
            is_remote=False,
            workplace_type="on-site",
        )
        assert r.is_remote is False
        assert r.workplace_type == "onsite"

    def test_workable_country_code(self):
        r = parse_structured_location(
            location_str="Portland, Oregon, United States",
            country_code="US",
            region="Oregon",
            city="Portland",
        )
        assert "US" in r.country_codes
        assert r.city == "Portland"
        assert r.region == "OR"


# ---------------------------------------------------------------------------
# Edge cases / regression tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_none_input(self):
        """parse_location should handle empty/whitespace gracefully."""
        r = parse_location("   ")
        assert r.is_remote is False

    def test_internal_codes(self):
        """Stripe-style internal codes like US-SF-HQ — we can't parse these
        but they shouldn't crash."""
        r = parse_location("US-SF-HQ")
        # Won't extract much, but shouldn't error
        assert isinstance(r.is_remote, bool)

    def test_remote_with_city_restriction(self):
        """Remote (Seattle, WA only) — still remote."""
        r = parse_location("Remote (Seattle, WA only)")
        assert r.is_remote is True

    def test_multiple_countries(self):
        r = parse_location("London, England; Paris, France")
        assert "GB" in r.country_codes
        assert "FR" in r.country_codes

    def test_us_state_full_name(self):
        r = parse_location("Florida, United States")
        assert "US" in r.country_codes

    def test_remote_india(self):
        """This is the key case — should NOT show up in US searches."""
        r = parse_location("Remote - India")
        assert r.is_remote is True
        assert "IN" in r.country_codes
        # remote_region should NOT be us_only
        assert r.remote_region != "us_only"
