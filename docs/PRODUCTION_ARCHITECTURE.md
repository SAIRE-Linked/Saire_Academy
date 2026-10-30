> **Current checkpoint (Django CMS v2, 30 October 2026):** Course, module, topic, lesson, section, quiz and project models, read-only public APIs, Django Admin and initial seed import are implemented in `backend/`. Any references below to future backend implementation mean **learner account and authenticated LMS workflows**. Read `DJANGO_CMS_SETUP.md` for the implemented CMS.

# Architecture: From Growth MVP to Full SAIRE-Linked LMS

## Current MVP architecture

```text
Browser
  ↳ Next.js app (React + TypeScript)
      ↳ curriculum.ts (version-controlled learning data)
      ↳ classroom + roadmap + projects + study planner
      ↳ localStorage (progress, quiz score, private notes, schedule)
```

This is a client-side learning experience, not a secure multi-user LMS. There is no remote user account identity or protected content. The user interface is implemented in `components/LearningPlatform.tsx` and styled by `app/globals.css`. The dependency-free preview shares the same curriculum dataset through a generated JS file.

## Production architecture proposal

```text
Next.js frontend (learn.sairelinked.com)
  ↕ HTTPS API
Django + Django REST Framework (api.learning...)
  ├── identity: email verification, sessions, roles
  ├── catalog: courses, modules, lessons, publication states
  ├── learning: enrolment, progress, quizzes, attempts, notes
  ├── submissions: projects, feedback, rubrics
  ├── payments: optional subscription / payment integration
  └── operations: audit log, admin, analytics
  ↕
PostgreSQL (durable transactional store)
Object storage (files, learner submissions, thumbnails)
Background worker/queue (emails, reports, media processing)
Monitoring/logging + managed secret storage
```

### Suggested entities and constraints

| Entity | Core fields | Key behaviour |
|---|---|---|
| User | ID, email, verified, status | Unique verified email and secure password/session management |
| Role | admin/instructor/learner | Server-enforced authorization |
| Course | ID, title, slug, status | Draft, review and published states |
| Module | ID, course_id, order | Ordered phase grouping |
| Lesson | ID, module_id, slug, published_revision | Stable identity with versioned content |
| Enrollment | user_id, course_id, status, enrolled_at | Unique per user/course, server-owned |
| Progress | user_id, lesson_id, completed_at | Only record valid outcomes |
| Quiz | lesson_id, pass_mark, revision | Questions and answers under server control |
| QuizAttempt | user_id, quiz_revision, score, submitted_at | Score calculated on server; retain history |
| ProjectSubmission | user_id, project_id, object_path, status | Validate file types and ownership |
| StudyPlan | user_id, weekday, minutes | Per-user schedule |
| Note | user_id, lesson_id, encrypted_content | Access limited to the note owner |

### Suggested API routes (not implemented yet)

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/me
GET    /api/v1/courses
GET    /api/v1/courses/:slug
GET    /api/v1/lessons/:id
GET    /api/v1/me/progress
PUT    /api/v1/me/study-plan
PUT    /api/v1/me/lessons/:id/notes
POST   /api/v1/quiz-attempts
POST   /api/v1/project-submissions
GET    /api/v1/admin/analytics
```

### Authentication, security and privacy essentials

- Use a vetted authentication solution with secure, HttpOnly/SameSite cookies; do not store auth tokens in localStorage.
- Enforce server-side authorization on **every** protected endpoint. Never rely on a hidden button as access control.
- Quizzes need server-side scoring and attempt management, because browser code can be changed by users.
- Protect against SQL injection, unsafe uploads, XSS/CSRF, rate abuse, credential stuffing and broken object-level authorization.
- For any AI agents later integrated into the platform: require explicit tool permissions, tool validation, secrets isolation, prompt-injection defenses, tracing and human approval for sensitive actions.
- Design around data minimisation, consent/notice, retention, access and deletion rights, and the South African POPIA framework, taking qualified legal advice when appropriate.
- Provide encrypted backups, recovery tests, environment isolation, logging and automated deployment checks.

## Content publication system

All 12 phase syllabuses and project outlines are included now. Only four detailed Python tutorials are written. Next build should model lessons as revisions with title, outcomes, worked examples, exercises, quiz links, status, author, review timestamp and related project milestone. Do not automatically mark merely viewed topic outline items as completed lessons.

## Future optional AI-powered tutoring

A tutoring assistant can eventually explain code, generate hints, review submissions and recommend study materials, but it requires source-grounding, safety controls, cost limits and evaluation. Keep it separate from definitive grading and make clear when feedback is AI-generated. The present interface does **not** make calls to a large language model.
