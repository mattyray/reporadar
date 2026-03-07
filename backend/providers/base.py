from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ContactResult:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    confidence: int = 0
    verified: bool = False
    position: str = ""
    department: str = ""
    seniority: str = ""
    linkedin_url: str = ""


@dataclass
class DomainInfo:
    domain: str
    organization: str = ""
    total_emails: int = 0
    personal_emails: int = 0
    contacts: list[ContactResult] = field(default_factory=list)


class EnrichmentProvider(ABC):
    """Base class for contact enrichment providers (Hunter.io, Apollo.io)."""

    @abstractmethod
    def check_credits(self, api_key: str) -> dict:
        """Return remaining credits info. Should be free/no-cost call."""

    @abstractmethod
    def email_count(self, api_key: str, domain: str) -> int:
        """Return count of emails available for domain. Should be free/no-cost."""

    @abstractmethod
    def domain_search(
        self, api_key: str, domain: str, department: str | None = None
    ) -> DomainInfo:
        """Search for contacts at a domain. Costs credits."""

    @abstractmethod
    def find_email(
        self, api_key: str, domain: str, first_name: str, last_name: str
    ) -> ContactResult:
        """Find specific person's email. Costs credits."""
