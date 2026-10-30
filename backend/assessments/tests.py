"""API / grading contract tests. Run: python manage.py test assessments courses"""
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from courses.models import Course, Module
from .models import Assignment, AssignmentAttempt, CodeReview, Submission


class ProofLoopApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('student1', password='SafeTestPassword123!')
        cls.other = get_user_model().objects.create_user('student2', password='SafeTestPassword123!')
        cls.staff = get_user_model().objects.create_user('instructor', password='SafeTestPassword123!', is_staff=True)
        cls.course = Course.objects.create(slug='ai-engineer-agentic-systems', title='AI Eng', status='published')
        cls.module = Module.objects.create(course=cls.course, name='Python', position=1, published=True)
        cls.assignment = Assignment.objects.create(module=cls.module, slug='saire-quotation-engine', title='Quotation Engine',
            brief='Write original code', learning_outcomes='Testing\nPython', published=True, duration_days=7,
            q1='Q1?', q2='Q2?', q3='Q3?', q4='Q4?', q5='Q5?')
        cls.token = Token.objects.create(user=cls.user)
        cls.other_token = Token.objects.create(user=cls.other)
        cls.sha = 'a' * 40

    def auth(self, token=None):
        return {'HTTP_AUTHORIZATION': f'Token {(token or self.token).key}'}

    def test_only_published_visible(self):
        response = self.client.get('/api/v1/assignments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['review_questions'], ['Q1?', 'Q2?', 'Q3?', 'Q4?', 'Q5?'])
        self.assignment.published=False;self.assignment.save()
        self.assertEqual(self.client.get('/api/v1/assignments/').json(), [])
        self.assertEqual(self.client.get('/api/v1/assignments/saire-quotation-engine/').status_code, 404)

    def test_requires_authentication(self):
        self.assertEqual(self.client.post('/api/v1/assignments/saire-quotation-engine/start/').status_code, 401)
        self.assertEqual(self.client.post('/api/v1/assignments/saire-quotation-engine/submit/', {}).status_code, 401)

    def test_login_and_invalid_credentials(self):
        ok=self.client.post('/api/v1/auth/login/', {'username':'student1','password':'SafeTestPassword123!'}, content_type='application/json')
        self.assertEqual(ok.status_code,200)
        self.assertEqual(ok.json()['token'], self.token.key)
        bad=self.client.post('/api/v1/auth/login/', {'username':'student1','password':'incorrect'}, content_type='application/json')
        self.assertEqual(bad.status_code,400)

    def test_start_is_idempotent_deadline_fixed(self):
        path='/api/v1/assignments/saire-quotation-engine/start/'
        first=self.client.post(path, data={}, content_type='application/json', **self.auth())
        second=self.client.post(path, data={}, content_type='application/json', **self.auth())
        self.assertEqual(first.status_code,201)
        self.assertEqual(second.status_code,200)
        self.assertEqual(first.json()['attempt']['due_at'],second.json()['attempt']['due_at'])
        self.assertEqual(AssignmentAttempt.objects.count(),1)

    def test_student_cannot_access_another_students_attempt(self):
        self.client.post('/api/v1/assignments/saire-quotation-engine/start/', data={}, content_type='application/json', **self.auth())
        url='/api/v1/assignments/saire-quotation-engine/mine/'
        self.assertEqual(self.client.get(url, **self.auth(self.other_token)).status_code,404)
        self.assertEqual(self.client.get(url, **self.auth()).status_code,200)

    def test_unstarted_submission_rejected(self):
        r=self.client.post('/api/v1/assignments/saire-quotation-engine/submit/',data={
            'repository_url':'https://github.com/myuser/quotation','commit_sha':self.sha
        },content_type='application/json', **self.auth())
        self.assertEqual(r.status_code,404)

    def test_submit_rejects_malicious_repo_and_sha(self):
        self.client.post('/api/v1/assignments/saire-quotation-engine/start/', data={}, content_type='application/json', **self.auth())
        url='/api/v1/assignments/saire-quotation-engine/submit/'
        for bad in ['https://evil.example/repo', 'https://github.com/u/repo?x=1', 'https://github.com/u/repo/../bad', 'https://github.com@evil.example/u/r']:
            result=self.client.post(url, data={'repository_url':bad,'commit_sha':self.sha}, content_type='application/json', **self.auth())
            self.assertEqual(result.status_code,400, bad)
        invalid=self.client.post(url,data={'repository_url':'https://github.com/u/repo','commit_sha':'git-head'},content_type='application/json', **self.auth())
        self.assertEqual(invalid.status_code,400)
        self.assertEqual(Submission.objects.count(),0)

    def test_submission_idempotent_and_local_test_counts_untrusted(self):
        self.client.post('/api/v1/assignments/saire-quotation-engine/start/', data={}, content_type='application/json', **self.auth())
        url='/api/v1/assignments/saire-quotation-engine/submit/'
        data={'repository_url':'https://github.com/myuser/quotation','commit_sha':self.sha,
            'local_tests_passed':7,'local_tests_failed':0,'local_tests_errors':0}
        first=self.client.post(url,data=data,content_type='application/json',**self.auth())
        second=self.client.post(url,data=data,content_type='application/json',**self.auth())
        self.assertEqual(first.status_code,201)
        self.assertEqual(second.status_code,200)
        self.assertEqual(Submission.objects.count(),1)
        self.assertEqual(first.json()['submission']['status'],Submission.REVIEW_PENDING)
        self.assertFalse(first.json()['submission']['local_tests']['verified'])
        self.assertIsNone(first.json()['submission']['review'])

    def test_cannot_set_grade_from_learner_submission(self):
        self.client.post('/api/v1/assignments/saire-quotation-engine/start/', data={}, content_type='application/json', **self.auth())
        r=self.client.post('/api/v1/assignments/saire-quotation-engine/submit/',data={
          'repository_url':'https://github.com/myuser/quotation', 'commit_sha':self.sha,
          'status':'reviewed','verified_test_score':100,'final_score':100},
          content_type='application/json',**self.auth())
        self.assertEqual(r.status_code,201)
        self.assertEqual(Submission.objects.get().status, Submission.REVIEW_PENDING)
        self.assertFalse(CodeReview.objects.exists())

    def test_verified_review_scoring_and_deadline(self):
        a=AssignmentAttempt.objects.create(assignment=self.assignment,learner=self.user,
                                          started_at=timezone.now()-timedelta(days=1),due_at=timezone.now()+timedelta(days=6))
        s=Submission.objects.create(attempt=a,repository_url='https://github.com/user/repo',commit_sha=self.sha)
        review=CodeReview.objects.create(submission=s,reviewer=self.staff,verified_test_score=80,code_quality_score=90,
                                        q1_score=8,q2_score=8,q3_score=8,q4_score=8,q5_score=8,feedback='Good reasoning')
        self.assertEqual(review.final_score, Decimal('83.00')) # 40 + 24 + 9 + 10
        s.refresh_from_db()
        self.assertEqual(s.status,Submission.REVIEWED)
        r=self.client.get('/api/v1/assignments/saire-quotation-engine/mine/',**self.auth())
        self.assertEqual(r.json()['submissions'][0]['review']['final_score'],'83.00')

    def test_late_penalty_only_affects_deadline_component(self):
        start=timezone.now()-timedelta(days=10)
        a=AssignmentAttempt.objects.create(assignment=self.assignment,learner=self.user,started_at=start,due_at=start+timedelta(days=7))
        s=Submission.objects.create(attempt=a,repository_url='https://github.com/user/repo',commit_sha=self.sha,
                                    submitted_at=a.due_at+timedelta(days=2,hours=1))
        self.assertEqual(s.late_days,3)
        review=CodeReview.objects.create(submission=s,reviewer=self.staff,verified_test_score=100,code_quality_score=100,
                                         q1_score=10,q2_score=10,q3_score=10,q4_score=10,q5_score=10)
        self.assertEqual(review.final_score,Decimal('94.00')) # on time=100, 3 days late => deadline 40/100, -6 total.

    def test_nonstaff_cannot_create_reviews_via_api(self):
        self.assertEqual(self.client.post('/api/v1/reviews/', {},**self.auth()).status_code,404)

    def test_logout_revokes_token(self):
        r=self.client.post('/api/v1/auth/logout/', data={}, content_type='application/json', **self.auth())
        self.assertEqual(r.status_code,200)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.get('/api/v1/auth/me/', **self.auth()).status_code,401)
