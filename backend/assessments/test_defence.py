from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from courses.models import Course, Lesson, Module
from progression.models import LessonIteration

from .models import Assignment, AssignmentAttempt, CodeDefence, CodeReview, Submission


class CodeDefenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.learner = users.create_user('defence-learner')
        cls.other = users.create_user('other-learner')
        cls.instructor = users.create_superuser('defence-instructor')
        course = Course.objects.create(title='Engineering', slug='defence-course', status='published')
        module = Module.objects.create(course=course, name='First module', position=1)
        lesson = Lesson.objects.create(module=module, title='Foundation', published=True)
        now = timezone.now()
        for learner in (cls.learner, cls.other):
            LessonIteration.objects.create(
                learner=learner, lesson=lesson, status='passed', started_at=now, due_at=now,
            )
        cls.assignment = Assignment.objects.create(
            module=module, slug='build', title='Build a tool', brief='Build it',
            published=True, learning_outcomes='Explain decisions and tests',
            q1='Decision?', q2='Test?', q3='Trade-off?', q4='Inputs?', q5='Next change?',
        )
        attempt = AssignmentAttempt.objects.create(learner=cls.learner, assignment=cls.assignment, due_at=now)
        cls.submission = Submission.objects.create(
            attempt=attempt, repository_url='https://github.com/learner/tool', commit_sha='a' * 40,
            submitted_at=now,
        )
        cls.path = f'/api/v1/assignments/build/submissions/{cls.submission.pk}/defence/'

    def setUp(self):
        cache.clear()
        self.client.force_login(self.learner)

    def save(self, action, revision, answers, questions=None):
        return self.client.post(self.path, {
            'action': action, 'revision': revision, 'answers': answers,
            'questions': self.assignment.questions if questions is None else questions,
        }, content_type='application/json')

    def test_private_commit_bound_draft_and_hand_in(self):
        record = self.client.get(self.path).json()
        self.assertEqual(record['commit_sha'], self.submission.commit_sha)
        self.assertEqual(record['revision'], 0)
        draft = ['A choice I made', '', '', '', '']
        self.assertEqual(self.save('save', 0, draft).json()['revision'], 1)
        self.assertEqual(self.client.get(self.path).json()['answers'], draft)
        self.assertEqual(self.save('submit', 1, draft).status_code, 400)
        self.assertEqual(self.save('save', 0, ['New'] * 5).status_code, 409)

        # Instructor question edits must not re-label the original draft answers.
        original_questions = self.assignment.questions
        self.assignment.q1 = 'New rubric question?'
        self.assignment.save()
        self.assertEqual(self.client.get(self.path).json()['questions'], original_questions)
        self.assertEqual(self.save('save', 1, ['New'] * 5).status_code, 409)

        final = ['Explanation of the chosen implementation.'] * 5
        response = self.save('submit', 1, final, original_questions)
        self.assertEqual(response.status_code, 200)
        handed_in = response.json()
        self.assertEqual(handed_in['status'], 'submitted')
        self.assertFalse(handed_in['editable'])
        self.assertEqual(self.save('submit', 1, final, original_questions).json(), handed_in)
        self.assertEqual(self.save('save', 2, ['Overwrite'] * 5, original_questions).status_code, 409)
        self.assertFalse(CodeReview.objects.exists())
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, Submission.REVIEW_PENDING)

    def test_ownership_and_module_gate(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.path).status_code, 404)
        self.assertEqual(self.save('save', 0, [''] * 5).status_code, 404)
        self.assertEqual(self.client.post(self.path + 'practice/', {'mode': 'question'},
                                          content_type='application/json').status_code, 404)
        self.client.force_login(self.learner)
        LessonIteration.objects.filter(learner=self.learner).delete()
        self.assertEqual(self.client.get(self.path).status_code, 403)

    @override_settings(STORAGES={
        **settings.STORAGES,
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    })
    def test_draft_is_hidden_from_review_and_handed_in_text_is_escaped(self):
        answers = ['<script>unsafe</script>'] * 5
        self.save('save', 0, answers)
        url = f'/admin/assessments/submission/{self.submission.pk}/change/'
        self.client.force_login(self.instructor)
        self.assertNotContains(self.client.get(url), 'unsafe')
        self.client.force_login(self.learner)
        self.save('submit', 1, answers)
        self.client.force_login(self.instructor)
        page = self.client.get(url)
        self.assertContains(page, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertNotContains(page, '<script>unsafe</script>')

    def test_previously_reviewed_submission_stays_compatible(self):
        review = CodeReview.objects.create(
            submission=self.submission, reviewer=self.instructor, verified_test_score=100,
            code_quality_score=100, q1_score=10, q2_score=10, q3_score=10, q4_score=10, q5_score=10,
        )
        self.assertEqual(review.final_score, 100)
        self.assertEqual(self.client.get(self.path).json()['status'], 'reviewed')
        self.assertEqual(self.save('submit', 0, ['Answer'] * 5).status_code, 409)

    @patch('assessments.defence_api.configured_provider', return_value='gemini')
    @patch('assessments.defence_api.make_defence_practice')
    def test_practice_requires_consent_and_does_not_create_grading_records(self, coach, provider):
        payload = {'mode': 'feedback', 'question': 'What decision did you make?', 'answer': 'I chose named functions.'}
        url = self.path + 'practice/'
        self.assertEqual(self.client.post(url, payload, content_type='application/json').status_code, 400)
        coach.assert_not_called()
        coach.return_value = {'observation': 'You stated a choice.', 'evidence_gap': 'Name a test.', 'next_step': 'Describe an edge case.'}
        payload['share_practice_answer'] = True
        response = self.client.post(url, payload, content_type='application/json')
        self.assertEqual(response.json(), coach.return_value)
        coach.assert_called_once_with(self.assignment, 'feedback', question=payload['question'], answer=payload['answer'])
        self.assertFalse(CodeDefence.objects.exists())
        self.assertFalse(CodeReview.objects.exists())

    @patch('mentoring.provider.configured_provider', return_value='gemini')
    @patch('mentoring.provider._gemini_reply', return_value='{"question":"Which test explains your design?","score":100}')
    def test_provider_receives_allowlisted_context_and_only_returns_practice_fields(self, send, provider):
        from mentoring.provider import make_defence_practice
        output = make_defence_practice(self.assignment, 'question')
        self.assertEqual(output, {'question': 'Which test explains your design?'})
        prompt = send.call_args.args[0][0]['text']
        self.assertIn('Explain decisions and tests', prompt)
        self.assertNotIn(self.submission.repository_url, prompt)
        self.assertNotIn(self.submission.commit_sha, prompt)
        self.assertNotIn(self.learner.username, prompt)
