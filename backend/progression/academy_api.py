"""Authenticated orientation and study tools. None of these endpoints starts a timer."""
from collections.abc import Mapping
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from assessments.models import Assignment, CodeReview
from courses.models import GlossaryEntry, Module
from .api import lesson_for
from .models import FormativeCheck, LessonIteration, MistakeNote, OrientationAcknowledgment, SetupCompletion
from .policy import LESSON_DAYS, MENTOR_DAILY_RATE, MENTOR_HOURLY_RATE, SUPPLEMENTARY_DAYS, orientation_state
from .services import admin_access, can_access

SETUP_TEMPLATE = [
    'Identify what the language or runtime does and which operating systems are supported.',
    'Find the official installation instructions, supported version, editor and any required extension.',
    'Confirm the runtime and version in a terminal. Record the command and the output you expect.',
    'Run one small starter program or tool command. Compare what you saw with the expected result.',
    'Write down one fix for common setup errors and an alternative if you cannot install software.',
]


def _resource_data(resources):
    return list(resources.filter(url__startswith='https://').values('title', 'url', 'purpose'))


def lesson_enrichment(lesson):
    guide = getattr(lesson, 'guide', None)
    return {
        'guide': {name: getattr(guide, name) for name in (
            'explanation', 'demonstration', 'example', 'guided_exercise', 'independent_exercise', 'further_explanation',
        )} if guide else None,
        'resources': _resource_data(lesson.learning_resources.all()),
    }


