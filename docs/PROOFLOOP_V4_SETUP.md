# SAIRE ProofLoop v4 — first working assignment cycle

**What we built:** A learner can sign in, start an original assignment, download a starter ZIP, build and run public unit tests locally, submit an exact pushed Git commit, and see an instructor's graded code review. Course content remains Django-managed. Next.js adds a `/assignments` workspace; a Python `saire` CLI offers terminal-based workflows.

**Not yet implemented:** independent secure automated grading (the test score is manually entered by an instructor); server-verification of GitHub repository ownership/commit; GitHub App automated repository provisioning; self-service registration; cloud-secure code execution; graded AI Code Defence; multi-learner enrolment management. Local tests are **self-reported and untrusted**, and they do not determine an official grade. Do not use v4 for a public high-stakes exam.

## Phase A — Start Django locally (Windows PowerShell)

From the extracted project root:

```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_curriculum
python manage.py seed_proofloop
python manage.py createsuperuser
python manage.py runserver
```

The `seed_curriculum` and `seed_proofloop` commands **do not overwrite** existing entries edited in Django Admin. `seed_proofloop` creates the SAIRE Quotation Engine, links it to Phase 1 of the AI Engineering course, and stores an original starter ZIP in Django's **private media** directory.

## Phase B — Start the frontend

Open a second terminal in the project root:

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

- Academy: `http://localhost:3000`
- **ProofLoop lab:** `http://localhost:3000/assignments`
- Django Admin: `http://127.0.0.1:8000/admin/`
- Public assignment list: `http://127.0.0.1:8000/api/v1/assignments/`

## Phase C — Prepare a test learner

In Django Admin, use **Authentication and Authorization → Users → Add**. Create an ordinary active learner, e.g. `pilot_student`. Do not tick *Staff status* or *Superuser*. Log in to the ProofLoop lab as the learner, select Quotation Engine, and click **Start project**. The deadline is permanently recorded as 7 days after the first start. Download the starter ZIP.

Instructor/admin can view assignment attempts and submissions, but **cannot change learner assignment start dates or submission records through the default admin screens**.

## Phase D — Install and use the CLI

In a terminal with Python installed, from the repository root:

```powershell
python -m pip install -e ./tools
saire login --server http://127.0.0.1:8000/api/v1
saire list
saire start saire-quotation-engine
cd saire-quotation-engine
saire test
```

The starter tests **initially fail** (`NotImplementedError`) until you implement `src/quotation.py`. Solve the assignment independently; then run `saire test` again.

To create a **private repository in your own GitHub account**, install GitHub's official `gh` CLI and authenticate via `gh auth login`. You can run `saire start saire-quotation-engine --github` from a fresh directory to provision the repository automatically. Alternatively, from the already downloaded project folder, run GitHub CLI yourself:

```powershell
git init
git add .
git commit -m "Start quotation engine"
gh repo create my-quotation-engine --private --source . --push
```

Then implement, test, commit and push:

```powershell
saire test
git add .
git commit -m "Implement quotation calculations"
git push
saire submit saire-quotation-engine
saire grade saire-quotation-engine
```

`saire submit` checks that HEAD has been pushed to the remote and records its SHA. **It does not verify that the submitted code passes a secure grading suite.** A learner's self-reported test results are marked unverified in API responses. `saire grade` shows “Review pending” until an instructor assesses the submission.

To sign out/revoke the local token: `saire logout`. For this pilot, a single DRF token is shared by all client sessions of the same learner; logging out from any one session revokes that token everywhere.

## Phase E — Instructor grading

Go to Django Admin → **ProofLoop assessments → Code reviews → Add**. Select the specific submission SHA. Review the student's GitHub repository at **that exact commit**, manually verify test results in your approved environment, conduct a five-question code defence, and enter:

- Verified test score: **0–100**
- Five review answers: **0–10 each**
- Code quality score: **0–100**
- Feedback and constructive next steps

Django calculates and saves:

`final = verified_tests * 0.50 + (sum_of_five_question_scores / 50 * 100) * 0.30 + code_quality * 0.10 + deadline_component * 0.10`

The deadline component starts at 100 and loses 20 points for each **started** 24-hour period past the deadline. Therefore, even a late submission may retain most of its total marks. Instructors should publish extensions/appeals and configure accommodations before real use. Existing attempts keep their original due dates even if assignment duration changes.

After saving the review, the student's latest submission changes from **pending_review** to **reviewed**. Refresh `/assignments` or run `saire grade saire-quotation-engine` to see the feedback.

## Instructor checklist

1. Django migrates and both seed commands succeed.
2. Anonymous users see the published assignment but cannot start, submit or download starter ZIP.
3. Learner A can start twice without moving their deadline.
4. Learner B cannot read Learner A's attempt or submissions.
5. The starter ZIP is downloadable after start and contains only our original files.
6. The CLI runs visible tests without running anything on the Django server.
7. The learner pushes a real commit to GitHub and submits its SHA.
8. Instructor records a review; the learner sees the score and feedback.
9. A new course or project in Django Admin can be linked to future assignments without rewriting the API.

## Security & production boundaries

- HTTPS is mandatory for remote CLI credentials. Django uses the built-in DRF token endpoint in this **pilot**; tokens are stored in a private local config file, and browser tokens are held in memory only. The API login endpoint has a basic per-IP rate limit. Use an identity provider / short-lived tokens, stricter brute-force prevention, account recovery, email verification, and audit logging before production.
- `starter_bundle` is stored in `backend/private_media` and served only by an authenticated Django view to a learner who has started the assignment. Do **not** publicly expose that folder with Nginx, object-storage public URLs, static hosting, or CDN rules.
- `Submission.repository_url` and `commit_sha` are validated but **not independently verified by GitHub**. Instructors must confirm the repository owner, permissions and actual commit before grading. Do not trust user-provided `local_tests_*` data.
- Do not execute student-submitted Python from Django, Celery sharing the same trust boundary, the Next.js server or the host's production account. A later dedicated ephemeral worker must enforce network isolation, timeouts, resource ceilings, read-only base images, no secrets, no Docker socket and strict access to student content. Even container isolation alone is insufficient for highly adversarial workloads.
- Publishing private student repositories requires GitHub authorisation. `--github` uses the **student's authenticated GitHub CLI on their computer**, not a server-side GitHub App. Instructors need explicit repository access for manual reviews.
- Prohibit uploading third-party student repos or institutional assessment materials without sufficient permission. The starter is independently authored for SAIRE Academy.

## Local checks

```powershell
python manage.py test courses assessments
python manage.py makemigrations --check --dry-run
npm run typecheck
npm run build
python -m unittest discover -s tools/tests -v
```

The project is delivered without installed Python or Node dependencies. In a restricted tool environment, syntax and standalone CLI safety checks may run but the full Django/Next.js suites cannot. Always run the commands above on your machine or CI before deployment.

**Next engineering batch:** GitHub App + verified repository ownership, separate secure worker executing instructor-controlled hidden tests, review workflow/audit logs, and basic enrolment permissions. Then extend ProofLoop with a Socratic AI Mentor without revealing hidden test cases.
