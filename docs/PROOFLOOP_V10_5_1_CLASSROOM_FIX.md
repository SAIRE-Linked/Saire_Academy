# v10.5.1 — IT classroom prerequisite guidance

The previous classroom used “No lesson is available yet” whenever no lesson was currently unlocked. This was misleading for a new learner selecting an IT course: v10.5 has four published IT foundations lessons and two published database lessons, but they require the shared Python foundation and reviewed final projects. The same empty message hid both locked content and genuinely unpublished content.

This fix adds a server-generated classroom entry explanation and a direct link to the next required lesson or project. It follows the existing canonical module order and cross-course prerequisites, including the Year 2 → workflow → intake → shared Python chain. The link selects the appropriate course and exact lesson, rather than reopening an older saved lesson. Opening the classroom does not start an iteration; the learner still chooses the start button after orientation and setup.

It handles these states separately:

- Published lessons waiting on prerequisites: show the required modules and open the first available prerequisite lesson.
- Prerequisite lessons passed: open the required final project.
- Submitted final awaiting review: explain that review is pending and link to the submitted project.
- Actual course outline without lessons: state that content has not been published.
- Unpublished or inconsistent prerequisite configuration: ask for instructor attention without offering an unsafe unlock or a navigation loop.
- Active superuser: preserve unrestricted classroom preview. An ordinary Google/GitHub learner account remains subject to progression rules.

Only the shared Python **module** and its final project are required before IT foundations. The learner does not need to finish the whole AI Engineering course that currently contains that shared module. Its completion counts toward both pathways. The database sample also requires the intake and workflow modules with their reviewed finals. The 17 remaining IT outline units are not made into complete courses by this hotfix.

## Apply

This patch was prepared from the current local `Documents/Saire_Academy` source inspected on 10 November 2026. The original project and database were left unchanged during development.

Use the guarded upgrade ZIP for a source compatibility check and a backup of affected files. Extract it outside the Academy project, then run from its extracted folder:

```powershell
python apply_upgrade.py "C:\path\to\Saire_Academy" --check
python apply_upgrade.py "C:\path\to\Saire_Academy" --apply
```

Alternatively, from the Academy project root:

```powershell
git apply --check C:\path\to\SAIRE_Academy_v10_5_to_v10_5_1_Classroom_Fix.patch
git apply C:\path\to\SAIRE_Academy_v10_5_to_v10_5_1_Classroom_Fix.patch
```

Choose one upgrade method. Both check for conflicting edits; merge a conflict manually instead of replacing your current files. The full source ZIP is also supplied as a separate comparison/install folder. Keep your own environment files, database and private media.

Restart Django. Rebuild/restart Next.js (`npm run build`, then `npm run start`) or restart its development server. **No migration, reseeding, credential change or progress reset is required for this fix.** The change does not remove the shared foundation requirement, change deadlines or award any grades.

For unrestricted testing, sign into the browser with an actual Django superuser. Creating a superuser does not turn a separate Google/GitHub identity into that administrator. This fix does not automatically promote accounts or bypass permissions.

## Verification

Run the existing Django regression suite and the added `courses.test_classroom_entry` tests. Frontend regression checks can be run with `node scripts/test-classroom-gate.cjs`, followed by the existing typecheck/build. The checks cover fresh/partially completed learners, required finals, review pending, another learner's marks, empty content, anonymous access, unpublished requirements, imported cycles and admin preview. Validation results for this release are in `VALIDATION_V10_5_1.md`.
