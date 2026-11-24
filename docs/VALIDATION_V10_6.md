# v10.6 validation

Tested 10 November 2026 against an isolated copy of the latest local Documents/Saire_Academy source. Live source, accounts, database and private media were not changed. Browser tests used a separate SQLite fixture with ordinary learner accounts.

## Automated checks

- Django: 121 tests pass (including five session logout tests covering private-route denial, POST-only logout, real CSRF enforcement, CLI token preservation and account isolation).
- Django migration check: no changes detected. No migration or seed is needed for this release.
- Next.js production build passes, including type validation. Existing CSS autoprefixer warnings about start/end alignment remain non-blocking.
- `node scripts/test-practice.cjs`: passes runtime message validation, opaque-frame policy, code/output limits, worker termination, stdin/stdout handling, lazy loading and account-control rendering.
- `node scripts/test-browser-session.cjs`: passes authenticated and expired-session logout, failure handling, cross-tab signalling and listener cleanup.
- `node scripts/test-classroom-gate.cjs`: existing classroom access regression checks pass.
- `npm run check:content`: existing content/syntax/offline preview checks pass.

## Browser checks

Real bundled Pyodide, rather than mocked output, executed Python in the classroom: hello-world, arithmetic, input(), literal HTML text, Python exceptions, output truncation and clean variables between runs. Endless loops stopped after ten seconds; manual Stop retained the code. A practice request to an Academy API endpoint was blocked by the frame's runtime-only connection policy. Lesson navigation and the existing learner deadline remained visible. The runtime initially failed with module workers in the isolated frame; the delivered version uses the successfully tested classic worker mode.

Manual Stop followed by a successful edited-program run also passed on the final build. A browser reload restored the account/lesson draft. The visible header logout returned both the current pathways tab and an open classroom tab to the signed-out page with Google and GitHub choices; the private lesson disappeared, and opening the dashboard again returned to the sign-in page.

Neither Google/GitHub credential exchange nor live Gemini/external grading infrastructure was revalidated; these integrations are preserved. Browser practice does not create a score, complete a lesson, review a project or change a deadline. Desktop-editor use is a course rule; the platform cannot prove which editor a learner used.

## Delivery checks

The packager verifies published-runtime per-file checksums, ZIP CRC/content hashes, guarded compatibility/apply/repeat behavior, conflict rejection with zero writes, and exact binary Git patch application on separate baseline copies. It aborts if the inspected live source changed. Secrets, databases, learner media, dependency/build caches and obsolete runtime experiments are excluded. The generated release-check JSON reports the actual packaging results.

## Operational limits

The practice runtime is optional and approximately 12.3 MB before compression/cache effects. Extra packages, desktop apps, multi-file workspaces and cloud draft sync are outside this release. Drafts are browser-local and account/lesson scoped; shared-device users should download needed work and clear site data when appropriate. The ten-second stop is not a hard memory quota. Keep graded submissions in the existing grading worker.
