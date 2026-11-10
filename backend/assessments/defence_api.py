"""Commit-bound defence records and optional, ungraded practice."""
from collections.abc import Mapping

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from mentoring.provider import MentorProviderError, configured_provider, make_defence_practice
from progression.services import require_module
from .api import visible
from .models import CodeDefence, Submission

ANSWER_LIMIT = 2000


class DefencePracticeThrottle(UserRateThrottle):
    scope = 'defence_practice'
    rate = '8/hour'


def _assignment(user, slug):
    assignment = get_object_or_404(visible(user), slug=slug)
    require_module(user, assignment.module)
    return assignment


def _submission(user, assignment, submission_id, *, lock=False):
    records = Submission.objects.all()
    if lock:
        records = records.select_for_update(of=('self',))
    return get_object_or_404(
        records, pk=submission_id, attempt__learner=user, attempt__assignment=assignment,
    )


def _record(assignment, submission, record):
    reviewed = submission.status == Submission.REVIEWED
    submitted_at = record.submitted_at if record else None
    return {
        'submission_id': submission.pk,
        'commit_sha': submission.commit_sha,
        'repository_url': submission.repository_url,
        'questions': record.questions if record else assignment.questions,
        'answers': record.answers if record else ['', '', '', '', ''],
        'revision': record.revision if record else 0,
        'status': 'reviewed' if reviewed else 'submitted' if submitted_at else 'draft',
        'editable': not (reviewed or submitted_at),
        'submitted_at': submitted_at,
        'practice_provider': configured_provider(),
    }


def _conflict(message):
    return Response({'detail': message}, status=409)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def defence(request, slug, submission_id):
    assignment = _assignment(request.user, slug)
    if request.method == 'GET':
        submission = _submission(request.user, assignment, submission_id)
        record = CodeDefence.objects.filter(submission=submission).first()
        return Response(_record(assignment, submission, record))

    if not isinstance(request.data, Mapping):
        raise ValidationError({'detail': 'Send a JSON object with the defence answers.'})
    action = request.data.get('action')
    revision = request.data.get('revision')
    answers = request.data.get('answers')
    if action not in ('save', 'submit') or type(revision) is not int or revision < 0:
        raise ValidationError({'detail': 'Send a valid action and draft revision.'})
    if not isinstance(answers, list) or len(answers) != 5 or any(
        not isinstance(answer, str) or len(answer) > ANSWER_LIMIT for answer in answers
    ):
        raise ValidationError({'detail': f'Send five text answers, each up to {ANSWER_LIMIT} characters.'})
    answers = [answer.strip() for answer in answers]
    if action == 'submit' and not all(answers):
        raise ValidationError({'detail': 'Answer all five questions before handing in your defence.'})

    with transaction.atomic():
        submission = _submission(request.user, assignment, submission_id, lock=True)
        record = CodeDefence.objects.filter(submission=submission).first()
        current = _record(assignment, submission, record)
        same_answers = record is not None and record.answers == answers
        if action == 'submit' and same_answers and record.submitted_at:
            return Response(current)  # Safe retry if the first confirmation response was lost.
        if not current['editable']:
            return _conflict('This defence is read-only. Review the submitted copy in the room.')
        if revision != current['revision'] or request.data.get('questions') != current['questions']:
            return _conflict('The defence changed since you opened it. Reload the saved copy before editing.')
        if record is None:
            record = CodeDefence(submission=submission, questions=current['questions'], revision=0)
        if same_answers and action == 'save':
            return Response(current)
        record.answers = answers
        record.revision += 1
        if action == 'submit':
            record.submitted_at = timezone.now()
        record.save()
    return Response(_record(assignment, submission, record))


def _practice_text(data, key, limit):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValidationError({'detail': f'Enter {key} text up to {limit} characters.'})
    return value.strip()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([DefencePracticeThrottle])
def practice(request, slug, submission_id):
    assignment = _assignment(request.user, slug)
    _submission(request.user, assignment, submission_id)
    if not isinstance(request.data, Mapping):
        raise ValidationError({'detail': 'Send a JSON object with the practice request.'})
    mode = request.data.get('mode')
    if mode not in ('question', 'feedback'):
        raise ValidationError({'detail': 'Choose a practice question or feedback.'})
    question = answer = ''
    if mode == 'feedback':
        if request.data.get('share_practice_answer') is not True:
            raise ValidationError({'detail': 'Choose to share your practice text before asking for AI feedback.'})
        question = _practice_text(request.data, 'question', 400)
        answer = _practice_text(request.data, 'answer', 1200)
    if not configured_provider():
        return Response({'detail': 'Live practice needs an AI provider configured by the Academy.'}, status=503)
    try:
        return Response(make_defence_practice(assignment, mode, question=question, answer=answer))
    except MentorProviderError:
        return Response({'detail': 'AI practice is temporarily unavailable. Your defence is still available.'}, status=503)
