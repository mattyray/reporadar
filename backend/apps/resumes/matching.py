"""Resume-to-job matching logic.

Pure functions that match a user's resume tech stack against active job listings.
"""

import logging

from django.db.models import Q

logger = logging.getLogger(__name__)


def match_jobs_for_user(user_id: int, max_matches: int = 200) -> int:
    """Find jobs matching a user's resume tech stack and store matches.

    Returns the number of matches created/updated.
    """
    from apps.jobs.models import JobListing

    from .models import ResumeJobMatch, ResumeProfile

    try:
        profile = ResumeProfile.objects.get(user_id=user_id)
    except ResumeProfile.DoesNotExist:
        logger.info("No resume profile for user %s", user_id)
        return 0

    tech_stack = profile.tech_stack
    if not tech_stack:
        logger.info("Empty tech stack for user %s", user_id)
        return 0

    # Normalize to lowercase for matching
    user_techs_lower = {t.lower() for t in tech_stack}

    # Find jobs that contain at least one of the user's techs
    tech_q = Q()
    for tech in tech_stack:
        tech_q |= Q(detected_techs__contains=[tech])

    candidate_jobs = (
        JobListing.objects.filter(tech_q, is_active=True)
        .only("id", "detected_techs")
    )

    # Score each job by overlap count
    matches = []
    for job in candidate_jobs:
        job_techs_lower = {t.lower() for t in job.detected_techs}
        overlap = user_techs_lower & job_techs_lower
        if overlap:
            matches.append((job.id, len(overlap), sorted(overlap)))

    # Sort by score descending, take top N
    matches.sort(key=lambda x: x[1], reverse=True)
    top_matches = matches[:max_matches]

    # Clear old matches and bulk create new ones
    ResumeJobMatch.objects.filter(user_id=user_id).delete()

    match_objects = [
        ResumeJobMatch(
            user_id=user_id,
            job_id=job_id,
            match_score=score,
            matched_techs=techs,
        )
        for job_id, score, techs in top_matches
    ]

    if match_objects:
        ResumeJobMatch.objects.bulk_create(match_objects)

    logger.info(
        "Matched %d jobs for user %s (from %d candidates)",
        len(match_objects), user_id, len(matches),
    )
    return len(match_objects)
