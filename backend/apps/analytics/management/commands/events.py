"""
Usage:  python manage.py events          # last 7 days
        python manage.py events --days 30
        python manage.py events --today
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.analytics.models import Event


class Command(BaseCommand):
    help = "Show user behavior events from the analytics app"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Look back N days (default 7)")
        parser.add_argument("--today", action="store_true", help="Show today only")

    def handle(self, *args, **options):
        if options["today"]:
            since = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            label = "Today"
        else:
            days = options["days"]
            since = timezone.now() - timedelta(days=days)
            label = f"Last {days} days"

        events = Event.objects.filter(created_at__gte=since)
        total = events.count()

        self.stdout.write(f"\n{'='*55}")
        self.stdout.write(f"  StackJefe User Behavior — {label}")
        self.stdout.write(f"  (since {since.strftime('%Y-%m-%d %H:%M')})")
        self.stdout.write(f"{'='*55}\n")

        self.stdout.write(f"  Total events: {total}\n")

        if total == 0:
            self.stdout.write("  No events recorded yet. Events will appear once users")
            self.stdout.write("  interact with the site (search, click jobs, apply, etc.)\n")
            return

        # By category
        self.stdout.write(f"  {'Events by Category':-<45}")
        by_cat = events.values("category").annotate(count=Count("id")).order_by("-count")
        for c in by_cat:
            self.stdout.write(f"    {c['count']:>5}  {c['category']}")

        # Top event types
        self.stdout.write(f"\n  {'Top Event Types':-<45}")
        top = (
            events.values("category", "event_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:15]
        )
        for t in top:
            self.stdout.write(f"    {t['count']:>5}  {t['category']}/{t['event_type']}")

        # Job metrics
        self.stdout.write(f"\n  {'Job Activity':-<45}")
        job = events.filter(category="job")
        self.stdout.write(f"    Searches:       {job.filter(event_type='search').count()}")
        self.stdout.write(f"    Job clicks:     {job.filter(event_type='click').count()}")
        self.stdout.write(f"    Apply clicks:   {job.filter(event_type='apply_click').count()}")
        self.stdout.write(f"    Filter changes: {job.filter(event_type='filter_change').count()}")

        # Company metrics
        self.stdout.write(f"\n  {'Company Activity':-<45}")
        co = events.filter(category="company")
        self.stdout.write(f"    Company clicks: {co.filter(event_type='click').count()}")
        self.stdout.write(f"    Company saves:  {co.filter(event_type='save').count()}")
        self.stdout.write(f"    Job checks:     {co.filter(event_type='check_jobs').count()}")
        self.stdout.write(f"    Scans:          {co.filter(event_type='scan_company').count()}")
        self.stdout.write(f"    AI analyses:    {co.filter(event_type='analyze_repo').count()}")

        # Auth / conversion
        self.stdout.write(f"\n  {'Auth / Conversion':-<45}")
        auth = events.filter(category="auth")
        self.stdout.write(f"    Google login clicks:  {auth.filter(event_type='google_login_click').count()}")
        self.stdout.write(f"    Signup CTA clicks:    {auth.filter(event_type='signup_cta_click').count()}")

        # Resume
        self.stdout.write(f"\n  {'Resume Activity':-<45}")
        res = events.filter(category="resume")
        self.stdout.write(f"    Uploads:        {res.filter(event_type='upload').count()}")

        # Top searched techs
        self.stdout.write(f"\n  {'Top Searched Technologies':-<45}")
        tech_searches = events.filter(
            category="job", event_type="search"
        ).values_list("metadata", flat=True)
        tech_counts: dict = {}
        for meta in tech_searches:
            if isinstance(meta, dict):
                for tech in meta.get("techs", []):
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1
        if tech_counts:
            for tech, count in sorted(tech_counts.items(), key=lambda x: -x[1])[:15]:
                self.stdout.write(f"    {count:>5}  {tech}")
        else:
            self.stdout.write("    (no search data yet)")

        # Daily breakdown
        self.stdout.write(f"\n  {'Daily Breakdown':-<45}")
        daily = (
            events.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        self.stdout.write(f"    {'Date':<12} {'Events':>8}")
        self.stdout.write(f"    {'-'*12} {'-'*8}")
        for d in daily:
            self.stdout.write(f"    {d['day'].strftime('%Y-%m-%d'):<12} {d['count']:>8}")

        # Recent events (last 15)
        self.stdout.write(f"\n  {'Recent Events (last 15)':-<45}")
        recent = events.order_by("-created_at")[:15]
        for e in recent:
            ts = e.created_at.strftime("%m/%d %H:%M")
            label = f" — {e.label}" if e.label else ""
            self.stdout.write(f"    {ts}  {e.category}/{e.event_type}{label}")

        self.stdout.write("")
