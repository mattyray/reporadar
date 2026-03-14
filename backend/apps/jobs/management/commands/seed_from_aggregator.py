"""Seed ATSMapping records from open-source slug lists.

Downloads company slug lists from the Feashliaa/job-board-aggregator GitHub repo
and creates ATSMapping records for each. Does NOT fetch jobs — use --fetch or
the fetch_unfetched_mappings Celery task to populate jobs afterward.

Usage:
    python manage.py seed_from_aggregator
    python manage.py seed_from_aggregator --fetch   (also queue job fetching)
    python manage.py seed_from_aggregator --platform greenhouse
"""

import logging

import requests
from django.core.management.base import BaseCommand

from apps.jobs.models import ATSMapping

logger = logging.getLogger(__name__)

# Raw GitHub URLs for the aggregator's slug lists
AGGREGATOR_BASE = (
    "https://raw.githubusercontent.com/Feashliaa/job-board-aggregator/main/data"
)

PLATFORM_FILES = {
    "greenhouse": f"{AGGREGATOR_BASE}/greenhouse_companies.json",
    "lever": f"{AGGREGATOR_BASE}/lever_companies.json",
    "ashby": f"{AGGREGATOR_BASE}/ashby_companies.json",
}

# Slugs that are clearly not real companies
SKIP_SLUGS = {"api", "www", "app", "embed", "widget", "v1", "v0", "test", "demo", ""}


def slug_to_company_name(slug):
    """Convert a slug like 'acme-corp' to 'Acme Corp'."""
    return slug.replace("-", " ").replace("_", " ").title()


class Command(BaseCommand):
    help = "Seed ATSMapping table from open-source slug aggregator lists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--platform",
            type=str,
            choices=list(PLATFORM_FILES.keys()),
            help="Only seed a specific platform.",
        )
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Queue Celery tasks to fetch jobs for new mappings.",
        )

    def handle(self, *args, **options):
        platform_filter = options.get("platform")
        platforms = (
            {platform_filter: PLATFORM_FILES[platform_filter]}
            if platform_filter
            else PLATFORM_FILES
        )

        total_created = 0
        total_skipped = 0

        for platform, url in platforms.items():
            self.stdout.write(f"Fetching {platform} slugs...")
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                slugs = response.json()
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  Failed to fetch {platform}: {e}")
                )
                continue

            if not isinstance(slugs, list):
                self.stdout.write(
                    self.style.WARNING(f"  Unexpected format for {platform}")
                )
                continue

            created = 0
            skipped = 0
            for slug in slugs:
                slug = str(slug).strip().lower()
                if slug in SKIP_SLUGS or len(slug) < 2:
                    skipped += 1
                    continue

                _, was_created = ATSMapping.objects.get_or_create(
                    ats_platform=platform,
                    ats_slug=slug,
                    defaults={
                        "company_name": slug_to_company_name(slug),
                        "is_verified": False,
                    },
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

            self.stdout.write(
                f"  {platform}: {created} new, {skipped} skipped "
                f"({len(slugs)} total in list)"
            )
            total_created += created
            total_skipped += skipped

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {total_created} new mappings created, "
                f"{total_skipped} already existed or skipped."
            )
        )

        if options["fetch"]:
            from apps.jobs.tasks import fetch_unfetched_mappings

            self.stdout.write("Queuing job fetch tasks...")
            fetch_unfetched_mappings.delay()
            self.stdout.write(
                self.style.SUCCESS("Fetch tasks queued. Jobs will populate in background.")
            )
