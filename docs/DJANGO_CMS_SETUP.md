# Django CMS integration — step by step

**Architecture:** Next.js + React + Framer Motion (public learner website) → Django REST Framework (public read-only curriculum API) → PostgreSQL (production database). Staff use Django Admin for content editing. The existing client-side progress remains local; learner registration is **not** implemented in this release.

## 1. Run the API locally

From the project root, on Windows PowerShell:

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_curriculum
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

On macOS/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` instead. The development database defaults to SQLite for ease of setup. **PostgreSQL is the intended production database**, enabled through `DATABASE_URL`.

Open:
- Admin: `http://127.0.0.1:8000/admin/`
- Course catalogue: `http://127.0.0.1:8000/api/v1/courses/`
- Original course: `http://127.0.0.1:8000/api/v1/courses/ai-engineer-agentic-systems/`
- Health: `http://127.0.0.1:8000/api/v1/health/`

You can also start both services and PostgreSQL together with `docker compose up --build`, then create your admin user with `docker compose exec backend python manage.py createsuperuser`. The Compose credentials are for local learning **only**.

## 2. Connect the existing Next.js frontend

In a **second terminal**, at the project root:

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Visit `http://localhost:3000`. The small banner above the dashboard should say **Live curriculum from Django CMS**. Use the **COURSE** dropdown to switch between published courses.

If the API is offline, the frontend deliberately falls back to the original AI Engineering sample course and shows an **offline/demo** banner. `public/preview/index.html` is an independent static preview and is **not** connected to Django — use the Next.js app for CMS changes.

## 3. Edit your current AI Engineering curriculum

1. Log in at `/admin/` with your staff/superuser account.
2. Under **Learning content → Courses**, open **AI Engineer & Agentic Systems Mastery Programme**.
3. Courses contain modules (phases). Edit phase titles, duration, publication status, etc. Save.
4. Under **Modules**, open the relevant phase. Edit its descriptions and add/reorder **Topics** inline.
5. Under **Lessons**, open a lesson. Edit its objective, challenge, duration and publication status. Add/reorder **Lesson sections** inline, with heading, explanation, code example and note. Add quiz questions inline; choose the correct A/B/C/D answer.
6. Under **Projects**, edit the phase's practical project milestone and its comma-separated skills.
7. Refresh the public LMS webpage to fetch the latest published content.

**Draft vs published:** courses start as drafts. A course needs status **Published** to appear in the public catalogue. Modules, lessons and projects have independent published switches; unpublished content is hidden even if its parent course is published. This lets you prepare future lessons before releasing them.

**IMPORTANT:** Do not change a published lesson's `public_id` or a course's `slug`: these are stable identifiers for existing browser progress and links. The `seed_curriculum` command **never overwrites** an existing course; it is safe to rerun after admin edits.

## 4. Create your next course

A realistic example: **AI Automation for Small Businesses**.

1. Go to **Admin → Courses → Add**.
2. Set title, unique slug (e.g. `ai-automation-business`), subtitle, description, timeframe and sorting order. Leave status as **Draft** while preparing it.
3. Save the course; add modules inline or from **Modules → Add** with unique positions `1, 2, 3...` within this course.
4. Create each module's topic list in **Modules**.
5. Under **Lessons → Add**, choose the module, write a title, objective and challenge. Add lesson sections (with a per-section code language) and quiz questions. Check **Published** only when the content is ready.
6. Add its projects under **Projects → Add**.
7. Publish the course and ensure its modules are published. Refresh the website. The new course automatically appears in the course selector and course gallery. No frontend code change is required.

**Lesson styling:** explanations are plain text rendered safely (line breaks are preserved). Examples go in the `code` field and appear in the website's copyable code panels. Don't paste arbitrary HTML or scripts into text fields.

## 5. API contract

`GET /api/v1/courses/` returns published course summaries.  
`GET /api/v1/courses/<slug>/` returns course metadata and nested `phases`, `lessons`, and `projects` compatible with the React app. Quiz questions are attached to individual lessons.

The API is deliberately **read-only** to anonymous learners. Staff manage content through Django Admin using Django's built-in account permissions. Public quiz answers are exposed for **self-study practice only**; this is not a secure examination platform.

## 6. Production / hosting

Use separate services for Next.js and Django with a managed PostgreSQL database (for example on Render, if the chosen region and pricing suit you):

- **Django web service** root directory: `backend`. Install dependencies: `pip install -r requirements.txt`. Build: `python manage.py collectstatic --noinput`. Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`.
- **Before first deploy**, run `python manage.py migrate` then `python manage.py seed_curriculum` as a one-off deployment step. Use `python manage.py createsuperuser` through a secure shell, not an automated build step.
- Configure `DJANGO_DEBUG=0`, a strong unique `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=api.your-domain...`, `DATABASE_URL=postgresql://...`, `CORS_ALLOWED_ORIGINS=https://your-frontend-domain`, and `CSRF_TRUSTED_ORIGINS=https://your-backend-admin-domain`.
- **Next.js web service** root directory: project root. Configure `NEXT_PUBLIC_LMS_API_URL=https://your-backend-domain/api/v1` **before building Next.js** (public environment variables are embedded into client bundles).
- Enable HTTPS, managed database backups and monitoring, plus appropriate admin access control. On trusted HTTPS-terminating proxies, configure `SECURE_SSL_REDIRECT=1` and confirm proxy headers.
- Run `python manage.py check --deploy` with production variables and fix deployment warnings. Run `python manage.py test` before each release.
- Verify Django Admin's CSS is available in production; WhiteNoise serves collected Django static files.

This is a curriculum CMS implementation, **not yet a full authenticated production LMS**. Learner accounts, enrollments, payment/subscriptions, server-stored progress, certificates, server-side grading and detailed audit/history still require dedicated design and implementation. Plan POPIA-compliant handling before collecting learner personal data.

## 7. What each file does

- `backend/courses/models.py` — database tables and relationships.
- `backend/courses/admin.py` — editor-friendly content management with inlines.
- `backend/courses/serializers.py` — API shape consumed by React.
- `backend/courses/views.py` — public read-only endpoints.
- `backend/courses/migrations/0001_initial.py` — first database migration.
- `backend/courses/management/commands/seed_curriculum.py` — safe initial import.
- `backend/content/ai_engineering_seed.json` — preserved original course contents.
- `lib/lms-api.ts` — typed frontend API integration and explicit demo fallback.
- `components/LearningPlatform.tsx` — existing design + live course selection, lessons and quizzes.
- `backend/courses/tests.py` — Django API and import tests.

## 8. First tests to perform

1. Open the public website with both servers running and confirm the **connected** banner.
2. In admin, rename an existing lesson; refresh the website and confirm the new name appears.
3. Add a **draft** lesson and confirm that it is **not** visible publicly.
4. Publish the lesson; refresh and confirm that it appears with its sections.
5. Add a draft course with one module and lesson, then publish it; confirm it appears in the course picker.
6. Change course via picker and complete lessons — ensure each course has separate browser progress.
7. Disconnect Django. Confirm the original course loads with an offline/demo notice; do not mistake this for live CMS data.
8. Test desktop/mobile widths and animations (including reduced-motion preferences).
