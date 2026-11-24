# ProofLoop v10.1

The public homepage explains SAIRE-Linked Academy and offers Google, GitHub and pilot account sign-in. Both OAuth confirmation pages use the Academy design. The provider hosts its own consent screen. A successful sign-in opens `/dashboard/`, which brings together the live roadmap, project lab, Mentor, Learning Twin and links to the v9 study tools.

## Update your v10 installation

Back up your database, then apply the patch from your project root or merge the full source into a separate copy of your project. Keep your existing local environment settings, database and private media. The patch was prepared against the earlier ProofLoop v10 source ZIP.

```powershell
git apply --check .\SAIRE_Academy_v10_to_v10_1.patch
git apply .\SAIRE_Academy_v10_to_v10_1.patch
cd backend
python manage.py migrate
```

Run the Django and Next.js servers as before. If running a production build, rebuild and restart Next.js. For a fresh install or first-time OAuth setup, follow the [v10 setup guide](PROOFLOOP_V10_LEARNER_EXPERIENCE.md). Its OAuth credentials and callback paths still apply. Use the Next.js public origin when visiting the homepage or account pages so the shared stylesheet, session and callback routes are available.

## Module completion

1. Pass the module’s published lessons in order. Existing 14-day lesson windows and supplementary rules apply.
2. Open the designated final project in ProofLoop. Submit a commit for instructor review using the existing grading workflow.
3. A saved review at or above the assignment’s module pass mark completes the module. Django then unlocks the next published module. A pending review, a below-pass score or an optional assignment keeps the gate closed. Any passing review on the learner’s designated final project counts, including existing reviews on that assignment.

Migration `assessments.0003` designates the existing **SAIRE Quotation Engine** as module 1’s final project with a **70%** pass mark. It preserves attempts, submissions and reviews. Fresh seeds apply the same designation. In Django Admin, set **Module pass score** on one published assignment per module to designate its final project. Leave that field blank for optional assignments. The percentage sets the progression threshold and does not change how ProofLoop calculates the project grade.

The original v9 seed contains four live lessons and one graded assignment in module 1. Later module outlines are visible as syllabus previews. To offer a later module, publish its lessons and designate a published final assignment. A module with no published lessons or final project cannot be marked complete. Superusers keep their existing preview access. Study plans and sample activity remain local to the browser.

## Quick acceptance check

- Open the homepage signed out. Both configured providers should open the same Academy confirmation layout, then redirect through the provider to your dashboard.
- Sign in with a learner account. Module 1 should have a lesson available and later modules should show as locked.
- Complete the module’s lessons. The Quotation Engine should open in the project lab. Verify that a pending review or a below-pass mark leaves the next module locked.
- Record a passing instructor review. Refresh the dashboard. Module 1 should show as complete. A subsequent module with no published lessons will show as coming soon.
