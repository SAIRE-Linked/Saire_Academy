# v10.5 academic pathways — upgrade instructions

This release was built against the latest local source found at `Documents/Saire_Academy` on 9 November 2026. That source contains the working v10.4 foundations and additional local files. The patch is against that verified local baseline, not a generic older v9 or v10 package. The full source ZIP includes its retained customizations. Your original project/database were not changed during this work.

## Upgrade safely

Back up your project, database, backend private media and environment files first. Prefer the matching patch for an existing installation. From the project root:

```powershell
git apply --check C:\path\to\SAIRE_Academy_latest_local_to_v10_5.patch
git apply C:\path\to\SAIRE_Academy_latest_local_to_v10_5.patch
cd backend
python manage.py migrate
python manage.py seed_academic_pathways
python manage.py check
```

If the patch check reports local differences, keep your files and merge the affected changes; do not force the patch or replace your database. A separate guarded upgrade ZIP is also supplied: its `apply_upgrade.py` checks every affected file before writing, supports `--check`, and stops on conflicts. Review its README. The full source ZIP is useful as a separate comparison/install folder; it contains no credentials, accounts, database, original study guides or private uploads. Keep your existing `.env`/`.env.local` and private media when upgrading.

New migrations: `courses.0005_learningpathway_sourcereference_moduleprerequisite_and_more` adds pathways, units, cross-course prerequisites and private provenance tables. `courses.0006_module_curriculum_key` adds an optional unique internal seed identity. Existing module rows receive NULL and keep their data. No assessment, iteration, OAuth or Mentor schema is removed. Curriculum publication is an explicit seed command rather than an automatic content migration.

The seed requires the existing shared Python lesson `p1-l1` and a published designated final assignment. If they are missing, it stops with guidance. On a fresh install, initialise in this order:

```powershell
python manage.py migrate
python manage.py seed_curriculum
python manage.py seed_proofloop
python manage.py seed_skills
python manage.py seed_academic_pathways
```

Use the existing Python virtual environment and requirements. From the frontend project root:

```powershell
npm ci
npm run build
npm run start
```

For development use `npm run dev` and the existing Django runserver. Restart both services. No new package dependency is introduced. Next.js may normalise its generated `next-env.d.ts` and the required `jsx` setting during build; this release preserves the user's original versions of those local files in the deliverable.

## Where to look

- `/pathways/`: public learner discovery with search, year filter, authored-only filter, outcomes, scope and actual personal progress when signed in.
- `/dashboard/?course=it-foundations&view=roadmap`: the familiar dashboard with the IT course selected. Signed-in users who still owe orientation are shown Study Hub first.
- `/dashboard/?course=it-data-systems&view=roadmap`: the Year 2 sample course.
- `/assignments/`: existing ProofLoop workspace with the three new gated assignments, code defence, Mentor and Twin integration.
- Django Admin: Learning pathways + inline units; Module prerequisites; Source references + inline private coverage; existing module guides, lessons, resources, assignments and skills.

Public API addition: GET `/api/v1/pathways/`. It returns pathway/unit metadata, published outcomes and the caller's own progress. It exposes no guide files, source hashes, internal coverage, lesson bodies or quiz keys. Mutations are not allowed. Existing canonical course/lesson/assignment APIs enforce cross-course prerequisites; there is no separate client-only unlock store. API responses retain private/no-store and credential variation headers.

## Authentication and deployment configuration

OAuth/session/CSRF and CLI token behaviour are unchanged. Keep `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET` on Django only. Keep the existing public frontend origin in `CSRF_TRUSTED_ORIGINS`. Next proxies `/api/v1/` and `/accounts/` using `LMS_BACKEND_ORIGIN`; the Django backend should remain private behind the trusted proxy in production.

For the existing default local origin `http://localhost:3000`, provider callbacks are `http://localhost:3000/accounts/google/login/callback/` and `http://localhost:3000/accounts/github/login/callback/`. Use your actual HTTPS origin in production, keep hostnames consistent and configure the exact provider callback. The shared branded sign-in flow remains intact. This batch does not test real provider credentials or establish that live OAuth is configured.

Mentor credentials remain server-only. No real Gemini/OpenAI calls were needed to author or grade these lessons. The configured provider, consent and rate limits are preserved. See the existing v9/v10 setup guides for the complete provider configuration. No live AI success is claimed here.

New assignments `saire-service-intake`, `saire-workflow-ledger`, `saire-lending-records` use trusted suites `intake`, `workflow`, `records` on the separate grading worker. Deploy the updated worker source/suites as well as Django. Keep the existing strong `SAIRE_WORKER_SHARED_TOKEN`, approved repository access and dedicated isolated runner configuration. Starting a project downloads its private starter bundle only after the learner is eligible. Docker/GitHub end-to-end grading still requires your deployment credentials and runtime.

## Policy and completeness

Lesson timers remain 14 days with one supplementary window ending at day 21, default credited cap 70%. Setup is untimed. Existing attempts retain their original dates and grade cap. New projects have independent 14-day assignment deadlines and a 70% reviewed pass threshold; the existing quotation project's duration and records are unchanged. Project grade weights remain 50/30/10/10. There is no new automatic project resit timer.

The new route has six complete original lessons and three final projects, reusing four existing Python lessons. Seventeen IT units remain clearly marked outlines. Complete all currently released lessons/finals along the enforced practical route to open the sample; doing so does not imply completion of all Year 1 subjects. The full-program prerequisite proposals in the backlog are not installed automatically.

Only six unique guides were available for topic audit. Fifteen guides and two textbooks are still needed for the complete source audit. Missing-source curriculum entries are provisional and have no claimed verified chapter mapping. No copyrighted guide/textbook/exam content is publicly served.

The [editable blueprint](academic/Academic_Curriculum_Blueprint.md), [coverage matrix](academic/Source_Coverage_Matrix.csv), [backlog](academic/Curriculum_Backlog.csv) and [authoring guide](academic/Authoring_Guide.md) identify current behaviour and remaining work. Validation results distinguish automated/local checks from unverified live services.
