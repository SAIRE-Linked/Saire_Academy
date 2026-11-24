# ProofLoop v10 validation

Validated locally on Windows, Python 3.13.15 / Django 5.2.18, Node 24.19.0 / Next.js 15.5.28.

| Check | Actual result |
| --- | --- |
| Django progression, OAuth flow/state, CMS, assessment, worker API, Mentor and Twin tests | 74 passed |
| Independent worker safety tests | 8 passed |
| CLI tests, including Windows archive path handling | 4 passed |
| Django system checks and migration drift | Passed; no changes detected |
| Fresh database migrate + curriculum/assessment/skills seeds | Passed; starter ZIP created privately |
| TypeScript | Passed |
| Next.js production build | Passed; inherited CSS alignment compatibility warnings remain |
| Offline sample content, navigation, quiz and saved demo progress | Passed |
| Real HTTP through production Next server to Django | Passed: session password login, dashboard, lesson start/content, quiz submission, locked-next-lesson denial |
| OAuth initiation through Next proxy | Passed with dummy credentials: CSRF confirmation, redirect state and correct public callback origin |

Total automated Python tests: **86 passed**. OAuth tests do not contact providers. HTTP smoke checks used a temporary development database excluded from the package.

Not verified: real Google/GitHub sign-in, live Gemini/OpenAI requests, a real isolated Docker grading run, PostgreSQL concurrency/load, Docker/hosting rollout, mobile/browser visual QA or a production security audit. No production-readiness certification is implied. Existing AI-provider privacy tests are included in the Django suite. UI demo content is distinct from graded Django seed material.

The source package excludes local databases, accounts, environment files, private media, dependency directories and build outputs. The v9-to-v10 patch is generated against the exact original Downloads ZIP; use `git apply --check` first. It includes a dependency lockfile, migrations, backend access controls and frontend changes.
