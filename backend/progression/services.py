"""Server clock and database state are the only progression authority."""
from collections import defaultdict
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from courses.models import Lesson, Module
from .models import LessonIteration


def admin_access(user):
    return bool(user.is_authenticated and user.is_active and user.is_superuser)


def ordered_lessons(course_id):
    return Lesson.objects.filter(module__course_id=course_id, module__published=True,
                                 module__course__status='published', published=True).order_by('module__position', 'position', 'pk')


def course_progress(user, course_id):
    """Return module state and accessible lessons from saved grades, in curriculum order."""
    from assessments.models import Assignment, Submission

    modules = Module.objects.filter(course_id=course_id, published=True, course__status='published')
    lessons_by_module = defaultdict(list)
    for lesson_id, module_id in ordered_lessons(course_id).values_list('pk', 'module_id'):
        lessons_by_module[module_id].append(lesson_id)

    finals = {a.module_id: a for a in Assignment.objects.filter(
        module__in=modules, published=True, module_pass_score__isnull=False,
    )}
    submissions = defaultdict(list)
    passed_lessons = set()
    if user.is_authenticated:
        passed_lessons = set(LessonIteration.objects.filter(
            learner=user, lesson__module__course_id=course_id, status='passed',
        ).values_list('lesson_id', flat=True))
        for assignment_id, score in Submission.objects.filter(
            attempt__learner=user, attempt__assignment__in=finals.values(),
        ).values_list('attempt__assignment_id', 'review__final_score'):
            submissions[assignment_id].append(score)

    states = {}
    accessible_lessons = set()
    prerequisites_passed = user.is_authenticated
    for module_id in modules.values_list('pk', flat=True):
        lessons = lessons_by_module[module_id]
        lessons_passed = bool(lessons) and all(pk in passed_lessons for pk in lessons)
        if prerequisites_passed:
            for lesson_id in lessons:
                accessible_lessons.add(lesson_id)
                if lesson_id not in passed_lessons:
                    break

        final = finals.get(module_id)
        project = None
        project_passed = False
        if final:
            scores = submissions[final.pk]
            project_passed = any(score is not None and score >= final.module_pass_score for score in scores)
            project_status = 'ready'
            if project_passed:
                project_status = 'passed'
            elif None in scores:
                project_status = 'awaiting_review'
            elif scores:
                project_status = 'needs_revision'
            project = {
                'slug': final.slug, 'title': final.title,
                'pass_score': final.module_pass_score, 'status': project_status,
            }

        project_unlocked = prerequisites_passed and lessons_passed
        complete = project_unlocked and project_passed
        if not prerequisites_passed:
            status = 'locked'
        elif not lessons:
            status = 'coming_soon'
        elif complete:
            status = 'completed'
        elif lessons_passed:
            status = 'final_project' if final else 'awaiting_project'
        else:
            status = 'lessons'
        states[module_id] = {
            'status': status, 'project_unlocked': project_unlocked, 'final_project': project,
            'lessons_passed': sum(pk in passed_lessons for pk in lessons), 'lesson_count': len(lessons),
        }
        prerequisites_passed = complete
    return states, accessible_lessons


def can_access(user, lesson):
    if admin_access(user):
        return True
    if not user.is_authenticated:
        return False
    _, accessible = course_progress(user, lesson.module.course_id)
    return lesson.pk in accessible


def module_access(user, module):
    if admin_access(user):
        return True
    if not user.is_authenticated:
        return False
    states, _ = course_progress(user, module.course_id)
    return states.get(module.pk, {}).get('project_unlocked', False)


def require_module(user, module):
    if not module_access(user, module):
        raise PermissionDenied(
            'Pass earlier modules and their final projects, then finish this module’s lessons.',
        )


def expire(iteration, now=None):
    now = now or timezone.now()
    if iteration.status == 'active' and now >= iteration.due_at:
        LessonIteration.objects.filter(pk=iteration.pk, status='active', due_at__lte=now).update(
            status='failed', primary_failed_at=iteration.due_at, raw_score=0, credited_score=0)
        iteration.refresh_from_db()
    end = iteration.supplementary_due_at or (iteration.due_at + timedelta(days=7))
    if iteration.status in ('failed', 'supplementary') and now >= end:
        LessonIteration.objects.filter(pk=iteration.pk, status__in=['failed', 'supplementary']).update(
            status='exhausted', raw_score=0, credited_score=0)
        iteration.refresh_from_db()
    return iteration


def begin(user, lesson, now=None):
    if not can_access(user, lesson):
        raise PermissionDenied('Pass earlier lessons and the final projects of earlier modules first.')
    now = now or timezone.now()
    iteration, created = LessonIteration.objects.get_or_create(learner=user, lesson=lesson, defaults={
        'started_at': now, 'due_at': now + timedelta(days=14),
        'grade_cap': settings.SAIRE_SUPPLEMENTARY_GRADE_CAP})
    return expire(iteration, now), created


def credit(iteration, raw, passed, now=None):
    now = now or timezone.now()
    expire(iteration, now)
    if iteration.status not in ('active', 'supplementary'):
        raise PermissionDenied('No active attempt. Request your supplementary attempt if available.')
    iteration.raw_score = raw
    iteration.credited_score = min(raw, iteration.grade_cap) if iteration.status == 'supplementary' else raw
    if passed:
        iteration.status = 'passed'
        iteration.completed_at = now
    iteration.save()
    return iteration


def iteration_data(i):
    if not i:
        return None
    expire(i)
    return {field: getattr(i, field).isoformat() if getattr(i, field) else None for field in
            ['started_at', 'due_at', 'supplementary_started_at', 'supplementary_due_at', 'primary_failed_at', 'completed_at']} | {
        'status': i.status, 'raw_score': i.raw_score, 'credited_score': i.credited_score,
        'grade_cap': i.grade_cap, 'quiz_submissions': i.quiz_submissions}
