from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model, logout as session_logout
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.throttling import UserRateThrottle
from courses.models import Lesson
from .models import LessonIteration
from .policy import SUPPLEMENTARY_DAYS, orientation_state
from .services import begin, can_access, credit, expire, iteration_data, admin_access


@require_GET
def csrf(request):
    return JsonResponse({'csrfToken': get_token(request), 'providers': [p for p, cfg in settings.SOCIALACCOUNT_PROVIDERS.items() if cfg.get('APP')]})


def lesson_for(user, public_id):
    qs = Lesson.objects.select_related('module__course')
    if not admin_access(user):
        qs = qs.filter(published=True, module__published=True, module__course__status='published')
    return get_object_or_404(qs, public_id=public_id)


class QuizThrottle(UserRateThrottle):
    rate = '30/hour'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    from learning_twin.api import build_profile
    from assessments.api import attempt_data
    from assessments.models import AssignmentAttempt
    rows = list(LessonIteration.objects.filter(learner=request.user).select_related('lesson'))
    for row in rows:
        expire(row)
    passed = sum(i.status == 'passed' for i in rows)
    return Response({'username': request.user.get_username(), 'admin': admin_access(request.user),
        'server_now': timezone.now().isoformat(), 'passed': passed,
        'orientation': orientation_state(request.user),
        'quote': ['Small steps, repeated with care, become engineering skill.',
                  'A failing test is a clue. Follow it.', 'Build one thing you can explain today.'][passed % 3],
        'badges': (['First proof'] if passed else []) + (['Building momentum'] if passed >= 3 else []),
        'iterations': {i.lesson.public_id: iteration_data(i) for i in rows},
        'projects': [attempt_data(a) for a in AssignmentAttempt.objects.filter(learner=request.user).select_related('assignment')],
        'learning_twin': build_profile(request.user)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail(request, public_id):
    from .academy_api import lesson_enrichment
    lesson = lesson_for(request.user, public_id)
    if not can_access(request.user, lesson):
        raise PermissionDenied('Lesson locked.')
    i = LessonIteration.objects.filter(learner=request.user, lesson=lesson).first()
    if not i and not admin_access(request.user):
        raise PermissionDenied('Start the lesson to open its content and begin the 14-day iteration.')
    return Response({'id': lesson.public_id, 'title': lesson.title, 'objective': lesson.objective,
        'challenge': lesson.challenge, 'iteration': iteration_data(i),
        **lesson_enrichment(lesson),
        'sections': list(lesson.sections.values('heading', 'body', 'code', 'language', 'note')),
        'quiz': [{'id': q.pk, 'question': q.question, 'answers': [q.option_a, q.option_b, q.option_c, q.option_d]} for q in lesson.quiz_questions.all()],
        'passing_count': lesson.passing_score or (lesson.quiz_questions.count() * 3 + 3) // 4})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([QuizThrottle])
def action(request, public_id, action):
    lesson = lesson_for(request.user, public_id)
    existing = LessonIteration.objects.filter(learner=request.user, lesson=lesson).first()
    if existing:
        # Persist clock-driven expiry even if the following rejected mutation rolls back.
        expire(existing)
    # Lock the parent user, including when there is no iteration row yet. PostgreSQL
    # serialises simultaneous starts/submits across tabs; SQLite is development only.
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if action == 'start':
            i, created = begin(request.user, lesson)
            return Response({'created': created, 'iteration': iteration_data(i)}, status=201 if created else 200)
        if not can_access(request.user, lesson):
            raise PermissionDenied('Lesson locked.')
        i = get_object_or_404(LessonIteration.objects.select_for_update(), learner=request.user, lesson=lesson)
        expire(i)
        if action == 'supplement':
            if i.supplementary_started_at:
                return Response({'iteration': iteration_data(i)})
            if i.status != 'failed':
                raise PermissionDenied('A supplementary attempt is available only after the original deadline and before day 21.')
            i.supplementary_started_at = timezone.now()
            i.supplementary_due_at = i.due_at + timedelta(days=SUPPLEMENTARY_DAYS)
            i.status = 'supplementary'
            i.save()
        elif action == 'submit':
            if i.status == 'passed':
                return Response({'iteration': iteration_data(i)})
            questions = list(lesson.quiz_questions.all())
            answers = request.data.get('answers')
            if not questions:
                raise ValidationError('This lesson requires instructor sign-off; a quiz cannot award completion.')
            if not isinstance(answers, list) or len(answers) != len(questions) or any(type(a) is not int or a not in range(4) for a in answers):
                raise ValidationError('Send one answer index (0–3) per question, in displayed order.')
            correct = sum(q.correct == a for q, a in zip(questions, answers))
            required = lesson.passing_score or (len(questions) * 3 + 3) // 4
            credit(i, correct * 100 // len(questions), correct >= required)
            i.quiz_submissions += 1
            i.save(update_fields=['quiz_submissions'])
        else:
            raise ValidationError('Unknown action.')
        return Response({'iteration': iteration_data(i)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    session_logout(request)
    return Response({'detail': 'Browser session ended. CLI tokens remain valid.'})
