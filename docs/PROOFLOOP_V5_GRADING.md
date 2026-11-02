# SAIRE ProofLoop v5 — independent grading pilot

## Scope and security guarantees

This release extends the **original v4 full-stack LMS**, keeping Next.js animations, course CMS, Django Admin, learner CLI, and starter projects. It adds a distinct grading **queue + worker**, but does **not** claim production-grade hostile-code isolation or automatic ownership verification.

**Implemented in source**

- Submitting a commit creates exactly one `GradingJob` for that new submission. Initial state is `awaiting_approval`.
- A Django instructor independently confirms repository ownership/access and approves the selected job in Django Admin.
- A worker authenticated by a high-entropy shared secret claims one approved job; concurrent worker claims use a database compare-and-set update.
- Worker contacts GitHub's API to verify the exact 40-character commit SHA in the requested repository, downloads that immutable commit archive, validates and extracts the ZIP with explicit limits.
- The *separate* Linux worker invokes a Docker sandbox with no network, read-only base, dropped capabilities, unprivileged user, 256 MB memory, 1 CPU, 64 PID limit, 90-second default timeout, 16 MB temporary storage and a fixed instructor-written test suite.
- Worker reports trusted test counts and score; Django rejects mismatched counts/scores, fake leases and duplicate reports.
- Instructor conducts the five-question code defence, rates code quality, and publishes a final mark. For completed independent grading jobs, test score is taken **only from the worker record**, not from user input or instructor form entry.
- Learner dashboard and `saire grade` display the queue state and independent grading evidence.

**Still required for a public/high-stakes platform**

- Real GitHub App/OAuth linkage proving learner repository rights (v5 uses **manual instructor authorization**; a GitHub commit's existence is not ownership proof).
- Independent security assessment of the grading host, strong container/VM boundary and hardened seccomp/AppArmor/SELinux policy. Linux containers are not a total hostile-code sandbox. Operate on a separate disposable host/VM, never with production database or LMS secrets.
- GitHub App fine-grained credential rotation (v5 accepts a narrowly scoped worker-host `GITHUB_TOKEN` for private repositories).
- Secure test distribution, queue retry and idempotent result reconciliation, lease expiry/recovery audit, per-user quotas, alerts, event logging, privacy and appeal process.
- The instructor's tests are **not** included in the learner starter ZIP, but student code executing in the same container can potentially inspect mounted tests. Do not promise absolute secrecy of tests, or use this pilot for a high-stakes exam.
- No automated GitHub repository provisioning on the backend (the existing learner-side `gh` option remains).

## Setup A — Django and Next.js (Windows PowerShell)

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

In a second PowerShell window from the *project root*:

```powershell
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Dashboard: `http://localhost:3000/assignments` and Django Admin: `http://127.0.0.1:8000/admin/`.

Create an ordinary learner in Django Admin. Follow the v4 CLI guide to log in, `saire start saire-quotation-engine`, finish the exercise, push a GitHub repository and `saire submit saire-quotation-engine`. In this pilot, do not submit repositories containing secrets.

## Setup B — configure worker access

**Use a separate Linux VM for the worker.** Only that VM should have the Docker socket and an approved grading runtime image. The Django and Next.js machines should not have access to Docker or GitHub grading credentials. Require network isolation, VPN/private worker-to-Django HTTPS, firewall restrictions and dedicated non-root identities. Docker daemon access on the worker host is highly privileged; do not use a shared host.

Generate a random secret using Python:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Set the **same** value of `SAIRE_WORKER_SHARED_TOKEN` on the Django host and isolated worker. Set it as a *secret environment variable*, never commit it to Git. The API blocks worker access unless the secret has at least 32 characters. Make sure the `/api/v1/internal/grading/*` routes are only reachable over your private network. In the public-facing reverse proxy, deny external traffic to them. A shared token alone is not network isolation.

On the worker host (after installing Docker, loading a reviewed Python runtime image, and copying the project):

```bash
export SAIRE_WORKER_API_URL=https://your-private-django-host/api/v1
export SAIRE_WORKER_SHARED_TOKEN='your-unique-long-random-secret'
export GITHUB_TOKEN='fine-grained-read-access-token-for-learner-repositories'
# In production, pin a vetted image by digest rather than a mutable tag.
export SAIRE_GRADER_IMAGE='python:3.12-slim'
python -m grading_worker --once
# Or poll continuously when the host is deliberately provisioned for it:
python -m grading_worker --interval 10
```

The Docker image must be pre-pulled and verified on the host; the test container has no network. Public repositories may be accessible without `GITHUB_TOKEN`; private ones require access. The token is **never passed into the student container**. If no job exists, `--once` exits without grading anything.

For Windows-only pilot development, a Linux virtual machine or WSL2 with a dedicated Docker backend is required; the runner uses Linux-specific I/O and isolation assumptions. Do not point the grading runner at the production Django host.

## Instructor workflow

1. Navigate to Django Admin → **ProofLoop assessments → Grading jobs**.
2. Open the submission's exact repository/commit. Verify that the repository belongs to the expected learner, that the exact pushed SHA exists, and that the learner intentionally submitted it.
3. Select the job and run **Approve selected repositories and queue for isolated grading**. This manual step is essential until GitHub OAuth/App integration is implemented.
4. The worker claims it, fetches the immutable commit, runs the instructor-authored tests, and reports evidence to Django.
5. Refresh the job. `complete` means an independent score is available. `error` means verification/infrastructure did not complete; review the cause and only use **Requeue failed grading jobs** after fixing it. Running jobs are **not automatically retried**. After 15 minutes, an instructor may use **Mark stalled running jobs as errors**, investigate the worker, and explicitly requeue. Old lease tokens are invalidated.
6. Conduct the five-question code defence, then use **Code reviews → Add** to enter five question scores (0–10) and code quality (0–100). The test score field is overridden by the completed worker evidence on save; do not represent manually entered scores as independent results.
7. Learner refreshes `/assignments` or runs `saire grade saire-quotation-engine`.

**Final formula unchanged from v4:** independent tests 50%, code defence 30%, code quality 10%, deadline compliance 10%. Late penalties affect the deadline component only. Existing v4 reviews remain intact, with no grading job; these remain manually graded historical results.

## Verification commands

```bash
# From project root: run these source-level tests (Python standard library only)
PYTHONPATH=tools python -m unittest discover -s tools/tests -v
python -m unittest discover -s grading_worker/tests -v
python -m compileall -q backend grading_worker tools

# Run Django framework tests after installing requirements
cd backend
python manage.py test courses assessments
python manage.py makemigrations --check --dry-run

# From project root after npm install
npm run typecheck
npm run build
```

## Safety boundaries

This worker intentionally does **not** execute the Django `Assignment.test_command` field. Trusted suites are mapped by fixed server-side code (`SUITES`) to files distributed only with the grading service. Learner GitHub contents are always untrusted. Worker API access is authenticated and network-restricted; learner tokens cannot claim jobs or send test results. Do not load secrets into the runner container or mount the host Docker socket, `.ssh`, Docker credentials, GitHub tokens, backend API keys or production source.

For actual deployment, prefer a separate ephemeral VM per run, a locked-down container runtime, central security logging, and a full threat-model review. Until then, this release is a **testable prototype**, not a certified secure grading environment.
