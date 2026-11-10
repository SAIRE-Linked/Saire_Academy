from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token

from assessments.models import Assignment, AssignmentAttempt, CodeReview, Submission
from courses.models import GlossaryEntry, Lesson, ModuleGuide
from progression.models import LessonIteration


class AcademyFoundationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_curriculum', verbosity=0)
        cls.learner = get_user_model().objects.create_user('new-learner')
        cls.other = get_user_model().objects.create_user('other-learner')
        cls.lesson = Lesson.objects.get(public_id='p1-l1')
        cls.setup_path = f'/api/v1/academy/modules/{cls.lesson.module_id}/setup/'
        cls.start_path = '/api/v1/lessons/p1-l1/start/'

    def setUp(self):
        cache.clear()
        self.client.force_login(self.learner)

    def post(self, path, payload):
        return self.client.post(path, payload, content_type='application/json')

    def acknowledge(self):
        return self.post('/api/v1/academy/orientation/', {
            'version': settings.SAIRE_ORIENTATION_VERSION, 'accept': True,
        })

    def complete_setup(self):
        setup = self.client.get(self.setup_path).json()
        return self.post(self.setup_path, {
            'revision': setup['revision'], 'checked': [step['id'] for step in setup['steps']],
        })

    def test_orientation_and_setup_are_independent_and_neither_starts_a_timer(self):
        self.assertEqual(self.post(self.start_path, {}).status_code, 403)
        self.assertEqual(self.post('/api/v1/academy/orientation/', {'version': 'stale', 'accept': True}).status_code, 400)
        self.assertTrue(self.acknowledge().json()['acknowledged'])
        self.assertEqual(self.post(self.start_path, {}).status_code, 403)
        self.assertEqual(self.post(self.setup_path, {'revision': 1, 'checked': []}).status_code, 400)
        self.assertTrue(self.complete_setup().json()['completed'])
        self.assertFalse(LessonIteration.objects.exists())
        self.assertEqual(self.post(self.start_path, {}).status_code, 201)
        attempt = LessonIteration.objects.get()
        self.assertEqual(attempt.due_at - attempt.started_at, timedelta(days=14))
        with override_settings(SAIRE_ORIENTATION_VERSION='new-rules'):
            self.assertFalse(self.client.get('/api/v1/academy/orientation/').json()['acknowledged'])
            self.assertEqual(self.post(self.start_path, {}).status_code, 200)
        self.assertEqual(LessonIteration.objects.count(), 1)

    def test_setup_revision_requires_fresh_confirmation(self):
        self.acknowledge()
        self.complete_setup()
        guide = ModuleGuide.objects.get(module=self.lesson.module)
        guide.revision += 1
        guide.save(update_fields=['revision'])
        self.assertEqual(self.post(self.start_path, {}).status_code, 403)
        self.assertFalse(self.client.get(self.setup_path).json()['completed'])
        self.assertTrue(self.complete_setup().json()['completed'])
        self.assertEqual(self.post(self.start_path, {}).status_code, 201)

    def test_checks_are_private_untimed_and_supply_revision_evidence(self):
        before = '/api/v1/academy/lessons/p1-l1/check/before/'
        after = '/api/v1/academy/lessons/p1-l1/check/after/'
        self.assertEqual(self.client.get(after).status_code, 403)
        questions = self.client.get(before).json()['questions']
        self.assertTrue(questions)
        self.assertTrue(all('correct' not in question for question in questions))
        payload = {'question_ids': [q['id'] for q in questions], 'answers': [0] * len(questions)}
        self.assertEqual(self.post(before, payload).json()['results']['before']['correct'], 0)
        self.assertFalse(LessonIteration.objects.exists())
        self.acknowledge()
        self.complete_setup()
        self.post(self.start_path, {})
        self.assertEqual(self.post(before, payload).status_code, 403)
        self.assertEqual(self.post(after, payload).json()['results']['after']['correct'], 0)
        self.assertEqual(LessonIteration.objects.get().status, 'active')
        tools = self.client.get('/api/v1/academy/study-tools/').json()
        self.assertIn('0/2', tools['revision'][0]['reason'])
        self.assertEqual(tools['achievements'][0]['title'], 'First program')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(before).json()['results'], {})
        self.assertFalse(self.client.get('/api/v1/academy/study-tools/').json()['achievements'])

    def test_notebook_only_allows_owner_to_read_edit_and_delete(self):
        path = '/api/v1/academy/notes/'
        note = self.post(path, {'action': 'save', 'title': 'Loop error', 'mistake': 'Wrong endpoint'}).json()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(path).json(), [])
        self.assertEqual(self.post(path, {'action': 'delete', 'id': note['id']}).status_code, 404)
        self.client.force_login(self.learner)
        changed = self.post(path, {'action': 'save', 'id': note['id'], 'title': 'Loop error',
                                   'mistake': 'Wrong endpoint', 'correction': 'Check range'}).json()
        self.assertEqual(changed['correction'], 'Check range')
        self.assertTrue(self.post(path, {'action': 'delete', 'id': note['id']}).json()['deleted'])

    def test_cli_start_uses_gates_and_review_records_supply_milestones(self):
        module = self.lesson.module
        now = timezone.now()
        for lesson in module.lessons.all():
            LessonIteration.objects.create(
                learner=self.learner, lesson=lesson, status='passed',
                started_at=now - timedelta(days=5), due_at=now + timedelta(days=9),
                completed_at=now - timedelta(days=4),
            )
        assignment = Assignment.objects.create(
            module=module, slug='test-cli', title='Test challenge', published=True,
            q1='One', q2='Two', q3='Three', q4='Four', q5='Five',
        )
        token = Token.objects.create(user=self.learner)
        path = '/api/v1/assignments/test-cli/start/'
        headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}
        self.assertEqual(self.client.post(path, **headers).status_code, 403)
        self.acknowledge()
        self.assertEqual(self.client.post(path, **headers).status_code, 403)
        self.complete_setup()
        self.assertEqual(self.client.post(path, **headers).status_code, 201)
        submission = Submission.objects.create(
            attempt=AssignmentAttempt.objects.get(assignment=assignment),
            repository_url='https://github.com/test/project', commit_sha='a' * 40,
        )
        instructor = get_user_model().objects.create_superuser('reviewer')
        CodeReview.objects.create(
            submission=submission, reviewer=instructor,
            verified_test_score=80, code_quality_score=80,
            q1_score=8, q2_score=8, q3_score=8, q4_score=8, q5_score=8,
        )
        evidence = self.client.get('/api/v1/academy/study-tools/').json()
        self.assertTrue(any('at least three days ago' in row['reason'] for row in evidence['revision']))
        self.assertIn('First reviewed challenge', [badge['title'] for badge in evidence['achievements']])

    def test_seed_preserves_authored_content_and_exposes_setup_templates(self):
        from django.apps import apps
        from courses.foundations_v104 import add_foundation_guides
        entry = GlossaryEntry.objects.get(term='Program')
        entry.definition = 'Instructor definition'
        entry.save(update_fields=['definition'])
        add_foundation_guides(apps, 'default')
        entry.refresh_from_db()
        self.assertEqual(entry.definition, 'Instructor definition')
        second = ModuleGuide.objects.get(module__position=2, module__course=self.lesson.module.course)
        setup = self.client.get(f'/api/v1/academy/modules/{second.module_id}/setup/').json()
        self.assertTrue(setup['outcomes'])
        self.assertTrue(setup['template'])
        self.assertFalse(setup['required'])
