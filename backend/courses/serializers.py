"""Public API contracts shaped for the existing React LMS frontend."""
from django.db.models import Prefetch
from rest_framework import serializers
from .models import Course, Module, Lesson, Project


class CourseSummarySerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    phase_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("slug", "title", "subtitle", "description", "estimated_months", "phase_count", "lesson_count")

    def get_phase_count(self, obj):
        return sum(m.published for m in obj.modules.all())

    def get_lesson_count(self, obj):
        return sum(len([l for l in m.lessons.all() if l.published]) for m in obj.modules.all() if m.published)


def course_payload(course, user=None):
    from django.contrib.auth.models import AnonymousUser
    from progression.services import course_progress, admin_access
    from progression.models import SetupCompletion
    user = user or AnonymousUser()
    is_admin = admin_access(user)
    states, accessible_lessons = course_progress(user, course.pk)
    completions = set(SetupCompletion.objects.filter(
        learner=user, guide__module__course=course,
    ).values_list('guide_id', 'revision')) if user.is_authenticated else set()
    phases, lessons, projects = [], [], []
    for module in course.modules.all():
        if not module.published and not is_admin:
            continue
        progress = states.get(module.pk, {})
        final_project = progress.get('final_project')
        if is_admin:
            final = module.assignments.filter(module_pass_score__isnull=False).first()
            if final and not final_project:
                final_project = {'slug': final.slug, 'title': final.title,
                                 'pass_score': final.module_pass_score, 'status': 'ready'}
        guide = getattr(module, 'guide', None)
        required = bool(guide and guide.published and guide.required_setup)
        phases.append({'setup_required': required,
            'setup_complete': not required or (guide.pk, guide.revision) in completions,
            'id': module.position, 'module_id': module.pk, 'name': module.name, 'duration': module.duration_weeks,
            'category': module.category, 'desc': module.description, 'icon': module.icon,
            'topics': [t.text for t in module.topics.all()], 'project': 'Module milestone',
            'progress': {**progress, 'status': 'admin_preview' if is_admin else progress['status'],
                         'project_unlocked': is_admin or progress.get('project_unlocked', False),
                         'final_project': final_project}})
        for lesson in module.lessons.all():
            if not lesson.published and not is_admin:
                continue
            lessons.append({'id': lesson.public_id, 'phaseId': module.position, 'title': lesson.title,
                'minutes': lesson.minutes, 'difficulty': lesson.difficulty, 'locked': not (is_admin or lesson.pk in accessible_lessons)})
        for project in module.projects.all():
            if not project.published and not is_admin:
                continue
            unlocked = is_admin or progress['project_unlocked']
            projects.append({'id': project.public_id, 'name': project.name, 'phase': module.position,
                'level': project.level, 'locked': not unlocked,
                **({'description': project.description, 'skills': [s.strip() for s in project.skills_csv.split(',') if s.strip()]} if unlocked else {})})
    from .classroom import classroom_entry
    entry = classroom_entry(course, user, states, accessible_lessons, bool(lessons))
    return {'classroom_entry': entry, 'slug': course.slug, 'title': course.title, 'subtitle': course.subtitle,
        'description': course.description, 'estimated_months': course.estimated_months,
        'updated_at': course.updated_at.isoformat(), 'phases': phases, 'lessons': lessons, 'projects': projects}
