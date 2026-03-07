"""Hunter.io API v2 adapter.

Free tier: 50 unified credits/month.
Email Count endpoint is FREE — always call before Domain Search.
"""

import requests

from .base import ContactResult, DomainInfo, EnrichmentProvider

HUNTER_API_BASE = "https://api.hunter.io/v2"


class HunterProvider(EnrichmentProvider):
    def check_credits(self, api_key: str) -> dict:
        resp = requests.get(
            f"{HUNTER_API_BASE}/account", params={"api_key": api_key}
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return {
            "total": data["requests"]["searches"]["available"],
            "used": data["requests"]["searches"]["used"],
        }

    def email_count(self, api_key: str, domain: str) -> int:
        """FREE endpoint — check if Hunter has data before spending credits."""
        resp = requests.get(
            f"{HUNTER_API_BASE}/email-count", params={"domain": domain, "api_key": api_key}
        )
        resp.raise_for_status()
        return resp.json()["data"]["total"]

    def domain_search(
        self, api_key: str, domain: str, department: str | None = None
    ) -> DomainInfo:
        """Costs 1 credit per call. Returns up to 10 emails."""
        params = {"domain": domain, "api_key": api_key}
        if department:
            params["department"] = department
        resp = requests.get(f"{HUNTER_API_BASE}/domain-search", params=params)
        resp.raise_for_status()
        data = resp.json()["data"]
        contacts = [
            ContactResult(
                first_name=e.get("first_name", ""),
                last_name=e.get("last_name", ""),
                email=e.get("value", ""),
                confidence=e.get("confidence", 0),
                position=e.get("position", ""),
                department=e.get("department", ""),
                seniority=e.get("seniority", ""),
                linkedin_url=e.get("linkedin", ""),
            )
            for e in data.get("emails", [])
        ]
        return DomainInfo(
            domain=domain,
            organization=data.get("organization", ""),
            total_emails=data.get("total", 0),
            contacts=contacts,
        )

    def find_email(
        self, api_key: str, domain: str, first_name: str, last_name: str
    ) -> ContactResult:
        resp = requests.get(
            f"{HUNTER_API_BASE}/email-finder",
            params={
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": api_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return ContactResult(
            first_name=first_name,
            last_name=last_name,
            email=data.get("email", ""),
            confidence=data.get("confidence", 0),
        )
