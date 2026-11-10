"""Real browser session termination, independent of CLI tokens and other users."""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework.authtoken.models import Token


class BrowserLogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('logout-learner')
        cls.other = get_user_model().objects.create_user('logout-other')

    def test_browser_logout_removes_session_and_denies_private_endpoints(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/api/v1/dashboard/').status_code, 200)
        response = self.client.post('/api/v1/auth/session-logout/', {}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        for route in ('/api/v1/dashboard/', '/api/v1/auth/me/', '/api/v1/learning-twin/me/'):
            self.assertIn(self.client.get(route).status_code, (401,403))

    def test_logout_is_post_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/api/v1/auth/session-logout/').status_code, 405)
        self.assertEqual(self.client.get('/api/v1/dashboard/').status_code, 200)

    def test_authenticated_browser_requires_csrf_before_logout(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/v1/auth/session-logout/', {}).status_code, 403)
        self.assertEqual(client.get('/api/v1/dashboard/').status_code, 200)
        csrf = client.get('/api/v1/auth/csrf/').json()['csrfToken']
        self.assertEqual(client.post('/api/v1/auth/session-logout/', {}, HTTP_X_CSRFTOKEN=csrf).status_code, 200)
        self.assertIn(client.get('/api/v1/dashboard/').status_code, (401,403))

    def test_browser_logout_preserves_explicit_cli_token(self):
        token = Token.objects.create(user=self.user)
        self.client.force_login(self.user)
        self.client.post('/api/v1/auth/session-logout/', {})
        self.assertTrue(Token.objects.filter(key=token.key).exists())
        client = Client()
        self.assertEqual(client.get('/api/v1/auth/me/', HTTP_AUTHORIZATION='Token '+token.key).status_code, 200)

    def test_cannot_log_out_a_different_account_with_body_override(self):
        other = Client(); other.force_login(self.other)
        self.client.force_login(self.user)
        self.client.post('/api/v1/auth/session-logout/', {'user_id':self.other.pk})
        self.assertEqual(other.get('/api/v1/auth/me/').status_code, 200)
        self.assertIn(self.client.get('/api/v1/auth/me/').status_code, (401,403))
