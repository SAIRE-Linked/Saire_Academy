"""Django integration tests for protected grading queue and instructor score."""
import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from courses.models import Course, Module
from .models import Assignment, AssignmentAttempt, Submission, CodeReview, GradingJob
from django.utils import timezone
from datetime import timedelta

SECRET = 'a-secure-illustrative-token-with-more-than-32-characters'


class GradingQueueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user('grader_student', password='P@ssword-234567')
        cls.other = User.objects.create_user('other_student', password='P@ssword-234567')
        cls.instructor = User.objects.create_superuser('reviewer', 'reviewer@example.test', 'P@ssword-234567')
        cls.token = Token.objects.create(user=cls.student)
        cls.other_token = Token.objects.create(user=cls.other)
        course = Course.objects.create(title='Grader course', slug='grader-course', status='published')
        module = Module.objects.create(course=course, name='Python', position=1, published=True)
        cls.assignment = Assignment.objects.create(
            module=module, slug='saire-quotation-engine', title='Quotation engine',
            brief='Original exercise', learning_outcomes='Decimals', published=True,
            q1='a', q2='b', q3='c', q4='d', q5='e')

    def learner(self):
        return {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def submit(self):
        self.client.post('/api/v1/assignments/saire-quotation-engine/start/',
                         data={}, content_type='application/json', **self.learner())
        return self.client.post('/api/v1/assignments/saire-quotation-engine/submit/',
                                data={'repository_url':'https://github.com/user/repo',
                                      'commit_sha':'a'*40},content_type='application/json',**self.learner())

    def worker(self, path, body, secret=SECRET):
        return self.client.post(path, body, content_type='application/json',
                                HTTP_X_SAIRE_WORKER_TOKEN=secret)

    @patch.dict(os.environ, {'SAIRE_WORKER_SHARED_TOKEN':SECRET})
    def test_submission_awaits_approval_and_worker_cannot_claim(self):
        self.assertEqual(self.submit().status_code, 201)
        job = GradingJob.objects.get()
        self.assertEqual(job.status, GradingJob.WAITING)
        claim = self.worker('/api/v1/internal/grading/claim/', {})
        self.assertEqual(claim.status_code, 200)
        self.assertIsNone(claim.json()['job'])
        self.assertEqual(self.worker('/api/v1/internal/grading/claim/', {}, 'wrong').status_code,403)
        self.assertEqual(self.client.post('/api/v1/internal/grading/claim/',{},content_type='application/json',**self.learner()).status_code,403)
        self.assertEqual(self.client.get('/api/v1/assignments/saire-quotation-engine/mine/',**self.learner()).json()['submissions'][0]['grading']['status'], 'awaiting_approval')

    @patch.dict(os.environ, {'SAIRE_WORKER_SHARED_TOKEN':SECRET})
    def test_approved_job_claims_once_report_validates_scores_and_human_review(self):
        self.submit()
        job=GradingJob.objects.get()
        job.approved_by=self.instructor
        job.approved_at=timezone.now()
        job.status=GradingJob.QUEUED
        job.save()
        claim=self.worker('/api/v1/internal/grading/claim/',{}).json()['job']
        self.assertEqual(claim['commit_sha'], 'a'*40)
        self.assertEqual(claim['assignment_slug'],'saire-quotation-engine')
        self.assertIsNone(self.worker('/api/v1/internal/grading/claim/',{}).json()['job'])
        report_url='/api/v1/internal/grading/report/'
        report={'job_id':job.pk,'claim_token':claim['claim_token'],
                'outcome':'complete','github_commit_verified':True,
                'passed':9,'failed':2,'errors':1,'score':75,'log':'12 checks'}
        tampered={**report,'score':100}
        self.assertEqual(self.worker(report_url,tampered).status_code,400)
        self.assertEqual(self.worker(report_url,{**report,'claim_token':'00000000-0000-0000-0000-000000000000'}).status_code,400)
        self.assertEqual(self.worker(report_url,report).status_code,200)
        self.assertEqual(self.worker(report_url,report).status_code,400) # no replay
        job.refresh_from_db()
        self.assertEqual(job.verified_test_score,75)
        self.assertTrue(job.github_commit_verified)
        self.assertEqual(job.status,GradingJob.COMPLETE)
        review=CodeReview.objects.create(submission=job.submission,reviewer=self.instructor,
            verified_test_score=100, code_quality_score=80,
            q1_score=8,q2_score=8,q3_score=8,q4_score=8,q5_score=8)
        self.assertEqual(review.verified_test_score,75) # cannot inflate test marks
        self.assertEqual(str(review.final_score),'79.50') # 37.5+24+8+10

    @patch.dict(os.environ, {'SAIRE_WORKER_SHARED_TOKEN':SECRET})
    def test_failed_worker_does_not_claim_verified_score(self):
        self.submit()
        job=GradingJob.objects.get()
        job.approved_by=self.instructor;job.approved_at=timezone.now();job.status=GradingJob.QUEUED;job.save()
        claimed=self.worker('/api/v1/internal/grading/claim/',{}).json()['job']
        resp=self.worker('/api/v1/internal/grading/report/',{
            'job_id':job.pk,'claim_token':claimed['claim_token'],'outcome':'error',
            'github_commit_verified':False,'failure_reason':'GitHub access denied'})
        self.assertEqual(resp.status_code,200)
        job.refresh_from_db()
        self.assertEqual(job.status,GradingJob.ERROR)
        self.assertIsNone(job.verified_test_score)

    def test_other_learner_cannot_read_submission(self):
        self.submit()
        response=self.client.get('/api/v1/assignments/saire-quotation-engine/mine/',
                HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        self.assertEqual(response.status_code,404)
