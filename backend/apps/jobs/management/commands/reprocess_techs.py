"""Re-run tech extraction on all active job listings.

Usage:
    python manage.py reprocess_techs           # process all active jobs
    python manage.py reprocess_techs --offset 60000  # resume from offset
    python manage.py reprocess_techs --batch 500     # custom batch size
"""

from django.core.management.base import BaseCommand

from apps.jobs.models import JobListing
from apps.jobs.tech_extraction import extract_techs_from_text


class Command(BaseCommand):
    help = "Re-run tech extraction on all active jobs (use after updating TECH_KEYWORDS)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch", type=int, default=1000, help="Batch size for bulk_update (default: 1000)"
        )
        parser.add_argument(
            "--offset", type=int, default=0, help="Skip first N jobs (resume from previous run)"
        )

    def handle(self, *args, **options):
        batch_size = options["batch"]
        offset = options["offset"]

        qs = (
            JobListing.objects.filter(is_active=True)
            .exclude(description_text="")
            .order_by("id")
            .only("id", "description_text", "detected_techs")
        )

        total = qs.count()
        self.stdout.write(f"Total active jobs with descriptions: {total}")

        if offset:
            qs = qs[offset:]
            self.stdout.write(f"Starting from offset {offset}")

        updated = 0
        processed = 0
        batch = []

        for job in qs.iterator(chunk_size=batch_size):
            new_techs = extract_techs_from_text(job.description_text)
            if new_techs != job.detected_techs:
                job.detected_techs = new_techs
                batch.append(job)

            processed += 1

            if len(batch) >= batch_size:
                JobListing.objects.bulk_update(batch, ["detected_techs"])
                updated += len(batch)
                batch = []
                self.stdout.write(f"  processed {processed + offset}, updated {updated}...")

        if batch:
            JobListing.objects.bulk_update(batch, ["detected_techs"])
            updated += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f"Done! Processed {processed} jobs, updated {updated}."
        ))
