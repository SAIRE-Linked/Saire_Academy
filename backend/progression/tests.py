from datetime import timedelta, datetime, timezone as dt_timezone
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from courses.models import Course, Module, Lesson, LessonSection, QuizQuestion, Project
from assessments.models import Assignment, AssignmentAttempt, CodeReview, Submission
from .models import LessonIteration, OrientationAcknowledgment
from .services import begin, expire, credit


class ProgressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U = get_user_model()
        cls.user = U.objects.create_user('learner', password='SafeTestPassword123!')
        cls.other = U.objects.create_user('other')
        cls.staff = U.objects.create_user('staff', is_staff=True)
        cls.admin = U.objects.create_superuser('admin', 'a@example.test', 'SafeTestPassword123!')
        cls.course = Course.objects.create(title='Engineering', slug='eng', status='published')
        cls.module = Module.objects.create(course=cls.course, name='Start', position=1)
        cls.lesson = Lesson.objects.create(module=cls.module, title='One', public_id='one', published=True)
        cls.next = Lesson.objects.create(module=cls.module, title='Two', public_id='two', position=2, published=True)
        LessonSection.objects.create(lesson=cls.lesson, heading='Private section', body='Protected content')
        QuizQuestion.objects.create(lesson=cls.lesson, question='Pick A', option_a='A', option_b='B', option_c='C', option_d='D', correct=0, reason='Secret reason')
        Project.objects.create(module=cls.module, name='Project', description='Private project')
        Assignment.objects.create(module=cls.module, slug='project', title='Project', brief='Private brief', published=True, learning_outcomes='Test', q1='a',q2='b',q3='c',q4='d',q5='e')

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client.force_login(self.user)
        OrientationAcknowledgment.objects.create(learner=self.user, version=settings.SAIRE_ORIENTATION_VERSION)

    def post(self, action, body=None, lesson='one'):
        return self.client.post(f'/api/v1/lessons/{lesson}/{action}/', body or {}, content_type='application/json')

    def test_catalogue_is_metadata_only_and_first_unlocked(self):
        data=self.client.get('/api/v1/courses/eng/').json()
        self.assertFalse(data['lessons'][0]['locked']);self.assertTrue(data['lessons'][1]['locked'])
        self.assertNotIn('sections',data['lessons'][0]);self.assertNotIn('quiz',data['lessons'][0])
        self.assertNotIn('description',data['projects'][0])
        self.client.logout()
        self.assertTrue(all(l['locked'] for l in self.client.get('/api/v1/courses/eng/').json()['lessons']))

    def test_no_content_before_start_and_no_answer_key(self):
        self.assertEqual(self.client.get('/api/v1/lessons/one/').status_code,403)
        self.post('start')
        response=self.client.get('/api/v1/lessons/one/')
        self.assertContains(response,'Protected content')
        self.assertNotContains(response,'Secret reason')
        self.assertNotIn('correct',response.json()['quiz'][0])

    def test_start_is_idempotent_14_days_and_ignores_browser_dates(self):
        first=self.post('start',{'due_at':'2099-01-01','status':'passed'}).json()['iteration']
        self.assertEqual(first,self.post('start').json()['iteration'])
        i=LessonIteration.objects.get();self.assertEqual(i.due_at-i.started_at,timedelta(days=14))
        self.assertTrue(timezone.is_aware(i.due_at))

    def test_locked_detail_start_submit_and_project_routes(self):
        self.assertEqual(self.client.get('/api/v1/lessons/two/').status_code,403)
        for action in ['start','submit','supplement']:
            self.assertEqual(self.post(action,lesson='two').status_code,403)
        for path in ['','start/','starter/','submit/','mentor/']:
            method=self.client.post if path in ['start/','submit/'] else self.client.get
            self.assertEqual(method('/api/v1/assignments/project/'+path).status_code,403)

    def test_failed_quiz_does_not_unlock_pass_unlocks_next(self):
        self.post('start')
        self.assertEqual(self.post('submit',{'answers':[1],'score':100}).json()['iteration']['status'],'active')
        self.assertEqual(self.post('submit',{'answers':[0]}).json()['iteration']['status'],'passed')
        self.assertEqual(self.post('start',lesson='two').status_code,201)
        self.assertTrue(self.client.get('/api/v1/courses/eng/').json()['projects'][0]['locked'])
        i=LessonIteration.objects.get(lesson=self.next);credit(i,100,True)
        self.assertFalse(self.client.get('/api/v1/courses/eng/').json()['projects'][0]['locked'])
        self.assertEqual(self.client.post('/api/v1/assignments/project/start/').status_code,201)

    def test_next_module_requires_own_passing_final_review(self):
        second = Module.objects.create(course=self.course, name='Next module', position=2)
        Lesson.objects.create(module=second, title='Next module lesson', public_id='three', published=True)
        assignment = Assignment.objects.get(slug='project')
        for lesson in (self.lesson, self.next):
            iteration, _ = begin(self.user, lesson)
            credit(iteration, 100, True)

        def state():
            return self.client.get('/api/v1/courses/eng/').json()['phases']

        self.assertEqual(state()[0]['progress']['status'], 'awaiting_project')
        self.assertEqual(self.post('start', lesson='three').status_code, 403)
        assignment.module_pass_score = 70
        assignment.save()
        self.assertEqual(state()[0]['progress']['status'], 'final_project')
        attempt = AssignmentAttempt.objects.create(
            learner=self.user, assignment=assignment, due_at=timezone.now() + timedelta(days=7),
        )
        submission = Submission.objects.create(
            attempt=attempt, repository_url='https://github.com/learner/project',
            commit_sha='a' * 40, local_tests_passed=100,
        )
        self.assertEqual(state()[0]['progress']['final_project']['status'], 'awaiting_review')
        self.assertEqual(self.post('start', lesson='three').status_code, 403)

        scores = dict(reviewer=self.staff, code_quality_score=100, q1_score=0, q2_score=0,
                      q3_score=0, q4_score=0, q5_score=0)
        other_attempt = AssignmentAttempt.objects.create(
            learner=self.other, assignment=assignment, due_at=timezone.now() + timedelta(days=7),
        )
        other_submission = Submission.objects.create(
            attempt=other_attempt, repository_url='https://github.com/other/project', commit_sha='b' * 40,
        )
        CodeReview.objects.create(submission=other_submission, verified_test_score=100, **scores)
        review = CodeReview.objects.create(submission=submission, verified_test_score=98, **scores)
        self.assertEqual(review.final_score, 69)
        self.assertEqual(state()[0]['progress']['final_project']['status'], 'needs_revision')
        self.assertEqual(self.post('start', lesson='three').status_code, 403)

        review.verified_test_score = 100
        review.save()
        self.assertEqual(review.final_score, 70)
        assignment.published = False
        assignment.save()
        self.assertEqual(self.post('start', lesson='three').status_code, 403)
        assignment.published = True
        assignment.save()
        modules = state()
        self.assertEqual(modules[0]['progress']['status'], 'completed')
        self.assertEqual(modules[1]['progress']['status'], 'lessons')
        self.assertEqual(self.post('start', lesson='three').status_code, 201)

    def test_empty_previous_module_blocks_later_module(self):
        second = Module.objects.create(course=self.course, name='Empty', position=2)
        third = Module.objects.create(course=self.course, name='Later', position=3)
        Lesson.objects.create(module=third, title='Later lesson', public_id='later', published=True)
        assignment = Assignment.objects.get(slug='project')
        assignment.module_pass_score = 70
        assignment.save()
        for lesson in (self.lesson, self.next):
            credit(begin(self.user, lesson)[0], 100, True)
        attempt = AssignmentAttempt.objects.create(
            learner=self.user, assignment=assignment, due_at=timezone.now() + timedelta(days=7),
        )
        submission = Submission.objects.create(
            attempt=attempt, repository_url='https://github.com/learner/project', commit_sha='c' * 40,
        )
        CodeReview.objects.create(
            submission=submission, reviewer=self.staff, verified_test_score=100,
            code_quality_score=100, q1_score=0, q2_score=0, q3_score=0, q4_score=0, q5_score=0,
        )
        phases = self.client.get('/api/v1/courses/eng/').json()['phases']
        self.assertEqual(phases[1]['id'], second.position)
        self.assertEqual(phases[1]['progress']['status'], 'coming_soon')
        self.assertEqual(self.post('start', lesson='later').status_code, 403)

    def test_deadline_exact_boundary_and_supplementary_cap(self):
        self.post('start');i=LessonIteration.objects.get()
        from rest_framework.authtoken.models import Token
        self.client.defaults['HTTP_AUTHORIZATION']='Token '+Token.objects.get_or_create(user=self.user)[0].key
        with patch('django.utils.timezone.now',return_value=i.due_at):
            self.assertEqual(self.post('submit',{'answers':[0]}).status_code,403)
            self.assertEqual(self.post('supplement').status_code,200)
            self.assertEqual(self.post('supplement').status_code,200)
            self.assertEqual(self.post('submit',{'answers':[0]}).json()['iteration']['credited_score'],70)
        i.refresh_from_db();self.assertEqual(i.status,'passed');self.assertEqual(i.primary_failed_at,i.due_at)
        self.assertEqual(i.supplementary_due_at,i.due_at+timedelta(days=7))

    def test_day21_no_reset_or_late_supplement(self):
        self.post('start');i=LessonIteration.objects.get()
        from rest_framework.authtoken.models import Token
        self.client.defaults['HTTP_AUTHORIZATION']='Token '+Token.objects.get_or_create(user=self.user)[0].key
        with patch('django.utils.timezone.now',return_value=i.due_at+timedelta(days=7)):
            self.assertEqual(self.post('supplement').status_code,403)
            self.assertEqual(self.post('start').json()['iteration']['status'],'exhausted')
            self.assertEqual(self.post('submit',{'answers':[0]}).status_code,403)

    def test_dashboard_private_and_no_user_override(self):
        self.post('start');self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/api/v1/dashboard/?learner={self.user.pk}').json()['iterations'],{})
        self.assertEqual(self.client.get('/api/v1/lessons/one/').status_code,403)

    def test_only_superuser_bypasses_locks_and_can_preview_drafts(self):
        self.client.force_login(self.staff);self.assertEqual(self.post('start',lesson='two').status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/api/v1/lessons/two/').status_code,200)
        self.assertEqual(self.client.get('/api/v1/assignments/project/').status_code,200)
        self.next.published=False;self.next.save()
        self.assertEqual(self.client.get('/api/v1/lessons/two/').status_code,200)
        self.assertEqual(LessonIteration.objects.count(),0)

    def test_invalid_answers_and_no_quiz_cannot_self_complete(self):
        self.post('start')
        for answers in [[],[True],[4],['0'],[0,0]]:
            self.assertEqual(self.post('submit',{'answers':answers}).status_code,400)
        self.post('submit',{'answers':[0]});self.post('start',lesson='two')
        self.assertEqual(self.post('submit',{'answers':[]},lesson='two').status_code,400)

    def test_supplement_cap_snapshotted_and_timezone_safe(self):
        now=datetime(2026,10,25,0,30,tzinfo=dt_timezone.utc)
        with override_settings(SAIRE_SUPPLEMENTARY_GRADE_CAP=65,TIME_ZONE='Europe/London'):
            i,_=begin(self.user,self.lesson,now)
        self.assertEqual(i.grade_cap,65);self.assertEqual((i.due_at-now).total_seconds(),14*86400)

    def test_session_csrf_enforced(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        self.assertEqual(c.post('/api/v1/lessons/one/start/').status_code,403)
        token=c.get('/api/v1/auth/csrf/').json()['csrfToken']
        self.assertEqual(c.post('/api/v1/lessons/one/start/',HTTP_X_CSRFTOKEN=token).status_code,201)

    def test_stale_expiry_cannot_overwrite_a_pass(self):
        i,_=begin(self.user,self.lesson);stale=LessonIteration.objects.get(pk=i.pk)
        credit(i,100,True)
        expire(stale,i.due_at+timedelta(days=1))
        i.refresh_from_db();self.assertEqual(i.status,'passed');self.assertEqual(i.credited_score,100)

    def test_seed_creates_private_starter_and_is_idempotent(self):
        import tempfile
        from pathlib import Path
        from django.core.management import call_command
        with tempfile.TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            call_command('seed_curriculum',verbosity=0)
            call_command('seed_proofloop',verbosity=0)
            a=Assignment.objects.get(slug='saire-quotation-engine')
            self.assertEqual(a.module_pass_score, 70)
            self.assertTrue(Path(a.starter_bundle.path).is_file())
            self.assertTrue(Path(a.starter_bundle.path).is_relative_to(root))
            call_command('seed_proofloop',verbosity=0)
            self.assertEqual(Assignment.objects.filter(slug=a.slug).count(),1)

    def test_original_foundation_lessons_open_and_complete_in_order(self):
        from django.core.management import call_command
        call_command('seed_curriculum', verbosity=0)
        module_id = Lesson.objects.get(public_id='p1-l1').module_id
        path = f'/api/v1/academy/modules/{module_id}/setup/'
        setup = self.client.get(path).json()
        completed = self.client.post(path, {
            'revision': setup['revision'], 'checked': [step['id'] for step in setup['steps']],
        }, content_type='application/json')
        self.assertTrue(completed.json()['completed'])
        for number in range(1, 5):
            lesson_id = f'p1-l{number}'
            lesson = Lesson.objects.get(public_id=lesson_id)
            self.assertEqual(self.post('start', lesson=lesson_id).status_code, 201)
            detail = self.client.get(f'/api/v1/lessons/{lesson_id}/').json()
            self.assertTrue(detail['sections'])
            self.assertEqual(len(detail['quiz']), 4)
            self.assertTrue(all('correct' not in question for question in detail['quiz']))
            answers = list(lesson.quiz_questions.values_list('correct', flat=True))
            result = self.post('submit', {'answers': answers}, lesson=lesson_id)
            self.assertEqual(result.json()['iteration']['status'], 'passed')
        course = self.client.get('/api/v1/courses/ai-engineer-agentic-systems/').json()
        self.assertTrue(course['phases'][0]['progress']['project_unlocked'])
        self.assertEqual(course['phases'][1]['progress']['status'], 'locked')

    def test_private_cache_headers(self):
        response=self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.headers['Cache-Control'],'private, no-store')
        self.assertIn('Cookie',response.headers['Vary'])

    def test_rejected_late_submission_still_records_failure(self):
        from rest_framework.authtoken.models import Token
        self.client.defaults['HTTP_AUTHORIZATION']='Token '+Token.objects.get_or_create(user=self.user)[0].key
        self.post('start');i=LessonIteration.objects.get()
        with patch('django.utils.timezone.now',return_value=i.due_at):
            self.assertEqual(self.post('submit',{'answers':[0]}).status_code,403)
        i.refresh_from_db();self.assertEqual(i.status,'failed');self.assertEqual(i.credited_score,0)


@override_settings(SOCIALACCOUNT_PROVIDERS={'google': {'APP': {'client_id':'example','secret':'example','key':''}}, 'github': {'APP': {'client_id':'example','secret':'example','key':''}}})
class OAuthTests(TestCase):
    def test_get_confirms_post_starts_state_protected_flow(self):
        for provider in ['github','google']:
            url=f'/accounts/{provider}/login/'
            response = self.client.get(url)
            self.assertContains(response, '/academy-auth.css')
            self.assertContains(response, 'SAIRE-Linked Academy')
            self.assertContains(response, 'name="csrfmiddlewaretoken"')
            res=self.client.post(url)
            self.assertEqual(res.status_code,302)
            self.assertIn('state=',res.url)
            self.assertIn('client_id=example',res.url)

    def test_pilot_login_lands_on_dashboard(self):
        get_user_model().objects.create_user('pilot', password='SafeTestPassword123!')
        response = self.client.post('/accounts/login/', {
            'login': 'pilot', 'password': 'SafeTestPassword123!',
        })
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)

    def test_provider_callback_lands_on_dashboard(self):
        from urllib.parse import parse_qs, urlsplit

        from allauth.socialaccount.models import SocialAccount
        from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
        from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter

        user = get_user_model().objects.create_user('returning-learner')
        for provider, adapter in [('google', GoogleOAuth2Adapter), ('github', GitHubOAuth2Adapter)]:
            with self.subTest(provider=provider):
                SocialAccount.objects.create(user=user, provider=provider, uid='12345')
                client = Client()
                start = client.post(f'/accounts/{provider}/login/?next=/dashboard/')
                state = parse_qs(urlsplit(start.url).query)['state'][0]

                def profile(provider_adapter, request, app, token, **kwargs):
                    data = {'sub': '12345'} if provider == 'google' else {'id': 12345}
                    return provider_adapter.get_provider().sociallogin_from_response(request, data)

                with patch.object(OAuth2Adapter, 'get_access_token_data', return_value={'access_token': 'test-token'}):
                    with patch.object(adapter, 'complete_login', autospec=True, side_effect=profile):
                        response = client.get(
                            f'/accounts/{provider}/login/callback/', {'code': 'test-code', 'state': state},
                        )
                self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
                self.assertEqual(client.get('/api/v1/dashboard/').json()['username'], user.username)

    def test_missing_state_callback_cannot_authenticate(self):
        for provider in ['github','google']:
            response=self.client.get(f'/accounts/{provider}/login/callback/?code=fake')
            self.assertNotIn('_auth_user_id',self.client.session)
            self.assertIn(response.status_code,[200,302,400,401])
