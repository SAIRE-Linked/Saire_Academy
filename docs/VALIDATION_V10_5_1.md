# v10.5.1 classroom fix validation

Checked locally on 10 November 2026 against an isolated copy of the latest accessible working project. The working source, accounts, marks and database were not modified.

- **116 Django tests passed**, including 14 new classroom-entry regression tests and the existing 102 tests for curriculum, academic pathways, progression, OAuth/session behaviour, assessments, Mentor and Learning Twin.
- **Four frontend rendering scenarios passed** using `node scripts/test-classroom-gate.cjs`: required foundation link, genuinely empty course, fallback for an older API and pending project review.
- TypeScript checking, the existing content/offline-preview check and the Next.js production build passed.
- Django system check passed; `makemigrations --check --dry-run` found no model changes. No migration or seed command is required for this fix.
- Browser verification used a normal fictional learner (no superuser bypass) in a separate database snapshot. IT foundations showed its four published/locked lessons, the shared foundation explanation and a working link to the real Python classroom. The requested lesson title, preparation control and separate start button were visible after following the link. Opening these views did not create an attempt.
- The final browser screenshot shows test data and the existing dashboard style with the new prerequisite panel. It does not show real learner grades or prove a live OAuth exchange.

Backend regressions cover fresh learners, Year 2 prerequisite chains, partially completed foundations, another learner's completed marks, final projects, pending review, reviewed scores below/above the pass threshold, shared-module wording, anonymous requests, true empty courses, unpublished requirements, imported cycles and unrestricted superuser preview. Canonical lesson/project permission checks remain authoritative.

The guarded upgrade is checked against the captured local file hashes before writing. Release packaging verifies clean check/apply, a repeat run, conflict rejection with zero writes, Git patch application and ZIP integrity. Git byte-for-byte comparison uses `core.autocrlf=false`; a user's normal Git settings may choose different line endings while preserving the text. Generated dependencies, environment secrets, databases, private media and original guides are excluded from the deliverables. Existing local TypeScript configuration is restored after build verification.

External OAuth, Gemini/OpenAI and deployed Docker/GitHub worker services were not reconfigured or called for this UI/navigation fix. Existing non-fatal CSS compatibility warnings and missing collected static-files directory warnings may still appear in a development test environment. The latter is handled by the existing production collectstatic setup.
