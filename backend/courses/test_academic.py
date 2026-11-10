"""Integration checks for canonical shared credit, server gates and additive seeds."""
import tempfile
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from assessments.models import Assignment, AssignmentAttempt, Submission, CodeReview
from progression.models import LessonIteration, OrientationAcknowledgment, SetupCompletion
from progression.services import course_progress
from .models import (Course, Module, Lesson, ModulePrerequisite, LearningPathway,
                     PathwayUnit, SourceReference, SourceCoverage)


class AcademicJourneyTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = tempfile.TemporaryDirectory(prefix='saire-academic-tests-')
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media.name)
        cls.settings_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.settings_override.disable()
        cls.media.cleanup()

    @classmethod
    def setUpTestData(cls):
        call_command('seed_curriculum', verbosity=0)
        call_command('seed_proofloop', verbosity=0)
        call_command('seed_academic_pathways', verbosity=0)
        U = get_user_model()
        cls.learner = U.objects.create_user('academic-learner')
        cls.other = U.objects.create_user('academic-other')
        cls.admin = U.objects.create_superuser('academic-admin', 'admin@example.test', 'TestPassword123!')
        cls.python = Module.objects.get(course__slug='ai-engineer-agentic-systems', position=1)
        cls.intake = Module.objects.get(course__slug='it-foundations', position=1)
        cls.workflow = Module.objects.get(course__slug='it-foundations', position=2)
        cls.records = Module.objects.get(course__slug='it-data-systems', position=1)

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client.force_login(self.learner)

    def paths(self):
        return {path['slug']: path for path in self.client.get('/api/v1/pathways/').json()}

    def pass_module(self, module, reviewed=True):
        now = timezone.now()
        for lesson in module.lessons.filter(published=True):
            LessonIteration.objects.get_or_create(learner=self.learner, lesson=lesson, defaults={
                'started_at': now, 'due_at': now + timedelta(days=14), 'completed_at': now,
                'status': 'passed', 'raw_score': 100, 'credited_score': 100})
        assignment = module.assignments.get(module_pass_score__isnull=False)
        attempt, _ = AssignmentAttempt.objects.get_or_create(learner=self.learner, assignment=assignment,
            defaults={'due_at': now + timedelta(days=assignment.duration_days)})
        submission = Submission.objects.create(attempt=attempt, repository_url='https://github.com/student/example', commit_sha='a'*40)
        if reviewed:
            CodeReview.objects.create(submission=submission, reviewer=self.admin, verified_test_score=100,
                code_quality_score=100, q1_score=10, q2_score=10, q3_score=10, q4_score=10, q5_score=10)
        return submission

    def test_shared_module_is_one_record_and_credit_is_reused(self):
        paths = self.paths()
        self.assertEqual(paths['ai-engineering']['units'][0]['module_id'], self.python.pk)
        self.assertEqual(paths['it-academic-foundations']['units'][0]['module_id'], self.python.pk)
        self.pass_module(self.python)
        for path in self.paths().values():
            self.assertEqual(path['units'][0]['progress']['status'], 'completed')
        self.assertEqual(LessonIteration.objects.filter(learner=self.learner).count(), 4)

    def test_outline_counts_and_private_source_metadata(self):
        path = self.paths()['it-academic-foundations']
        self.assertEqual(len(path['units']), 21)
        self.assertEqual(sum(u['readiness'] == 'authored_slice' for u in path['units']), 4)
        self.assertEqual(sum(u['lesson_count'] for u in path['units']), 10)
        self.assertEqual(SourceReference.objects.filter(availability='audited').count(), 6)
        self.assertEqual(SourceReference.objects.filter(availability='missing').count(), 17)
        self.assertEqual(SourceCoverage.objects.filter(source__code='IS512').count(), 7)
        response = self.client.get('/api/v1/pathways/')
        for private in ('sha256', 'Richfield', 'SRC-01', 'page_range', 'audit_note', 'correct'):
            self.assertNotContains(response, private)
        self.assertEqual(self.client.post('/api/v1/pathways/', {}).status_code, 405)

    def test_all_access_routes_respect_cross_course_prerequisite(self):
        self.assertEqual(self.paths()['it-academic-foundations']['units'][1]['progress']['status'], 'locked')
        for route in ('', 'start/', 'submit/', 'supplement/'):
            method = self.client.get if not route else self.client.post
            self.assertEqual(method('/api/v1/lessons/it-intake-1/' + route).status_code, 403)
        for route in ('', 'start/', 'starter/', 'submit/'):
            method = self.client.post if route in ('start/', 'submit/') else self.client.get
            self.assertEqual(method('/api/v1/assignments/saire-service-intake/' + route).status_code, 403)

    def test_reviewed_final_required_and_other_learner_has_no_credit(self):
        submission = self.pass_module(self.python, reviewed=False)
        states, _ = course_progress(self.learner, self.intake.course_id)
        self.assertEqual(states[self.intake.pk]['status'], 'locked')
        self.assertEqual(submission.local_tests_passed, 0)
        submission.local_tests_passed = 100
        submission.save()
        self.assertEqual(course_progress(self.learner, self.intake.course_id)[0][self.intake.pk]['status'], 'locked')
        CodeReview.objects.create(submission=submission, reviewer=self.admin, verified_test_score=100,
            code_quality_score=100, q1_score=10, q2_score=10, q3_score=10, q4_score=10, q5_score=10)
        self.assertEqual(course_progress(self.learner, self.intake.course_id)[0][self.intake.pk]['status'], 'lessons')
        self.assertEqual(course_progress(self.other, self.intake.course_id)[0][self.intake.pk]['status'], 'locked')

    def test_setup_is_untimed_orientation_and_setup_enforced_then_api_journey(self):
        self.pass_module(self.python)
        before = LessonIteration.objects.count()
        url = f'/api/v1/academy/modules/{self.intake.pk}/setup/'
        setup = self.client.get(url).json()
        self.assertEqual(LessonIteration.objects.count(), before)
        self.assertEqual(self.client.post('/api/v1/lessons/it-intake-1/start/').status_code, 403)
        OrientationAcknowledgment.objects.create(learner=self.learner, version=settings.SAIRE_ORIENTATION_VERSION)
        self.assertEqual(self.client.post('/api/v1/lessons/it-intake-1/start/').status_code, 403)
        result = self.client.post(url, {'revision': setup['revision'], 'checked': [s['id'] for s in setup['steps']]}, content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(LessonIteration.objects.count(), before)
        for public_id in ('it-intake-1', 'it-intake-2'):
            response = self.client.post(f'/api/v1/lessons/{public_id}/start/')
            self.assertEqual(response.status_code, 201)
            iteration = LessonIteration.objects.get(learner=self.learner, lesson__public_id=public_id)
            self.assertEqual(iteration.due_at - iteration.started_at, timedelta(days=14))
            self.assertTrue(timezone.is_aware(iteration.due_at))
            detail = self.client.get(f'/api/v1/lessons/{public_id}/').json()
            self.assertEqual(len(detail['sections']), 5)
            self.assertNotIn('correct', detail['quiz'][0])
            lesson = Lesson.objects.get(public_id=public_id)
            answers = list(lesson.quiz_questions.values_list('correct', flat=True))
            result = self.client.post(f'/api/v1/lessons/{public_id}/submit/', {'answers': answers}, content_type='application/json')
            self.assertEqual(result.json()['iteration']['status'], 'passed')
        response = self.client.post('/api/v1/assignments/saire-service-intake/start/')
        self.assertEqual(response.status_code, 201)
        attempt = AssignmentAttempt.objects.get(learner=self.learner, assignment__slug='saire-service-intake')
        self.assertEqual(attempt.due_at - attempt.started_at, timedelta(days=14))
        self.assertEqual(self.client.get('/api/v1/assignments/saire-service-intake/starter/').status_code, 200)
        self.assertEqual(course_progress(self.learner, self.workflow.course_id)[0][self.workflow.pk]['status'], 'locked')

    def test_year_two_requires_year_one_final_projects(self):
        self.pass_module(self.python)
        self.pass_module(self.intake)
        self.assertEqual(course_progress(self.learner, self.records.course_id)[0][self.records.pk]['status'], 'locked')
        self.pass_module(self.workflow)
        self.assertEqual(course_progress(self.learner, self.records.course_id)[0][self.records.pk]['status'], 'lessons')

    def test_only_superuser_has_unrestricted_preview(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/api/v1/lessons/it-records-2/').status_code, 200)
        self.assertEqual(self.paths()['it-academic-foundations']['units'][11]['progress']['status'], 'admin_preview')
        self.other.is_staff = True; self.other.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get('/api/v1/lessons/it-records-2/').status_code, 403)

    def test_seed_preserves_all_customisations_and_original_project_duration(self):
        lesson = Lesson.objects.get(public_id='it-intake-1')
        lesson.title = 'My customised teaching'; lesson.save()
        self.python.name = 'My Python foundation'; self.python.save()
        source = SourceReference.objects.get(code='DS500'); source.audit_note = 'My private audit note'; source.save()
        outline = Module.objects.get(curriculum_key='academic-web511')
        outline.position = 99; outline.name = 'My web outline'; outline.save()
        count = Lesson.objects.count()
        call_command('seed_academic_pathways', verbosity=0)
        self.assertEqual(Lesson.objects.count(), count)
        self.assertEqual(Lesson.objects.get(pk=lesson.pk).title, 'My customised teaching')
        self.assertEqual(Module.objects.get(pk=self.python.pk).name, 'My Python foundation')
        self.assertEqual(SourceReference.objects.get(pk=source.pk).audit_note, 'My private audit note')
        self.assertEqual(Assignment.objects.get(slug='saire-quotation-engine').duration_days, 7)
        self.assertEqual(Module.objects.get(pk=outline.pk).position, 99)
        self.assertEqual(Module.objects.get(pk=outline.pk).name, 'My web outline')

    def test_cycles_rejected_and_imported_cycle_fails_closed(self):
        with self.assertRaises(ValidationError):
            ModulePrerequisite.objects.create(module=self.python, required_module=self.records)
        with self.assertRaises(ValidationError):
            ModulePrerequisite.objects.create(module=self.intake, required_module=self.workflow)
        # A bulk import can bypass save validation; progress must still deny access.
        ModulePrerequisite.objects.bulk_create([ModulePrerequisite(module=self.python, required_module=self.records)])
        self.assertEqual(course_progress(self.learner, self.python.course_id)[1], set())

    def test_drafts_and_unpublished_pathways_hidden(self):
        path = LearningPathway.objects.get(slug='it-academic-foundations')
        path.published = False; path.save()
        self.assertNotIn(path.slug, self.paths())
        self.python.published = False; self.python.save()
        self.assertEqual(self.paths()['ai-engineering']['units'][0]['readiness'], 'outline')

    def test_all_new_lessons_have_original_sequence_checks_and_guides(self):
        lessons = Lesson.objects.filter(module__course__slug__in=['it-foundations', 'it-data-systems'])
        self.assertEqual(lessons.count(), 6)
        for lesson in lessons:
            self.assertEqual(list(lesson.sections.values_list('heading', flat=True)),
                ['Explain', 'Demonstrate', 'Guided exercise', 'Independent exercise', 'Check understanding'])
            self.assertGreater(len(lesson.guide.explanation), 900)
            self.assertEqual(lesson.quiz_questions.count(), 2)
            self.assertEqual(lesson.formative_questions.count(), 2)
