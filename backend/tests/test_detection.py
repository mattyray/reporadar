"""Tests for stack detection pure functions."""

from pathlib import Path

from apps.search.detection import (
    detect_from_build_gradle,
    detect_from_cargo_toml,
    detect_from_gemfile,
    detect_from_go_mod,
    detect_from_package_json,
    detect_from_pom_xml,
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

    def test_detects_go_mod(self):
        files = {
            "go.mod": 'module example.com/app\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n\tgorm.io/gorm v1.25.0\n)\n',
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Gin" in tech_names
        assert "GORM" in tech_names

    def test_detects_cargo_toml(self):
        files = {
            "Cargo.toml": '[dependencies]\nactix-web = "4"\ntokio = { version = "1", features = ["full"] }\nserde = "1"\n',
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Actix Web" in tech_names
        assert "Tokio" in tech_names
        assert "Serde" in tech_names

    def test_detects_gemfile(self):
        files = {
            "Gemfile": "source 'https://rubygems.org'\n\ngem 'rails', '~> 7.0'\ngem 'pg'\ngem 'sidekiq'\n",
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Ruby on Rails" in tech_names
        assert "PostgreSQL" in tech_names
        assert "Sidekiq" in tech_names

    def test_detects_pom_xml(self):
        files = {
            "pom.xml": '<project><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency></dependencies></project>',
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Spring Boot" in tech_names
        assert "PostgreSQL" in tech_names

    def test_detects_build_gradle(self):
        files = {
            "build.gradle": "dependencies {\n    implementation 'org.springframework.boot:spring-boot-starter-web:3.0.0'\n    implementation 'io.r2dbc:r2dbc-postgresql:1.0.0'\n}\n",
        }
        techs = detect_stack(files)
        tech_names = [t[0] for t in techs]
        assert "Spring Boot" in tech_names


class TestGoModDetection:
    def test_multi_line_require(self):
        contents = """module example.com/app

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/go-redis/redis/v8 v8.11.5
    github.com/jackc/pgx/v5 v5.0.0
)
"""
        techs = detect_from_go_mod(contents)
        tech_names = [t[0] for t in techs]
        assert "Gin" in tech_names
        assert "Redis" in tech_names
        assert "PostgreSQL" in tech_names

    def test_single_line_require(self):
        contents = "module example.com/app\n\nrequire github.com/gin-gonic/gin v1.9.0\n"
        techs = detect_from_go_mod(contents)
        assert len(techs) == 1
        assert techs[0][0] == "Gin"

    def test_empty(self):
        assert detect_from_go_mod("module example.com/app\n") == []


class TestCargoTomlDetection:
    def test_standard_deps(self):
        contents = "[dependencies]\naxum = \"0.7\"\nsqlx = { version = \"0.7\", features = [\"postgres\"] }\n"
        techs = detect_from_cargo_toml(contents)
        tech_names = [t[0] for t in techs]
        assert "Axum" in tech_names
        assert "SQLx" in tech_names

    def test_stops_at_next_section(self):
        contents = "[dependencies]\ntokio = \"1\"\n\n[dev-dependencies]\ncriterion = \"0.5\"\n"
        techs = detect_from_cargo_toml(contents)
        assert len(techs) == 1
        assert techs[0][0] == "Tokio"


class TestGemfileDetection:
    def test_standard_gems(self):
        contents = "gem 'rails'\ngem 'devise'\ngem \"rspec\"\n"
        techs = detect_from_gemfile(contents)
        tech_names = [t[0] for t in techs]
        assert "Ruby on Rails" in tech_names
        assert "Devise" in tech_names
        assert "RSpec" in tech_names

    def test_ignores_non_gem_lines(self):
        contents = "source 'https://rubygems.org'\nruby '3.2.0'\ngem 'rails'\n"
        techs = detect_from_gemfile(contents)
        assert len(techs) == 1


class TestPomXmlDetection:
    def test_multiple_artifacts(self):
        contents = """<project>
  <dependencies>
    <dependency><artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency><artifactId>kafka-clients</artifactId></dependency>
  </dependencies>
</project>"""
        techs = detect_from_pom_xml(contents)
        tech_names = [t[0] for t in techs]
        assert "Spring Boot" in tech_names
        assert "Apache Kafka" in tech_names


class TestBuildGradleDetection:
    def test_implementation_deps(self):
        contents = """dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web:3.0.0'
    api 'org.apache.kafka:kafka-clients:3.5.0'
    runtimeOnly 'org.postgresql:postgresql:42.6.0'
}"""
        techs = detect_from_build_gradle(contents)
        tech_names = [t[0] for t in techs]
        assert "Spring Boot" in tech_names
        assert "Apache Kafka" in tech_names
        assert "PostgreSQL" in tech_names
