# SAIRE academic curriculum blueprint — editable working edition

Release: v10.5, 9 November 2026. Status: first usable original slice plus a multi-phase authoring plan. This independent BSc IT-inspired pathway does not award or claim an accredited degree.

## Verified base and scope

The development base is the working source found at `Documents/Saire_Academy`, copied into a separate workspace on 9 November. It includes the v10.4 beginner foundations, earlier v10 OAuth/dashboard/deadline work and the user's additional local files and TypeScript settings. No live source or live database was changed during development. This is an additive continuation of that local state, not a return to v9/v10.

Two public pathways reference canonical Django modules. AI Engineering retains its existing course. Computing and IT reuses its Python foundation, then adds two original Year 1 modules and a Year 2 relational-data sample. A shared module has one lesson history, one final project and one set of evidence regardless of which pathway displays it.

### What is usable now

| Unit | Released teaching | Original assessed project | Gate |
|---|---|---|---|
| Shared Python foundation | Existing four lessons and Python setup lab, preserved | Existing SAIRE Quotation Engine, preserved | First lesson initially available after orientation/setup |
| Information systems in practice | From a request to a system; Validation that explains itself | Service intake validator | Shared Python lessons and reviewed final pass |
| Data and process reliability | A workflow is a set of promises; Reports that preserve their evidence | Workflow ledger | Intake lessons and reviewed final pass |
| Relational data design: a first slice | A table with rules; Queries with safe values and clear results | Lending records database | Workflow module complete, which also requires intake and shared Python |

There are **six new complete lesson bodies**, three untimed preparatory labs, twelve new graded quiz questions, twelve formative practice questions, five new glossary definitions and three project starter/suite pairs. The IT pathway displays ten lessons including the four shared existing lessons. Its other **17 units are outlines**, with original planned outcomes, preparation briefs, project ideas, resource links and a content backlog. An outline is not a released course.

Each new lesson follows explain → demonstrate → guided exercise → independent exercise → check understanding. Examples use invented repair, shelf, parcel and lending records. They introduce the collection and database concepts needed by the practical projects. Learners write implementations; the platform does not award project credit for reading, a self-reported CLI result or Mentor conversation.

The small Year 2 sample is deliberately reachable after the two completed Year 1 practical modules. It does **not** certify completion of all Year 1 subjects. Outlines do not create a false requirement to complete unavailable material. Before releasing a full Year 2 programme, author and enforce its full prerequisites.

## Source inventory and limits

The referenced collection is described as 21 unique guides plus two textbooks. The tools expose **six unique guides** through ten distinct filenames: four filename pairs have identical SHA-256 hashes. These are Mathematics 512 (90 pages), Web Technology 512 (153), Information Systems 512 (169), Networks 512 (114), Data Science 500 (82) and Programming 512 (108): **716 PDF pages** in total. All pages were text-extracted locally; contents, chapter headings and explicit learning outcomes were reviewed to map topic scope. The blank extracted Information Systems page 169 was visually confirmed blank. Selected title/contents pages were also checked visually. This is a topic/outcome coverage audit, not a line-by-line factual certification of every source claim or diagram.

The other **15 guides and two textbooks are unavailable** here. Their records say `missing`; no chapters, authors, editions or learning outcomes are invented for them. Provisional labels use 511/512/500 for Year 1 and 621/622/600 for Year 2 per the latest request. Source verification may revise these labels. The unspecified textbooks are not the books merely cited inside an available guide.

An additional local file called `IS 621.pdf` was inspected and excluded: it is an eight-page 2019 examination, not a study guide. No questions, answers or assessment structures from it are used. Unrelated local assignment documents are also excluded.

Internal records and the editable [coverage matrix](Source_Coverage_Matrix.csv) retain institutional attribution, source fingerprints, PDF page spans, independently paraphrased topic groups, target units and remaining gaps. The matrix has 40 topic groups from available guides and 17 pending-source entries. Five topic groups have a **partial** original practical overlap; none is claimed fully covered. The programme is not aligned to 21 full courses yet.

