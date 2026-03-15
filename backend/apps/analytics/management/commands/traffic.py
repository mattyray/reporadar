"""
Usage:  python manage.py traffic          # last 7 days
        python manage.py traffic --days 30
        python manage.py traffic --today
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.analytics.models import PageView, Session


class Command(BaseCommand):
    help = "Show traffic stats from the analytics app"

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

        humans = Q(is_bot=False)
        sessions = Session.objects.filter(started_at__gte=since)
        page_views = PageView.objects.filter(viewed_at__gte=since)

        human_sessions = sessions.filter(humans)
        bot_sessions = sessions.filter(is_bot=True)
        human_pvs = page_views.filter(session__is_bot=False)

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"  RepoRadar Traffic — {label}")
        self.stdout.write(f"  (since {since.strftime('%Y-%m-%d %H:%M')})")
        self.stdout.write(f"{'='*50}\n")

        # Totals
        self.stdout.write(f"  Unique visitors (humans):  {human_sessions.count()}")
        self.stdout.write(f"  Page views (humans):       {human_pvs.count()}")
        self.stdout.write(f"  Bot sessions:              {bot_sessions.count()}")

        # Avg time on page
        avg_time = human_pvs.filter(time_on_page_seconds__isnull=False).aggregate(
            avg=Avg("time_on_page_seconds")
        )["avg"]
        if avg_time:
            self.stdout.write(f"  Avg time on page:          {avg_time:.1f}s")

        # Top pages
        self.stdout.write(f"\n  {'Top Pages':-<40}")
        top_pages = (
            human_pvs.values("path")
            .annotate(views=Count("id"))
            .order_by("-views")[:10]
        )
        for p in top_pages:
            self.stdout.write(f"    {p['views']:>5}  {p['path']}")

        # Daily breakdown
        self.stdout.write(f"\n  {'Daily Breakdown':-<40}")
        daily = (
            human_pvs.annotate(day=TruncDate("viewed_at"))
            .values("day")
            .annotate(views=Count("id"), visitors=Count("session", distinct=True))
            .order_by("day")
        )
        self.stdout.write(f"    {'Date':<12} {'Visitors':>8} {'Views':>8}")
        self.stdout.write(f"    {'-'*12} {'-'*8} {'-'*8}")
        for d in daily:
            self.stdout.write(
                f"    {d['day'].strftime('%Y-%m-%d'):<12} {d['visitors']:>8} {d['views']:>8}"
            )

        # Device breakdown
        self.stdout.write(f"\n  {'Devices':-<40}")
        devices = (
            human_sessions.values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        for d in devices:
            self.stdout.write(f"    {d['count']:>5}  {d['device_type']}")

        # Browser breakdown
        self.stdout.write(f"\n  {'Browsers':-<40}")
        browsers = (
            human_sessions.values("browser")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        for b in browsers:
            self.stdout.write(f"    {b['count']:>5}  {b['browser']}")

        # Geo (top countries)
        self.stdout.write(f"\n  {'Countries':-<40}")
        countries = (
            human_sessions.exclude(country="")
            .values("country")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        if countries:
            for c in countries:
                self.stdout.write(f"    {c['count']:>5}  {c['country']}")
        else:
            self.stdout.write("    (no geo data)")

        # Referrer domains
        self.stdout.write(f"\n  {'Referrer Domains':-<40}")
        referrers = (
            human_sessions.exclude(referrer_domain="")
            .values("referrer_domain")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        if referrers:
            for r in referrers:
                self.stdout.write(f"    {r['count']:>5}  {r['referrer_domain']}")
        else:
            self.stdout.write("    (no referrer data)")

        # UTM sources
        self.stdout.write(f"\n  {'UTM Sources':-<40}")
        utms = (
            human_sessions.exclude(utm_source="")
            .values("utm_source", "utm_medium", "utm_campaign")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        if utms:
            for u in utms:
                parts = [u["utm_source"]]
                if u["utm_medium"]:
                    parts.append(u["utm_medium"])
                if u["utm_campaign"]:
                    parts.append(u["utm_campaign"])
                self.stdout.write(f"    {u['count']:>5}  {' / '.join(parts)}")
        else:
            self.stdout.write("    (no UTM data)")

        self.stdout.write("")
