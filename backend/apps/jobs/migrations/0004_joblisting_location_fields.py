"""Add structured location fields to JobListing."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0003_alter_joblisting_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="joblisting",
            name="is_remote",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="joblisting",
            name="workplace_type",
            field=models.CharField(
                choices=[
                    ("remote", "Remote"),
                    ("hybrid", "Hybrid"),
                    ("onsite", "On-site"),
                    ("unknown", "Unknown"),
                ],
                default="unknown",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="joblisting",
            name="remote_region",
            field=models.CharField(
                blank=True,
                choices=[
                    ("us_only", "US Only"),
                    ("us_canada", "US & Canada"),
                    ("americas", "Americas"),
                    ("europe", "Europe"),
                    ("emea", "EMEA"),
                    ("apac", "APAC"),
                    ("global", "Global / Worldwide"),
                    ("unspecified", "Unspecified"),
                ],
                default="unspecified",
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="joblisting",
            name="country_codes",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="joblisting",
            name="loc_region",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="joblisting",
            name="loc_city",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["is_remote"], name="jobs_joblist_is_remo_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["workplace_type"], name="jobs_joblist_workpla_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["remote_region"], name="jobs_joblist_remote__idx"),
        ),
    ]
