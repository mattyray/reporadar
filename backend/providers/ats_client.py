"""ATS (Applicant Tracking System) client — fetches job listings from public job board APIs.

Supports Greenhouse, Lever, Ashby, and Workable. All endpoints are public, no auth required.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10  # seconds


@dataclass
class JobPost:
    """Normalized job posting from any ATS platform."""

    external_id: str
    title: str
    department: str = ""
    location: str = ""
    employment_type: str = ""
    description_text: str = ""
    apply_url: str = ""
    posted_at: str | None = None


@dataclass
class ProbeResult:
    """Result of probing a slug across all ATS platforms."""

    slug: str
    platforms: dict[str, bool] = field(default_factory=dict)


class ATSClient:
    """Fetches job listings from public ATS board APIs."""

    def probe_company(self, slug: str) -> dict[str, bool]:
        """Try a slug across all 4 platforms in parallel. Returns which ones respond."""
        results = {}

        def _check(platform: str, url: str) -> tuple[str, bool]:
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                # Greenhouse returns 404 for invalid boards
                # Lever returns empty array for invalid companies
                # Ashby returns 404 for invalid boards
                # Workable returns 404 for invalid accounts
                if resp.status_code == 200:
                    data = resp.json()
                    # Lever returns an empty list for nonexistent companies
                    if platform == "lever" and isinstance(data, list) and len(data) == 0:
                        return platform, False
                    # Greenhouse wraps in {"jobs": []}
                    if platform == "greenhouse" and isinstance(data, dict):
                        return platform, True
                    # Ashby wraps in {"jobs": []}
                    if platform == "ashby" and isinstance(data, dict):
                        return platform, True
                    # Workable wraps in {"jobs": []}
                    if platform == "workable" and isinstance(data, dict):
                        return platform, True
                    # Lever returns a list directly
                    if platform == "lever" and isinstance(data, list):
                        return platform, True
                return platform, False
            except (requests.RequestException, ValueError):
                return platform, False

        urls = {
            "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            "lever": f"https://api.lever.co/v0/postings/{slug}?mode=json",
            "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            "workable": f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(_check, platform, url): platform
                for platform, url in urls.items()
            }
            for future in as_completed(futures):
                platform, found = future.result()
                results[platform] = found

        return results

    def fetch_greenhouse_jobs(self, slug: str) -> list[JobPost]:
        """Fetch jobs from Greenhouse public board API."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Greenhouse fetch failed for %s: %s", slug, e)
            return []

        jobs = []
        for job in data.get("jobs", []):
            # Strip HTML from content to get plain text
            content = job.get("content", "")
            plain_text = _strip_html(content)

            location_name = ""
            if job.get("location"):
                location_name = job["location"].get("name", "")

            departments = [d.get("name", "") for d in job.get("departments", [])]

            jobs.append(JobPost(
                external_id=str(job.get("id", "")),
                title=job.get("title", ""),
                department=", ".join(departments),
                location=location_name,
                description_text=plain_text,
                apply_url=job.get("absolute_url", ""),
                posted_at=job.get("updated_at"),
            ))
        return jobs

    def fetch_lever_jobs(self, slug: str) -> list[JobPost]:
        """Fetch jobs from Lever public postings API."""
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Lever fetch failed for %s: %s", slug, e)
            return []

        if not isinstance(data, list):
            return []

        jobs = []
        for posting in data:
            # Combine description + lists for full text
            desc_parts = [posting.get("descriptionPlain", "")]
            for section in posting.get("lists", []):
                desc_parts.append(section.get("text", ""))
                desc_parts.append(_strip_html(section.get("content", "")))
            desc_parts.append(posting.get("additionalPlain", ""))
            full_text = "\n".join(p for p in desc_parts if p)

            categories = posting.get("categories", {})
            jobs.append(JobPost(
                external_id=str(posting.get("id", "")),
                title=posting.get("text", ""),
                department=categories.get("department", "") or categories.get("team", ""),
                location=categories.get("location", ""),
                employment_type=categories.get("commitment", ""),
                description_text=full_text,
                apply_url=posting.get("hostedUrl", ""),
                posted_at=None,  # Lever provides createdAt as epoch, handle if needed
            ))
        return jobs

    def fetch_ashby_jobs(self, slug: str) -> list[JobPost]:
        """Fetch jobs from Ashby public job board API."""
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Ashby fetch failed for %s: %s", slug, e)
            return []

        jobs = []
        for job in data.get("jobs", []):
            jobs.append(JobPost(
                external_id=str(job.get("id", "")),
                title=job.get("title", ""),
                department=job.get("department", ""),
                location=job.get("location", ""),
                employment_type=job.get("employmentType", ""),
                description_text=_strip_html(job.get("descriptionHtml", "")),
                apply_url=job.get("jobUrl", ""),
                posted_at=job.get("publishedAt"),
            ))
        return jobs

    def fetch_workable_jobs(self, slug: str) -> list[JobPost]:
        """Fetch jobs from Workable public widget API."""
        url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Workable fetch failed for %s: %s", slug, e)
            return []

        jobs = []
        for job in data.get("jobs", []):
            location_parts = []
            loc = job.get("location", {})
            if isinstance(loc, dict):
                for field in ["city", "region", "country"]:
                    if loc.get(field):
                        location_parts.append(loc[field])
            location_str = ", ".join(location_parts)

            jobs.append(JobPost(
                external_id=str(job.get("shortcode", job.get("id", ""))),
                title=job.get("title", ""),
                department=job.get("department", ""),
                location=location_str,
                description_text="",  # Workable widget doesn't include description by default
                apply_url=job.get("url", ""),
            ))
        return jobs

    def fetch_jobs(self, platform: str, slug: str) -> list[JobPost]:
        """Fetch jobs from any supported platform."""
        fetchers = {
            "greenhouse": self.fetch_greenhouse_jobs,
            "lever": self.fetch_lever_jobs,
            "ashby": self.fetch_ashby_jobs,
            "workable": self.fetch_workable_jobs,
        }
        fetcher = fetchers.get(platform)
        if not fetcher:
            logger.error("Unknown ATS platform: %s", platform)
            return []
        return fetcher(slug)


def _strip_html(html: str) -> str:
    """Simple HTML tag stripper. Good enough for extracting text from job descriptions."""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
