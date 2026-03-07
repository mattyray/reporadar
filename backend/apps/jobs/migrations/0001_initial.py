import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("prospects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ATSMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(max_length=200)),
                ("ats_platform", models.CharField(choices=[("greenhouse", "Greenhouse"), ("lever", "Lever"), ("ashby", "Ashby"), ("workable", "Workable")], max_length=20)),
                ("ats_slug", models.CharField(max_length=200)),
                ("is_verified", models.BooleanField(default=False)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ats_mappings", to="prospects.organization")),
            ],
            options={
                "unique_together": {("ats_platform", "ats_slug")},
            },
        ),
        migrations.AddIndex(
            model_name="atsmapping",
            index=models.Index(fields=["organization"], name="jobs_atsmap_organiz_idx"),
        ),
        migrations.AddIndex(
            model_name="atsmapping",
            index=models.Index(fields=["is_verified"], name="jobs_atsmap_is_veri_idx"),
        ),
        migrations.CreateModel(
            name="JobListing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=200)),
                ("title", models.CharField(max_length=500)),
                ("department", models.CharField(blank=True, max_length=200)),
                ("location", models.CharField(blank=True, max_length=300)),
                ("employment_type", models.CharField(blank=True, max_length=50)),
                ("description_text", models.TextField(blank=True)),
                ("apply_url", models.URLField(max_length=500)),
                ("detected_techs", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ats_mapping", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="jobs.atsmapping")),
            ],
            options={
                "unique_together": {("ats_mapping", "external_id")},
            },
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["is_active"], name="jobs_joblis_is_acti_idx"),
        ),
    ]
