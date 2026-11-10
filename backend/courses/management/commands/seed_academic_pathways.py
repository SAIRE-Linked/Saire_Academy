"""Opt-in curriculum seed. No updates/deletes: retained database edits always win."""
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from courses.academic_content import MODULES, OUTLINES, PRACTICE
from courses.academic_backlog import PLANS
from courses.models import (Course, Module, Lesson, LessonSection, QuizQuestion, Project,
    ModuleGuide, SetupStep, LessonGuide, LearningResource, FormativeQuestion, GlossaryEntry,
    LearningPathway, PathwayUnit, ModulePrerequisite, SourceReference, SourceCoverage)
from assessments.models import Assignment
from learning_twin.models import Skill, AssignmentSkill

ROOT = Path(__file__).resolve().parents[4]


class Command(BaseCommand):
    help = 'Add original academic pathway slice, outlines and internal audit metadata. Preserve existing edits.'

    @transaction.atomic
    def handle(self, *args, **options):
        # Resolve shared credit by stable lesson identity, even after an admin reorder.
        shared_lesson = Lesson.objects.filter(public_id='p1-l1', module__course__slug='ai-engineer-agentic-systems').select_related('module').first()
        python_module = shared_lesson.module if shared_lesson else None
        if not python_module or not python_module.lessons.filter(published=True).exists():
            raise CommandError('Run seed_curriculum first; the shared Python foundation must exist.')
        if not python_module.assignments.filter(published=True, module_pass_score__isnull=False).exists():
            raise CommandError('Run seed_proofloop first; shared Python needs its existing final project.')
        year1, _ = Course.objects.get_or_create(slug='it-foundations', defaults={
            'title': 'IT foundations: systems and workflows', 'status': 'published', 'position': 1,
            'subtitle': 'Original Year 1 practical foundations', 'estimated_months': 'Flexible',
            'description': 'Two authored modules followed by clearly marked curriculum outlines. Complete the shared Python foundation first.'})
        year2, _ = Course.objects.get_or_create(slug='it-data-systems', defaults={
            'title': 'IT data systems: Year 2 sample', 'status': 'published', 'position': 2,
            'subtitle': 'A first relational database slice', 'estimated_months': 'Flexible',
            'description': 'One authored database sample, with the remaining Year 2 subjects planned. Requires the reviewed Year 1 foundation projects.'})
        modules = {'PR511': python_module}
        for spec in MODULES:
            course = year2 if spec['key'] == 'DB600' else year1
            module, created = Module.objects.get_or_create(curriculum_key='academic-' + spec['key'].lower(), defaults={
                'course': course, 'position': spec['position'],
                'name': spec['name'], 'description': spec['description'], 'duration_weeks': 4,
                'category': 'foundations', 'icon': 'database' if spec['key'] == 'DB600' else 'code'})
            modules[spec['key']] = module
            if created:
                self.author(module, spec)
        for year in (1, 2):
            position = 3 if year == 1 else 2
            for code, unit_year, title, summary in OUTLINES:
                if unit_year != year:
                    continue
                module, _ = Module.objects.get_or_create(curriculum_key='academic-' + code.lower(),
                    defaults={'course': year1 if year == 1 else year2, 'position': position,
                              'name': title, 'description': 'Outline only. ' + summary, 'category': 'foundations'})
                modules[code] = module
                plan = PLANS[code]
                ModuleGuide.objects.get_or_create(module=module, defaults={
                    'title': 'Planned outcomes: ' + title, 'published': True, 'required_setup': False,
                    'introduction': 'Outline only. Use the reusable setup template to plan; no lesson or project is released for this unit.',
                    'outcomes': '\n'.join(plan['outcomes'])})
                LearningResource.objects.get_or_create(module=module, url=plan['url'], defaults={
                    'title': 'Optional reference for planned unit', 'purpose': 'Reference only: this unit is an outline, with lessons and assessments still to be authored.'})
                position += 1
        for module, required in [(modules['IS511'], python_module), (modules['DB600'], modules['IS512'])]:
            ModulePrerequisite.objects.get_or_create(module=module, required_module=required)
        it, _ = LearningPathway.objects.get_or_create(slug='it-academic-foundations', defaults={
            'title': 'Computing and IT: academic foundations', 'published': True,
            'description': 'An original BSc IT-inspired pathway: shared Python, practical systems work and a relational data sample.',
            'disclaimer': 'Independent learning pathway, not an accredited BSc degree. Six new lessons and three projects form a usable slice; other units are outlines.'})
        order = ['PR511', 'IS511', 'IS512', 'WEB511', 'MATH511', 'NET511', 'PR512', 'WEB512', 'MATH512', 'NET512', 'DS500',
                 'DB600', 'PR621', 'PR622', 'IP621', 'IP622', 'IS621', 'IS622', 'CC600', 'ML600', 'BDI600']
        for index, code in enumerate(order, 1):
            scope = ('Shared existing four-lesson Python foundation and quotation project. Collections, OOP and GUI remain future work.' if code == 'PR511' else
                     'Two fully authored lessons, preparatory lab and reviewed final project. This is a first slice, not full subject coverage.' if code in ('IS511', 'IS512', 'DB600') else
                     'Outline only: lesson bodies, setup lab, assessment and grading suite remain to be authored.')
            PathwayUnit.objects.get_or_create(pathway=it, module=modules[code], defaults={
                'position': index, 'year': 1 if index <= 11 else 2, 'scope': scope, 'shared': code == 'PR511'})
        ai, _ = LearningPathway.objects.get_or_create(slug='ai-engineering', defaults={
            'title': 'AI Engineering', 'published': True, 'description': 'Your existing AI Engineering and Agentic Systems pathway.',
            'disclaimer': 'Existing content and project policies are preserved. Later modules without published lessons remain outlines.'})
        for module in python_module.course.modules.all():
            PathwayUnit.objects.get_or_create(pathway=ai, module=module, defaults={
                'position': module.position, 'year': 1, 'shared': module.pk == python_module.pk,
                'scope': 'Existing module; its published lessons and reviewed final project determine progress.' if module.lessons.filter(published=True).exists() else 'Existing syllabus outline; lesson content remains to be authored.'})
        for term, definition in [
            ('Acceptance criterion', 'An observable condition used to decide whether a requirement has been met.'),
            ('State transition', 'An allowed change from one named state to another.'),
            ('Primary key', 'A column or combination of columns that uniquely identifies a row.'),
            ('Query parameter', 'A value supplied separately from the fixed text of a database statement.'),
            ('Schema', 'The defined structure and rules of stored data.'),
        ]:
            GlossaryEntry.objects.get_or_create(term=term, defaults={'definition': definition})
        audit = json.loads((ROOT / 'backend/content/academic_source_audit.json').read_text(encoding='utf-8'))
        for row in audit:
            source, _ = SourceReference.objects.get_or_create(code=row['code'], defaults={k: row[k] for k in
                ('title', 'attribution', 'availability', 'sha256', 'pages', 'audit_note')})
            for topic in row['topics']:
                module = modules.get(topic.get('target', row['code']))
                if module:
                    SourceCoverage.objects.get_or_create(source=source, module=module, topic=topic['topic'], defaults={
                        'page_range': topic['pages'], 'coverage': topic['coverage'], 'gap': topic['gap']})
        self.stdout.write(self.style.SUCCESS('Academic pathways seeded. Existing content, grades, dates and custom edits preserved.'))

    def author(self, module, spec):
        guide = ModuleGuide.objects.create(module=module, title='Getting ready: ' + spec['name'],
            introduction='Prepare with invented data. Setup is untimed and does not start a graded iteration.',
            outcomes='\n'.join(spec['outcomes']), published=True, required_setup=True)
        for index, (heading, instructions, command, verification) in enumerate(spec['setup'], 1):
            SetupStep.objects.create(guide=guide, position=index, heading=heading, instructions=instructions, command=command, verification=verification)
        for index, item in enumerate(spec['lessons'], 1):
            lesson = Lesson.objects.create(module=module, public_id=item['id'], position=index, title=item['title'],
                objective=item['objective'], challenge=item['independent'], minutes=40, published=True)
            LessonGuide.objects.create(lesson=lesson, explanation=item['explain'], demonstration=item['demo'], example=item['example'],
                guided_exercise=item['guided'], independent_exercise=item['independent'], further_explanation=item['extra'])
            for pos, (heading, body, code) in enumerate([
                ('Explain', item['explain'], ''), ('Demonstrate', item['demo'], item['example']),
                ('Guided exercise', item['guided'], ''), ('Independent exercise', item['independent'], ''),
                ('Check understanding', 'Complete the short check below. Explain each answer in your own words. A quiz pass unlocks the next lesson; your final project still needs instructor review.', '')], 1):
                LessonSection.objects.create(lesson=lesson, position=pos, heading=heading, body=body, code=code)
            for pos, (question, answers, correct, reason) in enumerate(item['checks'], 1):
                QuizQuestion.objects.create(lesson=lesson, position=pos, question=question, correct=correct, reason=reason,
                    option_a=answers[0], option_b=answers[1], option_c=answers[2], option_d=answers[3])
            for pos, (question, answers, correct, reason) in enumerate(PRACTICE[item['id']], 1):
                FormativeQuestion.objects.create(lesson=lesson, position=pos, prompt=question, option_a=answers[0],
                    option_b=answers[1], option_c=answers[2], correct=correct, explanation=reason)
        links = [('Python collections', 'https://docs.python.org/3/tutorial/datastructures.html', 'Revisit lists and dictionaries after the original examples.')]
        if spec['key'] == 'DB600':
            links = [('Python sqlite3', 'https://docs.python.org/3/library/sqlite3.html', 'Check parameter binding and connection transaction behaviour.'),
                     ('SQLite CREATE TABLE', 'https://www.sqlite.org/lang_createtable.html', 'Look up primary keys, NOT NULL and CHECK constraints.')]
        for index, (title, url, purpose) in enumerate(links, 1):
            LearningResource.objects.create(module=module, title=title, url=url, purpose=purpose, position=index)
        project = spec['project']
        public_project = Project.objects.create(module=module, public_id=project['slug'], name=project['title'],
            description=project['brief'], skills_csv=', '.join(s[1] for s in project['skills']))
        assignment = Assignment.objects.create(module=module, project=public_project, slug=project['slug'], title=project['title'],
            brief=project['brief'], learning_outcomes='\n'.join(spec['outcomes']), published=True, duration_days=14, module_pass_score=70,
            **{f'q{i}': text for i, text in enumerate(project['questions'], 1)})
        archive = BytesIO()
        with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
            starter = ROOT / 'assignments' / project['slug']
            for path in sorted(starter.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts:
                    z.write(path, path.relative_to(starter).as_posix())
        assignment.starter_bundle.save(project['slug'] + '-starter.zip', ContentFile(archive.getvalue()), save=True)
        for slug, name, dimension in project['skills']:
            skill, _ = Skill.objects.get_or_create(slug=slug, defaults={'name': name, 'category': 'engineering',
                'description': 'Evidence comes from mapped, instructor-reviewed ProofLoop work; no score is inferred from reading.'})
            AssignmentSkill.objects.get_or_create(assignment=assignment, skill=skill, dimension=dimension)
