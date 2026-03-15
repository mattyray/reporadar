"""Celery tasks for ATS job board probing and refreshing."""

import logging

from celery import shared_task
from django.utils import timezone

from apps.prospects.models import Organization

from .location_parser import parse_location, parse_structured_location
from .models import ATSMapping, JobListing
from .tech_extraction import extract_techs_from_text

logger = logging.getLogger(__name__)


@shared_task
def probe_org_ats(org_id: int):
    """Probe all ATS platforms for an organization's job board.

    Tries the org's github_login as the slug across Greenhouse, Lever, Ashby, Workable.
    Creates ATSMapping records for any matches and fetches their jobs.
    """
    from providers.ats_client import ATSClient

    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        logger.warning("probe_org_ats: Organization %s not found", org_id)
        return

    client = ATSClient()
    slug = org.github_login.lower()
    found_platforms = set()

    def _save_and_fetch(platform, ats_slug):
        """Create/update mapping and fetch jobs for a discovered ATS board."""
        mapping, created = ATSMapping.objects.update_or_create(
            ats_platform=platform,
            ats_slug=ats_slug,
            defaults={
                "organization": org,
                "company_name": org.name or org.github_login,
                "is_verified": True,
                "last_checked_at": timezone.now(),
            },
        )
        _refresh_mapping_jobs(client, mapping)
        found_platforms.add(platform)

    # Strategy 1: Try slug variants (github_login, name variants)
    slugs_to_try = _generate_slug_candidates(slug, org.name)

    for try_slug in slugs_to_try:
        results = client.probe_company(try_slug)
        for platform, found in results.items():
            if found and platform not in found_platforms:
                _save_and_fetch(platform, try_slug)

    # Strategy 2: Scrape company website for ATS URLs (catches mismatched slugs)
    if org.website:
        discovered = client.discover_ats_from_website(org.website)
        for platform, ats_slug in discovered.items():
            if platform not in found_platforms:
                # Verify the discovered slug actually works
                verify = client.probe_company(ats_slug)
                if verify.get(platform):
                    _save_and_fetch(platform, ats_slug)

    logger.info(
        "probe_org_ats completed for org %s (%s): found %s",
        org_id, org.github_login, list(found_platforms) or "none",
    )


CORPORATE_SUFFIXES = {
    "inc", "llc", "ltd", "corp", "corporation", "co", "company",
    "group", "holdings", "enterprises", "solutions", "technologies",
    "international",
}


def _generate_slug_candidates(github_login: str, org_name: str | None) -> list[str]:
    """Generate slug candidates for ATS board discovery.

    Tries multiple variations to maximize the chance of finding a match:
    - github_login as-is
    - org name: no spaces, with dashes
    - org name: stripped of corporate suffixes (Inc, LLC, etc.)
    - first word only
    """
    import re

    candidates = [github_login]
    seen = {github_login}

    def _add(slug: str):
        s = slug.strip().lower()
        # Only valid slug chars
        s = re.sub(r"[^a-z0-9-]", "", s)
        s = re.sub(r"-+", "-", s).strip("-")
        if s and s not in seen and len(s) >= 2:
            seen.add(s)
            candidates.append(s)

    if not org_name:
        return candidates

    name = org_name.strip()

    # Basic variants
    _add(name.replace(" ", ""))
    _add(name.replace(" ", "-"))

    # Strip corporate suffixes
    words = name.split()
    stripped = [w for w in words if w.lower().rstrip(".,") not in CORPORATE_SUFFIXES]
    if stripped and len(stripped) < len(words):
        _add("".join(stripped))
        _add("-".join(stripped))

    # First word only (e.g., "Stripe" from "Stripe Inc")
    if words:
        _add(words[0])

    # First two words (e.g., "palo-alto" from "Palo Alto Networks")
    if len(words) >= 2:
        _add(f"{words[0]}-{words[1]}")

    return candidates


@shared_task
def refresh_jobs(ats_mapping_id: int):
    """Refresh job listings for a single ATS mapping."""
    from providers.ats_client import ATSClient

    try:
        mapping = ATSMapping.objects.get(pk=ats_mapping_id)
    except ATSMapping.DoesNotExist:
        logger.warning("refresh_jobs: ATSMapping %s not found", ats_mapping_id)
        return

    client = ATSClient()
    _refresh_mapping_jobs(client, mapping)


