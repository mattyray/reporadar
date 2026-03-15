"""ATS (Applicant Tracking System) client — fetches job listings from public job board APIs.

Supports Greenhouse, Lever, Ashby, and Workable. All endpoints are public, no auth required.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

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
    # Structured location fields (populated by platforms that provide them)
    structured_is_remote: bool | None = None
    structured_workplace_type: str = ""  # remote, hybrid, onsite, on-site
    structured_country: str = ""
    structured_country_code: str = ""
    structured_region: str = ""
    structured_city: str = ""


@dataclass
class ProbeResult:
    """Result of probing a slug across all ATS platforms."""

    slug: str
    platforms: dict[str, bool] = field(default_factory=dict)


ATS_URL_PATTERNS = {
    "greenhouse": [
        r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
        r"job-boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
        r"boards-api\.greenhouse\.io/v1/boards/([a-zA-Z0-9_-]+)",
    ],
    "lever": [
        r"jobs\.lever\.co/([a-zA-Z0-9_-]+)",
        r"api\.lever\.co/v0/postings/([a-zA-Z0-9_-]+)",
    ],
    "ashby": [
        r"jobs\.ashbyhq\.com/([a-zA-Z0-9_.-]+)",
        r"api\.ashbyhq\.com/posting-api/job-board/([a-zA-Z0-9_.-]+)",
    ],
    "workable": [
        r"apply\.workable\.com/([a-zA-Z0-9_-]+)",
    ],
}

# Links on a homepage that likely lead to a careers/jobs page
CAREERS_LINK_PATTERN = re.compile(
    r'href=["\']([^"\']*(?:career|jobs?|work-with-us|join-us|hiring|openings|open-roles|positions|team)[^"\']*)["\']',
    re.IGNORECASE,
)


class ATSClient:
    """Fetches job listings from public ATS board APIs."""

    def discover_ats_from_website(self, website_url: str) -> dict[str, str]:
        """Scrape a company website to find ATS job board URLs.

        Fetches the homepage, looks for careers/jobs links, fetches those too,
        then scans all HTML for known ATS URL patterns.

        Returns dict of {platform: slug} for any discovered ATS boards.
        """
        discovered = {}
        pages_to_scan = []

        # Normalize URL
        if not website_url.startswith(("http://", "https://")):
            website_url = f"https://{website_url}"

        # Fetch homepage
        try:
            resp = requests.get(
                website_url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (compatible; RepoRadar/1.0)"},
                allow_redirects=True,
            )
            if resp.status_code == 200:
                pages_to_scan.append(resp.text)

                # Look for careers/jobs links
                career_links = CAREERS_LINK_PATTERN.findall(resp.text)
                base_url = resp.url  # after redirects
                seen_urls = set()

                for link in career_links[:5]:  # cap at 5 links
                    full_url = _resolve_url(base_url, link)
                    if full_url and full_url not in seen_urls:
                        seen_urls.add(full_url)
                        try:
                            sub_resp = requests.get(
                                full_url,
                                timeout=REQUEST_TIMEOUT,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; RepoRadar/1.0)"},
                                allow_redirects=True,
                            )
                            if sub_resp.status_code == 200:
                                pages_to_scan.append(sub_resp.text)
                                # Also check if we redirected to an ATS domain directly
                                pages_to_scan.append(sub_resp.url)
                        except requests.RequestException:
                            continue
        except requests.RequestException as e:
            logger.info("Could not fetch website %s: %s", website_url, e)
            return discovered

        # Scan all collected HTML for ATS URL patterns
        all_text = "\n".join(pages_to_scan)
        for platform, patterns in ATS_URL_PATTERNS.items():
            if platform in discovered:
                continue
            for pattern in patterns:
                match = re.search(pattern, all_text)
                if match:
                    slug = match.group(1).lower().rstrip("/")
                    # Skip generic slugs that aren't real company boards
                    if slug not in ("api", "www", "app", "embed", "widget", "v1", "v0"):
                        discovered[platform] = slug
                        break

        if discovered:
            logger.info("Discovered ATS from %s: %s", website_url, discovered)

        return discovered

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
                structured_workplace_type=posting.get("workplaceType", ""),
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
            # Extract structured address if available
            address = job.get("address") or {}
            postal = address.get("postalAddress") or {}

            jobs.append(JobPost(
                external_id=str(job.get("id", "")),
                title=job.get("title", ""),
                department=job.get("department", ""),
                location=job.get("location", ""),
                employment_type=job.get("employmentType", ""),
                description_text=_strip_html(job.get("descriptionHtml", "")),
                apply_url=job.get("jobUrl", ""),
                posted_at=job.get("publishedAt"),
                structured_is_remote=job.get("isRemote"),
                structured_workplace_type=job.get("workplaceType", ""),
                structured_country=postal.get("addressCountry", ""),
                structured_region=postal.get("addressRegion", ""),
                structured_city=postal.get("addressLocality", ""),
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
            loc = job.get("location", {})
            loc_city = ""
            loc_region = ""
            loc_country = ""
            loc_country_code = ""
            if isinstance(loc, dict):
                loc_city = loc.get("city", "")
                loc_region = loc.get("region", "")
                loc_country = loc.get("country", "")
                loc_country_code = loc.get("country_code", "")

            location_parts = [p for p in [loc_city, loc_region, loc_country] if p]
            location_str = ", ".join(location_parts)

            # Workable has telecommuting bool and workplace_type enum
            is_remote = job.get("telecommuting")
            workplace_type = job.get("workplace_type", "")

            jobs.append(JobPost(
                external_id=str(job.get("shortcode", job.get("id", ""))),
                title=job.get("title", ""),
                department=job.get("department", ""),
                location=location_str,
                description_text="",  # Workable widget doesn't include description by default
                apply_url=job.get("url", ""),
                structured_is_remote=is_remote,
                structured_workplace_type=workplace_type,
                structured_country=loc_country,
                structured_country_code=loc_country_code,
                structured_region=loc_region,
                structured_city=loc_city,
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
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _resolve_url(base_url: str, link: str) -> str | None:
    """Resolve a relative or absolute link against a base URL."""
    if not link:
        return None
    # Skip javascript: and mailto: links
    if link.startswith(("javascript:", "mailto:", "#")):
        return None
    # Absolute URL
    if link.startswith(("http://", "https://")):
        return link
    # Relative URL
    return urljoin(base_url, link)
