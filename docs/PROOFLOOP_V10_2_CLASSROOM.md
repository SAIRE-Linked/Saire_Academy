# ProofLoop v10.2 · Restored classroom

The signed-in dashboard uses the original v9 interface shown in the v10.1 demo. It includes Overview, Learning roadmap, My classroom, Project lab, Study planner and Resource library. The classroom loads the original published lesson text, code snippets, challenges and quizzes from Django. Use **Start learning**, choose **Start 14-day lesson**, then complete the knowledge check to continue. Notes and study plans are stored on this device per Academy account. Lesson completion and deadlines come from Django.

The public homepage and OAuth routes from v10.1 are the sign-in entry points. The dashboard is at `/dashboard/`. The separate `/demo/` route contains sample content.

## Upgrade from v10.1

Back up your project and database. Apply the patch from the project root or use the full ZIP. Keep your existing Django database, environment files and private media. Run the migration, then restart Django and Next.js. Rebuild Next.js first if you run a production build.

```powershell
git apply --check .\SAIRE_Academy_v10_1_to_v10_2.patch
git apply .\SAIRE_Academy_v10_1_to_v10_2.patch
cd backend
python manage.py migrate
```

The new migration supplies knowledge checks for the original foundation lessons 2–4 when those lessons have no instructor-authored checks or custom pass threshold. Existing lesson records, deadlines and submissions are retained. Fresh installs get the same checks when running `seed_curriculum`. If the database has no published course, run `python manage.py seed_curriculum`, then `python manage.py seed_proofloop` and `python manage.py seed_skills`.

The seeded first module has four self-paced lessons. Its Quotation Engine final project opens after all four pass. The next module still requires a passing final-project review, and the later v9 syllabus outlines require published lessons. Older browser-only completion does not award a Django pass. Use a superuser to preview all published lessons through the familiar classroom.

See the v10.1 guide for OAuth setup and project progression.
