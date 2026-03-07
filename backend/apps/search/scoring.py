"""Scoring algorithm — pure functions that calculate prospect scores.

Each prospect gets a score from 0-100 based on:
- Stack match (40 points max)
- AI tool signals (20 points max)
- Production signals (20 points max)
- Activity (10 points max)
- Team size (10 points max)
"""

from datetime import datetime, timezone


def calculate_stack_score(
    detected_techs: list[str],
    must_have: list[str],
    nice_to_have: list[str],
) -> int:
    """Score based on how well detected technologies match the search criteria.

    Args:
        detected_techs: list of technology names found in the repo
        must_have: technologies the user requires (8 pts each, max 40)
        nice_to_have: technologies the user prefers (4 pts each, max 40)

    Returns:
        Score 0-40
    """
    score = 0
    detected_lower = {t.lower() for t in detected_techs}

    for tech in must_have:
        if tech.lower() in detected_lower:
            score += 8

    for tech in nice_to_have:
        if tech.lower() in detected_lower:
            score += 4

    return min(score, 40)


def calculate_ai_tool_score(
    has_claude_md: bool = False,
    has_cursor_config: bool = False,
    has_copilot_config: bool = False,
    has_windsurf_config: bool = False,
) -> int:
    """Score based on AI development tool signals found in the repo.

    Returns:
        Score 0-20
    """
    score = 0
    if has_claude_md:
        score += 10
    if has_cursor_config:
        score += 5
    if has_copilot_config:
        score += 5
    if has_windsurf_config:
        score += 5
    return min(score, 20)


def calculate_production_score(
    has_docker: bool = False,
    has_ci_cd: bool = False,
    has_tests: bool = False,
    has_deployment_config: bool = False,
) -> int:
    """Score based on production-readiness signals.

    Returns:
        Score 0-20
    """
    score = 0
    if has_docker:
        score += 5
    if has_ci_cd:
        score += 5
    if has_tests:
        score += 5
    if has_deployment_config:
        score += 5
    return score


def calculate_activity_score(last_pushed_at: datetime | None) -> int:
    """Score based on how recently the repo was updated.

    Args:
        last_pushed_at: datetime of last push (timezone-aware)

    Returns:
        Score 0-10
    """
    if last_pushed_at is None:
        return 0

    now = datetime.now(timezone.utc)
    days_ago = (now - last_pushed_at).days

    if days_ago <= 30:
        return 10
    elif days_ago <= 90:
        return 7
    elif days_ago <= 180:
        return 4
    return 0


def calculate_team_size_score(contributor_count: int) -> int:
    """Score based on number of contributors.

    Returns:
        Score 0-10
    """
    if contributor_count >= 5:
        return 10
    elif contributor_count >= 3:
        return 7
    elif contributor_count >= 2:
        return 4
    return 0


def calculate_total_score(
    detected_techs: list[str],
    must_have: list[str],
    nice_to_have: list[str],
    has_claude_md: bool = False,
    has_cursor_config: bool = False,
    has_copilot_config: bool = False,
    has_windsurf_config: bool = False,
    has_docker: bool = False,
    has_ci_cd: bool = False,
    has_tests: bool = False,
    has_deployment_config: bool = False,
    last_pushed_at: datetime | None = None,
    contributor_count: int = 0,
) -> int:
    """Calculate the total prospect score (0-100).

    Combines all sub-scores:
    - Stack match: 0-40
    - AI tools: 0-20
    - Production signals: 0-20
    - Activity: 0-10
    - Team size: 0-10
    """
    return (
        calculate_stack_score(detected_techs, must_have, nice_to_have)
        + calculate_ai_tool_score(has_claude_md, has_cursor_config, has_copilot_config, has_windsurf_config)
        + calculate_production_score(has_docker, has_ci_cd, has_tests, has_deployment_config)
        + calculate_activity_score(last_pushed_at)
        + calculate_team_size_score(contributor_count)
    )
