# SAIRE-Linked Digital Learning Platform — Django CMS Edition (v2)

**Build Smarter. Learn Deeper.** This upgraded project preserves the original animated Next.js learning website and adds a real Django + Django REST Framework curriculum management backend.

### What's new in v2

- **Django Admin content management:** create/update courses, phases, topics, lessons, copyable code examples, quizzes, and portfolio projects without editing React source files.
- **Draft/publish workflow:** prepare unpublished courses and lessons privately, then publish them when ready.
- **Live read-only curriculum API:** all published content appears in the frontend after refresh; the homepage now offers a course selector and a catalogue when multiple courses exist.
- **Original programme preserved:** safe idempotent import loads all 12 phases, 72 topics, 4 introductory lessons, 12 projects and Lesson 1 quiz. Running the import again never overwrites existing admin edits.
- **PostgreSQL-ready:** SQLite works for local development; PostgreSQL connects through `DATABASE_URL`. A development Docker Compose stack is included.
- **Branded administration:** SAIRE-Linked colours and logo appear in Django Admin; the original frontend branding and Framer Motion interactions remain.
- **Separate per-course learner progress:** saved locally in the browser, including compatibility with the original default course's progress.

**First read:** [`docs/DJANGO_CMS_SETUP.md`](docs/DJANGO_CMS_SETUP.md) — complete Windows/VS Code setup, admin workflows, API, deployment, production limitations, and hands-on tests.

### Quick setup (Windows PowerShell)

Terminal 1 — backend:

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_curriculum
python manage.py createsuperuser
python manage.py runserver
```

Terminal 2 — frontend (from project root):

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

- Website: **http://localhost:3000**
- Content admin: **http://127.0.0.1:8000/admin/**
- Published course API: **http://127.0.0.1:8000/api/v1/courses/**

Alternative: `docker compose up --build` for Next.js + Django + PostgreSQL. Then create the staff account with `docker compose exec backend python manage.py createsuperuser`.

**Scope:** This is an *editable-curriculum Growth-package MVP*, **not** a finished subscription-based multi-user LMS. Learner progress and quiz grading are browser-local; no real enrolments, account login, payment, certificates or secure exams have been implemented. The offline HTML preview is a separate static demo and does not sync with Django.

---

# SAIRE-Linked Digital Learning Platform

**Build Smarter. Learn Deeper.**

The original custom-branded, responsive learning-management **MVP** for the AI Engineer & Agentic Systems Mastery Programme. Developed for SAIRE-Linked, using the uploaded SAIRE-Linked logo assets and a blue/green premium technology aesthetic.

## What's inside

- **Overview dashboard:** programme introduction, learner progress, next lesson, first-month study plan and featured phases.
- **Complete programme roadmap:** 12 phases, 72 syllabus topics, duration estimates and 12 practical capstone milestones. Search and category filters work.
- **Interactive classroom:** four fully authored introductory Python lessons, step-by-step examples, code copy, learner notes and lesson completion.
- **Knowledge check:** four-question Lesson 1 quiz, graded with explanations and a 3/4 passing threshold.
- **Project lab:** 12 project descriptions, technology tags, success criteria and phase links.
- **Weekly study planner:** seven adjustable study sessions with automatic local saving and live weekly totals.
- **Resource library:** a five-part technology stack and links to six reputable learning resources.
- **Motion system:** Framer Motion transitions in the Next.js app, responsive hover/micro-interactions, floating hero graphic, glowing effects, and respect for `prefers-reduced-motion`.
- **Local progress persistence:** completed lessons, quiz best score, notes, current lesson, and study schedule are saved locally, with a JSON backup action.
- **SEO basics:** page title, description, keywords and Open Graph metadata.
- **Brand kit:** all three original supplied PNGs, optimised WebP variants and a favicon.

### Important scope distinction

This is a **working, Django-managed curriculum Growth-package MVP**, not a multi-user production LMS. **Django now provides the curriculum backend and content database. There is still no learner login, payment processing, email automation, server-side progress storage, or Python execution sandbox.** Browser progress is not secure, private across shared devices, or synchronized across devices. The complete 12-phase **syllabus** is published, but only the first **four detailed lessons** have been authored in this initial build. Additional tutorials, quizzes, and project workbooks must be produced phase by phase. Do not advertise the other 68 topics as fully taught yet.

The larger SAIRE-Linked product vision builds upon the implemented course authoring/admin to add enrolment, cross-device syncing, assessments, downloadable certificates, analytics and payment integrations. See `docs/PRODUCTION_ARCHITECTURE.md`.

## Open an interactive preview immediately (no installation)

1. Open `public/preview/index.html` in Chrome, Edge, Firefox or another modern browser, or open the separate preview ZIP that accompanies this project.
2. Click the sidebar navigation to view the roadmap, classroom, project lab, planner and resources.
3. Complete Lesson 1 and its knowledge check, then mark the lesson complete.
4. Try adjusting the weekly schedule. Your changes save to your own browser profile.

The offline preview is independently implemented in vanilla JavaScript so it can run without a build step. **The main source of truth is the Next.js/React/TypeScript application.** Both versions share the same curriculum content; use the Next.js version for ongoing product development. The local-storage key is shared when both run under the same web origin.

## Run the Next.js application locally

**Prerequisites:** Node.js 20+ (Node 22 recommended), npm, Git (optional).

```bash
npm install
npm run dev
```

Open http://localhost:3000 and explore the application.

**Build / production smoke test:**

```bash
npm run typecheck
npm run build
npm run start
```

If your dependencies have not yet been installed, the typecheck and Next.js build will not work. The supplied `scripts/check-project.cjs` performs an offline source/data sanity check in an environment with the TypeScript compiler installed globally. This sandbox did not have access to the npm package registry, so I could not complete `npm install` or verify a production Next.js build here. Please run `npm install && npm run build` on your laptop or CI before deployment.

### Offline content check

```bash
node scripts/check-project.cjs
```

`check-project.cjs` expects the global TypeScript installation used while developing this starter project. If that path differs on your computer, edit the import in `scripts/check-project.cjs`, or run `npx tsc --noEmit` after installing dependencies instead.

## Folder structure

```text
app/
  page.tsx                 Main entry page
  layout.tsx               Next.js layout and metadata
  globals.css              Theme, responsive components, animations
  icon.png                 Brand favicon
