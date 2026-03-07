"""Tests for scoring algorithm pure functions."""

from datetime import datetime, timedelta, timezone

from apps.search.scoring import (
    calculate_activity_score,
    calculate_ai_tool_score,
    calculate_production_score,
    calculate_stack_score,
    calculate_team_size_score,
    calculate_total_score,
)


class TestStackScore:
    def test_perfect_must_have_match(self):
        score = calculate_stack_score(
            detected_techs=["Django", "React", "LangGraph"],
            must_have=["django", "react", "langgraph"],
            nice_to_have=[],
        )
        assert score == 24  # 3 * 8

    def test_nice_to_have(self):
        score = calculate_stack_score(
            detected_techs=["Django", "TypeScript"],
            must_have=["django"],
            nice_to_have=["typescript", "react"],
        )
        assert score == 12  # 8 + 4

    def test_capped_at_40(self):
        score = calculate_stack_score(
            detected_techs=["Django", "React", "LangGraph", "Celery", "Redis", "PostgreSQL"],
            must_have=["django", "react", "langgraph", "celery", "redis", "postgresql"],
            nice_to_have=[],
        )
        assert score == 40  # 6 * 8 = 48, capped at 40

    def test_no_matches(self):
        score = calculate_stack_score(
            detected_techs=["Flask", "Vue.js"],
            must_have=["django", "react"],
            nice_to_have=[],
        )
        assert score == 0

    def test_case_insensitive(self):
        score = calculate_stack_score(
            detected_techs=["Django"],
            must_have=["DJANGO"],
            nice_to_have=[],
        )
        assert score == 8

    def test_empty_everything(self):
        score = calculate_stack_score([], [], [])
        assert score == 0


class TestAIToolScore:
    def test_claude_md_only(self):
        assert calculate_ai_tool_score(has_claude_md=True) == 10

    def test_all_tools(self):
        score = calculate_ai_tool_score(
            has_claude_md=True,
            has_cursor_config=True,
            has_copilot_config=True,
            has_windsurf_config=True,
        )
        assert score == 20  # 10 + 5 + 5 + 5 = 25, capped at 20

    def test_no_tools(self):
        assert calculate_ai_tool_score() == 0


class TestProductionScore:
    def test_all_signals(self):
        score = calculate_production_score(
            has_docker=True, has_ci_cd=True, has_tests=True, has_deployment_config=True
        )
        assert score == 20

    def test_partial_signals(self):
        score = calculate_production_score(has_docker=True, has_tests=True)
        assert score == 10

    def test_no_signals(self):
        assert calculate_production_score() == 0


class TestActivityScore:
    def test_recent_push(self):
        recent = datetime.now(timezone.utc) - timedelta(days=5)
        assert calculate_activity_score(recent) == 10

    def test_push_60_days_ago(self):
        past = datetime.now(timezone.utc) - timedelta(days=60)
        assert calculate_activity_score(past) == 7

    def test_push_120_days_ago(self):
        past = datetime.now(timezone.utc) - timedelta(days=120)
        assert calculate_activity_score(past) == 4

    def test_push_over_180_days(self):
        old = datetime.now(timezone.utc) - timedelta(days=365)
        assert calculate_activity_score(old) == 0

    def test_none(self):
        assert calculate_activity_score(None) == 0


class TestTeamSizeScore:
    def test_large_team(self):
        assert calculate_team_size_score(10) == 10

    def test_medium_team(self):
        assert calculate_team_size_score(3) == 7

    def test_small_team(self):
        assert calculate_team_size_score(2) == 4

    def test_solo(self):
        assert calculate_team_size_score(1) == 0

    def test_zero(self):
        assert calculate_team_size_score(0) == 0


class TestTotalScore:
    def test_perfect_score(self):
        score = calculate_total_score(
            detected_techs=["Django", "React", "LangGraph", "Celery", "Redis"],
            must_have=["django", "react", "langgraph", "celery", "redis"],
            nice_to_have=[],
            has_claude_md=True,
            has_cursor_config=True,
            has_copilot_config=True,
            has_docker=True,
            has_ci_cd=True,
            has_tests=True,
            has_deployment_config=True,
            last_pushed_at=datetime.now(timezone.utc) - timedelta(days=1),
            contributor_count=10,
        )
        assert score == 100

    def test_zero_score(self):
        score = calculate_total_score(
            detected_techs=[],
            must_have=["django"],
            nice_to_have=[],
        )
        assert score == 0

    def test_mixed_score(self):
        score = calculate_total_score(
            detected_techs=["Django", "React"],
            must_have=["django"],
            nice_to_have=["react"],
            has_claude_md=True,
            has_docker=True,
            last_pushed_at=datetime.now(timezone.utc) - timedelta(days=15),
            contributor_count=3,
        )
        # stack: 8 + 4 = 12, ai: 10, prod: 5, activity: 10, team: 7 = 44
        assert score == 44
