"""The learner-facing ProofLoop API (TokenAuth for CLI; staff grading in Django Admin)."""
import re
from datetime import timedelta
from urllib.parse import urlsplit

from django.contrib.auth import authenticate
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Assignment, AssignmentAttempt, Submission


class LoginThrottle(AnonRateThrottle):
    rate = '5/minute'


def visible():
    return Assignment.objects.filter(published=True, module__published=True, module__course__status='published').select_related('module__course')


def public_data(a):
    return {
        'slug': a.slug, 'title': a.title, 'brief': a.brief,
        'course_slug': a.module.course.slug, 'module': a.module.name,
        'phase': a.module.position, 'learning_outcomes': [x for x in a.learning_outcomes.splitlines() if x.strip()],
        'test_command': a.test_command, 'duration_days': a.duration_days,
        'late_penalty_per_day': a.late_penalty_per_day,
        'review_questions': a.questions, 'has_starter': bool(a.starter_bundle),
        'template_url': a.template_url,
        'grading': {'verified_tests': 50, 'code_defence': 30, 'code_quality': 10, 'deadline': 10},
    }


def submission_data(s):
    review = getattr(s, 'review', None)
    return {
        'id': s.pk, 'commit_sha': s.commit_sha, 'repository_url': s.repository_url,
        'submitted_at': s.submitted_at.isoformat(), 'status': s.status,
        'late_days': s.late_days,
        'local_tests': {'passed': s.local_tests_passed, 'failed': s.local_tests_failed, 'errors': s.local_tests_errors,
                        'verified': False},
        'review': ({'final_score': str(review.final_score), 'verified_test_score': review.verified_test_score,
                    'code_quality_score': review.code_quality_score,
                    'question_scores': [review.q1_score, review.q2_score, review.q3_score, review.q4_score, review.q5_score],
                    'feedback': review.feedback, 'reviewed_at': review.reviewed_at.isoformat()}
                   if review is not None else None),
    }


def attempt_data(attempt):
    return {'id': str(attempt.pk), 'assignment': attempt.assignment.slug,
            'started_at': attempt.started_at.isoformat(), 'due_at': attempt.due_at.isoformat(),
            'submissions': [submission_data(s) for s in attempt.submissions.select_related('review').all()]}


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        raise ValidationError({'detail': 'Username and password are required.'})
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        raise ValidationError({'detail': 'Invalid credentials.'})
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.get_username()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    # Token logout revokes all CLI/browser clients using this user's single token.
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': 'Token revoked. Sign in again on all devices.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({'username': request.user.get_username(), 'staff': request.user.is_staff})


@api_view(['GET'])
@permission_classes([AllowAny])
def assignments(request):
    return Response([public_data(a) for a in visible()])


@api_view(['GET'])
@permission_classes([AllowAny])
def assignment_detail(request, slug):
    return Response(public_data(get_object_or_404(visible(), slug=slug)))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start(request, slug):
    a = get_object_or_404(visible(), slug=slug)
    with transaction.atomic():
        started = timezone.now()
        attempt, created = AssignmentAttempt.objects.get_or_create(
            learner=request.user, assignment=a,
            defaults={'started_at': started, 'due_at': started + timedelta(days=a.duration_days)},
        )
    return Response({'created': created, 'attempt': attempt_data(attempt), 'assignment': public_data(a)},
                    status=201 if created else 200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_attempt(request, slug):
    a = get_object_or_404(visible(), slug=slug)
    attempt = get_object_or_404(AssignmentAttempt.objects.select_related('assignment'), learner=request.user, assignment=a)
    return Response(attempt_data(attempt))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def starter(request, slug):
    a = get_object_or_404(visible(), slug=slug)
    get_object_or_404(AssignmentAttempt, learner=request.user, assignment=a)
    if not a.starter_bundle:
        raise Http404('Starter ZIP not yet published')
    try:
        handle = a.starter_bundle.open('rb')
    except FileNotFoundError:
        raise Http404('Starter ZIP missing from configured private storage')
    response = FileResponse(handle, as_attachment=True, filename=f'{a.slug}.zip', content_type='application/zip')
    response['Cache-Control'] = 'private, no-store'
    return response


REPOSITORY = re.compile(r'^https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})(?:/)?$')
SHA = re.compile(r'^[a-fA-F0-9]{40}$')


def validate_repository(url):
    if not isinstance(url, str) or len(url) > 220 or not REPOSITORY.fullmatch(url):
        raise ValidationError({'repository_url': 'Use a canonical HTTPS GitHub repository URL (owner/repo).'})
    if urlsplit(url).username or urlsplit(url).password:
        raise ValidationError({'repository_url': 'URLs with credentials are not allowed.'})
    return url.rstrip('/')


def positive_test_count(data, key):
    val = data.get(key, 0)
    if type(val) is not int or not 0 <= val <= 10000:
        raise ValidationError({key: 'Must be an integer between 0 and 10,000.'})
    return val


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit(request, slug):
    a = get_object_or_404(visible(), slug=slug)
    attempt = get_object_or_404(AssignmentAttempt, learner=request.user, assignment=a)
    url = validate_repository(request.data.get('repository_url'))
    sha = request.data.get('commit_sha')
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValidationError({'commit_sha': 'Use a full 40-character hexadecimal Git commit hash.'})
    passed = positive_test_count(request.data, 'local_tests_passed')
    failed = positive_test_count(request.data, 'local_tests_failed')
    errors = positive_test_count(request.data, 'local_tests_errors')
    # The API never clones or runs user-supplied repositories.
    with transaction.atomic():
        s, created = Submission.objects.get_or_create(
            attempt=attempt, commit_sha=sha.lower(),
            defaults={'repository_url': url, 'local_tests_passed': passed,
                      'local_tests_failed': failed, 'local_tests_errors': errors},
        )
    if not created and s.repository_url != url:
        raise ValidationError({'repository_url': 'This commit was already submitted from a different repository.'})
    return Response({'created': created, 'submission': submission_data(s)}, status=201 if created else 200)