components/
  LearningPlatform.tsx     Interactive LMS UI and local learning state
data/
  curriculum.ts            Original offline/demo fallback and study plan
lib/
  lms-api.ts               Type-safe fetcher and Django API contract
backend/
  courses/                 Django models, admin, read-only API, seed command and tests
  config/                  Django settings and URLs
  content/                 Original AI course seed JSON
  requirements.txt         Python dependencies
  manage.py                Django CLI
public/
  brand/                   3 uploaded PNG logos + optimized WebPs
  preview/                 Dependency-free interactive preview
docs/
  DJANGO_CMS_SETUP.md       Start here for full-stack setup
  PRODUCTION_ARCHITECTURE.md
  DEPLOYMENT.md
scripts/
  generate-preview-data.cjs
  check-project.cjs
render.yaml                Render configuration
```

## Suggested next build order

1. **Core UX refinement and content:** review the designs, publish further Phase 1 lessons and add more assessments.
2. **Authentication:** secure registration/login, roles (admin, instructor, learner), reset links, account verification.
3. **Next LMS API layer:** extend existing Django + DRF models with enrolments, authenticated progress, notes, secure assessments and teacher roles.
4. **Next admin enhancements:** rich text/Markdown authoring, media uploads, lesson revisions and content version history. Plain-text sections and draft publishing already work.
5. **Secure product features:** subscription billing (only after deciding on a business model), audit logging, uploads, analytics, accessibility, monitoring and comprehensive automated tests.
6. **Production rollout:** release process, learner migration from demo state, backups and South African POPIA considerations.

## Growth package fit

The source was scoped as an **advanced branded website + interactive learning MVP**, aligned with the Growth package's emphasis on advanced web development, brand identity, SEO and engagement. A multi-user, subscription-enabled LMS is a substantially larger custom-platform scope and should be estimated separately rather than represented as included in a base Growth offering.

## Brand usage

The three supplied logos are included untouched as:

- `saire-pcb.png` — circuit-heart logo with original SAIRE-Linked name.
- `saire-symbol.png` — clean circular icon.
- `saire-horizontal.png` — horizontal icon-and-wordmark composition.

Their optimised `.webp` counterparts are used in the application for faster loading. The site is visually based on SAIRE-Linked's blue/green brand language; individual spacing/typography choices are newly designed for this product, not claimed to be exact source-code copies of the existing website.

© 2026 SAIRE-Linked — All rights reserved by the brand owner.


## Content protection prototype (v3)
See `docs/CONTENT_PROTECTION.md`. Print/save restrictions are **deterrents only**; screenshot blocking and secure subscription content are NOT implemented.
