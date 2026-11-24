# Applying v9 to an existing merged v8 project

If you already merged the v8 project into your own local repository, **commit or back up your working tree first**. The full v9 ZIP is a complete independent checkpoint; do not overwrite any files containing local changes without reviewing the diff.

You can use the companion `SAIRE_Academy_v8_to_v9.patch` file if your local repository is at (or very close to) the original v8 checkpoint.

From the root of your local Git repository:

```bash
git status
git apply --check /path/to/SAIRE_Academy_v8_to_v9.patch
git apply /path/to/SAIRE_Academy_v8_to_v9.patch
```

On Windows PowerShell, the path may look like `C:\Users\<user>\Downloads\SAIRE_Academy_v8_to_v9.patch`. If `git apply --check` fails, stop and compare the changed files manually; do not use a forced patch. Keep your own local edits to the dashboard, grading worker, content and deployment settings.

Main changed paths: `backend/mentoring/{api.py,provider.py,tests.py,test_provider.py}`, `backend/config/settings.py`, `backend/requirements.txt`, `backend/.env.example`, `app/assignments/{page.tsx,proofloop.css}`, `compose.yaml`, `README.md`, and new v9 documentation.

**Do not copy credentials between archives or put API keys into Git.** The `backend/.env` file must be created locally after rotating any exposed credential, and it is excluded from Git.
