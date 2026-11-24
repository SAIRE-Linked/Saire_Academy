# SAIRE Academy V11 development notes

24 November 2026 · Based on the local v10.6 working tree

## Release scope

V11 updates the Next.js learner experience and two read APIs in Django. The public demo, assessed classroom, project submissions, instructor reviews, and Learning Twin continue to use their respective data sources. The 2D campus remains an optional future feature.

## From walkthrough to implementation

I reviewed the running homepage and demo at localhost:3000, then traced the dashboard route to LiveLearningPlatform and LearningPlatform. The older LearnerDashboard component is not mounted by that route. I took a working copy of the current source, including the local changes and untracked v10.6 components. Development and fixture tests used that copy.

| Reported issue | V11 change |
| --- | --- |
| The expense tracker opened the Pocket Garden Planner | The demo roadmap opens a project-specific expense tracker outline. The garden planner stays in the sample project lab. The live project page distinguishes assessed final projects from additional ideas and uses the assessment slug for its brief. An explicitly requested locked or unavailable project no longer silently selects another project. |
| Assignment cards omitted the number of days | The locked assignment summary includes the CMS duration. The client handles missing values from older servers. Locked records still exclude the brief and assessment questions. |
| Signed-out roadmaps returned to the homepage without explanation | The dashboard retains its path and query, and the sign-in panel explains the return journey. Pilot, Google and GitHub links carry the validated dashboard destination. |
| Curriculum availability was easy to miss | Pathways show published and outline counts before the filters. The dashboard and roadmap show coverage for the selected course. The published totals come from curriculum records, independently of the learner’s unlock state. |
| Singular counts used plural nouns | Updated project, lesson, question, term, week, module and other affected labels, including the sample roadmap. |
| The suggested timeframe had no unit | Numeric estimates and ranges display months. Existing descriptive or unit-bearing estimates retain their wording. |

## Navigation and learner workspace

One navigation component supplies the six agreed groups across the entry page, demo, learner workspace, pathways, and ProofLoop. Dashboard links preserve the course. The demo uses its own classroom and planner links. The existing mobile drawer and a compact menu on the public and lab pages expose the same destinations.

The dashboard prioritises a current or supplementary lesson, then an unlocked unfinished lesson. New learners can open the handbook. The course panel shows passed versus published lessons, the next panel lists lesson and unsubmitted project deadlines, and the review panel links to project records. Narrow layouts move the mentor below the main workspace.

The mentor panel uses the existing project conversation for an accessible, started final project. Sending a question requires an explicit action and the existing server configuration. The panel provides a study prompt when a conversation is unavailable. Learning Twin now applies project unlock rules to suggested assignments.

## Verification

| Check | Result |
| --- | --- |
| Next.js production build and TypeScript | Passed. All nine static pages generated. |
| Django test suite | 129 tests passed on an isolated test database. |
| Existing frontend regressions | Content and offline demo, classroom gates, Python practice protocol, session logout and cross-tab handling passed. |
| V11 component regressions | Counts and timeframe formats, allowed return destinations, six navigation groups, sample links, orientation, supplementary deadlines, empty states and project mentor eligibility passed. |
| Pilot sign-in | Django returned HTTP 302 to the exact requested course roadmap. The authenticated dashboard API then returned HTTP 200. |
| Seeded curriculum and assignment responses | Computing & IT returned 4 modules with lessons and 17 outlines. AI Engineering returned 1 and 11. Locked assignment durations were 7 or 14 days as configured. |

The original localhost site was available in the in-app browser. The V11 test server ran in an isolated workspace, but the browser connection timed out. Final pixel layout, mobile drawer interaction and a full signed-in browser walkthrough remain to be verified on the merged app. External OAuth callbacks, paid provider calls and external grading jobs were not exercised.

## Apply the patch

The patch is based on the **current local files**, including uncommitted v10.6 work. From the Academy repository, point Git at the downloaded patch.

```powershell
git apply --check "C:\path\to\SAIRE-Academy-V11.patch"
if ($LASTEXITCODE -eq 0) {
    git apply "C:\path\to\SAIRE-Academy-V11.patch"
}
```

A failed preflight identifies conflicting files before applying any changes. No package installation, database migration or production seed is required for V11. Restart the frontend and backend using the existing project setup.

To repeat the main release checks, run the following from the repository with its usual Node dependencies and Django environment active.

```powershell
npm run build
npm run check:content
node scripts/test-v11.cjs
node scripts/test-classroom-gate.cjs
node scripts/test-practice.cjs
node scripts/test-browser-session.cjs
Push-Location backend
python manage.py test
Pop-Location
```

For browser acceptance, follow a pathway roadmap while signed out, complete sign-in, then confirm the course and view. At desktop and mobile widths, use the Academy menu, resume a lesson, inspect a locked project, and open the mentor from an eligible project. Use a test learner for timed or graded actions.
