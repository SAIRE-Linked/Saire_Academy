# v10.6 — account controls and Python practice

This release continues the latest working local project inspected on 10 November 2026, including the v10.5.1 classroom fix and user customizations. Development and browser tests use an isolated copy. The working project, database, credentials and deadlines have not been overwritten.

## What changes for learners

- A visible **Log out** button appears in the dashboard header. Home, pathway discovery and the project lab have account controls too. The sidebar retains its logout control.
- Logout ends the real Django browser session, redirects to the Academy sign-in card and shows Google, GitHub and the existing pilot-account sign-in route. An expired session can return to sign-in too; a connection/CSRF failure while still signed in is reported rather than displayed as a successful logout.
- Open dashboard/project/pathway tabs receive a local logout notification and leave the learning workspace. Restored dashboard pages revalidate the session. Django still decides whether each private request is allowed.
- Python lessons with Python-labelled examples gain an optional **Python practice studio** after the lesson is opened. Learners can edit code, run it, read output/errors, supply `input()` lines, stop a run, reset the example and download a `.py` file.
- Practice drafts are saved locally by account and lesson. They are not submitted to Django, the Mentor or the grading worker. Each run uses a fresh Python worker and a fresh variable namespace. Drafts remain on the device after logout; Reset example replaces the saved practice code. Local device storage is not a secure vault against other users of that device.

Practice is optional and ungraded. It does not start/reset an iteration, complete a lesson, earn a verified achievement, change Learning Twin evidence or unlock a module. Opening the protected lesson still follows the existing orientation, setup and 14-day iteration policy. Setup remains untimed. Existing 7-day supplementary windows and saved grade caps are unchanged.

## Local IDEs for final projects

The studio is for short experiments during lessons. End-of-module projects use the learner's local IDE/editor, local tests, Git and the existing ProofLoop submission of a pushed repository and exact commit SHA. There is no project-submit button in the practice studio. Instructor review and independent grading remain authoritative.

The platform can verify the submitted commit and assess its work; it cannot establish which editor produced a commit. The local-IDE requirement is the Academy's workflow policy, not a fabricated verified editor-use flag. Existing accessible-editor and accommodation arrangements remain available through the Academy.

## Runtime and isolation

The complete basic runtime is bundled under `public/python-runtime/v0.29.5/`. Normal use needs no external CDN request. The first load transfers about 12.3 MB of uncompressed runtime files from the Academy; browser caching can reduce later transfers. Nothing is loaded until the learner chooses Load Python or Run. Lessons remain readable without loading it. A fresh worker can still take time to initialise even when assets are cached; this is not a promise of instantaneous execution or a fully offline Academy.

The bundled Pyodide 0.29.5 distribution uses Python 3.13. This maintained release supports the classic worker mode used inside the opaque-origin iframe. Module workers failed in that isolated frame during browser testing, so the runner uses a tested classic worker instead. The files come from the official npm distribution and remain unmodified. The download was checked against its published SHA-512 integrity value. Per-file SHA-256 values and licence texts accompany the runtime.

Learner code is sent to the worker through structured messages, never interpolated into an HTML/script document. The iframe has `sandbox="allow-scripts"` without `allow-same-origin`, an unpredictable channel and source/origin checks. Its CSP allows only the pinned static runtime path for scripts/connections, rather than the Academy API or arbitrary external hosts. Output/error text is bounded and rendered as text. The worker is terminated after a result, on Stop, on lesson disposal/logout or after its execution timeout.

Limits: 20,000 code characters, 8,000 input characters, 16,000 output characters, a 90-second load timeout and 10 seconds for a running script. These are usability/resource safeguards, not a hard memory quota or a substitute for the dedicated hostile-submission grading environment. No learner code runs in Django. Basic Python is supported; desktop GUI tools and packages not included in the bundle require a local IDE. No automatic package installation is offered.

The narrow CORS/CORP headers added in `next.config.mjs` apply only to public runtime assets so the isolated frame can load them. They do not enable credentialed cross-origin API access. Existing OAuth callbacks, CSRF settings, server credentials and private API response headers are preserved.

## Upgrade

Use the guarded upgrade ZIP to merge into the working project. Keep its installer, manifest and `files` folder together. The supplied **Check upgrade.cmd** and **Apply upgrade.cmd** locate `apply_upgrade.py` relative to the launcher, avoiding the earlier problem of running it from `backend`. They default to `%USERPROFILE%\Documents\Saire_Academy` and use its existing Python environment when present. Check first, then apply after reading the result.

To run manually, open a terminal in the **extracted installer folder**, not `backend`:

```powershell
python .\apply_upgrade.py "C:\Users\tjroc\Documents\Saire_Academy" --check
python .\apply_upgrade.py "C:\Users\tjroc\Documents\Saire_Academy" --apply
```

Those commands use this user's verified project location. A different installation must use its actual project path. The guarded updater checks all affected hashes, backs up previous affected files and stops on conflicting edits. Do not force a conflict or replace your database. The complete project ZIP is also available as a separate comparison/install folder. The Git patch includes the runtime binary assets; the ZIP is usually more convenient.

**No migrations, reseeding, OAuth credential changes or new npm dependencies are required.** Rebuild and restart Next.js so its new runtime headers and client code are active. Stop the current frontend server first, then use:

```powershell
cd "C:\Users\tjroc\Documents\Saire_Academy"
npm run build
npm run start
```

For development, restart `npm run dev` instead. Keep the existing Django server running or restart it using the existing environment. The browser-session logout endpoint already exists in the working backend. The isolated grading worker needs no update for this batch.

## Authoring and later work

The studio uses a Python-labelled lesson section and prefers the authored guide's example where available. Give code blocks accurate language labels; SQL, shell and JavaScript blocks are not Python interpreters. Keep examples short, original and safe for a beginner. Required desktop/package setup still belongs in Getting Ready. Do not put proprietary course exercises, production data or credentials in starter examples.

This is a lightweight practice editor, not a full desktop IDE. Syntax highlighting, file trees, third-party package environments, cloud draft sync and additional languages are future work. Existing lesson notes, private mistakes notebook, quizzes, Mentor, Learning Twin, project code defence and CLI workflow remain available.

Technical references: [Pyodide releases](https://github.com/pyodide/pyodide/releases), [versioned Pyodide source](https://github.com/pyodide/pyodide/tree/0.29.5), [standard streams](https://pyodide.org/en/stable/usage/streams.html), [MDN iframe isolation](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe). These are optional engineering references; the lesson explanations remain original Academy content.
