"""Explain a locked classroom using the same saved evidence as the access gates.

Discovery never starts attempts or awards credit. Only published metadata is returned.
"""
from urllib.parse import urlencode
from courses.models import Module, ModulePrerequisite
from progression.services import admin_access, course_progress
from progression.models import LessonIteration


def classroom_entry(course, user, states, accessible_lessons, has_lessons):
    if not has_lessons:
        return {'kind': 'empty', 'title': 'This course has no published lessons yet',
                'message': 'Its roadmap is an outline. Detailed lessons still need to be published.',
                'requirements': [], 'action': None}
    if admin_access(user) or accessible_lessons:
        return {'kind': 'available', 'requirements': [], 'action': None}
    if not user.is_authenticated:
        return {'kind': 'sign_in', 'title': 'Sign in to open your classroom',
                'message': 'Your lesson access and progress belong to your Academy account.',
                'requirements': [], 'action': {'label': 'Sign in', 'href': '/'}}

    cache = {course.pk: states}
    allowed_cache = {course.pk: accessible_lessons}

    def progress(module):
        if module.course_id not in cache:
            cache[module.course_id], allowed_cache[module.course_id] = course_progress(user, module.course_id)
        return cache[module.course_id].get(module.pk, {})

    def published(module):
        return module.published and module.course.status == 'published'

    def metadata(module):
        return {'module_id': module.pk, 'title': module.name, 'course_slug': module.course.slug,
                'status': progress(module).get('status', 'locked')}

    def blocked(message):
        return {'kind': 'configuration', 'title': 'A required module needs attention',
                'message': message, 'requirements': [], 'action': None}

    def resolve(module, trail):
        if module.pk in trail:
            return blocked('The prerequisite order needs an instructor review. Your lessons remain locked until it is corrected.')
        if not published(module):
            return blocked('A required module is not published. Ask your instructor about the next available step.')
        trail = trail | {module.pk}
        # Match canonical same-course ordering, including its reviewed final projects.
        earlier = list(Module.objects.filter(course_id=module.course_id, published=True,
            position__lt=module.position).select_related('course').order_by('position', 'pk'))
        external = [r.required_module for r in ModulePrerequisite.objects.filter(module=module)
                    .select_related('required_module__course').order_by('pk')]
        for required in earlier + external:
            if progress(required).get('status') != 'completed':
                result = resolve(required, trail)
                # Do not reveal unpublished prerequisite titles through discovery.
                if published(required) and required.pk not in {r['module_id'] for r in result['requirements']}:
                    result['requirements'].append(metadata(required))
                return result

        state = progress(module)
        if state.get('status') in ('final_project', 'awaiting_project'):
            final = state.get('final_project')
            if not final or not state.get('project_unlocked'):
                return blocked('Your prerequisite lessons are complete, but their final project is not published. Contact your instructor.')
            status = final['status']
            waiting = status == 'awaiting_review'
            return {'kind': 'review' if waiting else 'project',
                'title': 'Your prerequisite project is awaiting review' if waiting else 'Complete the prerequisite final project',
                'message': f"{module.name} requires its reviewed final project to pass at {final['pass_score']}% or higher. "
                           + ('Submitting work does not award a pass until it is reviewed.' if waiting else 'Passing the lesson quizzes alone does not complete the module.'),
                'requirements': [], 'action': {'label': 'View submitted project' if waiting else 'Open required final project',
                    'href': '/assignments/?' + urlencode({'assignment': final['slug']})}}
        # Status may be locked if imported dependencies are inconsistent. Never offer
        # an inaccessible lesson just because it exists in the catalogue.
        allowed = allowed_cache[module.course_id]
        passed = LessonIteration.objects.filter(learner=user, status='passed').values_list('lesson_id', flat=True)
        lesson = module.lessons.filter(published=True, pk__in=allowed).exclude(pk__in=passed).order_by('position', 'pk').first()
        if lesson:
            shared = module.pathway_units.filter(shared=True, pathway__published=True).exists()
            return {'kind': 'prerequisite', 'title': 'Start with the required foundation' if shared else 'Complete the required earlier module',
                'message': f'The lessons in {course.title} are published. First complete {module.name} and its reviewed final project. '
                           + ('This shared module counts toward both pathways. ' if shared else '')
                           + 'You do not need to finish the entire course that contains it.',
                'requirements': [], 'action': {'label': f'Open {module.name} classroom',
                    'href': '/dashboard/?' + urlencode({'course': module.course.slug, 'view': 'classroom', 'lesson': lesson.public_id})}}
        if not module.lessons.filter(published=True).exists():
            return blocked('A required module is still an outline. Ask your instructor when its lessons and project will be published.')
        return blocked('The saved prerequisite state needs an instructor review. No lesson or project has been unlocked by this message.')

    first = next((m for m in course.modules.all() if published(m) and states.get(m.pk, {}).get('status') != 'completed'), None)
    return resolve(first, frozenset()) if first else blocked('Ask your instructor which module is available next.')