### Audit findings that affect authoring

- Data Science 500's cover and contents identify data science; its inner title page incorrectly names Programming 511. Keep one guide, record the inconsistency and verify against the institution before treating it as official metadata.
- Programming 512 contains five major groups: collections, mappings/sets, OOP, Tkinter and SQLite. Its printed page numbering restarts near the database section, so the matrix uses PDF pages. GUI outcomes repeat OOP wording; author fresh, observable GUI outcomes.
- Information Systems 512 contains seven chapters, including emerging technologies. The filename says 2025 while body headers say Year 1 2024. The practical workflow slice covers only a small part of software/data and organisational-process topics.
- Web Technology 512 includes legacy scripting conventions. Future lessons should use current JavaScript and accessible form/DOM practices, and explain server-side validation.
- Networks 512 includes classful IPv4 and future mobile-network claims. Teach CIDR and IPv6 using current primary references; identify historical models and forecasts explicitly.
- Mathematics 512 requires independently checked limit/tangent explanations; a tangent need not avoid crossing a curve. Author fresh graphs and examples.

No guide PDFs, extracted passages, diagrams, exercises, examination material or textbook content are included in public routes or learner downloads. Internal provenance models are registered only in Django Admin. Public resource links go to independent official/reliable references. This release contains original teaching and original assessment contracts rather than rewritten source exercises.

## Sequencing and grade rules

Django decides access from published canonical modules, saved lesson passes and reviewed final scores. A browser flag, URL change or local-storage value cannot unlock content. Within a course, modules follow their saved position, and lessons follow position then primary key. Every earlier module must have all released lessons passed and its designated reviewed final project passed. If a final is missing, the next module remains locked. Cross-course `ModulePrerequisite` records add the shared Python/IT/Year 2 gates. Admin validation rejects same-course edges and course cycles; the runtime also fails closed on imported cycles. Only active superusers have unrestricted testing access; ordinary staff accounts do not bypass gates.

Pathway order is a recommended study map, not a second conflicting grade system. The current enforceable route is shared Python → intake → workflow → relational sample. Later subjects stay outlines until authoring/review is complete. The proposed full-program prerequisites in `Curriculum_Backlog.csv` are **planning recommendations**, not automatically installed gates.

| Rule | Current behaviour | Configuration |
|---|---|---|
| Orientation | Current version acknowledgment required before new graded starts | `SAIRE_ORIENTATION_VERSION`; bump after material Handbook changes |
| Setup | Published required checklist and current revision required for a new start; setup does not start a clock | ModuleGuide required flag/revision and setup steps |
| Lesson iteration | 14 elapsed days from the first server-recorded start; retries do not reset it | Existing policy constants, preserved |
| Missed lesson deadline | At or after due time, primary attempt fails | Server clock, timezone-aware datetimes |
| Supplement | One supplementary window, ending at original due time + 7 days; joining late does not move its end | New attempts snapshot `SAIRE_SUPPLEMENTARY_GRADE_CAP`, default 70% |
| Supplement mark | Raw passing quiz result can complete the lesson; credited score is capped | Saved attempt cap; raw and credited scores are separate |
| Lesson pass | Default ceiling of 75% of questions; both questions required in each new two-question quiz | Lesson.passing_score is a question count, not a percentage |
| New project deadline | 14 days from its own first assignment start; separate from the lesson clock | Assignment.duration_days; existing quotation project retains its current duration (seed default 7 days) |
| Final project pass | Reviewed final score at least 70% in new projects | Assignment.module_pass_score; existing policy remains editable |
| Project rubric | 50% verified correctness, 30% five-question defence, 10% quality, 10% deadline | Existing CodeReview calculation; weights are code policy, not an environment setting |
| Project lateness | Default 20 percentage points off the deadline component for each started late 24-hour period, minimum zero; other components preserved | Assignment.late_penalty_per_day; no automatic project supplementary timer |
| Mentor | Existing authenticated practice, 8/hour and 40/day limits; optional provider and explicit Twin context opt-in | Existing provider/environment and throttling configuration |

