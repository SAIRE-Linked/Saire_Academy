# Independent grading worker

Run from the **project root** as `python -m grading_worker --once`. Requires a separate Linux host and Docker. The only automatically graded assignment in v5 is `saire-quotation-engine`; trusted test suites are mapped by assignment slug in `runner.py`.

The worker uses the GitHub REST API to verify the exact submitted commit, downloads a bounded ZIP, rejects unsafe archive members, then executes trusted tests under a highly restricted Docker invocation with no network. The output includes only test counts and bounded output. It has no Django ORM, no database connection and never receives a learner API token.

Operational installation, threats and test commands: `docs/PROOFLOOP_V5_GRADING.md`.
