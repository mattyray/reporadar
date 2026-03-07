"""GitHub REST API v3 adapter.

Handles code search, repo contents, org details, and contributor profiles.
Each method takes a token so requests use the caller's rate limits.
"""

import base64

import requests

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def code_search(self, query: str, page: int = 1, per_page: int = 30) -> dict:
        """Search code on GitHub. Rate limit: 10 req/min."""
        resp = self.session.get(
            f"{GITHUB_API_BASE}/search/code",
            params={"q": query, "page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def get_repo(self, owner: str, repo: str) -> dict:
        """Get repository details."""
        resp = self.session.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
        resp.raise_for_status()
        return resp.json()

    def get_file_contents(self, owner: str, repo: str, path: str) -> str | None:
        """Get file contents decoded from base64. Returns None if not found."""
        resp = self.session.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8")
        return None

    def check_file_exists(self, owner: str, repo: str, path: str) -> bool:
        """Check if a file or directory exists in a repo (HEAD request)."""
        resp = self.session.head(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        )
        return resp.status_code == 200

    def get_org(self, org: str) -> dict:
        """Get organization details."""
        resp = self.session.get(f"{GITHUB_API_BASE}/orgs/{org}")
        resp.raise_for_status()
        return resp.json()

    def get_contributors(
        self, owner: str, repo: str, per_page: int = 5
    ) -> list[dict]:
        """Get top contributors for a repo. Returns basic data only."""
        resp = self.session.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors",
            params={"per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def get_user(self, username: str) -> dict:
        """Get full user profile (email, company, bio, etc.)."""
        resp = self.session.get(f"{GITHUB_API_BASE}/users/{username}")
        resp.raise_for_status()
        return resp.json()

    @property
    def rate_limit(self) -> dict:
        """Check current rate limit status."""
        resp = self.session.get(f"{GITHUB_API_BASE}/rate_limit")
        resp.raise_for_status()
        return resp.json()
