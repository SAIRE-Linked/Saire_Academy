"""Pure, independently testable evidence aggregation and next-step selection.

An observed score is a weighted average of *mapped rubric results*, NOT an AI
estimate of intelligence, future success, or a validated psychometric measure.
"""
from decimal import Decimal, ROUND_HALF_UP

DIMENSION_LABELS = {
    'tests': 'Verified tests',
    'defence': 'Instructor code defence',
    'quality': 'Instructor code quality',
}
ACTIONS = {
    'tests': 'Try a new edge case, write a regression test, and trace the input to the output before changing your code.',
    'defence': 'Explain one important function aloud: its inputs, choices, failure cases, and the reason behind your design.',
    'quality': 'Review naming, function responsibilities, error handling, and duplication; refactor one area while keeping tests green.',
}


def summarise_skill(evidence, next_assignment=None):
    """Return transparent evidence summary. Items must have scores 0–100 and weight 1–5."""
    if not evidence:
        prompt = (f"Start {next_assignment} to create your first assessment evidence."
                  if next_assignment else 'No mapped assessment has been reviewed yet; ask your instructor which challenge measures this skill.')
        return dict(score=None, status='not_assessed', evidence_strength='none',
                    evidence_count=0, projects_count=0, next_action=prompt)
    numerator = sum(Decimal(str(row['score'])) * Decimal(row['weight']) for row in evidence)
    denominator = sum(Decimal(row['weight']) for row in evidence)
    observed_score = int((numerator / denominator).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    projects = len({row['assignment_slug'] for row in evidence})
    source = min(evidence, key=lambda item: (item['score'], item['weight']))['dimension']
    strength = 'initial' if projects == 1 else ('growing' if projects <= 3 else 'repeated')
    status = 'needs_practice' if observed_score < 60 else ('developing' if observed_score < 80 else 'strong_evidence')
    return dict(score=observed_score, status=status, evidence_strength=strength,
                evidence_count=len(evidence), projects_count=projects, next_action=ACTIONS[source])


def suggest_skills(skills, limit=3):
    """Prioritise practice needs, then unassessed skills with mapped assignments."""
    needs_practice = sorted((s for s in skills if s['score'] is not None and s['score'] < 80), key=lambda s: (s['score'], s['position']))
    unassessed = [s for s in skills if s['score'] is None and s.get('next_assignment')]
    stronger = sorted((s for s in skills if s['score'] is not None and s['score'] >= 80), key=lambda s: s['position'])
    return [dict(skill_slug=s['slug'], skill_name=s['name'], action=s['next_action'],
                 reason=('Needs practice' if s['score'] is not None and s['score'] < 60 else 'Build further evidence' if s['score'] is None else 'Keep developing'))
            for s in (needs_practice + unassessed + stronger)[:limit]]
