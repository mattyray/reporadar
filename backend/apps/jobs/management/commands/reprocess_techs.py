"""Re-run tech extraction on all active job listings.

Usage:
    python manage.py reprocess_techs                # process all active jobs
    python manage.py reprocess_techs --batch 500    # custom batch size
    python manage.py reprocess_techs --dry-run      # show changes without saving
"""

from django.core.management.base import BaseCommand
from django.db import connection

from apps.jobs.models import JobListing
from apps.jobs.tech_extraction import extract_techs_from_text


class Command(BaseCommand):
    help = "Re-run tech extraction on all active jobs (use after updating TECH_KEYWORDS)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch", type=int, default=500, help="Batch size (default: 500)"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would change without saving"
        )

    def handle(self, *args, **options):
        batch_size = options["batch"]
        dry_run = options["dry_run"]

        total = (
            JobListing.objects.filter(is_active=True)
            .exclude(description_text="")
            .count()
        )
        self.stdout.write(f"Total active jobs with descriptions: {total}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be saved."))

        updated = 0
        processed = 0
        last_id = 0

        while True:
            # Close stale connections before each batch to avoid Railway timeouts
            connection.close()

            batch = list(
                JobListing.objects.filter(
                    is_active=True, id__gt=last_id
                )
                .exclude(description_text="")
                .order_by("id")
                .values_list("id", "description_text", "detected_techs")[:batch_size]
            )
            if not batch:
                break

            bulk_updates = []
            for job_id, description, old_techs in batch:
                new_techs = extract_techs_from_text(description or "")
                old_sorted = sorted(old_techs) if old_techs else []
                if new_techs != old_sorted:
                    if not dry_run:
                        bulk_updates.append(
                            JobListing(id=job_id, detected_techs=new_techs)
                        )
                    updated += 1
                last_id = job_id

            if bulk_updates:
                JobListing.objects.bulk_update(
                    bulk_updates, ["detected_techs"], batch_size=batch_size
                )

            processed += len(batch)
            if processed % 5000 == 0:
                self.stdout.write(f"  {processed}/{total} processed, {updated} updated...")

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"Done. {verb} {updated}/{total} jobs.")
        )
