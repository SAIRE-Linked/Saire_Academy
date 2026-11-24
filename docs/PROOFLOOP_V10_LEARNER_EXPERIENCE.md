# ProofLoop v10 — Learner experience

This is an incremental update of the supplied v9 Gemini + Learning Twin ZIP. The existing Django CMS, assessment rubric, private starter downloads, independent grading worker, CLI, Mentor provider selection and Learning Twin remain. The home page now uses Django learner records. `/demo/` and `/preview/index.html` contain distinct, ungraded sample material.

## Rules shipped in this batch

| Decision | Rule |
| --- | --- |
| Enrollment | An authenticated learner can start the first published lesson of each published course. Enrollment/billing controls are outside this batch. |
| Sequence | Order is module position, lesson position, then database ID. Every earlier published lesson must have a server-recorded pass. Titles are public catalogue metadata; lesson bodies and questions require a start. |
| Start | Explicit POST creates one iteration per learner/lesson. Repeating a start returns the same record and deadline. Opening the dashboard never starts an iteration. |
| Primary window | Exactly 14 × 24 hours from Django's start instant. At or after the due instant, the original attempt fails and receives zero credited marks until a supplementary pass. |
| Supplement | One explicit supplementary request after failure, before day 21. Ends exactly seven days after the original deadline; requesting late does not shift the end. The original failure timestamp remains recorded. |
| Quiz pass | Existing lesson `passing_score` is a required question count; zero means ceil(75% × question count). Raw correct answers determine competence. Only Django receives answer keys. Failed quizzes may be retried within the active window, subject to a 30 actions/hour per-user throttle. |
| Grade penalty | Primary credit is the raw percentage. Supplementary credit is `min(raw percentage, grade_cap)`, default 70%. This is a ceiling, not a 30-point deduction. Competence/pass and credited marks are separate: raw 100%, supplementary credit 70%, passed. The cap is snapshotted when the iteration starts. |
| Day 21 | A still-failed or supplementary iteration becomes exhausted with zero credit. There is no automatic reset or second supplementary. Contact an instructor; formal appeals/reset workflows are future work. |
| No quiz | Never automatically passed. An instructor with Django change permission on lesson iterations uses the sign-off action after checking the challenge. Sign-off must occur inside the active window and receives 100 raw, with the supplementary cap when applicable. |
| Projects | All published lessons in the project's module and earlier modules must be passed. A module without any published lessons stays locked. Passing later lessons does not require passing a module project in this batch. |
| Existing assignment grading | Separate from lesson iterations. Existing assignment durations (including the seeded seven-day project), submissions, lateness rubric, worker results and instructor reviews retain v9 behavior. The new supplementary cap applies to lesson credit only. No combined course qualification grade is invented. |
| Admin testing | Active Django superusers bypass sequencing and publication restrictions, can preview lesson bodies, assignments and starters, and use the Mentor without starting. Ordinary `is_staff` instructors do not receive unrestricted learner access. Previewing never creates a learner pass. Use a separate learner account to test timed grading. |

## Local setup (PowerShell)

Back up your existing project and database. Extract the complete source into a new folder, or apply the included patch to an unchanged v9 tree after `git apply --check`. Keep your existing environment files, database, private media and secrets. Do not overwrite production data with a development database.

From the extracted project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
Copy-Item .env.local.example .env.local
cd backend
python manage.py migrate
python manage.py seed_curriculum
python manage.py seed_proofloop
python manage.py seed_skills
python manage.py createsuperuser
python manage.py runserver
```

Copy environment examples only if those local files do not already exist. Existing seed commands preserve instructor edits. Existing v9 assignment attempts, reviews and Mentor records are not deleted or regraded. Browser-only demo completion is deliberately not imported as trusted evidence. Consequently, existing learners initially need server-recorded lesson passes to unlock projects, while their historical attempts remain on the dashboard and in the database. Seeded v9 contains 12 phases but only four detailed lessons; empty future phases remain locked until real content is published.

In another terminal at project root:

```powershell
npm ci
npm run dev
```

Use **http://localhost:3000/** consistently. Keep `NEXT_PUBLIC_LMS_API_URL=/api/v1`. Next.js proxies `/api/v1/` and `/accounts/` to `LMS_BACKEND_ORIGIN` (default http://127.0.0.1:8000). Trailing slashes are intentional and avoid Django/Next redirect loops. Django Admin stays at **http://127.0.0.1:8000/admin/** in local development. Create pilot users there or sign up through OAuth.

## GitHub / Google credentials

The integration uses django-allauth's provider flows with state validation and Django HTTP-only session cookies. Browser requests use CSRF protection. CLI token authentication remains available; OAuth tokens and client secrets are not placed in browser storage. Automatic linking by matching email is disabled, and social signup cannot grant staff/superuser status.

Set these in `backend/.env`, then restart Django:

```dotenv
GOOGLE_OAUTH_CLIENT_ID=your-google-web-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GITHUB_OAUTH_CLIENT_ID=your-github-oauth-app-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret
DJANGO_USE_X_FORWARDED_HOST=1
SAIRE_SUPPLEMENTARY_GRADE_CAP=70
```

Create a Google OAuth web application and configure its consent screen/test users as needed. Register the exact authorized redirect URI:

`http://localhost:3000/accounts/google/login/callback/`

