"""Tests for GitHub REST API client with mocked responses."""

import json
from pathlib import Path

import responses

from providers.github_client import GITHUB_API_BASE, GitHubClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@responses.activate
def test_code_search():
    fixture = load_fixture("github_code_search_response.json")
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/search/code",
        json=fixture,
        status=200,
    )

    client = GitHubClient(token="fake-token")
    result = client.code_search("filename:requirements.txt django")

    assert result["total_count"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["repository"]["owner"]["login"] == "acme-corp"
    assert result["items"][0]["repository"]["owner"]["type"] == "Organization"


@responses.activate
def test_code_search_sends_auth_header():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/search/code",
        json={"total_count": 0, "items": []},
        status=200,
    )

    client = GitHubClient(token="my-secret-token")
    client.code_search("test")

    assert responses.calls[0].request.headers["Authorization"] == "Bearer my-secret-token"


@responses.activate
def test_get_file_contents_decodes_base64():
    fixture = load_fixture("github_repo_contents_response.json")
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp/contents/requirements.txt",
        json=fixture,
        status=200,
    )

    client = GitHubClient(token="fake-token")
    contents = client.get_file_contents("acme-corp", "webapp", "requirements.txt")

    assert contents is not None
    assert "django>=5.1" in contents
    assert "langchain>=0.3" in contents


@responses.activate
def test_get_file_contents_returns_none_for_404():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp/contents/CLAUDE.md",
        json={"message": "Not Found"},
        status=404,
    )

    client = GitHubClient(token="fake-token")
    contents = client.get_file_contents("acme-corp", "webapp", "CLAUDE.md")

    assert contents is None


@responses.activate
def test_check_file_exists_true():
    responses.add(
        responses.HEAD,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp/contents/CLAUDE.md",
        status=200,
    )

    client = GitHubClient(token="fake-token")
    assert client.check_file_exists("acme-corp", "webapp", "CLAUDE.md") is True


@responses.activate
def test_check_file_exists_false():
    responses.add(
        responses.HEAD,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp/contents/.cursor",
        status=404,
    )

    client = GitHubClient(token="fake-token")
    assert client.check_file_exists("acme-corp", "webapp", ".cursor") is False


@responses.activate
def test_get_contributors():
    fixture = load_fixture("github_contributors_response.json")
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp/contributors",
        json=fixture,
        status=200,
    )

    client = GitHubClient(token="fake-token")
    contributors = client.get_contributors("acme-corp", "webapp", per_page=5)

    assert len(contributors) == 3
    assert contributors[0]["login"] == "janedev"
    assert contributors[0]["contributions"] == 142
    # Contributors endpoint does NOT return email/company/bio
    assert "email" not in contributors[0]
    assert "company" not in contributors[0]


@responses.activate
def test_get_user_returns_full_profile():
    fixture = load_fixture("github_user_profile_response.json")
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/janedev",
        json=fixture,
        status=200,
    )

    client = GitHubClient(token="fake-token")
    user = client.get_user("janedev")

    assert user["name"] == "Jane Developer"
    assert user["email"] == "jane@acme.com"
    assert user["company"] == "Acme Corp"
    assert user["bio"] == "Staff Engineer at Acme Corp. Django, Python, AI."
    assert user["twitter_username"] == "janedev"
    assert user["location"] == "San Francisco, CA"


@responses.activate
def test_get_repo():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/repos/acme-corp/webapp",
        json={
            "id": 100001,
            "name": "webapp",
            "full_name": "acme-corp/webapp",
            "description": "Main web application",
            "stargazers_count": 42,
            "forks_count": 5,
            "fork": False,
            "default_branch": "main",
            "pushed_at": "2026-03-01T10:00:00Z",
            "owner": {"login": "acme-corp", "type": "Organization"},
        },
        status=200,
    )

    client = GitHubClient(token="fake-token")
    repo = client.get_repo("acme-corp", "webapp")

    assert repo["full_name"] == "acme-corp/webapp"
    assert repo["stargazers_count"] == 42
    assert repo["owner"]["type"] == "Organization"


@responses.activate
def test_get_org():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/orgs/acme-corp",
        json={
            "login": "acme-corp",
            "id": 50001,
            "name": "Acme Corporation",
            "description": "Building the future",
            "blog": "https://acme.com",
            "location": "San Francisco",
            "email": "hello@acme.com",
            "public_repos": 25,
            "avatar_url": "https://avatars.githubusercontent.com/u/50001",
        },
        status=200,
    )

    client = GitHubClient(token="fake-token")
    org = client.get_org("acme-corp")

    assert org["name"] == "Acme Corporation"
    assert org["email"] == "hello@acme.com"
    assert org["public_repos"] == 25
