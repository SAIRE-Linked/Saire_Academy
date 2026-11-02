"""Authenticated queue API for an independent, isolated grading host.

Deploy behind a private network and HTTPS; never expose these URLs publicly.
No student code is downloaded or executed in this Django service.
"""
import hmac
import os
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import GradingJob


def worker_authorized(request):
    configured = os.getenv('SAIRE_WORKER_SHARED_TOKEN', '')
    supplied = request.headers.get('X-Saire-Worker-Token', '')
    if len(configured) < 32 or not supplied or not hmac.compare_digest(configured, supplied):
        raise PermissionDenied('Unauthorized worker')


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def claim(request):
    worker_authorized(request)
    # CAS update avoids duplicate claims even when using SQLite for local testing.
    # Running jobs never auto-requeue: operator inspects timeouts before retrying.
    for _ in range(8):
        queued = GradingJob.objects.filter(status=GradingJob.QUEUED, approved_at__isnull=False).order_by('created_at').first()
        if queued is None:
            return Response({'job': None})
        token = uuid.uuid4()
        now = timezone.now()
        changed = GradingJob.objects.filter(pk=queued.pk, status=GradingJob.QUEUED).update(
            status=GradingJob.RUNNING, claim_token=token, claimed_at=now)
        if not changed:
            continue
        submission = queued.submission
        return Response({'job': {
            'id': queued.pk, 'claim_token': str(token), 'submission_id': submission.pk,
            'assignment_slug': submission.attempt.assignment.slug,
            'repository_url': submission.repository_url,
            'commit_sha': submission.commit_sha,
        }})
    return Response({'job': None})


def numeric(data, key, maximum=1000):
    val = data.get(key)
    if type(val) is not int or not (0 <= val <= maximum):
        raise ValidationError({key: f'Expected integer 0–{maximum}'})
    return val


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def report(request):
    worker_authorized(request)
    try:
        job_id = int(request.data.get('job_id'))
        lease = uuid.UUID(str(request.data.get('claim_token')))
    except (TypeError, ValueError, AttributeError):
        raise ValidationError({'detail': 'Invalid job identifier or claim token'})
    outcome = request.data.get('outcome')
    if outcome not in ('complete', 'error'):
        raise ValidationError({'outcome': 'Expected complete or error'})
    verified = request.data.get('github_commit_verified') is True
    if outcome == 'complete':
        if not verified:
            raise ValidationError({'github_commit_verified': 'Commit must be verified for completed grading'})
        passed = numeric(request.data, 'passed')
        failed = numeric(request.data, 'failed')
        errors = numeric(request.data, 'errors')
        count = passed + failed + errors
        if not (1 <= count <= 1000):
            raise ValidationError({'detail': 'A completed run must execute 1–1000 tests'})
        score = numeric(request.data, 'score', 100)
        if score != round(100 * passed / count):
            raise ValidationError({'score': 'Score must match independently reported test counts'})
    else:
        passed = failed = errors = 0
        score = None
    log = request.data.get('log', '')
    reason = request.data.get('failure_reason', '')
    if not isinstance(log, str) or not isinstance(reason, str):
        raise ValidationError({'detail': 'Invalid log or failure_reason'})
    with transaction.atomic():
        job = GradingJob.objects.select_for_update().filter(pk=job_id).first()
        if job is None or job.status != GradingJob.RUNNING or job.claim_token != lease:
            raise ValidationError({'detail': 'Grading job is not active for this worker lease'})
        job.github_commit_verified = verified
        job.status = GradingJob.COMPLETE if outcome == 'complete' else GradingJob.ERROR
        job.verified_test_score = score
        job.tests_passed = passed
        job.tests_failed = failed
        job.tests_errors = errors
        job.execution_log = log[:5000]
        job.failure_reason = reason[:300] if outcome == 'error' else ''
        job.completed_at = timezone.now()
        job.save(update_fields=['github_commit_verified', 'status', 'verified_test_score',
                                'tests_passed', 'tests_failed', 'tests_errors', 'execution_log',
                                'failure_reason', 'completed_at'])
    return Response({'accepted': True, 'job_id': job_id, 'status': job.status})
