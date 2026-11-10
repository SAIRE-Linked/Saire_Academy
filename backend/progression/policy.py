"""Shared learner policy for the handbook and graded starts."""
from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from courses.models import ModuleGuide
from .models import OrientationAcknowledgment, SetupCompletion

LESSON_DAYS = 14
SUPPLEMENTARY_DAYS = 7
MENTOR_HOURLY_RATE = '8/hour'
MENTOR_DAILY_RATE = '40/day'


def orientation_state(user):
    version = settings.SAIRE_ORIENTATION_VERSION
    return {
        'version': version,
        'acknowledged': OrientationAcknowledgment.objects.filter(learner=user, version=version).exists(),
    }


def require_ready_to_start(user, module):
    from .services import admin_access
    if admin_access(user):
        return
    if not orientation_state(user)['acknowledged']:
        raise PermissionDenied('Read the Academy Handbook and acknowledge the rules in Study Hub before starting.')
    guide = ModuleGuide.objects.filter(module=module, published=True, required_setup=True).first()
    if guide and not SetupCompletion.objects.filter(learner=user, guide=guide, revision=guide.revision).exists():
        raise PermissionDenied('Complete this module’s Getting Ready checklist before starting.')
