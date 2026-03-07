"""Celery tasks for ATS job board probing and refreshing."""

import logging

from celery import shared_task
from django.utils import timezone

from apps.prospects.models import Organization

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

    # Also try the org name (without spaces) as a fallback slug
    slugs_to_try = [slug]
    if org.name and org.name.lower().replace(" ", "") != slug:
        slugs_to_try.append(org.name.lower().replace(" ", ""))
    if org.name and org.name.lower().replace(" ", "-") != slug:
        slugs_to_try.append(org.name.lower().replace(" ", "-"))

    for try_slug in slugs_to_try:
        results = client.probe_company(try_slug)

        for platform, found in results.items():
            if not found:
                continue

            mapping, created = ATSMapping.objects.update_or_create(
                ats_platform=platform,
                ats_slug=try_slug,
                defaults={
                    "organization": org,
                    "company_name": org.name or org.github_login,
                    "is_verified": True,
                    "last_checked_at": timezone.now(),
                },
            )

            # Fetch and store jobs
            _refresh_mapping_jobs(client, mapping)

    logger.info("probe_org_ats completed for org %s (%s)", org_id, org.github_login)


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
            posted_at = parse_datetime(job_post.posted_at)

        JobListing.objects.update_or_create(
            ats_mapping=mapping,
            external_id=job_post.external_id,
            defaults={
                "title": job_post.title[:500],
                "department": job_post.department[:200],
                "location": job_post.location[:300],
                "employment_type": job_post.employment_type[:50],
                "description_text": job_post.description_text,
                "apply_url": job_post.apply_url[:500],
                "detected_techs": techs,
                "is_active": True,
                "posted_at": posted_at,
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
