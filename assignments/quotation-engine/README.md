# SAIRE-Linked Academy: Quotation Engine (Original Starter Assignment)

**Course:** Programming Fundamentals · **Phase:** 1 · **Estimated working time:** 5–8 hours  
**Learning outcomes:** functions, inputs, decimal arithmetic, validation, unit testing, documentation.

## Your mission

A small digital services business needs a reusable way to calculate quotations. Implement the missing functions in `src/quotation.py` without changing the public function signatures. **Do not hardcode example outputs.**

- Accept package price and additional service charge as non-negative `Decimal` values.
- Accept discounts as percentages from 0 through 100 inclusive.
- Reject invalid values with `ValueError`.
- Use decimal arithmetic and round monetary results to cents using `ROUND_HALF_UP`.
- Implement `calculate_subtotal`, `calculate_discount`, and `calculate_final_total`.
- Keep functions small, explain your assumptions, and write at least two additional edge-case tests.

## Run locally

```powershell
cd assignments/quotation-engine
python -m unittest discover -s tests -v
```

**Expected starter state:** tests initially fail with `NotImplementedError`. That is intentional; your work is to make them pass. The tests in this ZIP are learner-visible examples and not secure hidden grading tests.

## Submission evidence (planned Academy flow)

When GitHub assignment provisioning is implemented, a submission will record a specific commit hash and the timestamp. For now, save your work in a separate Git repository and share a commit when reviewing with your mentor. Do not submit personal secrets or third-party code.

## Code review (5 questions, 0–10 each)

1. Why did you choose Decimal rather than float for money calculations?
2. Explain how you validate the amount and discount range; demonstrate one rejected input.
3. What is the difference between a subtotal and a final total in your implementation?
4. Which edge case was hardest to test, and why?
5. A client wants stacked discounts; which design choices would you revisit first?

**Example rubric:** automated correctness 50%, explanation 30%, test quality 10%, deadline compliance 10%. This is a proposal, not an enforced platform scoring policy. Instructors set deadlines and accommodations.

**Copyright:** This assignment description and starter template were newly authored for SAIRE-Linked Academy. They do not incorporate old institution-owned source code.