def _object(request):
    if not isinstance(request.data, Mapping):
        raise ValidationError({'detail': 'Send a JSON object.'})
    return request.data


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orientation(request):
    state = orientation_state(request.user)
    if request.method == 'POST':
        data = _object(request)
        if data.get('version') != state['version'] or data.get('accept') is not True:
            raise ValidationError({'detail': 'Open the current Handbook and confirm that you have read the rules.'})
        OrientationAcknowledgment.objects.get_or_create(learner=request.user, version=state['version'])
        state['acknowledged'] = True
    return Response(state)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def handbook(request):
    return Response({
        'orientation': orientation_state(request.user),
        'lesson_days': LESSON_DAYS,
        'supplementary_days': SUPPLEMENTARY_DAYS,
        'grade_cap': settings.SAIRE_SUPPLEMENTARY_GRADE_CAP,
        'mentor_hourly': MENTOR_HOURLY_RATE,
        'mentor_daily': MENTOR_DAILY_RATE,
        'support_email': settings.SAIRE_SUPPORT_EMAIL,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def setup(request, module_id):
    modules = Module.objects.select_related('course', 'guide')
    if not admin_access(request.user):
        modules = modules.filter(published=True, course__status='published')
    module = get_object_or_404(modules, pk=module_id)
    guide = getattr(module, 'guide', None)
    if guide and not guide.published:
        guide = None
    steps = list(guide.steps.values('id', 'heading', 'instructions', 'command', 'verification')) if guide else []
    revision = guide.revision if guide else None
    completed = bool(guide and SetupCompletion.objects.filter(
        learner=request.user, guide=guide, revision=revision,
    ).exists())
    if request.method == 'POST':
        data = _object(request)
        ids = data.get('checked')
        if not steps or data.get('revision') != revision:
            raise ValidationError({'detail': 'Reload the published setup checklist before confirming.'})
        if not isinstance(ids, list) or any(type(item) is not int for item in ids) or set(ids) != {step['id'] for step in steps}:
            raise ValidationError({'detail': 'Confirm each verification step before completing setup.'})
        SetupCompletion.objects.get_or_create(learner=request.user, guide=guide, revision=revision)
        completed = True
    return Response({
        'title': guide.title if guide else f'Getting Ready · {module.name}',
        'introduction': guide.introduction if guide else 'Use this checklist to plan your setup while the module lab is being prepared.',
        'outcomes': [line.strip() for line in guide.outcomes.splitlines() if line.strip()] if guide else [],
        'revision': revision,
        'required': bool(guide and guide.required_setup),
        'completed': completed,
        'steps': steps,
        'template': SETUP_TEMPLATE if not steps else [],
        'resources': _resource_data(module.learning_resources.filter(lesson__isnull=True)),
        'final_project': Assignment.objects.filter(
            module=module, published=True, module_pass_score__isnull=False,
        ).values('title', 'duration_days', 'module_pass_score').first(),
    })


def _check_record(check):
    return {'correct': check.correct, 'total': check.total, 'checked_at': check.checked_at}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def formative(request, public_id, stage):
    if stage not in ('before', 'after'):
        raise ValidationError({'detail': 'Choose a before or after check.'})
    lesson = lesson_for(request.user, public_id)
    if not can_access(request.user, lesson):
        raise PermissionDenied('Unlock the lesson before taking its practice checks.')
    questions = list(lesson.formative_questions.all())
    attempts = LessonIteration.objects.filter(learner=request.user, lesson=lesson)

    def get_checks():
        return {check.stage: _check_record(check) for check in FormativeCheck.objects.filter(
            learner=request.user, lesson=lesson,
        )}

    if request.method == 'GET':
        started = attempts.exists()
        allowed = not started if stage == 'before' else started
        if stage == 'after' and not started and not admin_access(request.user):
            raise PermissionDenied('Open the lesson before taking its after check.')
        return Response({
            'questions': [{'id': q.pk, 'prompt': q.prompt, 'options': [q.option_a, q.option_b, q.option_c]} for q in questions],
            'can_answer': bool(questions and (allowed or admin_access(request.user))),
            'results': get_checks(),
        })

    data = _object(request)
    answers = data.get('answers')
    if not questions or data.get('question_ids') != [q.pk for q in questions]:
        raise ValidationError({'detail': 'Reload the current practice questions.'})
    if not isinstance(answers, list) or len(answers) != len(questions) or any(type(a) is not int or a not in range(3) for a in answers):
        raise ValidationError({'detail': 'Choose one option for each question.'})
    feedback = [
        {'correct': answer == q.correct, 'explanation': q.explanation}
        for q, answer in zip(questions, answers)
    ]
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        started = attempts.exists()
        if stage == 'before' and started and not admin_access(request.user):
            raise PermissionDenied('Your before check closes when the timed lesson starts.')
        if stage == 'after' and not started and not admin_access(request.user):
            raise PermissionDenied('Open the lesson before taking its after check.')
        FormativeCheck.objects.update_or_create(
            learner=request.user, lesson=lesson, stage=stage,
            defaults={'correct': sum(item['correct'] for item in feedback), 'total': len(questions)},
        )
    return Response({'results': get_checks(), 'feedback': feedback})


def _note_data(note):
    return {key: getattr(note, key) for key in ('id', 'title', 'mistake', 'correction', 'updated_at')}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notes(request):
    entries = MistakeNote.objects.filter(learner=request.user)
    if request.method == 'GET':
        return Response([_note_data(note) for note in entries])
    data = _object(request)
    action = data.get('action')
    if action not in ('save', 'delete'):
        raise ValidationError({'detail': 'Choose to save or delete a note.'})
    note_id = data.get('id')
    if note_id is not None and (type(note_id) is not int or note_id < 1):
        raise ValidationError({'detail': 'Invalid note ID.'})
    if action == 'delete':
        get_object_or_404(entries, pk=note_id).delete()
        return Response({'deleted': True})
    fields = {}
    for field, limit in [('title', 100), ('mistake', 1500), ('correction', 1500)]:
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > limit or (field != 'correction' and not value.strip()):
            raise ValidationError({'detail': f'Enter {field} text up to {limit} characters.'})
        fields[field] = value.strip()
    if note_id is not None:
        note = get_object_or_404(entries, pk=note_id)
        for name, value in fields.items():
            setattr(note, name, value)
        note.save(update_fields=[*fields, 'updated_at'])
    else:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if entries.count() >= 100:
                raise ValidationError({'detail': 'Your notebook holds 100 notes. Delete an old note to add another.'})
            note = entries.create(learner=request.user, **fields)
    return Response(_note_data(note))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def study_tools(request):
    user = request.user
    published = dict(lesson__published=True, lesson__module__published=True, lesson__module__course__status='published')
    suggestions = {}
    misses = FormativeCheck.objects.filter(
        learner=user, stage='after', correct__lt=F('total'), **published,
    ).select_related('lesson').order_by('-checked_at')[:6]
    for check in misses:
        suggestions[check.lesson_id] = {
            'lesson': check.lesson.title,
            'reason': f'Your after check was {check.correct}/{check.total}. Rework an example, then try the check again.',
        }
    past_passes = LessonIteration.objects.filter(
        learner=user, status='passed', completed_at__lte=timezone.now() - timedelta(days=3), **published,
    ).select_related('lesson').order_by('completed_at')[:6]
    for attempt in past_passes:
        suggestions.setdefault(attempt.lesson_id, {
            'lesson': attempt.lesson.title,
            'reason': 'You passed this lesson at least three days ago. Explain the main idea from memory, then compare it with your notes.',
        })
    achievements = []
    if SetupCompletion.objects.filter(learner=user, guide__first_program=True).exists():
        achievements.append({'title': 'First program', 'evidence': 'You confirmed the first program ran in your setup checklist.'})
    if CodeReview.objects.filter(submission__attempt__learner=user).exists():
        achievements.append({'title': 'First reviewed challenge', 'evidence': 'An instructor recorded a review of your submitted project.'})
    return Response({
        'glossary': list(GlossaryEntry.objects.filter(published=True).values('term', 'definition', 'example')),
        'revision': list(suggestions.values())[:8],
        'achievements': achievements,
    })
