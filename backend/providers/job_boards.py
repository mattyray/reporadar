"""Adapters for external job boards (RemoteOK, Remotive, We Work Remotely, HN).

Each adapter fetches jobs and returns a list of normalized JobPost dataclasses,
matching the same interface used by the ATS client.
"""

import logging
import re
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "RepoRadar/1.0 (job aggregator)"}
REQUEST_TIMEOUT = 30


@dataclass
class ExternalJobPost:
    """Normalized job post from an external board."""

    external_id: str
    source: str  # remoteok, remotive, wwr, hn
    company_name: str
    title: str
    department: str = ""
    location: str = ""
    employment_type: str = ""
    salary: str = ""
    description_text: str = ""
    apply_url: str = ""
    source_url: str = ""
    posted_at: str | None = None
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# RemoteOK
# ---------------------------------------------------------------------------

def fetch_remoteok_jobs() -> list[ExternalJobPost]:
    """Fetch all jobs from RemoteOK API.

    API: GET https://remoteok.com/api
    No auth, returns JSON array. First element is metadata (skip it).
    Attribution required: must link back to RemoteOK.
    """
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("RemoteOK fetch failed: %s", e)
        return []

    jobs = []
    for item in data:
        # First item is often metadata/legal notice
        if not isinstance(item, dict) or "id" not in item:
            continue

        salary = ""
        if item.get("salary_min") and item.get("salary_max"):
            salary = f"${item['salary_min']:,} - ${item['salary_max']:,}"
        elif item.get("salary_min"):
            salary = f"${item['salary_min']:,}+"

        jobs.append(
            ExternalJobPost(
                external_id=f"rok-{item['id']}",
                source="remoteok",
                company_name=item.get("company", ""),
                title=item.get("position", item.get("title", "")),
                location=item.get("location", "Remote"),
                salary=salary,
                description_text=_strip_html(item.get("description", "")),
                apply_url=item.get("apply_url") or item.get("url", ""),
                source_url=item.get("url", ""),
                posted_at=item.get("date"),
                tags=item.get("tags", []),
            )
        )

    logger.info("RemoteOK: fetched %d jobs", len(jobs))
    return jobs


# ---------------------------------------------------------------------------
# Remotive
# ---------------------------------------------------------------------------

def fetch_remotive_jobs() -> list[ExternalJobPost]:
    """Fetch software dev jobs from Remotive API.

    API: GET https://remotive.com/api/remote-jobs?category=software-dev
    No auth. Rate limit: 2 req/min. Attribution required.
    """
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("Remotive fetch failed: %s", e)
        return []

    jobs_data = data.get("jobs", [])
    jobs = []
    for item in jobs_data:
        jobs.append(
            ExternalJobPost(
                external_id=f"rem-{item['id']}",
                source="remotive",
                company_name=item.get("company_name", ""),
                title=item.get("title", ""),
                location=item.get("candidate_required_location", ""),
                employment_type=_normalize_job_type(item.get("job_type", "")),
                salary=item.get("salary", ""),
                description_text=_strip_html(item.get("description", "")),
                apply_url=item.get("url", ""),
                source_url=item.get("url", ""),
                posted_at=item.get("publication_date"),
            )
        )

    logger.info("Remotive: fetched %d jobs", len(jobs))
    return jobs


# ---------------------------------------------------------------------------
# We Work Remotely
# ---------------------------------------------------------------------------

def fetch_wwr_jobs() -> list[ExternalJobPost]:
    """Fetch programming jobs from We Work Remotely RSS feed.

    Feed: https://weworkremotely.com/categories/remote-programming-jobs.rss
    No auth. Attribution required.
    """
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser not installed — pip install feedparser")
        return []

    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    ]

    jobs = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logger.error("WWR fetch failed for %s: %s", feed_url, e)
            continue

        for entry in feed.entries:
            # WWR entry IDs are URLs
            entry_id = entry.get("id", entry.get("link", ""))
            # Extract company from title format: "Company: Job Title"
            title = entry.get("title", "")
            company = ""
            if ": " in title:
                company, title = title.split(": ", 1)

            description = entry.get("summary", entry.get("description", ""))

            jobs.append(
                ExternalJobPost(
                    external_id=f"wwr-{_hash_id(entry_id)}",
                    source="wwr",
                    company_name=company.strip(),
                    title=title.strip(),
                    location="Remote",
                    description_text=_strip_html(description),
                    apply_url=entry.get("link", ""),
                    source_url=entry.get("link", ""),
                    posted_at=entry.get("published"),
                )
            )

    logger.info("WWR: fetched %d jobs", len(jobs))
    return jobs


