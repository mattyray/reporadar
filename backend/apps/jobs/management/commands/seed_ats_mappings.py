"""Seed ATSMapping records for well-known tech companies.

Usage: python manage.py seed_ats_mappings
       python manage.py seed_ats_mappings --fetch  (also fetch jobs immediately)
"""

from django.core.management.base import BaseCommand

from apps.jobs.models import ATSMapping
from apps.jobs.tasks import refresh_jobs

# Known tech company ATS slugs.
# Format: (company_name, platform, slug)
KNOWN_MAPPINGS = [
    # Greenhouse companies
    ("Stripe", "greenhouse", "stripe"),
    ("Cloudflare", "greenhouse", "cloudflare"),
    ("Figma", "greenhouse", "figma"),
    ("Notion", "greenhouse", "notion"),
    ("Datadog", "greenhouse", "datadog"),
    ("GitLab", "greenhouse", "gitlab"),
    ("Twilio", "greenhouse", "twilio"),
    ("Airtable", "greenhouse", "airtable"),
    ("Plaid", "greenhouse", "plaid"),
    ("Gusto", "greenhouse", "gusto"),
    ("Brex", "greenhouse", "brex"),
    ("Ramp", "greenhouse", "ramp"),
    ("Scale AI", "greenhouse", "scaleai"),
    ("Anthropic", "greenhouse", "anthropic"),
    ("OpenAI", "greenhouse", "openai"),
    ("Vercel", "greenhouse", "vercel"),
    ("Supabase", "greenhouse", "supabase"),
    ("Linear", "greenhouse", "linear"),
    ("Loom", "greenhouse", "loom"),
    ("Retool", "greenhouse", "retool"),
    ("Postman", "greenhouse", "postman"),
    ("HashiCorp", "greenhouse", "hashicorp"),
    ("DigitalOcean", "greenhouse", "digitalocean"),
    ("PlanetScale", "greenhouse", "planetscale"),
    ("Render", "greenhouse", "render"),
    ("Sentry", "greenhouse", "sentry"),
    ("Snyk", "greenhouse", "snyk"),
    ("LaunchDarkly", "greenhouse", "launchdarkly"),
    ("Neon", "greenhouse", "neondatabase"),
    ("Resend", "greenhouse", "resend"),
    # Lever companies
    ("Netflix", "lever", "netflix"),
    ("Netlify", "lever", "netlify"),
    ("Coinbase", "lever", "coinbase"),
    ("Lyft", "lever", "lyft"),
    ("Reddit", "lever", "reddit"),
    ("Palantir", "lever", "palantir"),
    ("Spotify", "lever", "spotify"),
    ("Affirm", "lever", "affirm"),
    ("Zapier", "lever", "zapier"),
    ("Webflow", "lever", "webflow"),
    ("Weights & Biases", "lever", "wandb"),
    ("Replit", "lever", "replit"),
    ("Railway", "lever", "railway"),
    # Ashby companies
    ("Ashby", "ashby", "ashby"),
    ("Ramp", "ashby", "ramp"),
    ("Deel", "ashby", "deel"),
    ("Vanta", "ashby", "vanta"),
    ("Faire", "ashby", "faire"),
    ("Liveblocks", "ashby", "liveblocks"),
    ("Fly.io", "ashby", "fly"),
    ("Turso", "ashby", "turso"),
    # Workable companies
    ("Workable", "workable", "workable"),
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
            self.stdout.write("Queuing job refresh for all mappings...")
            for mapping in ATSMapping.objects.all():
                refresh_jobs.delay(mapping.id)
            self.stdout.write(self.style.SUCCESS("Done. Jobs will be fetched in the background."))
