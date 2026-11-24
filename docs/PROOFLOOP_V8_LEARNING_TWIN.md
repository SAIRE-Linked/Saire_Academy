# ProofLoop v8 — SAIRE Learning Twin (pilot)

This is the first **evidence-backed skills profile** for SAIRE-Linked Academy. It extends the v7 Django + Next.js project without changing the original curriculum, Socratic Mentor, CLI, submissions, or separate grading worker.

> The Learning Twin is **not** an intelligence score, employment predictor, psychometric test, certificate, or a black-box AI judgement. It summarises what mapped project rubrics have actually observed, and labels missing evidence as **not assessed**.

## Start v8 locally (Windows PowerShell)

Extract the **entire v8 ZIP**, open the extracted folder in VS Code, and use two terminals. You can follow the v5/v7 setup guides for the original complete stack. The new commands are added here.

**Terminal A — Django:**

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_curriculum
python manage.py seed_proofloop
python manage.py seed_skills
python manage.py createsuperuser
python manage.py runserver
```

Skip `createsuperuser` if you already have an administrator. On an existing database, `migrate` adds the two v8 tables without deleting previous courses or submissions. The three seed commands are designed not to overwrite existing instructor edits.

**Terminal B — Next.js (from project root):**

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000/assignments**, sign in with a learner account, and scroll to **SAIRE Learning Twin**. The Academy sidebar also has a direct Learning Twin link.

### Django Admin

Open **http://127.0.0.1:8000/admin/** and find **Learning Twin · Evidence and skills**.

- **Skills:** original competencies, explanations, categories, ordering and active status.
- **Assignment skill mappings:** connect a published project to the rubric dimension that genuinely measures the skill.
- Mapping dimensions: **Verified test results**, **Instructor code defence**, **Instructor code quality**.
- The optional weight (1–5) controls how strongly that piece of evidence contributes. The same project may support multiple skills, but a skill/project/dimension combination is unique.

Newly created project mappings become visible immediately through the existing Django API. You don't need to edit React code to add or remove a skill.

## Data flow

```
Learner completes and submits a project
        ↓
Instructor approves repo / independent worker tests it
        ↓
Instructor completes CodeReview in Django Admin
        ↓
Learning Twin reads latest reviewed submission per project
        ↓
Mapped rubric dimensions → observed skill results
        ↓
Learner sees provenance + recommended next practice
```

The Learning Twin does **not** read learner-reported test counts (`Submission.local_tests_passed`, etc.) and never reads AI mentor messages, hidden grader suites, repository code, grades belonging to other learners, or private instructor notes.

### What counts as evidence?

| Evidence field | Score | Provenance in profile |
|---|---:|---|
| Independently graded tests | `GradingJob.verified_test_score` (0–100), when a completed run has a verified commit | `independent_grader` |
| Instructor-reviewed tests | `CodeReview.verified_test_score` (0–100) if independent grading is not available | `instructor_review` |
| Instructor code defence | Sum of five instructor question scores (0–10 each) × 2 | `instructor_review` |
| Code quality | Instructor code-quality score (0–100) | `instructor_review` |

**Only reviewed submissions create profile evidence**. An instructor should not enter a manual test score until they have checked it themselves. An independent grading run by itself is not yet enough; this first version only publishes evidence after the instructor review.

For each skill, the **observed performance score** is a weighted average of its mapped rubric results, rounded to a whole percent. We use at most **one latest reviewed submission per assignment**, so resubmitting the same assignment ten times cannot count as ten independent projects. The panel shows the actual rubric entries, assessment provenance, partial Git commit, number of distinct projects, and whether the evidence is initial/growing/repeated.

A skill with no reviewed/mapped evidence has **no score**, not 0%. No inference about mastery, motivation, learning disability or intelligence is made from missing results.

### Recommendations

A simple, inspectable recommendation function prioritises low observed scores first, then unassessed skills with published assignments, then stretch practice. Recommendations are suggestions, not formal grades. The first seed creates six original skills; five are connected to the original Quotation Engine project. Debugging deliberately remains **not assessed** until a suitable challenge is introduced.

## HTTP endpoint

`GET /api/v1/learning-twin/me/` — requires Django Token authentication or a valid authenticated Django session. The user is derived from `request.user`, not from a supplied student ID. `POST` is not supported.

Example:

```bash
curl -H "Authorization: Token YOUR_DEV_TOKEN" http://127.0.0.1:8000/api/v1/learning-twin/me/
```

Do not paste real tokens into public bug reports or commit them to Git.

## Minimum pilot walkthrough

1. Run migrations and `seed_skills`. Confirm six skills and five mappings in Django Admin.
2. Create one learner and one instructor account (or reuse existing accounts).
3. Learner starts **SAIRE Quotation Engine** on `/assignments` and submits a pushed commit.
4. Independently verify the student's code and test score, then add a five-question `CodeReview` in Django Admin (or run the separate grading worker as described in v5).
5. Click **Refresh evidence** in the Learning Twin. Confirm that skills mapped to the reviewed project show results, a source, and a commit reference.
6. Confirm that a second learner cannot view the first learner's evidence. A new learner should see *not assessed* throughout.
7. Change a skill mapping or complete an improved submission/review, refresh, and confirm the profile reflects the new evidence without resetting the existing course.

## Checks

Offline, no installed Django required:

```bash
cd backend
python -m unittest learning_twin.test_scoring mentoring.test_provider -v
cd ..
node scripts/check-project.cjs
PYTHONPATH=tools python -m unittest discover -s tools/tests -v
python -m unittest discover -s grading_worker/tests -v
```

On your actual development computer, additionally run:

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test learning_twin assessments mentoring courses
cd ..
npm run typecheck
npm run build
```

The latter framework/database checks **were not run in the preparation environment**. Neither live PostgreSQL/Django verification nor a real AI request has been verified here. Do not deploy to paying learners without these checks and a security review.

## What v8 intentionally does not do

- It does not guess learner intelligence or ability from LLM chat.
- It does not copy data from other students or automatically share public profiles.
- It does not evaluate code on the Django server.
- It does not yet adapt the actual Socratic Mentor prompt to the skill profile (proposed v9).
- It does not persist lesson completion to the Django learner account; the older course UI still uses local browser progress.
- It is not a validated psychometric assessment system. Scores are transparently derived instructor/project rubrics, which may need calibration and fairness audits.

## Next safe milestone

After end-to-end verification, build a **learner-consented Learning Twin → Mentor integration**, limited to aggregated skill gaps and strengths. Keep instructor rubrics, hidden tests, other learners' data and API credentials out of model context.
