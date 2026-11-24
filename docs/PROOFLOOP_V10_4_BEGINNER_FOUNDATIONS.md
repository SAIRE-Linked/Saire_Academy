# ProofLoop v10.4 · Beginner Foundations

This batch builds on the verified v10.3 Code Defence Room source. It adds a Study Hub inside the signed-in v9-style dashboard and extends the live Django classroom with beginner teaching guides. Existing account, deadline, project, Mentor, Learning Twin and assessment records carry forward.

## Upgrade an existing v10.3 installation

Back up your project and database. Apply the patch in the v10.3 project root, or use the complete source ZIP. Keep your database, private media and local environment files.

```powershell
git apply --check .\SAIRE_Academy_v10_3_to_v10_4.patch
git apply .\SAIRE_Academy_v10_3_to_v10_4.patch
cd backend
python manage.py migrate
```

Restart Django and Next.js. Rebuild Next.js first if you serve a production build. The courses and progression migrations add the authoring and private study tables. The content migration adds the first Python lab, four lesson guides, practice checks and official references to the seeded course. It leaves existing lesson bodies, questions, marks, submissions and authored guide fields intact. A fresh installation receives the same content from `seed_curriculum`.

Optional Django environment settings:

- `SAIRE_ORIENTATION_VERSION` defaults to `2026-11-v1`. Increase or change it after a material Handbook revision so new starts require a new acknowledgment.
- `SAIRE_SUPPORT_EMAIL` displays the Academy’s support contact. When unset, the Handbook directs learners to their instructor’s contact channel.
- `SAIRE_SUPPLEMENTARY_GRADE_CAP` is the existing setting, 70% by default. Existing attempts retain their saved cap. Assignment pass marks and project durations are edited in Django Admin.

The existing OAuth and Mentor credentials continue to use the v10 setup. See the setup guide shipped in the source ZIP for callback URLs and environment variables.

## Learner journey

1. Sign in and open the welcome tour in Study Hub. Skip or replay the tour whenever useful. Read the searchable Handbook and save a rules acknowledgment.
2. Open **Getting Ready** for the module. Read the outcomes and confirm the tool checklist. This step and the optional before check use no timed attempt.
3. Open **My classroom** and start the lesson when ready. Read the plain-language explanation, run the example, try the guided and independent exercises, and use the optional after check. The separate graded quiz completes the lesson under its existing rules.
4. Keep a private account notebook. Revision suggests revisiting missed after checks or a lesson passed at least three days ago. First program is earned by confirming the lab checklist. First reviewed challenge comes from a recorded instructor review.

Django enforces current orientation and the latest required module checklist for **new** lesson or project starts, including CLI project starts. Previously started work can resume on its existing deadline. Superusers retain test access. The initial four Python lessons have authored examples. Future modules have outcomes and a reusable setup template. An instructor can publish a module-specific lab before enabling its required checklist.

## Authoring and support

In Django Admin, use **Module guides** for outcomes, setup steps and verification labels. Publish the guide once its steps are ready. Increase its revision when learners should confirm the checklist again. Use **Lessons** for the five-part teaching sequence and separate formative questions. Use **Learning resources** for HTTPS links at module or lesson level, and **Glossary entries** for reusable definitions.

Text-first mode suppresses decorative classroom and dashboard elements. The guided tour uses buttons and announces each step. Formative checks use labelled choices with keyboard access. The lab and core examples are text and code; optional reading is linked out. Accommodation requests and deadline exceptions are handled directly by Academy staff. This release suggests revision from recorded evidence. Automated reminders, adaptive scheduling, an accommodations request queue and fully authored labs for later modules are outside this batch.

Official tool pages checked for the Python lab are the [Python Windows downloads](https://www.python.org/downloads/windows/), [Python on Windows guide](https://docs.python.org/3/using/windows.html), [VS Code downloads](https://code.visualstudio.com/download), [Microsoft Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Git for Windows](https://git-scm.com/install/windows).
