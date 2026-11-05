"""Read-only, self-scoped Learning Twin evidence API.

Read from existing ProofLoop instructor reviews; no student-entered scores, chat
messages, or subjective model inferences are allowed into this profile.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from assessments.models import CodeReview, GradingJob
from .models import AssignmentSkill, Skill
from .scoring import DIMENSION_LABELS, summarise_skill, suggest_skills


def build_profile(learner):
    skills = list(Skill.objects.filter(active=True).order_by('position', 'name'))
    mappings = list(AssignmentSkill.objects.filter(skill__in=skills)
                    .select_related('assignment__module__course', 'skill').order_by('assignment__slug', 'skill__position'))
    by_assignment = {}
    for mapping in mappings:
        by_assignment.setdefault(mapping.assignment_id, []).append(mapping)

    reviews = (CodeReview.objects.filter(submission__attempt__learner=learner)
               .select_related('submission__attempt__assignment', 'submission__grading_job')
               .order_by('-reviewed_at', '-id'))

    # Only the newest instructor-reviewed submission per assignment counts.
    # Re-submissions cannot inflate the score by repeating the same project.
    latest = {}
    for review in reviews:
        assignment_id = review.submission.attempt.assignment_id
        if assignment_id not in latest:
            latest[assignment_id] = review

    evidence_by_skill = {skill.id: [] for skill in skills}
    for assignment_id, review in latest.items():
        if assignment_id not in by_assignment:
            continue
        submission = review.submission
        job = getattr(submission, 'grading_job', None)
        independently_verified = bool(job and job.status == GradingJob.COMPLETE
                                       and job.github_commit_verified and job.verified_test_score is not None)
        scores = {
            'tests': (job.verified_test_score if independently_verified else review.verified_test_score),
            'defence': sum([review.q1_score, review.q2_score, review.q3_score,
                            review.q4_score, review.q5_score]) * 2,
            'quality': review.code_quality_score,
        }
        for mapping in by_assignment[assignment_id]:
            dimension = mapping.dimension
            evidence_by_skill[mapping.skill_id].append({
                'assignment_slug': submission.attempt.assignment.slug,
                'assignment_title': submission.attempt.assignment.title,
                'commit': submission.commit_sha[:12],
                'dimension': dimension,
                'metric': DIMENSION_LABELS[dimension],
                'score': scores[dimension],
                'weight': mapping.weight,
                'source': ('independent_grader' if independently_verified else 'instructor_review')
                          if dimension == 'tests' else 'instructor_review',
                'reviewed_at': review.reviewed_at.isoformat(),
            })

    results = []
    for skill in skills:
        mapped = [m for m in mappings if m.skill_id == skill.pk and m.assignment.published and m.assignment.module.published
                  and m.assignment.module.course.status == 'published']
        possible_assignment = mapped[0].assignment.title if mapped else None
        evidence = evidence_by_skill[skill.pk]
        summary = summarise_skill(evidence, possible_assignment)
        results.append({
            'slug': skill.slug, 'name': skill.name, 'description': skill.description,
            'category': skill.category, 'position': skill.position,
            'next_assignment': possible_assignment,
            **summary, 'evidence': evidence,
        })

    reviewed_assignments = len(set(latest).intersection(by_assignment))
    return {
        'username': learner.get_username(),
        'methodology': 'Scores summarise instructor-reviewed rubric evidence, not intelligence or a validated estimate of ability. One latest reviewed submission per assignment; unassessed means no valid evidence.',
        'overview': {
            'skills_total': len(results),
            'skills_assessed': sum(s['score'] is not None for s in results),
            'reviewed_projects': reviewed_assignments,
            'evidence_items': sum(len(s['evidence']) for s in results),
        },
        'skills': results,
        'recommendations': suggest_skills(results),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_learning_twin(request):
    return Response(build_profile(request.user))
