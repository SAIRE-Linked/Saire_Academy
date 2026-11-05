"""Provider contract tests; no paid calls, Django installation or real keys needed.
Run from backend/: python -m unittest mentoring.test_provider -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace, ModuleType
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from mentoring.provider import (
    MentorProviderError, build_learning_context, configured_provider,
    extract_text, make_socratic_reply, twin_context_enabled,
)


class ProviderContractTests(unittest.TestCase):
    def setUp(self):
        self.assignment = SimpleNamespace(
            title='Quotation Engine', learning_outcomes='Functions\nValidation',
            hidden_tests='INSTRUCTOR-PRIVATE-TEST', q1='INSTRUCTOR-REVIEW-ANSWER',
            test_command='INSTRUCTOR-GRADER-COMMAND',
        )

    def test_provider_selection_requires_matching_key(self):
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': '', 'OPENAI_API_KEY': 'fake'}):
            self.assertIsNone(configured_provider())
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'demo'}):
            self.assertEqual(configured_provider(), 'gemini')
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'openai', 'OPENAI_API_KEY': 'demo'}):
            self.assertEqual(configured_provider(), 'openai')
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'invalid', 'OPENAI_API_KEY': 'demo'}):
            self.assertIsNone(configured_provider())

    def test_twin_context_is_opt_in_by_default(self):
        with patch.dict(os.environ, {'SAIRE_MENTOR_ENABLE_TWIN_CONTEXT': '0'}):
            self.assertFalse(twin_context_enabled())
        with patch.dict(os.environ, {'SAIRE_MENTOR_ENABLE_TWIN_CONTEXT': '1'}):
            self.assertTrue(twin_context_enabled())

    def test_skill_summary_excludes_identity_grades_and_review_notes(self):
        profile = {
            'username': 'LEARNER-PRIVATE-NAME',
            'skills': [
                {'name': 'Debugging', 'score': 47, 'evidence': [{'commit': 'SECRET-COMMIT', 'feedback': 'SECRET-FEEDBACK'}]},
                {'name': 'Python fundamentals', 'score': 92},
                {'name': 'Unknown skill', 'score': None},
            ],
        }
        summary = build_learning_context(profile)
        self.assertIn('Debugging', summary)
        self.assertIn('Python fundamentals', summary)
        for marker in ['LEARNER-PRIVATE-NAME', 'SECRET-COMMIT', 'SECRET-FEEDBACK', '47', '92', 'Unknown skill']:
            self.assertNotIn(marker, summary)

    def test_gemini_sdk_receives_only_public_context_and_selected_skills(self):
        parts, calls = [], []

        def from_text(*, text):
            parts.append(text)
            return {'text': text}
        def content(*, role, parts):
            calls.append(role)
            return {'role': role, 'parts': parts}

        fake_types = SimpleNamespace(
            Part=SimpleNamespace(from_text=from_text), Content=content,
            GenerateContentConfig=lambda **kwargs: kwargs,
            HttpOptions=lambda **kwargs: kwargs,
        )
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value.text = 'Which input caused the failure?'
        fake_genai = ModuleType('google.genai')
        fake_genai.Client = MagicMock(return_value=client)
        fake_genai.types = fake_types
        fake_google = ModuleType('google')
        fake_google.genai = fake_genai
        with patch.dict(sys.modules, {'google': fake_google, 'google.genai': fake_genai, 'google.genai.types': fake_types}), \
             patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'demo-key', 'SAIRE_GEMINI_MODEL': 'gemini-flash-latest'}):
            answer = make_socratic_reply(self.assignment, [], 'How do I debug?', learning_context='Practice area: Debugging')
        self.assertEqual(answer, 'Which input caused the failure?')
        self.assertEqual(calls, ['user', 'user'])
        full_text = '\n'.join(parts)
        self.assertIn('Practice area: Debugging', full_text)
        self.assertNotIn('INSTRUCTOR-PRIVATE-TEST', full_text)
        self.assertNotIn('INSTRUCTOR-REVIEW-ANSWER', full_text)
        self.assertNotIn('INSTRUCTOR-GRADER-COMMAND', full_text)
        kwargs = client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs['model'], 'gemini-flash-latest')
        self.assertEqual(kwargs['config']['max_output_tokens'], 450)
        self.assertEqual(fake_genai.Client.call_args.kwargs['api_key'], 'demo-key')

    def test_gemini_failure_does_not_expose_provider_errors(self):
        fake_genai = ModuleType('google.genai')
        fake_genai.Client = MagicMock(side_effect=RuntimeError('SECRET-UPSTREAM-ERROR'))
        fake_types = SimpleNamespace(Content=MagicMock(), Part=SimpleNamespace(from_text=MagicMock()), GenerateContentConfig=MagicMock(), HttpOptions=MagicMock())
        fake_genai.types = fake_types
        fake_google = ModuleType('google'); fake_google.genai = fake_genai
        with patch.dict(sys.modules, {'google': fake_google, 'google.genai': fake_genai, 'google.genai.types': fake_types}), \
             patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'demo'}):
            with self.assertRaises(MentorProviderError) as err:
                make_socratic_reply(self.assignment, [], 'hello')
            self.assertNotIn('SECRET-UPSTREAM-ERROR', str(err.exception))

    def test_openai_still_supported_and_keeps_store_disabled(self):
        result = {'output':[{'type':'message', 'role':'assistant', 'content':[{'type':'output_text','text':'What do you expect?'}]}]}
        response = MagicMock(); response.read.return_value = json.dumps(result).encode()
        cm = MagicMock();cm.__enter__.return_value = response
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER':'openai','OPENAI_API_KEY':'demo', 'SAIRE_OPENAI_MODEL':'test-model'}), \
             patch('mentoring.provider.request.urlopen', return_value=cm) as call:
            answer = make_socratic_reply(self.assignment, [], 'How do I begin?')
        self.assertEqual(answer, 'What do you expect?')
        payload = json.loads(call.call_args.args[0].data)
        self.assertFalse(payload['store'])
        self.assertEqual(payload['model'], 'test-model')
        self.assertEqual(call.call_args.args[0].full_url, 'https://api.openai.com/v1/responses')
        self.assertNotIn('INSTRUCTOR-PRIVATE-TEST', json.dumps(payload))

    def test_openai_exception_is_sanitised(self):
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER':'openai', 'OPENAI_API_KEY':'demo'}), \
             patch('mentoring.provider.request.urlopen', side_effect=URLError('SECRET-UPSTREAM-ERROR')):
            with self.assertRaises(MentorProviderError) as err:
                make_socratic_reply(self.assignment, [], 'Hello')
            self.assertNotIn('SECRET-UPSTREAM-ERROR', str(err.exception))

    def test_unconfigured_provider_rejects_requests(self):
        with patch.dict(os.environ, {'SAIRE_MENTOR_PROVIDER':'gemini','GEMINI_API_KEY':''}):
            with self.assertRaises(MentorProviderError):
                make_socratic_reply(self.assignment, [], 'Hello')

    def test_missing_openai_output_is_rejected(self):
        with self.assertRaises(MentorProviderError):
            extract_text({'output': []})


if __name__ == '__main__':
    unittest.main()
