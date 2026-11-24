# saire-workflow-ledger

Original SAIRE project using invented data. The exact function contract is below and in `src/workflow.py`.

```python
def transition(current, target):
    """Both inputs must be str. Allowed: new->assigned, assigned->closed, closed->new.
    Return target for an allowed move. All others raise ValueError (including
    unknown, non-text, or identical states). No automatic correction.
    """
    raise NotImplementedError("Implement this contract")

def summary(records):
    """records must be a list of dicts with a status in new/assigned/closed.
    Extra dictionary keys are allowed. Return all three counts as a fresh dict.
    Empty list returns zero counts. Missing/invalid states, non-dict elements,
    non-text status and non-list input raise ValueError. Never mutate records.
    """
    raise NotImplementedError("Implement this contract")
```

Implement the functions; keep the names, arguments and specified outputs/errors.
Use only the Python standard library. Add your own tests, including boundary and invalid cases.
Do not use real personal data or a production database.

Run from this project folder: `python -m unittest discover -s tests -v`.
The initial tests fail until you implement the functions; this is expected.
Local tests are practice evidence, never verified marks. Instructor suites include additional cases from this contract.

Start through the authenticated Academy after completing the required lessons.
The server starts a 14-day **project** deadline when you start this assignment.
Lesson iterations have a separate 14-day deadline and 7-day capped supplementary policy.
There is no automatic project supplementary timer in this batch.
Commit and push to GitHub, then use the existing ProofLoop CLI to submit the exact SHA.
Complete the five-question code defence and wait for instructor review.
Grading: 50% verified correctness, 30% defence, 10% quality, 10% deadline. Pass threshold: 70%, editable by an administrator.
GitHub repository authorisation and the isolated grading worker require instructor/deployment setup.
