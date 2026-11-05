"""Django integration tests: auth, evidence provenance, privacy and updates."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from assessments.models import Assignment, AssignmentAttempt, CodeReview, GradingJob, Submission
from courses.models import Course, Module
from .models import AssignmentSkill, Skill
from .api import build_profile


class LearningTwinApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.learner = user.objects.create_user('twinlearner', password='SafeTestPassword123!')
        cls.other = user.objects.create_user('twinother', password='SafeTestPassword123!')
        cls.staff = user.objects.create_user('twinreviewer', password='SafeTestPassword123!', is_staff=True)
        cls.token = Token.objects.create(user=cls.learner)
        cls.other_token = Token.objects.create(user=cls.other)
        course = Course.objects.create(slug='skill-course', title='Skills pilot', status='published')
        module = Module.objects.create(course=course, name='Python', position=1, published=True)
        cls.assignment = Assignment.objects.create(module=module, slug='skills-quotation',
            title='SAIRE Quotation Engine', brief='Original challenge',
            learning_outcomes='Testing\nDecomposition', published=True,
            q1='Why?', q2='How?', q3='When?', q4='Where?', q5='What?')
        cls.skill = Skill.objects.create(slug='python-fundamentals', name='Python fundamentals', position=1)
        cls.skill2 = Skill.objects.create(slug='code-explanation', name='Code explanation', position=2)
        cls.skill3 = Skill.objects.create(slug='debugging', name='Debugging', position=3)
        AssignmentSkill.objects.create(assignment=cls.assignment, skill=cls.skill, dimension='tests', weight=2)
        AssignmentSkill.objects.create(assignment=cls.assignment, skill=cls.skill2, dimension='defence', weight=1)

    def auth(self, other=False):
        return {'HTTP_AUTHORIZATION': f'Token {(self.other_token if other else self.token).key}'}

    def make_review(self, user=None, sha='a'*40, tests=80, answers=7, quality=90, when=None):
        user = user or self.learner
        attempt, _ = AssignmentAttempt.objects.get_or_create(
            learner=user, assignment=self.assignment,
            defaults={'due_at': timezone.now()+timedelta(days=7)})
        submission = Submission.objects.create(attempt=attempt, repository_url='https://github.com/demo/project',
            commit_sha=sha, local_tests_passed=10000)
        review = CodeReview.objects.create(submission=submission, reviewer=self.staff,
            verified_test_score=tests, code_quality_score=quality,
            q1_score=answers, q2_score=answers, q3_score=answers, q4_score=answers, q5_score=answers)
        if when:
            CodeReview.objects.filter(pk=review.pk).update(reviewed_at=when)
        return review

    def test_only_authenticated_learner_can_see_profile(self):
        self.assertEqual(self.client.get('/api/v1/learning-twin/me/').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/learning-twin/me/', **self.auth()).status_code, 200)

    def test_unassessed_not_zero_and_local_tests_do_not_count(self):
        attempt = AssignmentAttempt.objects.create(learner=self.learner, assignment=self.assignment,
            due_at=timezone.now()+timedelta(days=7))
        Submission.objects.create(attempt=attempt, repository_url='https://github.com/demo/project',
            commit_sha='f'*40, local_tests_passed=10000)
        result = self.client.get('/api/v1/learning-twin/me/', **self.auth()).json()
        self.assertEqual(result['overview']['skills_assessed'], 0)
        self.assertTrue(all(s['score'] is None for s in result['skills']))
        self.assertIn('not intelligence', result['methodology'])

    def test_review_creates_readable_evidence_without_exposing_other_learner(self):
        self.make_review(tests=84, answers=8)
        self.make_review(user=self.other, sha='b'*40, tests=12, answers=1)
        data = self.client.get('/api/v1/learning-twin/me/', **self.auth()).json()
        self.assertEqual(data['overview']['reviewed_projects'], 1)
        self.assertEqual(data['overview']['skills_assessed'], 2)
        python = next(s for s in data['skills'] if s['slug'] == 'python-fundamentals')
        self.assertEqual(python['score'], 84)
        self.assertEqual(python['evidence'][0]['source'], 'instructor_review')
        self.assertEqual(python['evidence'][0]['commit'], 'a'*12)
        explanation = next(s for s in data['skills'] if s['slug'] == 'code-explanation')
        self.assertEqual(explanation['score'], 80)
        self.assertEqual(next(s for s in data['skills'] if s['slug'] == 'debugging')['status'], 'not_assessed')
        other_profile = self.client.get('/api/v1/learning-twin/me/', **self.auth(other=True)).json()
        self.assertEqual(next(s for s in other_profile['skills'] if s['slug']=='python-fundamentals')['score'], 12)
        self.assertNotIn('b'*12, str(data))

    def test_independent_grader_overrides_manual_test_score(self):
        review = self.make_review(tests=25)
        GradingJob.objects.create(submission=review.submission,
            status=GradingJob.COMPLETE, github_commit_verified=True, verified_test_score=91)
        data = build_profile(self.learner)
        python = next(s for s in data['skills'] if s['slug'] == 'python-fundamentals')
        self.assertEqual(python['score'], 91)
        self.assertEqual(python['evidence'][0]['source'], 'independent_grader')

    def test_multiple_reviews_same_assignment_not_counted_as_multiple_projects(self):
        self.make_review(tests=20, sha='a'*40, when=timezone.now()-timedelta(days=3))
        self.make_review(tests=90, sha='b'*40, when=timezone.now())
        data = build_profile(self.learner)
        skill = next(s for s in data['skills'] if s['slug'] == 'python-fundamentals')
        self.assertEqual(skill['score'], 90)
        self.assertEqual(skill['projects_count'], 1)
        self.assertEqual(skill['evidence_count'], 1)

    def test_staff_mapping_update_changes_profile_without_reseed(self):
        review = self.make_review(tests=72, answers=9, quality=75)
        skill = next(s for s in build_profile(self.learner)['skills'] if s['slug']=='debugging')
        self.assertIsNone(skill['score'])
        AssignmentSkill.objects.create(assignment=self.assignment, skill=self.skill3, dimension='quality', weight=1)
        updated = next(s for s in build_profile(self.learner)['skills'] if s['slug']=='debugging')
        self.assertEqual(updated['score'], 75)
        self.assertEqual(updated['evidence'][0]['metric'], 'Instructor code quality')

    def test_cannot_post_skill_scores_to_read_only_endpoint(self):
        response = self.client.post('/api/v1/learning-twin/me/', {'score': 100},
                                    content_type='application/json', **self.auth())
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get('/api/v1/learning-twin/me/', **self.auth()).json()['overview']['skills_assessed'], 0)
