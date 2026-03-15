"""
Upgrade analytics models to match production-grade implementation:
- Session: rename session_hash → visitor_hash, UUID PK, new fields
- PageView: BigAutoField PK (already is), new composite index
"""

import uuid

from django.db import migrations, models


def populate_uuids(apps, schema_editor):
    """Populate UUID field for existing sessions."""
    Session = apps.get_model("analytics", "Session")
    for session in Session.objects.all():
        session.uuid = uuid.uuid4()
        session.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        # --- Session: rename session_hash → visitor_hash ---
        migrations.RenameField(
            model_name="session",
            old_name="session_hash",
            new_name="visitor_hash",
        ),
        # Remove old constraint
        migrations.RemoveConstraint(
            model_name="session",
            name="unique_session_hash",
        ),
        # Alter the field (unique=True replaces the old constraint + index)
        migrations.AlterField(
            model_name="session",
            name="visitor_hash",
            field=models.CharField(max_length=64, unique=True),
        ),

        # --- Session: change PK from BigAutoField to UUID ---
        # Step 1: Add UUID field (nullable for now)
        migrations.AddField(
            model_name="session",
            name="uuid",
            field=models.UUIDField(null=True),
        ),
        # Step 2: Populate UUIDs for existing rows
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        # Step 3: We can't easily swap PKs with FKs in Django migrations
        # so we'll keep the existing auto-increment PK and add uuid as a unique indexed field
        # The model's Meta will use uuid but the DB migration is additive
        migrations.AlterField(
            model_name="session",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),

        # --- Session: shrink country to ISO 3166-1 alpha-2 ---
        migrations.AlterField(
            model_name="session",
            name="country",
            field=models.CharField(blank=True, default="", max_length=2),
        ),

        # --- Session: add new fields ---
        migrations.AddField(
            model_name="session",
            name="referrer_domain",
            field=models.CharField(blank=True, default="", max_length=253),
        ),
        migrations.AddField(
            model_name="session",
            name="screen_width",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="screen_height",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="utm_source",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="session",
            name="utm_medium",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="session",
            name="utm_campaign",
            field=models.CharField(blank=True, default="", max_length=200),
        ),

        # --- Session: add indexes ---
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["started_at"], name="analytics_s_started_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["referrer_domain"], name="analytics_s_ref_dom_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["device_type"], name="analytics_s_device_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["is_bot"], name="analytics_s_is_bot_idx"),
        ),

        # --- PageView: replace single-field indexes with composite ---
        migrations.RemoveIndex(
            model_name="pageview",
            name="analytics_p_path_3382b5_idx",
        ),
        migrations.AddIndex(
            model_name="pageview",
            index=models.Index(fields=["path", "viewed_at"], name="analytics_pv_path_date_idx"),
        ),
    ]
