# Original curriculum authoring guide

## Models and ownership

`LearningPathway` holds the discovery title, description, disclaimer and publication flag. Its `PathwayUnit` rows reference existing canonical modules; position/year/scope/shared are editorial metadata. The public readiness label is derived from published lesson availability. Keep `scope` candid about the actual released slice. Do not publish empty placeholder lessons to make an outline look authored.

`Course` owns canonical module order. `Module.curriculum_key` is a stable internal seed identity, not a learner-facing code. Seeded new modules retain their identity when renamed or reordered. Existing AI modules are unchanged. `ModulePrerequisite` adds a cross-course required module; completion means lessons and reviewed designated final pass. Same-course order already applies. Cycles are rejected. Test a proposed dependency graph using an ordinary learner, not just the unrestricted superuser.

The private `SourceReference` and inline `SourceCoverage` models contain bibliographic metadata, hashes and independently paraphrased topic/outcome gaps. There is no file-upload or learner API for the study guides. Record authors/editions only after inspection. Missing inputs remain marked missing. Page spans use one-based PDF pages. Add no copied passages, diagrams, exercises or test material.

## Publish one module

1. Write an original purpose and measurable outcomes. Confirm prerequisite knowledge and a realistic workload. A BSc IT-inspired unit is not an accredited university course.
2. Create a ModuleGuide with plain-language introduction/outcomes and SetupStep rows with exact commands and observable verification. Set `required_setup` only when the checklist is complete. Increment guide revision after material setup changes. Setup confirmation is self-report, not a verified skill result.
3. Write each Lesson with stable public_id and ordered sections: explain, demonstrate, guided exercise, independent exercise, check understanding. Provide a short original analogy and its limits. Include code a beginner can run. Define unfamiliar terms in the glossary.
4. Add LessonGuide fields for optional extra explanation and the same teaching sequence. The existing interface supports both guide and section views; keep them consistent. New sample data lives in `courses/academic_content.py` and is deliberately duplicated into the relevant authoring models at first seed.
5. Add graded QuizQuestion rows and separate FormativeQuestion practice rows. Check every option and answer key. Default graded pass is ceiling(75% of question count), unless `passing_score` specifies an explicit count. Two questions therefore require both. Formative results do not replace graded completion.
6. Publish only complete lessons. Add HTTPS LearningResource rows with a purpose and an official/reliable source. Confirm the URL manually, note the check date in your editorial record and recheck during future releases. Optional resources must not hide required paid material.
7. Author an original Project and Assignment with an exact function/output/error contract, learning outcomes, five defence questions, public tests, independent grading suite and private starter bundle. `module_pass_score` designates the one final assignment; the database allows only one designated final per module. Set its duration/late policy deliberately.
8. Add the assignment slug and expected source filename to the worker's server-controlled allowlists. Never execute submitted code in Django. Deploy the suite on the separately configured worker. Verify a correct reference, missing/invalid inputs and intentionally broken solutions. Do not publish a full project solution as learner starter code.
9. Map real rubric dimensions to existing/new Learning Twin skills via AssignmentSkill. Explain the limited observation represented by each mapping. Reading and AI conversation do not become assessed evidence.
10. Update the source coverage matrix and backlog. Mark a source topic only partially covered when this is accurate. Keep outline scope labels until the complete planned material is actually authored. Verify keyboard operation, text-first reading and an ordinary learner's locked/unlocked routes before publication.

## Reusable preparation template

- What does this language/tool do, and why does this module use it?
- What is already required? Link to the earlier canonical module, rather than duplicating its marks.
- Which official runtime/editor/extension is needed on Windows? Offer a viable instructor-supported alternative when installation is inaccessible.
- What exact terminal command checks the environment, and what output indicates success?
- What first harmless program/query can the learner run using invented data?
- Which common setup failures should they recognise? Where can they request help?
- Confirm explicitly that setup does not start the 14-day lesson clock.

The released shared Python lab retains the authored Windows installation/download guidance from v10.4. The new labs build on it. The relational sample checks `sqlite3` locally and uses in-memory data; it requires no cloud account or separately running database server.

## Seed and editing policy

Run `seed_academic_pathways` explicitly after migrations; migrations do not silently publish a curriculum. The seed uses create-if-missing operations, never updates/deletes existing rows, and authors lesson children only when creating their module. Existing field edits survive repeated runs, including module names and positions. Missing mapping/outcome records may be recreated; deliberate deletions are not a durable way to customise a rerun. Keep a database backup, and edit/publish in Admin after first seed. Reserved new course slugs are `it-foundations` and `it-data-systems`; resolve pre-existing unrelated slug/position collisions before seeding.

Outline plans are in `courses/academic_backlog.py`; the editable planning artifacts are in this folder. Changing those files does not update a live edited database. Make a reviewed content migration or explicit import for later revisions rather than changing old migrations or overwriting instructor edits.

## Accessibility and learning support

Keep essentials as text/code, with labelled controls, readable errors, visible focus and natural keyboard order. Add meaningful alternate descriptions for independently drawn diagrams. Use non-timed setup, short practice steps, optional extra explanation and saved notes. State whether an achievement is self-reported or reviewed. Existing text-first mode and replayable tour remain available.

Staff handle accommodations and technical-problem exceptions individually. Do not promise an automatic extension, automatic reminder or adaptive intervention that is not implemented. Preserve timezone-aware server dates and record an exception's reason through an agreed staff process. A future formal support queue needs its own design and review.
