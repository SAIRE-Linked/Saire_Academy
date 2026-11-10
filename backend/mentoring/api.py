"""Mentor API: isolated per-learner histories, controlled usage and optional AI."""
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle

from assessments.api import visible
from assessments.models import AssignmentAttempt
from .models import MentorMessage
from .provider import MentorProviderError, build_learning_context, configured_provider, make_socratic_reply, twin_context_enabled


from progression.policy import MENTOR_DAILY_RATE, MENTOR_HOURLY_RATE


class MentorBurstThrottle(UserRateThrottle):
    scope = 'mentor_burst'
    rate = MENTOR_HOURLY_RATE


class MentorDailyThrottle(UserRateThrottle):
    scope = 'mentor_daily'
    rate = MENTOR_DAILY_RATE


def serialize(message):
    return {'id': message.pk, 'role': message.role, 'text': message.content, 'created_at': message.created_at.isoformat()}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_view(request):
    provider = configured_provider()
    return Response({'mode': 'ai' if provider else 'unconfigured',
                     'provider': provider, 'personalization_available': twin_context_enabled(),
                     'history_supported': True, 'conversation_saved': True,
                     'notice': 'Mentor messages are stored and sent to the configured provider when live AI is enabled. Personalised skill context requires an explicit opt-in.'})


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([MentorBurstThrottle, MentorDailyThrottle])
def mentor(request, slug):
    assignment = get_object_or_404(visible(request.user), slug=slug)
    from progression.services import require_module, admin_access
    require_module(request.user, assignment.module)
    if not admin_access(request.user) and not AssignmentAttempt.objects.filter(assignment=assignment, learner=request.user).exists():
        return Response({'detail': 'Start this assignment before using the mentor.'}, status=status.HTTP_403_FORBIDDEN)

    history = MentorMessage.objects.filter(assignment=assignment, learner=request.user)
    if request.method == 'GET':
        recent = list(history.order_by('-created_at', '-pk')[:40])
        recent.reverse()
        provider = configured_provider()
        return Response({'messages': [serialize(m) for m in recent],
                         'mode': 'ai' if provider else 'unconfigured',
                         'provider': provider, 'personalization_available': twin_context_enabled()})
    if request.method == 'DELETE':
        count, _ = history.delete()
        return Response({'deleted': count})

    question = request.data.get('message')
    if not isinstance(question, str) or not question.strip() or len(question) > 1200:
        return Response({'detail': 'Please send a question between 1 and 1200 characters.'}, status=400)
    if not configured_provider():
        return Response({'detail': 'The live AI mentor is not configured. Ask your instructor or use the guided hint preview.'}, status=503)

    personalization_requested = request.data.get('use_learning_twin', False)
    if not isinstance(personalization_requested, bool):
        return Response({'detail': 'use_learning_twin must be a boolean.'}, status=400)
    if personalization_requested and not twin_context_enabled():
        return Response({'detail': 'Personalised AI guidance is not enabled on this server.'}, status=400)

    question = question.strip()
    try:
        previous = list(history.order_by('-created_at', '-pk')[:8])
        previous.reverse()
        if personalization_requested:
            # Generate from server-only instructor-reviewed evidence. Never use chat
            # history as evidence of competency, and never expose raw review notes.
            from learning_twin.api import build_profile
            learning_context = build_learning_context(build_profile(request.user))
            reply = make_socratic_reply(assignment, previous, question, learning_context=learning_context)
        else:
            reply = make_socratic_reply(assignment, previous, question)
    except MentorProviderError:
        return Response({'detail': 'AI mentor unavailable. No message was saved; try again later.'}, status=503)
    user_message = MentorMessage.objects.create(assignment=assignment, learner=request.user, role=MentorMessage.LEARNER, content=question)
    mentor_message = MentorMessage.objects.create(assignment=assignment, learner=request.user, role=MentorMessage.MENTOR, content=reply)
    return Response({'learner_message': serialize(user_message), 'mentor_message': serialize(mentor_message), 'mode': 'ai'}, status=201)
