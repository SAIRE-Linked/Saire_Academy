"""Existing-account recovery through allauth's authenticated connect flow."""
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter


@override_settings(SOCIALACCOUNT_PROVIDERS={
    'google': {'APP': {'client_id':'example','secret':'example','key':''}},
    'github': {'APP': {'client_id':'example','secret':'example','key':''}},
})
class ExistingAccountConnectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner=get_user_model().objects.create_user('existing-learner',email='learner@example.test',password='ExampleSafePassword123!')
        cls.token=Token.objects.create(user=cls.owner)

    def callback(self, client, provider='google', connect=False, uid='provider-123', email=None):
        adapter=GoogleOAuth2Adapter if provider=='google' else GitHubOAuth2Adapter
        query='?process=connect&next='+reverse('socialaccount_connections') if connect else '?next=/dashboard/'
        start=client.post(f'/accounts/{provider}/login/'+query)
        self.assertEqual(start.status_code,302)
        state=parse_qs(urlsplit(start.url).query)['state'][0]
        def profile(provider_adapter,request,app,token,**kwargs):
            address=email or self.owner.email
            data={'sub':uid,'email':address,'email_verified':True} if provider=='google' else {'id':uid,'login':'learner','email':address}
            return provider_adapter.get_provider().sociallogin_from_response(request,data)
        with patch.object(OAuth2Adapter,'get_access_token_data',return_value={'access_token':'test-token'}), patch.object(adapter,'complete_login',autospec=True,side_effect=profile):
            return client.get(f'/accounts/{provider}/login/callback/',{'code':'test-code','state':state})

    def test_duplicate_email_stays_signed_out_and_offers_existing_account_route(self):
        response=self.callback(self.client)
        self.assertRedirects(response,reverse('socialaccount_signup'),fetch_redirect_response=False)
        page=self.client.get(response.url)
        self.assertContains(page,'Sign in to my existing account')
        self.assertContains(page,'next='+reverse('socialaccount_connections'))
        posted=self.client.post(reverse('socialaccount_signup'),{'email':self.owner.email,'username':'duplicate-name'})
        self.assertContains(posted,'An account already exists with this email address')
        self.assertNotIn('_auth_user_id',self.client.session)
        self.assertEqual(get_user_model().objects.count(),1)
        self.assertFalse(SocialAccount.objects.exists())

    def test_existing_password_login_continues_to_connections(self):
        response=self.client.post('/accounts/login/?next='+reverse('socialaccount_connections'),{'login':self.owner.username,'password':'ExampleSafePassword123!'})
        self.assertRedirects(response,reverse('socialaccount_connections'),fetch_redirect_response=False)
        page=self.client.get(response.url)
        self.assertContains(page,'/academy-auth.css')
        self.assertContains(page,'Connect Google')
        self.assertContains(page,'Connect GitHub')
        self.assertContains(page,'process=connect')

    def test_connections_requires_authenticated_session(self):
        response=self.client.get(reverse('socialaccount_connections'))
        self.assertEqual(response.status_code,302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_connect_requires_csrf_and_get_never_links_an_account(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.get('/accounts/google/login/?process=connect').status_code,200)
        self.assertFalse(SocialAccount.objects.exists())
        self.assertEqual(client.post('/accounts/google/login/?process=connect').status_code,403)
        self.assertFalse(SocialAccount.objects.exists())

    def test_authenticated_connect_preserves_user_and_allows_later_provider_login(self):
        for provider in ('google','github'):
            with self.subTest(provider=provider):
                client=Client();client.force_login(self.owner)
                response=self.callback(client,provider,connect=True)
                self.assertRedirects(response,reverse('socialaccount_connections'),fetch_redirect_response=False)
                account=SocialAccount.objects.get(provider=provider)
                self.assertEqual(account.user_id,self.owner.pk)
                self.assertEqual(get_user_model().objects.count(),1)
                self.assertTrue(Token.objects.filter(key=self.token.key,user=self.owner).exists())
                fresh=Client();login=self.callback(fresh,provider)
                self.assertRedirects(login,'/dashboard/',fetch_redirect_response=False)
                self.assertEqual(int(fresh.session['_auth_user_id']),self.owner.pk)

    def test_connected_identity_cannot_be_moved_from_another_account(self):
        other=get_user_model().objects.create_user('other-learner')
        account=SocialAccount.objects.create(user=other,provider='google',uid='provider-123')
        self.client.force_login(self.owner)
        self.callback(self.client,connect=True)
        account.refresh_from_db()
        self.assertEqual(account.user_id,other.pk)
        self.assertEqual(SocialAccount.objects.count(),1)
        self.assertEqual(int(self.client.session['_auth_user_id']),self.owner.pk)

    def test_new_unique_learner_can_still_sign_up_without_admin_privileges(self):
        response=self.callback(self.client,uid='new-id',email='new@example.test')
        self.assertRedirects(response,'/dashboard/',fetch_redirect_response=False)
        user=get_user_model().objects.get(pk=self.client.session['_auth_user_id'])
        self.assertNotEqual(user.pk,self.owner.pk)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
