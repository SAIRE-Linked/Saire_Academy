# SAIRE-Linked Digital Learning Platform

**Build Smarter. Learn Deeper.**

A custom-branded, responsive, interactive learning-management **MVP** for the AI Engineer & Agentic Systems Mastery Programme. Developed for SAIRE-Linked, using the uploaded SAIRE-Linked logo assets and a blue/green premium technology aesthetic.

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

This is a **working, frontend-first Growth-package MVP**, not a multi-user production LMS. **There is no login, backend database, payment processing, email automation, server-side progress storage, or actual Python execution sandbox yet.** Browser progress is not secure, private across shared devices, or synchronized across devices. The complete 12-phase **syllabus** is published, but only the first **four detailed lessons** have been authored in this initial build. Additional tutorials, quizzes, and project workbooks must be produced phase by phase. Do not advertise the other 68 topics as fully taught yet.

The larger SAIRE-Linked product vision includes a later authenticated LMS backend, course authoring and admin, enrolment, cross-device syncing, assessments, downloadable certificates, analytics and payment integrations. See `docs/PRODUCTION_ARCHITECTURE.md`.

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
  curriculum.ts            Phases, lessons, quizzes, projects, study plan, resources
public/
  brand/                   3 uploaded PNG logos + optimized WebPs
  preview/                 Dependency-free interactive preview
docs/
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
3. **Persistent LMS API:** Django + DRF + PostgreSQL, lessons, enrolments, progress, notes, assessments and teacher admin.
4. **Admin curriculum editor:** rich text, lesson revisions, unpublished drafts and content version history.
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
