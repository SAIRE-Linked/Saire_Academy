"""Versioned, additive seed data for v10.4. Keep this loader and its data stable."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'content' / 'academy_foundations_v104.json'
COURSE = 'ai-engineer-agentic-systems'


def add_foundation_guides(apps, database):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    table = lambda name: apps.get_model('courses', name).objects.using(database)
    modules = {
        module.position: module for module in table('Module').filter(course__slug=COURSE)
    }
    if not modules:
        return
    for position, outcomes in enumerate(data['outcomes'], start=1):
        module = modules.get(position)
        if not module:
            continue
        python = position == 1
        guide, created = table('ModuleGuide').get_or_create(module_id=module.pk, defaults={
            'title': 'Getting Ready · Your first Python program' if python else f'Getting Ready · {module.name}',
            'introduction': data['python_intro'] if python else 'Review these outcomes and use the checklist template to plan your setup.',
            'outcomes': '\n'.join(outcomes),
            'published': True,
            'required_setup': python,
            'first_program': python,
        })
        if python and created:
            for index, (heading, instructions, command, verification) in enumerate(data['steps'], start=1):
                table('SetupStep').create(guide_id=guide.pk, position=index, heading=heading,
                                          instructions=instructions, command=command, verification=verification)
            for index, (title, url, purpose) in enumerate(data['module_resources'], start=1):
                table('LearningResource').get_or_create(module_id=module.pk, lesson_id=None, url=url, defaults={
                    'title': title, 'purpose': purpose, 'position': index,
                })
    guide_fields = ('explanation', 'demonstration', 'example', 'guided_exercise',
                    'independent_exercise', 'further_explanation')
    for item in data['lessons']:
        lesson = table('Lesson').filter(public_id=item['id'], module__course__slug=COURSE).first()
        if not lesson:
            continue
        table('LessonGuide').get_or_create(lesson_id=lesson.pk, defaults=dict(zip(guide_fields, item['guide'])))
        title, url, purpose = item['resource']
        table('LearningResource').get_or_create(module_id=lesson.module_id, lesson_id=lesson.pk, url=url,
                                               defaults={'title': title, 'purpose': purpose})
        if not table('FormativeQuestion').filter(lesson_id=lesson.pk).exists():
            for index, (prompt, options, correct, explanation) in enumerate(item['checks'], start=1):
                table('FormativeQuestion').create(
                    lesson_id=lesson.pk, position=index, prompt=prompt, option_a=options[0],
                    option_b=options[1], option_c=options[2], correct=correct, explanation=explanation,
                )
    for term, definition, example in data['glossary']:
        table('GlossaryEntry').get_or_create(term=term, defaults={'definition': definition, 'example': example})
