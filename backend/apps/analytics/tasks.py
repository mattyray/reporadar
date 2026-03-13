from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def cleanup_old_analytics():
    from .models import PageView, Session

    cutoff = timezone.now() - timedelta(days=90)
    pv_deleted, _ = PageView.objects.filter(viewed_at__lt=cutoff).delete()
    s_deleted, _ = Session.objects.filter(started_at__lt=cutoff).delete()
    return f"Deleted {pv_deleted} page views, {s_deleted} sessions older than 90 days"