@shared_task
def refresh_all_jobs():
    """Refresh all verified ATS mappings. Schedule via Celery beat (daily)."""
    mapping_ids = list(
        ATSMapping.objects.filter(is_verified=True).values_list("id", flat=True)
    )
    for mapping_id in mapping_ids:
        refresh_jobs.delay(mapping_id)

    logger.info("refresh_all_jobs: queued %d mappings", len(mapping_ids))


@shared_task
def fetch_unfetched_mappings(batch_size=50):
    """Fetch jobs for ATS mappings that have never been checked.

    Queues in batches to avoid hammering ATS APIs. Each batch of refresh_jobs
    tasks runs with a countdown stagger so they don't all fire at once.
    """
    mapping_ids = list(
        ATSMapping.objects.filter(last_checked_at__isnull=True).values_list("id", flat=True)
    )
    if not mapping_ids:
        return

    logger.info("fetch_unfetched_mappings: found %d mappings to fetch", len(mapping_ids))
    for i, mapping_id in enumerate(mapping_ids[:batch_size]):
        # Stagger tasks: 2 seconds apart to respect rate limits
        refresh_jobs.apply_async(args=[mapping_id], countdown=i * 2)

    # If there are more, schedule the next batch in 5 minutes
    remaining = len(mapping_ids) - batch_size
    if remaining > 0:
        logger.info("fetch_unfetched_mappings: %d remaining, scheduling next batch", remaining)
        fetch_unfetched_mappings.apply_async(
            kwargs={"batch_size": batch_size}, countdown=300
        )



@shared_task
def reprocess_all_job_techs(batch_size=1000):
    """Re-run tech extraction on all active jobs.

    Useful after updating TECH_KEYWORDS to backfill detected_techs.
    """
    from .models import JobListing
    from .tech_extraction import extract_techs_from_text

    total = 0
    qs = JobListing.objects.filter(is_active=True).exclude(
        description_text=""
    ).only("id", "description_text", "detected_techs")

    batch = []
    for job in qs.iterator(chunk_size=batch_size):
        new_techs = extract_techs_from_text(job.description_text)
        if new_techs != job.detected_techs:
            job.detected_techs = new_techs
            batch.append(job)

        if len(batch) >= batch_size:
            JobListing.objects.bulk_update(batch, ["detected_techs"])
            total += len(batch)
            batch = []

    if batch:
        JobListing.objects.bulk_update(batch, ["detected_techs"])
        total += len(batch)

    logger.info("reprocess_all_job_techs: updated %d jobs", total)
    return total


# ---------------------------------------------------------------------------
# External job board tasks
# ---------------------------------------------------------------------------


@shared_task
def fetch_remoteok_jobs():
    """Fetch and store jobs from RemoteOK."""
    from providers.job_boards import fetch_remoteok_jobs as _fetch

    jobs = _fetch()
    _store_external_jobs(jobs)


@shared_task
def fetch_remotive_jobs():
    """Fetch and store jobs from Remotive."""
    from providers.job_boards import fetch_remotive_jobs as _fetch

    jobs = _fetch()
    _store_external_jobs(jobs)


@shared_task
def fetch_wwr_jobs():
    """Fetch and store jobs from We Work Remotely."""
    from providers.job_boards import fetch_wwr_jobs as _fetch

    jobs = _fetch()
    _store_external_jobs(jobs)


@shared_task
def fetch_hn_hiring(thread_id=None):
    """Fetch and store jobs from HN Who's Hiring thread."""
    from providers.job_boards import fetch_hn_hiring_jobs as _fetch

    jobs = _fetch(thread_id=thread_id)
    _store_external_jobs(jobs)


