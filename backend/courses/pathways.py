"""Public discovery uses canonical modules: no duplicate enrolments or grades."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from progression.services import admin_access, course_progress
from .models import LearningPathway


@api_view(['GET'])
@permission_classes([AllowAny])
def pathway_list(request):
    pathways = LearningPathway.objects.filter(published=True).prefetch_related(
        'units__module__course', 'units__module__lessons', 'units__module__guide')
    progress = {}
    result = []
    for pathway in pathways:
        units = []
        for unit in pathway.units.all():
            module = unit.module
            if not module.published or module.course.status != 'published':
                continue
            if module.course_id not in progress:
                progress[module.course_id] = course_progress(request.user, module.course_id)[0]
            state = progress[module.course_id].get(module.pk, {})
            count = sum(lesson.published for lesson in module.lessons.all())
            guide = getattr(module, 'guide', None)
            units.append({
                'position': unit.position, 'year': unit.year, 'module_id': module.pk,
                'title': module.name, 'summary': module.description,
                'course_slug': module.course.slug, 'module_position': module.position,
                'lesson_count': count, 'readiness': 'authored_slice' if count else 'outline',
                'scope': unit.scope, 'shared': unit.shared,
                'outcomes': guide.outcomes.splitlines() if guide and guide.published else [],
                'progress': {**state, 'status': 'admin_preview' if admin_access(request.user) else state.get('status', 'locked')},
            })
        result.append({'slug': pathway.slug, 'title': pathway.title, 'description': pathway.description,
                       'disclaimer': pathway.disclaimer, 'units': units})
    return Response(result)
