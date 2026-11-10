"""Regression: locked IT lessons must not be presented as missing content."""
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from assessments.models import Assignment, AssignmentAttempt, Submission, CodeReview
from progression.models import LessonIteration
from .models import Course, Module, Lesson, ModulePrerequisite, LearningPathway, PathwayUnit


class ClassroomEntryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.learner = U.objects.create_user('classroom-learner')
        cls.other = U.objects.create_user('classroom-other')
        cls.admin = U.objects.create_superuser('classroom-admin', 'admin@example.test', 'TestPassword123!')
        cls.foundation_course = Course.objects.create(slug='shared-foundation', title='Shared foundation', status='published')
        cls.foundation = Module.objects.create(course=cls.foundation_course, position=1, name='Python foundation')
        cls.first = Lesson.objects.create(module=cls.foundation, position=1, title='First Python lesson', public_id='shared-one', published=True)
        cls.second = Lesson.objects.create(module=cls.foundation, position=2, title='Next Python lesson', public_id='shared-two', published=True)
        cls.final = Assignment.objects.create(module=cls.foundation, slug='foundation-final', title='Foundation final', brief='Original test brief',
            published=True, module_pass_score=70, learning_outcomes='Tests', q1='a', q2='b', q3='c', q4='d', q5='e')
        cls.it = Course.objects.create(slug='it-course', title='IT course', status='published')
        cls.it_module = Module.objects.create(course=cls.it, position=1, name='IT intake')
        cls.it_lesson = Lesson.objects.create(module=cls.it_module, position=1, title='IT lesson', public_id='it-one', published=True)
        ModulePrerequisite.objects.create(module=cls.it_module, required_module=cls.foundation)
        cls.workflow = Module.objects.create(course=cls.it, position=2, name='Workflow')
        Lesson.objects.create(module=cls.workflow, public_id='workflow-one', title='Workflow lesson', published=True)
        cls.year2 = Course.objects.create(slug='it-year-two', title='IT Year 2', status='published')
        cls.database = Module.objects.create(course=cls.year2, name='Database sample')
        Lesson.objects.create(module=cls.database, public_id='db-one', title='Database lesson', published=True)
        ModulePrerequisite.objects.create(module=cls.database, required_module=cls.workflow)

    def setUp(self):
        self.client.force_login(self.learner)

    def payload(self, course=None):
        response = self.client.get(f'/api/v1/courses/{(course or self.it).slug}/')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def pass_lesson(self, lesson, learner=None):
        now = timezone.now()
        return LessonIteration.objects.create(learner=learner or self.learner, lesson=lesson,
            status='passed', raw_score=100, credited_score=100, started_at=now, due_at=now+timedelta(days=14))

    def finish_lessons(self):
        self.pass_lesson(self.first); self.pass_lesson(self.second)

    def submission(self):
        attempt = AssignmentAttempt.objects.create(learner=self.learner, assignment=self.final, due_at=timezone.now()+timedelta(days=14))
        return Submission.objects.create(attempt=attempt, repository_url='https://github.com/student/example', commit_sha='a'*40)

    def test_new_learner_sees_real_content_and_exact_foundation_link_without_timer(self):
        data = self.payload()
        self.assertEqual(len(data['lessons']), 2)
        self.assertTrue(all(lesson['locked'] for lesson in data['lessons']))
        entry = data['classroom_entry']
        self.assertEqual(entry['kind'], 'prerequisite')
        self.assertEqual(entry['requirements'][0]['title'], 'Python foundation')
        query = parse_qs(urlsplit(entry['action']['href']).query)
        self.assertEqual(query, {'course':['shared-foundation'], 'view':['classroom'], 'lesson':['shared-one']})
        self.assertEqual(LessonIteration.objects.count(), 0)
        self.assertEqual(AssignmentAttempt.objects.count(), 0)
        self.assertEqual(self.client.post('/api/v1/lessons/it-one/start/').status_code, 403)

    def test_year_two_resolves_the_whole_chain_to_first_available_lesson(self):
        entry = self.payload(self.year2)['classroom_entry']
        self.assertEqual(entry['kind'], 'prerequisite')
        self.assertEqual([r['title'] for r in entry['requirements']], ['Python foundation', 'IT intake', 'Workflow'])
        self.assertIn('lesson=shared-one', entry['action']['href'])

    def test_partial_progress_links_to_next_lesson_not_completed_first(self):
        self.pass_lesson(self.first)
        entry = self.payload()['classroom_entry']
        self.assertIn('lesson=shared-two', entry['action']['href'])

    def test_shared_foundation_is_identified_without_requiring_whole_ai_course(self):
        pathway=LearningPathway.objects.create(slug='shared-it', title='IT', description='Original pathway', published=True)
        PathwayUnit.objects.create(pathway=pathway, module=self.foundation, position=1, scope='Shared', shared=True)
        entry=self.payload()['classroom_entry']
        self.assertIn('shared module counts toward both pathways', entry['message'])
        self.assertIn('do not need to finish the entire course', entry['message'])

    def test_other_learners_pass_does_not_hide_own_active_lesson(self):
        self.pass_lesson(self.first, self.other)
        now=timezone.now()
        LessonIteration.objects.create(learner=self.learner, lesson=self.first, status='active', started_at=now, due_at=now+timedelta(days=14))
        self.assertIn('lesson=shared-one', self.payload()['classroom_entry']['action']['href'])

    def test_completed_quizzes_point_to_required_final_project(self):
        self.finish_lessons()
        entry = self.payload()['classroom_entry']
        self.assertEqual(entry['kind'], 'project')
        self.assertEqual(entry['action']['href'], '/assignments/?assignment=foundation-final')
        self.assertTrue(all(l['locked'] for l in self.payload()['lessons']))

    def test_pending_review_is_not_a_missing_lesson_or_a_pass(self):
        self.finish_lessons(); self.submission()
        entry = self.payload()['classroom_entry']
        self.assertEqual(entry['kind'], 'review')
        self.assertEqual(entry['action']['label'], 'View submitted project')
        self.assertEqual(self.client.post('/api/v1/lessons/it-one/start/').status_code, 403)

    def test_verified_pass_restores_normal_it_classroom(self):
        self.finish_lessons(); submission=self.submission()
        CodeReview.objects.create(submission=submission, reviewer=self.admin, verified_test_score=100,
            code_quality_score=100, q1_score=10, q2_score=10, q3_score=10, q4_score=10, q5_score=10)
        data=self.payload()
        self.assertEqual(data['classroom_entry']['kind'], 'available')
        self.assertFalse(data['lessons'][0]['locked'])

    def test_review_below_threshold_still_points_to_required_project(self):
        self.finish_lessons(); submission=self.submission()
        CodeReview.objects.create(submission=submission, reviewer=self.admin, verified_test_score=0,
            code_quality_score=0, q1_score=0, q2_score=0, q3_score=0, q4_score=0, q5_score=0)
        data=self.payload()
        self.assertEqual(data['classroom_entry']['kind'], 'project')
        self.assertTrue(all(l['locked'] for l in data['lessons']))

    def test_admin_preview_remains_available(self):
        self.client.force_login(self.admin)
        data=self.payload()
        self.assertEqual(data['classroom_entry']['kind'], 'available')
        self.assertTrue(all(not l['locked'] for l in data['lessons']))

    def test_truly_empty_course_is_distinct(self):
        empty=Course.objects.create(slug='outline-only', title='Outline', status='published')
        Module.objects.create(course=empty, name='Future module')
        entry=self.payload(empty)['classroom_entry']
        self.assertEqual(entry['kind'], 'empty')
        self.assertIsNone(entry['action'])

    def test_unpublished_requirement_has_no_title_or_content_leak(self):
        self.foundation_course.status='draft'; self.foundation_course.save()
        data=self.payload()
        self.assertEqual(data['classroom_entry']['kind'], 'configuration')
        self.assertEqual(data['classroom_entry']['requirements'], [])
        self.assertNotIn('Python foundation', str(data['classroom_entry']))
        self.assertIsNone(data['classroom_entry']['action'])

    def test_anonymous_request_does_not_receive_personal_entry(self):
        self.client.logout()
        entry=self.payload()['classroom_entry']
        self.assertEqual(entry['kind'], 'sign_in')
        self.assertEqual(entry['action']['href'], '/')

    def test_imported_cycle_fails_closed_without_navigation_loop(self):
        ModulePrerequisite.objects.bulk_create([ModulePrerequisite(module=self.foundation, required_module=self.database)])
        entry=self.payload()['classroom_entry']
        self.assertEqual(entry['kind'], 'configuration')
        self.assertIsNone(entry['action'])
