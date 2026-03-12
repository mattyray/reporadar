"""Seed ATSMapping records for well-known tech companies.

Usage: python manage.py seed_ats_mappings
       python manage.py seed_ats_mappings --fetch  (also fetch jobs immediately)
"""

from django.core.management.base import BaseCommand

from apps.jobs.models import ATSMapping

# Known tech company ATS slugs.
# Format: (company_name, platform, slug)
KNOWN_MAPPINGS = [
    # Greenhouse companies
    ("Stripe", "greenhouse", "stripe"),
    ("Cloudflare", "greenhouse", "cloudflare"),
    ("Figma", "greenhouse", "figma"),
    ("Datadog", "greenhouse", "datadog"),
    ("GitLab", "greenhouse", "gitlab"),
    ("Twilio", "greenhouse", "twilio"),
    ("Airtable", "greenhouse", "airtable"),
    ("Gusto", "greenhouse", "gusto"),
    ("Brex", "greenhouse", "brex"),
    ("Scale AI", "greenhouse", "scaleai"),
    ("Anthropic", "greenhouse", "anthropic"),
    ("Vercel", "greenhouse", "vercel"),
    ("Postman", "greenhouse", "postman"),
    ("PlanetScale", "greenhouse", "planetscale"),
    ("LaunchDarkly", "greenhouse", "launchdarkly"),
    # Lever companies
    ("Netflix", "lever", "netflix"),
    ("Spotify", "lever", "spotify"),
    ("Plaid", "lever", "plaid"),
    ("Weights & Biases", "lever", "wandb"),
    ("Replit", "lever", "replit"),
    ("Railway", "lever", "railway"),
    # Ashby companies
    ("Ashby", "ashby", "ashby"),
    ("Notion", "ashby", "notion"),
    ("OpenAI", "ashby", "openai"),
    ("Linear", "ashby", "linear"),
    ("Ramp", "ashby", "ramp"),
    ("Sentry", "ashby", "sentry"),
    ("Render", "ashby", "render"),
    ("Supabase", "ashby", "supabase"),
    ("Retool", "ashby", "retool"),
    ("Snyk", "ashby", "snyk"),
    ("Loom", "ashby", "loom"),
    ("Deel", "ashby", "deel"),
    ("Vanta", "ashby", "vanta"),
    ("Faire", "ashby", "faire"),
    ("Liveblocks", "ashby", "liveblocks"),
    ("Fly.io", "ashby", "fly"),
    ("Turso", "ashby", "turso"),
    # Workable companies
    ("Workable", "workable", "workable"),
    ("HashiCorp", "workable", "hashicorp"),
]


class Command(BaseCommand):
    help = "Seed ATSMapping table with known tech company job board slugs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Also fetch jobs for each mapping after seeding.",
        )

    def handle(self, *args, **options):
        created_count = 0
        for company_name, platform, slug in KNOWN_MAPPINGS:
            _, created = ATSMapping.objects.get_or_create(
                ats_platform=platform,
                ats_slug=slug,
                defaults={
                    "company_name": company_name,
                    "is_verified": False,  # Will be verified on first fetch
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created_count} new ATS mappings ({len(KNOWN_MAPPINGS)} total).")
        )

        if options["fetch"]:
            from providers.ats_client import ATSClient
            from apps.jobs.tasks import _refresh_mapping_jobs

            client = ATSClient()
            total_jobs = 0
            for mapping in ATSMapping.objects.all():
                try:
                    _refresh_mapping_jobs(client, mapping)
                    job_count = mapping.jobs.filter(is_active=True).count()
                    total_jobs += job_count
                    if job_count:
                        self.stdout.write(f"  {mapping.company_name} ({mapping.ats_platform}): {job_count} jobs")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  {mapping.company_name}: failed ({e})"))
            self.stdout.write(self.style.SUCCESS(f"Done. {total_jobs} total active jobs indexed."))
