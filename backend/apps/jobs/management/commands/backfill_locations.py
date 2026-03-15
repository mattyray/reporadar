"""Backfill structured location fields on all active job listings.

Parses the raw `location` string into is_remote, workplace_type, remote_region,
country_codes, loc_region, and loc_city.

Usage:
    python manage.py backfill_locations                # process all active jobs
    python manage.py backfill_locations --batch 500    # custom batch size
    python manage.py backfill_locations --start-id 0   # resume from a specific ID
    python manage.py backfill_locations --dry-run      # show changes without saving
"""

import time

from django.core.management.base import BaseCommand
from django.db import connection

from apps.jobs.location_parser import parse_location
from apps.jobs.models import JobListing


class Command(BaseCommand):
    help = "Backfill structured location fields on all active jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch", type=int, default=500, help="Batch size (default: 500)"
        )
        parser.add_argument(
            "--start-id", type=int, default=0, help="Resume from this job ID"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would change without saving"
        )

    def handle(self, *args, **options):
        batch_size = options["batch"]
        dry_run = options["dry_run"]
        last_id = options["start_id"]

        total = JobListing.objects.filter(is_active=True).count()
        self.stdout.write(f"Total active jobs: {total}")
        if last_id:
            self.stdout.write(f"Resuming from ID > {last_id}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be saved."))

        updated = 0
        processed = 0
        errors = 0

        while True:
            try:
                connection.close()

                batch = list(
                    JobListing.objects.filter(is_active=True, id__gt=last_id)
                    .order_by("id")
                    .values_list("id", "location")[:batch_size]
                )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"DB error fetching batch after id={last_id}: {e}")
                )
                if errors > 10:
                    self.stdout.write(self.style.ERROR("Too many errors, stopping."))
                    break
                time.sleep(2 ** min(errors, 5))
                continue

            if not batch:
                break

            bulk_updates = []
            for job_id, location_str in batch:
                try:
                    loc = parse_location(location_str or "")
                    if not dry_run:
                        job = JobListing(
                            id=job_id,
                            is_remote=loc.is_remote,
                            workplace_type=loc.workplace_type,
                            remote_region=loc.remote_region,
                            country_codes=loc.country_codes,
                            loc_region=loc.region[:100],
                            loc_city=loc.city[:150],
                        )
                        bulk_updates.append(job)
                    updated += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Job {job_id}: parse error: {e}")
                    )
                last_id = job_id

            if bulk_updates:
                try:
                    connection.close()
                    JobListing.objects.bulk_update(
                        bulk_updates,
                        ["is_remote", "workplace_type", "remote_region",
                         "country_codes", "loc_region", "loc_city"],
                        batch_size=batch_size,
                    )
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"bulk_update failed at id={last_id}: {e}. "
                            f"Resume with --start-id {batch[0][0]}"
                        )
                    )
                    if errors > 10:
                        break
                    time.sleep(2 ** min(errors, 5))
                    continue

            processed += len(batch)
            if processed % 5000 == 0 or processed == len(batch):
                self.stdout.write(
                    f"  {processed}/{total} processed, {updated} updated, "
                    f"last_id={last_id}, errors={errors}"
                )

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {verb} {updated}/{total} jobs. Errors: {errors}. "
                f"Last ID: {last_id}"
            )
        )
