# ProofLoop v10.3 · Code Defence Room

Open **Project lab** and select a project you have unlocked. Start the project, then submit a pushed GitHub commit from the lab or the CLI. Under **Your submissions**, select **Open Code Defence Room** beside the commit you want to explain.

- Answer the five assignment questions. Use the exact implementation, a specific test, and a trade-off where relevant.
- Select **Save draft** to resume later from your account. The questions are saved with the draft so an instructor edit cannot change which question an answer addresses. Reload the saved copy if another tab has changed it.
- Select **Hand in defence**, then **Confirm hand-in**. Your explanations become read-only and available on the submission record in Django Admin. A different commit gets a separate room.
- Instructors can open **Assessments → Submissions**, read the handed-in answers and start or open a Code Review from that record. The existing five rubric marks, independently verified tests, code quality and deadline calculations still determine the official grade. The final project unlocks the next module after a passing instructor review.

## Optional practice

The room includes a guided checklist that works locally. When the existing Gemini or OpenAI Mentor provider is configured, **Generate practice question** sends the assignment title and learning outcomes to that provider. **Get practice feedback** sends the selected practice question and the separate practice answer only after the learner checks the consent box for that request. Feedback describes what was explained, what evidence is missing, and what to practise next. Practice responses stay in the current browser view and do not contribute to instructor marks or Learning Twin evidence.

## Upgrade from v10.2

Back up your existing project and database. Apply the patch from the project root or use the complete ZIP. Keep your database, private media and local environment settings.

```powershell
git apply --check .\SAIRE_Academy_v10_2_to_v10_3.patch
git apply .\SAIRE_Academy_v10_2_to_v10_3.patch
cd backend
python manage.py migrate
```

Restart Django and Next.js. Rebuild Next.js first if you run a production build. Migration `assessments.0004` adds the defence record table. Existing submissions and official reviews remain available. A commit that was already reviewed can be opened as read-only. This batch does not require a written defence for an instructor to record an existing or independently conducted review.
