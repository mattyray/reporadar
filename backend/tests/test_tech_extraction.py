"""Tests for tech extraction from job description text."""

import pytest

from apps.jobs.tech_extraction import extract_techs_from_text


class TestExtractTechsFromText:
    def test_empty_text(self):
        assert extract_techs_from_text("") == []

    def test_none_text(self):
        assert extract_techs_from_text(None) == []

    def test_single_tech(self):
        result = extract_techs_from_text("We use Django for our backend.")
        assert "Django" in result

    def test_multiple_techs(self):
        text = "Looking for someone with React, TypeScript, and PostgreSQL experience."
        result = extract_techs_from_text(text)
        assert "React" in result
        assert "TypeScript" in result
        assert "PostgreSQL" in result

    def test_case_insensitive(self):
        result = extract_techs_from_text("Experience with DJANGO and react required.")
        assert "Django" in result
        assert "React" in result

    def test_ai_techs(self):
        text = "Building with LangChain and Claude API for our AI features."
        result = extract_techs_from_text(text)
        assert "LangChain" in result
        assert "Claude" in result

    def test_infrastructure_techs(self):
        text = "Must know Docker, Kubernetes, and AWS."
        result = extract_techs_from_text(text)
        assert "Docker" in result
        assert "Kubernetes" in result
        assert "AWS" in result

    def test_postgres_alias(self):
        result = extract_techs_from_text("We run Postgres in production.")
        assert "PostgreSQL" in result

    def test_nextjs_variants(self):
        result1 = extract_techs_from_text("Built with Next.js")
        result2 = extract_techs_from_text("Built with NextJS")
        assert "Next.js" in result1
        assert "Next.js" in result2

    def test_golang_alias(self):
        result = extract_techs_from_text("Backend written in Golang")
        assert "Go" in result

    def test_no_false_positives_on_common_words(self):
        text = "We are looking for a great engineer to join our team."
        result = extract_techs_from_text(text)
        assert len(result) == 0

    def test_deduplication(self):
        text = "Django Django Django"
        result = extract_techs_from_text(text)
        assert result.count("Django") == 1

    def test_returns_sorted(self):
        text = "We use React, Django, and AWS"
        result = extract_techs_from_text(text)
        assert result == sorted(result)

    def test_real_job_description(self):
        text = """
        Senior Backend Engineer

        We're building the next generation of developer tools using Python and Django.
        Our stack includes PostgreSQL, Redis, and Celery for background processing.
        We deploy with Docker on AWS and use GitHub Actions for CI/CD.
        Experience with React or TypeScript on the frontend is a plus.
        """
        result = extract_techs_from_text(text)
        assert "Python" in result
        assert "Django" in result
        assert "PostgreSQL" in result
        assert "Redis" in result
        assert "Celery" in result
        assert "Docker" in result
        assert "AWS" in result
        assert "React" in result
        assert "TypeScript" in result