Create a GitHub OAuth App with homepage `http://localhost:3000/` and callback:

`http://localhost:3000/accounts/github/login/callback/`

For deployment replace the scheme and host with your public HTTPS academy origin. Google requests profile/email; GitHub requests user email, without repository access. Configure provider apps through the environment only; do not also create duplicate allauth SocialApp records. The homepage displays a provider as awaiting credentials until both required environment values are present. The allauth confirmation page intentionally requires a POST before redirecting to a provider.

Provider references: [allauth configuration](https://docs.allauth.org/en/dev/socialaccount/configuration.html), [provider configuration](https://docs.allauth.org/en/dev/socialaccount/provider_configuration.html), [Google provider](https://docs.allauth.org/en/latest/socialaccount/providers/google.html). Successful real-provider sign-in needs your own credentials and acceptance testing.

OAuth users can obtain a CLI token by setting a password through the authenticated account settings/reset flow, then using the retained `saire login` command. Configure real email delivery before relying on password reset. A dedicated OAuth-to-CLI device flow is not implemented.

## Operations and time safety

- `USE_TZ=True`; Django stores aware instants. Windows include DST-safe elapsed durations of exactly 336 and 168 hours. The browser formats dates in its own zone; device clocks cannot extend deadlines.
- Schedule `python manage.py expire_iterations` every minute using your hosting scheduler. Request-time expiry also enforces deadlines if the scheduler is delayed. Expiry preserves the original failure time and conditionally updates records so a stale expiry cannot overwrite a pass.
- Use PostgreSQL in production. Mutations lock the learner row and iteration in a transaction; a database unique constraint prevents duplicate starts. SQLite is for local development and does not provide PostgreSQL's row-lock guarantees. PostgreSQL concurrency/load behavior still needs deployment verification.
- Use HTTPS, `DJANGO_DEBUG=0`, a strong `DJANGO_SECRET_KEY`, explicit public `DJANGO_ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS=https://your-academy-host`. Session and CSRF cookies become secure when debug is off.
- `DJANGO_USE_X_FORWARDED_HOST=1` trusts your proxy's host header. Keep Django private/firewalled behind a trusted proxy that overwrites forwarded headers. This is necessary for public-origin OAuth callbacks; do not expose an untrusted forwarding path. `LMS_BACKEND_ORIGIN` is used when Next builds rewrites, so rebuild after changing it.
- Keep private media outside public/static paths. This update fixes the v9 missing default storage backend so seeded starter ZIPs can be created. Never expose private media through a public media route.
- API/account responses are private and not cacheable. Do not override those headers with a public CDN cache.
- Keep an active cohort's published ordering, question sets and pass requirements stable. This batch snapshots dates/cap, not curriculum versions. Publishing/reordering prerequisite lessons can change access; schedule curriculum releases between cohorts.
- Instructor sign-off actions use Django Admin permissions, but this batch has no dedicated appeal log, grade-change approval workflow, or reset endpoint. Retain database backups and establish those policies before a formal accredited rollout.

## Verification and boundaries

Run from `backend/`:

```powershell
python manage.py test progression courses assessments mentoring learning_twin
python manage.py makemigrations --check --dry-run
```

Run from project root:

```powershell
npm run typecheck
npm run build
npm run check:content
python -m unittest discover -s grading_worker/tests -v
$env:PYTHONPATH=(Resolve-Path tools).Path
python -m unittest discover -s tools/tests -v
```

See `VALIDATION_V10.md` for the package's actual results. Live AI calls, real OAuth consent/callback completion, deployed PostgreSQL races, Docker deployment and a production security review are not claimed as verified. The Learning Twin still reports rubric evidence rather than a validated measure of ability. Gemini/OpenAI keys remain server-only; v9 provider/privacy settings are retained. Original motivating messages and milestone badges are presentation features; only Django evidence changes access or grades.
