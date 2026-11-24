# v10.5 validation record

Local checks performed on 9 November 2026, using a separate copy of the latest accessible working source. No live source/database was changed. This is a tested development batch, not a claim that external production services have been configured.

| Check | Result |
|---|---|
| Existing + new Django tests | 102 passed: courses, progression, assessments, Mentor, Learning Twin |
| Worker safety/integration unit tests | 9 passed, including each new assignment's expected file and server-selected suite |
| CLI safety tests | 4 passed |
| New instructor suites | 37 cases passed against independent local reference implementations: 11 intake, 14 workflow, 12 records |
| Negative suite checks | All starter stubs fail as expected; one deliberately broken reference per project is detected |
| New teaching examples | All six snippets execute successfully using the local Python interpreter |
| Django model/migration checks | No pending model changes; system check clean |
| Next.js typecheck | Passed |
| Existing content/offline-preview check | Passed |
| Next.js production build | Passed, all routes generated including `/pathways/` |
| Existing database upgrade | Read-only SQLite backup migrated and seeded successfully; all 453 existing rows across 43 tables preserved by comparing original column values |
| Browser smoke | Public discovery, search, authored-only filtering, shared completed credit, course query selection, orientation, setup and first new lesson start confirmed using fictional test fixtures |
| Narrow-screen layout | Single-column cards and no horizontal document overflow observed at a 375px client width |

The 115 Django/worker/CLI tests include unchanged regression coverage. New integration tests exercise private source metadata omission, read-only discovery, shared credit without duplicate iterations, no learner-to-learner credit transfer, no unlock from self-reported local results, cross-course lesson/project denial, required orientation/setup, untimed preparation, aware 14-day dates, final-review gates, Year 2 access, superuser-only preview, safe seed reruns after edits/reordering, cycle validation/runtime fail-closed behaviour, draft hiding and complete new lesson structure.

Project suite checks run only our authored references/stubs locally. They do not substitute for a live Docker/GitHub deployment test. Reference solutions are private development checks and are not included in learner starters or this source package. Public starter tests intentionally fail until a learner supplies an implementation.

Browser tests used an isolated fictional learner, with shared Python completion supplied as test-fixture data. The learner had no superuser bypass. Handbook acknowledgment, checklist confirmation and the first new iteration were then exercised through the UI. These are test records, not real learner marks. The saved pathway screenshot shows fixture progress and is only a UI preview.

Existing CSS reports non-fatal autoprefixer warnings about `start`/`end` alignment values on a clean build. The Django test environment reports a missing collected static-files directory; deployment still needs `collectstatic`. Next.js normalises generated TypeScript configuration during builds; the original user-local `next-env.d.ts` and `tsconfig.json` are restored in the source deliverable, and a typecheck is run against them.

Not verified here: real GitHub/Google OAuth credential exchange, live Gemini/OpenAI requests, actual GitHub commit/repository authorisation, Docker sandbox execution and production PostgreSQL concurrency/deployment. Existing tests cover contracts and permissions locally; configure and validate those external services before a public release.

Source audit limit: six unique guides (716 pages) were available. The audit maps their 40 chapter/topic groups, with five partial practical overlaps and the rest explicitly backlog. Fifteen guides and two textbooks remain missing; full 21-course alignment is not claimed. No source PDF/text/diagram/exercise or original examination material is included in public content.

The release packaging check verifies that the full ZIP and patch exclude secrets, databases, generated dependencies, private media and original guides, and that the nine identified local customization files are retained byte-for-byte. The guarded updater checks all affected checksums before writing. Both it and the patch were applied to clean baseline copies and compared with the release source. The guarded updater also passed a repeat-run check; a simulated later local edit caused a complete stop with zero writes. Git patch comparison used `core.autocrlf=false` for byte-exact verification; a user's normal Git configuration may choose different line endings without changing the text.
