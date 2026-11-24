# SAIRE-Linked Academy — ProofLoop v7: Socratic Mentor

This build extends v6's scripted mentor preview into a **real, optional AI tutor** served by Django. v5's independent grading architecture and v6's gradient/contrast fixes remain present. **It is an MVP, not a fully audited production tutoring service.**

## 1. How it works

1. Instructor publishes an assignment in Django Admin.
2. A learner signs in to `/assignments` and starts the project.
3. The frontend loads `GET /api/v1/assignments/<slug>/mentor/` with the learner's short-lived **in-memory** token from the existing v4 login flow (the token itself remains persistent on Django until revoked).
4. If `OPENAI_API_KEY` is configured on the Django server, the mentor sends the learner's question, a bounded conversation and only **public** assignment title and learning outcomes to OpenAI's Responses API. No API key enters JavaScript.
5. Django stores the learner's question and AI answer against their account and assignment. A learner may delete their own history with the **Clear saved history** control.
6. When the backend is unconfigured or the assignment isn't started, a conspicuously labelled **rule-based preview** remains available. These preview messages are not sent to an AI model and aren't persisted.

**Endpoint contract**

| Endpoint | Method | Auth | Result |
|---|---|---|---|
| `/api/v1/mentor/status/` | GET | learner token | configuration state (no secrets) |
| `/api/v1/assignments/<slug>/mentor/` | GET | learner token + started project | last 40 messages, chronological |
| same | POST | learner token + started project | save question/AI answer, max 1200 input characters |
| same | DELETE | learner token + started project | delete own conversation for that assignment |

Throttling: 8 requests/hour and 40/day per authenticated learner (GET, POST, DELETE each consume quota). These are pilot defaults in `backend/mentoring/api.py`; tune based on usage. **For multiple production Django instances, configure a shared Redis cache for throttling.**

## 2. Enable the live AI mentor on Windows PowerShell

Follow `docs/PROOFLOOP_V5_GRADING.md` for Django/Next.js setup. Then:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
$env:OPENAI_API_KEY="YOUR_REAL_API_KEY"
$env:SAIRE_MENTOR_MODEL="gpt-6-luna"
python manage.py runserver
```

Configure the API key in backend/server secrets for deployment, **never** in `.env.local` variables prefixed `NEXT_PUBLIC_`, a React component, committed `.env` files, or GitHub repository source. Avoid storing keys in PowerShell history where possible; configure environment secrets through your hosting provider. Choose a model supported by your actual API account; the example model is configurable and may not be available to all users. API usage may incur cost.

In another terminal, from the project root:

```powershell
npm install
npm run dev
```

Visit `http://localhost:3000/assignments`, sign in with a Django-created learner, start a project, then ask for a hint under **Think before you code**.

### Verify

- No API key: mentor displays **Guided preview · Not AI** (and does not pretend to be a model).
- API key configured and valid: mentor displays **Live AI · Saved privately** after sign-in and project start.
- Ask: *“My function gives a wrong total when the discount is negative. How can I debug it?”* The model should prompt reasoning, not give an entire solution.
- Refresh/sign in again: previous live history loads from Django.
- Sign in as another learner: the first learner's messages must not appear.
- Select **Clear saved history**: only that learner's history for that assignment is deleted.
- Provider unavailable: the UI displays an error and retains the question for retry; no false AI reply is shown.

## 3. Run tests

```powershell
cd backend
python -m unittest mentoring.test_provider -v
python manage.py test mentoring assessments courses
```

The first suite uses Python's standard library and can run even if Django is not installed. The second requires Django/DRF packages and an available test database; it checks authorization, student isolation, deletion, input validation and provider failures. Run the full Next.js build locally with `npm run build` after installing dependencies.

## 4. Privacy, costs and safeguards

- **Private content stays private by design:** only assignment title and learning outcomes are sent to the model, not full grading suites, private files or reviewer questions. A student's question may still include personal data or pasted code; warn users not to share credentials or confidential material.
- **Data retention:** mentor messages are stored on the SAIRE Django database until deleted. OpenAI requests use `store: false` to disable Responses API storage for that request where supported, but this is **not** a blanket zero-retention guarantee; review your provider's applicable data controls and contracts.
- **Safety:** a system instruction encourages Socratic questions and discourages completed solutions, but **LLM compliance is not guaranteed**. Validate tutor behaviour using instructor-curated cases, monitor abuse and allow manual escalation. Do not use AI replies to calculate official project grades.
- **Rates and spend:** a learner throttle limits calls, and `max_output_tokens` caps output length. Add per-account cost accounting, budget alarms, institution-level quotas, shared caches and audit policies before production.
- **Error handling:** API/credential errors are hidden from learners; no provider response body is forwarded.
- **Learner control:** DELETE supports history removal; build a complete privacy/data-deletion policy, retention automation, account deletion, and any required South African POPIA disclosures before launch.
- **Infrastructure:** do not deploy grading workers and Django together for untrusted student submissions; the mentor feature is independent of the sandbox grading runner.

## 5. Next recommended engineering batch

Per-learner usage accounting, instructor-configurable Socratic policies, encrypted long-lived tokens or secure session auth, structured skill-gap diagnostics and question quality evaluations; then review-guided recommendations driven by *verified* project evidence.
