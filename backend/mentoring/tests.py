"""Django tests: access boundaries, per-user history and provider failure safety."""
import os
from unittest.mock import patch
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from courses.models import Course, Module
from assessments.models import Assignment, AssignmentAttempt
from .models import MentorMessage


class MentorApiTests(TestCase):

    # v10: these regression tests exercise already-unlocked assignment workflows.
    # Locked modules and learners are tested independently in progression/tests.py.
    def grant_lesson_prerequisites(self):
        from progression.models import LessonIteration
        from courses.models import Lesson, Module
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        for module in Module.objects.all():
            lesson = Lesson.objects.create(module=module, title='Completed prerequisite', published=True)
            for user in get_user_model().objects.all():
                LessonIteration.objects.create(learner=user, lesson=lesson, started_at=timezone.now(),
                    due_at=timezone.now()+timedelta(days=14), status='passed', raw_score=100, credited_score=100)

    @classmethod
    def setUpTestData(cls):
        cls.learner = get_user_model().objects.create_user('mentorstudent', password='TestSecure2026!')
        cls.other = get_user_model().objects.create_user('othermentorstudent', password='TestSecure2026!')
        cls.t1 = Token.objects.create(user=cls.learner)
        cls.t2 = Token.objects.create(user=cls.other)
        cls.course = Course.objects.create(slug='mentor-course', title='Mentor Course', status='published')
        cls.module = Module.objects.create(course=cls.course, name='Programming', position=1, published=True)
        cls.assignment = Assignment.objects.create(module=cls.module, slug='mentor-project', title='Quotation Engine',
            brief='Implement basic calculations', learning_outcomes='Python\nUnit tests', published=True,
            q1='Why?', q2='How?', q3='When?', q4='Where?', q5='What?')
        cls.url = '/api/v1/assignments/mentor-project/mentor/'

    def setUp(self):
        self.grant_lesson_prerequisites()
        # Throttling counts requests across test methods in local-memory cache.
        cache.clear()

    def header(self, token=None):
        return {'HTTP_AUTHORIZATION': f'Token {(token or self.t1).key}'}

    def start(self, user=None):
        return AssignmentAttempt.objects.get_or_create(learner=user or self.learner,
            assignment=self.assignment, defaults={'due_at': timezone.now() + timedelta(days=7)})

    def test_unauthenticated_cannot_read_history(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_cannot_chat_before_starting(self):
        self.assertEqual(self.client.get(self.url, **self.header()).status_code, 403)
        self.assertEqual(self.client.post(self.url, data={'message':'Hi'}, content_type='application/json', **self.header()).status_code, 403)

    def test_history_is_private_between_students(self):
        self.start()
        self.start(self.other)
        MentorMessage.objects.create(learner=self.learner, assignment=self.assignment, role='learner', content='My private question')
        r=self.client.get(self.url, **self.header(self.t2))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['messages'], [])

    def test_blank_or_oversized_message_rejected(self):
        self.start()
        for value in ['', 'a'*1201]:
            r=self.client.post(self.url, data={'message':value}, content_type='application/json', **self.header())
            self.assertEqual(r.status_code, 400)

    def test_unconfigured_ai_does_not_store_message(self):
        self.start()
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': ''}):
            r=self.client.post(self.url, data={'message':'Hello'}, content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 503)
        self.assertEqual(MentorMessage.objects.count(), 0)

    def test_mentor_message_saved_only_for_current_learner(self):
        self.start()
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only'}), \
             patch('mentoring.api.make_socratic_reply', return_value='What input do you expect?'):
            r=self.client.post(self.url, data={'message':'How do I begin?'}, content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 201)
        self.assertEqual([m.role for m in MentorMessage.objects.all()], ['learner','mentor'])
        self.assertEqual(r.json()['mentor_message']['text'], 'What input do you expect?')

    def test_provider_failure_does_not_store_question(self):
        from mentoring.provider import MentorProviderError
        self.start()
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only'}), \
             patch('mentoring.api.make_socratic_reply', side_effect=MentorProviderError('unavailable')):
            r=self.client.post(self.url, data={'message':'Hello'}, content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 503)
        self.assertEqual(MentorMessage.objects.count(), 0)

    def test_clear_only_own_history(self):
        self.start()
        self.start(self.other)
        MentorMessage.objects.create(learner=self.learner, assignment=self.assignment, role='learner', content='Delete me')
        MentorMessage.objects.create(learner=self.other, assignment=self.assignment, role='learner', content='Keep me')
        self.assertEqual(self.client.delete(self.url, **self.header()).status_code, 200)
        self.assertEqual(MentorMessage.objects.count(), 1)
        self.assertEqual(MentorMessage.objects.first().content, 'Keep me')

    def test_personalization_requires_server_flag_and_explicit_consent(self):
        self.start()
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only',
                                     'SAIRE_MENTOR_ENABLE_TWIN_CONTEXT': '0'}):
            r=self.client.post(self.url, data={'message':'Help', 'use_learning_twin': True},
                               content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(MentorMessage.objects.count(), 0)

    def test_without_opt_in_never_builds_learning_profile(self):
        self.start()
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only',
                                     'SAIRE_MENTOR_ENABLE_TWIN_CONTEXT': '1'}), \
             patch('learning_twin.api.build_profile') as profile, \
             patch('mentoring.api.make_socratic_reply', return_value='Think about the inputs.') as provider:
            r=self.client.post(self.url, data={'message':'Hello'}, content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 201)
        profile.assert_not_called()
        self.assertNotIn('learning_context', provider.call_args.kwargs)

    def test_opt_in_sends_minimal_skill_context_not_profile_details(self):
        self.start()
        sensitive_profile = {'username': 'PRIVATE_NAME', 'skills': [
            {'name':'Debugging', 'score':45, 'evidence':[{'commit':'PRIVATE_SHA','feedback':'PRIVATE_REVIEW'}]}]}
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-only',
                                     'SAIRE_MENTOR_ENABLE_TWIN_CONTEXT': '1'}), \
             patch('learning_twin.api.build_profile', return_value=sensitive_profile), \
             patch('mentoring.api.make_socratic_reply', return_value='Which test fails?') as provider:
            r=self.client.post(self.url, data={'message':'Hello','use_learning_twin':True},
                               content_type='application/json', **self.header())
        self.assertEqual(r.status_code, 201)
        context=provider.call_args.kwargs['learning_context']
        self.assertIn('Debugging', context)
        for value in ('PRIVATE_NAME','PRIVATE_SHA','PRIVATE_REVIEW','45'):
            self.assertNotIn(value, context)