# ---------------------------------------------------------------------------
# HackerNews Who's Hiring
# ---------------------------------------------------------------------------

# Regex for the common HN format: Company | Role | Location | REMOTE | ...
HN_HEADER_RE = re.compile(
    r"^(?P<company>[^|]+)\|(?P<rest>.+)$",
    re.MULTILINE,
)


def fetch_hn_hiring_jobs(thread_id: str | None = None) -> list[ExternalJobPost]:
    """Fetch job postings from the latest HN 'Who is Hiring?' thread.

    Uses Algolia HN API to get the thread and all child comments.
    Parses pipe-delimited first lines with regex, extracts techs from body.

    Args:
        thread_id: Specific thread ID. If None, discovers the latest thread.
    """
    if not thread_id:
        thread_id = _find_latest_hn_thread()
        if not thread_id:
            logger.error("Could not find latest HN Who is Hiring thread")
            return []

    try:
        resp = requests.get(
            f"https://hn.algolia.com/api/v1/items/{thread_id}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("HN Algolia fetch failed: %s", e)
        return []

    children = data.get("children", [])
    jobs = []

    for comment in children:
        if comment.get("type") != "comment":
            continue

        text = comment.get("text", "")
        if not text:
            continue

        # Strip HTML tags from HN comment
        text_clean = _strip_html(text)

        parsed = _parse_hn_comment(text_clean)
        if not parsed:
            continue

        comment_id = str(comment.get("id", ""))
        hn_url = f"https://news.ycombinator.com/item?id={comment_id}"

        jobs.append(
            ExternalJobPost(
                external_id=f"hn-{comment_id}",
                source="hn",
                company_name=parsed["company"],
                title=parsed.get("role", ""),
                location=parsed.get("location", ""),
                description_text=text_clean,
                apply_url=parsed.get("apply_url", hn_url),
                source_url=hn_url,
                posted_at=comment.get("created_at"),
            )
        )

    logger.info("HN Who's Hiring: parsed %d jobs from thread %s", len(jobs), thread_id)
    return jobs


def _find_latest_hn_thread() -> str | None:
    """Find the most recent 'Ask HN: Who is hiring?' thread via Algolia."""
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": '"Ask HN: Who is hiring?"',
                "tags": "ask_hn",
                "hitsPerPage": 5,
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as e:
        logger.error("HN thread search failed: %s", e)
        return None

    for hit in hits:
        title = hit.get("title", "").lower()
        if "who is hiring" in title and "ask hn" in title.lower():
            return str(hit["objectID"])

    return None


def _parse_hn_comment(text: str) -> dict | None:
    """Parse a HN Who's Hiring comment into structured fields.

    Expected format (first line): Company | Role | Location | REMOTE | Full Time
    Returns dict with company, role, location, remote, or None if unparseable.
    """
    lines = text.strip().split("\n")
    if not lines:
        return None

    first_line = lines[0].strip()

    # Must have at least one pipe separator
    if "|" not in first_line:
        return None

    parts = [p.strip() for p in first_line.split("|")]
    if not parts or not parts[0]:
        return None

    result = {"company": parts[0]}

    # Parse remaining parts — they can be in any order
    remote_keywords = {"remote", "onsite", "hybrid", "on-site", "on site"}
    for part in parts[1:]:
        part_lower = part.lower().strip()
        if not part_lower:
            continue
        if part_lower in remote_keywords or "remote" in part_lower:
            if "remote" in part_lower:
                result.setdefault("location", "Remote")
        elif part_lower in {"full time", "full-time", "part time", "part-time", "contract", "internship"}:
            pass  # employment type — skip for now
        elif "role" not in result:
            result["role"] = part
        elif "location" not in result:
            result["location"] = part

    # Look for apply URL in the body
    url_match = re.search(r'https?://\S+', text)
    if url_match:
        result["apply_url"] = url_match.group(0).rstrip(".,;)")

    return result


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _strip_html(html: str) -> str:
    """Simple HTML tag stripping."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _hash_id(value: str) -> str:
    """Create a short hash for use as external_id."""
    import hashlib

    return hashlib.md5(value.encode()).hexdigest()[:12]


def _normalize_job_type(job_type: str) -> str:
    """Normalize job type strings."""
    mapping = {
        "full_time": "Full-time",
        "part_time": "Part-time",
        "contract": "Contract",
        "freelance": "Freelance",
        "internship": "Internship",
    }
    return mapping.get(job_type, job_type)
