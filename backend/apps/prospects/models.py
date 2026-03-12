from django.conf import settings
from django.db import models


class Organization(models.Model):
    github_login = models.CharField(max_length=100, unique=True)
    github_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    blog = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    public_repos_count = models.IntegerField(default=0)
    github_url = models.URLField(blank=True)
    careers_url = models.URLField(blank=True)
    linkedin_search_url = models.URLField(blank=True)
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["github_login"]),
            models.Index(fields=["github_id"]),
        ]

    def __str__(self):
        return self.name or self.github_login


class OrganizationRepo(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="repos"
    )
    github_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    url = models.URLField()
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    is_fork = models.BooleanField(default=False)
    default_branch = models.CharField(max_length=100, default="main")
    languages = models.JSONField(default=dict)
    has_claude_md = models.BooleanField(default=False)
    has_cursor_config = models.BooleanField(default=False)
    has_copilot_config = models.BooleanField(default=False)
    has_windsurf_config = models.BooleanField(default=False)
    has_aider_config = models.BooleanField(default=False)
    has_codeium_config = models.BooleanField(default=False)
    has_continue_config = models.BooleanField(default=False)
    has_bolt_config = models.BooleanField(default=False)
    has_v0_config = models.BooleanField(default=False)
    has_lovable_config = models.BooleanField(default=False)
    has_idx_config = models.BooleanField(default=False)
    has_amazonq_config = models.BooleanField(default=False)
    has_cline_config = models.BooleanField(default=False)
    has_roo_config = models.BooleanField(default=False)
    has_codex_config = models.BooleanField(default=False)
    has_docker = models.BooleanField(default=False)
    has_ci_cd = models.BooleanField(default=False)
    has_tests = models.BooleanField(default=False)
    has_deployment_config = models.BooleanField(default=False)
    last_pushed_at = models.DateTimeField(null=True, blank=True)
    created_at_github = models.DateTimeField(null=True, blank=True)
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    # AI-powered repo analysis
    AI_ANALYSIS_STATUS_CHOICES = [
        ("none", "Not analyzed"),
        ("pending", "Pending"),
        ("analyzing", "Analyzing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    ai_analysis_status = models.CharField(
        max_length=20, choices=AI_ANALYSIS_STATUS_CHOICES, default="none"
    )
    ai_analysis = models.JSONField(null=True, blank=True)
    ai_analysis_error = models.TextField(blank=True)
    ai_analyzed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["github_id"]),
            models.Index(fields=["full_name"]),
        ]

    def __str__(self):
        return self.full_name


class RepoStackDetection(models.Model):
    CATEGORY_CHOICES = [
        ("backend", "Backend"),
        ("frontend", "Frontend"),
        ("ai_ml", "AI/ML"),
        ("database", "Database"),
        ("infrastructure", "Infrastructure"),
        ("ai_tool", "AI Tool"),
    ]

    repo = models.ForeignKey(
        OrganizationRepo, on_delete=models.CASCADE, related_name="stack_detections"
    )
    technology_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    source_file = models.CharField(max_length=200)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("repo", "technology_name")

    def __str__(self):
        return f"{self.repo.full_name}: {self.technology_name}"


class RepoContributor(models.Model):
    repo = models.ForeignKey(
        OrganizationRepo, on_delete=models.CASCADE, related_name="contributors"
    )
    github_username = models.CharField(max_length=100)
    github_id = models.IntegerField()
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    blog = models.URLField(blank=True)
    twitter_username = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    contributions = models.IntegerField(default=0)
    profile_url = models.URLField(blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["github_username"]),
            models.Index(fields=["repo"]),
        ]

    def __str__(self):
        return f"{self.github_username} ({self.contributions} commits)"


class SavedProspect(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("researched", "Researched"),
        ("contacted", "Contacted"),
        ("interviewing", "Interviewing"),
        ("passed", "Passed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_prospects"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="saved_by"
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "organization")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} saved {self.organization}"