def _store_external_jobs(jobs):
    """Store a list of ExternalJobPost objects into the JobListing table."""
    if not jobs:
        return

    source = jobs[0].source
    seen_ids = set()

    for job in jobs:
        techs = extract_techs_from_text(job.description_text)
        # Also include tags if available (RemoteOK provides these)
        if hasattr(job, "tags") and job.tags:
            from .tech_extraction import TECH_KEYWORDS

            for tag in job.tags:
                canonical = TECH_KEYWORDS.get(tag.lower())
                if canonical and canonical not in techs:
                    techs.append(canonical)

        posted_at = None
        if job.posted_at:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz

            posted_at = parse_datetime(str(job.posted_at))
            if posted_at and posted_at.tzinfo is None:
                posted_at = tz.make_aware(posted_at)

        # Parse location — use structured hints from boards that provide them
        loc = parse_structured_location(
            location_str=job.location,
            is_remote=job.structured_is_remote,
        )
        # Override remote_region if the board gave us a specific one
        if job.structured_remote_region:
            loc.remote_region = job.structured_remote_region

        JobListing.objects.update_or_create(
            source=job.source,
            external_id=job.external_id,
            defaults={
                "ats_mapping": None,
                "company_name": job.company_name[:200],
                "title": job.title[:500],
                "department": job.department[:200],
                "location": job.location[:300],
                "employment_type": job.employment_type[:50],
                "salary": job.salary[:200],
                "description_text": job.description_text,
                "apply_url": job.apply_url[:500] if job.apply_url else "",
                "source_url": job.source_url[:500] if job.source_url else "",
                "detected_techs": techs,
                "is_active": True,
                "posted_at": posted_at,
                "is_remote": loc.is_remote,
                "workplace_type": loc.workplace_type,
                "remote_region": loc.remote_region,
                "country_codes": loc.country_codes,
                "loc_region": loc.region[:100],
                "loc_city": loc.city[:150],
            },
        )
        seen_ids.add(job.external_id)

    # Mark jobs from this source that we didn't see as inactive
    if seen_ids:
        stale = JobListing.objects.filter(
            source=source, is_active=True
        ).exclude(external_id__in=seen_ids)
        stale_count = stale.count()
        if stale_count:
            stale.update(is_active=False)
            logger.info("Marked %d stale %s jobs as inactive", stale_count, source)

    logger.info("Stored %d %s jobs", len(seen_ids), source)


def _refresh_mapping_jobs(client, mapping: ATSMapping):
    """Fetch jobs from ATS and sync with database."""
    from providers.ats_client import ATSClient

    jobs = client.fetch_jobs(mapping.ats_platform, mapping.ats_slug)

    # Track which external IDs we see in this refresh
    seen_ids = set()

    for job_post in jobs:
        techs = extract_techs_from_text(job_post.description_text)

        posted_at = None
        if job_post.posted_at:
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz

            posted_at = parse_datetime(job_post.posted_at)
            if posted_at and posted_at.tzinfo is None:
                posted_at = tz.make_aware(posted_at)

        # Parse location — use structured data if the platform provides it
        loc = parse_structured_location(
            location_str=job_post.location or "",
            is_remote=job_post.structured_is_remote,
            workplace_type=job_post.structured_workplace_type or None,
            country=job_post.structured_country,
            country_code=job_post.structured_country_code,
            region=job_post.structured_region,
            city=job_post.structured_city,
        )

        JobListing.objects.update_or_create(
            ats_mapping=mapping,
            external_id=job_post.external_id,
            defaults={
                "source": "ats",
                "company_name": mapping.company_name,
                "title": (job_post.title or "")[:500],
                "department": (job_post.department or "")[:200],
                "location": (job_post.location or "")[:300],
                "employment_type": (job_post.employment_type or "")[:50],
                "description_text": job_post.description_text or "",
                "apply_url": (job_post.apply_url or "")[:500],
                "detected_techs": techs,
                "is_active": True,
                "posted_at": posted_at,
                "is_remote": loc.is_remote,
                "workplace_type": loc.workplace_type,
                "remote_region": loc.remote_region,
                "country_codes": loc.country_codes,
                "loc_region": loc.region[:100],
                "loc_city": loc.city[:150],
            },
        )
        seen_ids.add(job_post.external_id)

    # Mark jobs we didn't see as inactive (they were likely removed)
    if seen_ids:
        mapping.jobs.exclude(external_id__in=seen_ids).update(is_active=False)

    mapping.last_checked_at = timezone.now()
    mapping.save(update_fields=["last_checked_at"])

    logger.info(
        "Refreshed %s/%s: %d active jobs",
        mapping.ats_platform,
        mapping.ats_slug,
        len(seen_ids),
    )
