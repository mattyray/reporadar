"""Tests for stack detection pure functions."""

from pathlib import Path

from apps.search.detection import (
    detect_from_package_json,
    detect_from_requirements_txt,
    detect_stack,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestRequirementsTxtDetection:
    def test_detects_django_and_langchain_stack(self):
        contents = (FIXTURES / "requirements_django_langchain.txt").read_text()
        techs = detect_from_requirements_txt(contents)
        tech_names = [t[0] for t in techs]
        assert "Django" in tech_names
        assert "Django REST Framework" in tech_names
        assert "Celery" in tech_names
        assert "LangChain" in tech_names
        assert "LangGraph" in tech_names
        assert "Claude API" in tech_names
        assert "PostgreSQL" in tech_names

    def test_detects_categories(self):
        contents = (FIXTURES / "requirements_django_langchain.txt").read_text()
        techs = detect_from_requirements_txt(contents)
        tech_dict = {name: cat for name, cat in techs}
        assert tech_dict["Django"] == "backend"
        assert tech_dict["LangGraph"] == "ai_ml"
        assert tech_dict["PostgreSQL"] == "database"
        assert tech_dict["Gunicorn"] == "infrastructure"

    def test_skips_comments_and_blank_lines(self):
        contents = "# this is a comment\n\ndjango==5.0\n"
        techs = detect_from_requirements_txt(contents)
        assert len(techs) == 1
        assert techs[0][0] == "Django"

    def test_empty_file(self):
        techs = detect_from_requirements_txt("")
        assert techs == []

    def test_unknown_packages_ignored(self):
        contents = "some-random-package==1.0.0\ndjango==5.0\n"
        techs = detect_from_requirements_txt(contents)
        assert len(techs) == 1
        assert techs[0][0] == "Django"


class TestPackageJsonDetection:
    def test_detects_react_typescript_stack(self):
        contents = (FIXTURES / "package_react_typescript.json").read_text()
        techs = detect_from_package_json(contents)
        tech_names = [t[0] for t in techs]
        assert "React" in tech_names
        assert "TypeScript" in tech_names
        assert "Tailwind CSS" in tech_names
        assert "TanStack Query" in tech_names
        assert "Vite" in tech_names
        assert "Vitest" in tech_names

    def test_includes_dev_dependencies(self):
        contents = (FIXTURES / "package_react_typescript.json").read_text()
        techs = detect_from_package_json(contents)
        tech_names = [t[0] for t in techs]
        assert "TypeScript" in tech_names  # devDependency
        assert "React Testing Library" in tech_names  # devDependency

    def test_invalid_json(self):
        techs = detect_from_package_json("not json at all")
        assert techs == []

    def test_empty_dependencies(self):
        techs = detect_from_package_json('{"name": "app"}')
        assert techs == []


class TestDetectStack:
    def test_combines_python_and_js(self):
        files = {
            "requirements.txt": "django==5.0\n",
            "package.json": '{"dependencies": {"react": "^19.0.0"}}',
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Django" in tech_names
        assert "React" in tech_names

    def test_deduplicates(self):
        files = {
            "requirements.txt": "redis==5.0\n",
            "pyproject.toml": '[project.dependencies]\n"redis>=5.0"\n',
        }
        techs = detect_stack(files)
        redis_count = sum(1 for t in techs if t[0] == "Redis")
        assert redis_count == 1

    def test_empty_files(self):
        techs = detect_stack({})
        assert techs == []

    def test_prefers_requirements_txt_over_subdirs(self):
        """If requirements.txt exists at root, don't also check requirements/base.txt."""
        files = {
            "requirements.txt": "django==5.0\n",
            "requirements/base.txt": "flask==3.0\n",
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Django" in tech_names
        assert "Flask" not in tech_names

    def test_falls_back_to_subdirectory_requirements(self):
        files = {
            "requirements/base.txt": "django==5.0\n",
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Django" in tech_names