Project correctness is established by instructor-verified evidence or a completed approved independent worker run. The five-question defence and quality still need instructor review. A submission awaiting review does not unlock the next module. A reviewed result below the pass threshold does not unlock it; learners may revise and submit a new pushed commit through the existing workflow. Learning Twin maps observed rubric evidence to skills; it does not certify mastery from reading or infer scores for unassessed outline units.

Academic integrity: write your own implementation, cite external help, explain the exact submitted commit and do not submit another person's work. Use the Socratic Mentor for hints and reasoning, not as official grading evidence. For an outage, technical problem or accessibility accommodation, contact the configured instructor/support channel promptly with the time and reproducible symptom. Staff handle exceptions individually under the existing policy. Automated extension approvals, a formal accommodation case queue and automatic project resit policies remain future work; this batch does not promise them.

## Content phases and acceptance gates

| Phase | Scope | Exit evidence |
|---|---|---|
| A — current release | Shared Python + intake + workflow + relational sample | Six complete new lessons, three projects/suites, migration, Admin, discovery and progression tests |
| B — verify missing inputs | Obtain 15 guides and two identified textbooks, de-duplicate, audit chapter/outcome/prerequisites | Complete private provenance; confirmed codes/years/editions; revised matrix with no invented source coverage |
| C — remaining Year 1 foundations | Web 511, maths 511, networks 511, full Python 512 | Original setup and lesson sequences, accessible worked examples, formative/graded checks, reviewed project and trusted suite per released module |
| D — Year 1 consolidation | Full IS512 breadth, Web512, Maths512, Networks512, DS500 | All 40 audited topic groups addressed or explicitly excluded with justification; outcomes mapped to original evidence |
| E — Year 2 core | PR621/622, IP621/622, IS621/622, full DB600 | Source-verified scope, multi-table design, transactions, application integration, full prerequisite graph and independent reviews |
| F — Year 2 specialisation | Cloud600, ML600, Big Data/IoT600; links into existing AI pathway | Reproducible synthetic workloads, responsible use, costs/failure analysis, original capstones and current references |
| G — operational refinement | Revision reminders, broader accessibility QA, support workflows and delivery evidence | Real user feedback, measured outcomes, privacy/retention policy and deployment validation |

The editable [content backlog](Curriculum_Backlog.csv) gives every remaining planned unit a prerequisite proposal, setup brief, planned topic, original final project concept, skill tags, official reference and definition of done. It includes completion work for partially authored IS511/IS512/DB600. Do not create learner-facing course-completion claims from this plan.

## Skill taxonomy and assessment design

Current projects add rubric mappings for input validation, systems thinking, state modelling, evidence reasoning, relational integrity, parameterised SQL and readable code. Correctness comes from tests; explanation/reasoning from defence; maintainability from quality. These mappings reuse the existing Twin schema and provenance rules. No synthetic scores or certificate claims are added.

Future tags in the backlog cover numeracy/algebra/calculus, HTML/CSS/accessibility, JavaScript/events/forms, network models/CIDR/IPv6/security, collections/OOP/GUI/CRUD, data quality/statistics/visualisation/evaluation, algorithms/refactoring, HTTP/auth/permissions, requirements/design/usability, cloud/cost/recovery and telemetry/privacy/resilience. Add a real rubric mapping only when the corresponding original assessment exists and reviewers can justify what it observes.

Assessments should progress from a tiny worked example to a new guided task, then a different independent task and a project contract. Public tests teach the interface; additional instructor cases test the **same documented contract**. No hidden requirement may affect a mark. Keep source audit records private, create fresh datasets and original diagrams, and have an educator independently check explanations and answer keys before broader release.

## Authoring and operational documents

Use [the authoring guide](Authoring_Guide.md) for fields, publication and a module checklist. Follow [the upgrade guide](../PROOFLOOP_V10_5_ACADEMIC_PATHWAYS.md) to migrate and seed. Verification results are recorded in `Validation_v10_5.md`. The source matrix and JSON inventory are editable internal documents; do not publish them as guide-download routes.
