# ProofLoop v9 — Gemini AI Mentor + Learning Twin

## Release scope

This release preserves the existing Academy curriculum, Django CMS, grading worker, learner CLI, code review, learner history, and v8 Learning Twin. It replaces the single-provider mentor adapter with a configurable **Gemini / OpenAI** implementation and offers **optional, consent-based** skill-aware hints.

This is a development prototype. The official Gemini SDK API shape was checked against Google's current documentation, but an end-to-end provider request was **not run** in the build environment. Follow the local verification steps before deploying.

## 1. Revoke the exposed key before anything else

An API key was pasted into the conversation. Assume it is compromised. In [Google AI Studio API keys](https://aistudio.google.com/apikey), delete or rotate that credential, then generate a replacement. **Do not use the pasted key in this project.** Never place a key in a chat, screenshot, committed repository, frontend `NEXT_PUBLIC_*` variable or starter code. If you need to demonstrate configuration, use placeholder values.

Important: the supplied key's format is not enough to prove it is an active Gemini Developer API credential. Verify the replacement through Google AI Studio; do not expose it during troubleshooting.

## 2. Setup on Windows (PowerShell)

From the new v9 project folder, in Terminal 1:

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` in VS Code (this file is excluded by `.gitignore`) and set **your newly rotated key**, never the old one:

```dotenv
SAIRE_MENTOR_PROVIDER=gemini
GEMINI_API_KEY=PASTE_YOUR_ROTATED_KEY_LOCALLY
SAIRE_GEMINI_MODEL=gemini-flash-latest
SAIRE_MENTOR_ENABLE_TWIN_CONTEXT=0
```

`python-dotenv` loads `backend/.env` automatically for local Django; production hosts must use their secrets manager or environment variables instead. The default `gemini-flash-latest` alias follows your example, but model availability and pricing vary with your project. If needed, choose another supported free-tier model in Google AI Studio and update `SAIRE_GEMINI_MODEL`.

Start Django:

```powershell
python manage.py migrate
python manage.py seed_curriculum
python manage.py seed_proofloop
python manage.py seed_skills
python manage.py createsuperuser  # only for a new installation
python manage.py runserver
```

In Terminal 2, from project root:

```powershell
npm install
npm run dev
```

Open `http://localhost:3000/assignments`. Sign in with a Django user created for the pilot, select the Quotation Engine, and **start the assignment**. The mentor must now display **Gemini AI** rather than the rule-based preview. Start with a fictional question such as "How should I test a function that rejects invalid discount percentages?".

### Environment variable approach (without a `.env` file)

In PowerShell, before `python manage.py runserver`, run:

```powershell
$env:SAIRE_MENTOR_PROVIDER="gemini"
$env:GEMINI_API_KEY="PASTE_ROTATED_KEY_LOCALLY"
$env:SAIRE_GEMINI_MODEL="gemini-flash-latest"
```

### Docker Compose development option

Docker Compose reads its own **root** `.env`, not `backend/.env`. Create a **separate untracked root `.env`** containing `GEMINI_API_KEY`, `SAIRE_MENTOR_PROVIDER` and `SAIRE_GEMINI_MODEL` if running `docker compose up --build`. `compose.yaml` forwards the values into Django. Avoid putting the key in compose.yaml itself.

## 3. Safe Learning Twin personalisation

The old Learning Twin scores remain based on instructor-reviewed assessment evidence; AI chat activity does not affect marks or skills. To **test** tailored guidance:

1. Use a synthetic learner, a fictional assignment, and locally generated review results; **never use real student profiles on Gemini's free tier** without completing a privacy/legal assessment.
2. Set `SAIRE_MENTOR_ENABLE_TWIN_CONTEXT=1` on Django and restart it.
3. Sign in and start an assignment. The mentor then shows a checkbox **Personalise hints with my Learning Twin**. It is **unchecked by default**, and consent applies to each question in this browser session.
4. With the box unchecked, the profile is not computed or forwarded. With it checked, Django sends only a concise summary of up to two assessed practice areas and one demonstrated strength.
5. The model does **not** receive usernames, numerical grades, commit identifiers, instructor comments, complete assessments or test suites. The regular chat question and a bounded conversation history are still shared with the selected provider when live AI is enabled.

The checkbox is a technical opt-in for testing, **not a complete legal consent-management system**. Before launching publicly, design proper policy disclosure, recorded consent and retention/deletion schedules, provider agreements and protections for children.

## 4. Switch to OpenAI later

Change the Django environment:

```dotenv
SAIRE_MENTOR_PROVIDER=openai
OPENAI_API_KEY=YOUR_NEW_PRIVATE_OPENAI_API_KEY
SAIRE_OPENAI_MODEL=YOUR_SUPPORTED_MODEL_ID
```

Remove the Gemini key if it is no longer in use. Restart Django. There is no frontend change required; learner chats and permission rules remain in Django. API provider requests are made server-side only. The OpenAI adapter uses `store: false` for the Responses API.

## 5. Verification checklist

From `backend/` with a Python environment:

```powershell
python -m unittest mentoring.test_provider -v
python manage.py test mentoring learning_twin assessments -v 2
```

From project root:

```powershell
npm run typecheck
npm run build
```

Manual checks: (a) no key in browser devtools request payload or static JS; (b) unsigned learners cannot ask live mentor questions; (c) conversations stay assigned to one authenticated learner; (d) no skills transmitted without both administrative permission and learner opt-in; (e) provider outage returns a generic error and does not save a partial exchange; (f) content protection and existing quizzes still function.

## 6. Security, privacy, and production limitations

- Gemini Developer API free-tier content may be used by Google to improve its products (see [official pricing](https://ai.google.dev/gemini-api/docs/pricing)). Use **synthetic data only** in this pilot.
- Free-tier model access and quotas can change. Rate limits can cause `503` responses. We should later add cost dashboards, global budgets, monitoring and queued retries.
- Gemini responses are **generative** and should not be treated as assessment evidence or final grades. The Socratic prompt reduces solution-spoonfeeding but cannot guarantee it.
- The learner's token still lives only in frontend memory. This is a pilot auth flow; review production credential handling, CSRF/session design, consent storage and auditing before launch.
- The grading worker needs the independent deployment and security verification described in v5 docs. A model provider change does not alter grading safety.
- Full Django, SDK, Docker, and Next.js runtime integration needs verification on your machine.
