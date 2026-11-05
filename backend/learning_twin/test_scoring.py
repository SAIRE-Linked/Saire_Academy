"""Offline scoring tests: python -m unittest learning_twin.test_scoring (from backend/)."""
import unittest
from .scoring import summarise_skill, suggest_skills


class SkillScoringTests(unittest.TestCase):
    def row(self, slug, score, weight=1, dimension='tests'):
        return {'assignment_slug': slug, 'score': score, 'weight': weight, 'dimension': dimension}

    def test_unassessed_not_misrepresented_as_zero(self):
        r = summarise_skill([], 'Quotation Engine')
        self.assertIsNone(r['score'])
        self.assertEqual(r['status'], 'not_assessed')
        self.assertEqual(r['projects_count'], 0)
        self.assertIn('Quotation Engine', r['next_action'])

    def test_weighted_evidence_and_distinct_project_count(self):
        r = summarise_skill([self.row('a', 85, 3), self.row('a', 45, 1, 'defence'), self.row('b', 75, 2)])
        self.assertEqual(r['score'], 75)
        self.assertEqual(r['projects_count'], 2)
        self.assertEqual(r['evidence_count'], 3)
        self.assertEqual(r['evidence_strength'], 'growing')

    def test_score_uses_round_half_up(self):
        r = summarise_skill([self.row('a', 80), self.row('b', 81)])
        self.assertEqual(r['score'], 81)

    def test_lowest_metric_drives_guided_action(self):
        r = summarise_skill([self.row('a', 85), self.row('a', 45, dimension='defence')])
        self.assertEqual(r['status'], 'developing')
        self.assertIn('Explain', r['next_action'])

    def test_recommendations_prioritise_gaps_then_unassessed(self):
        skills = [
            {'slug': 'b', 'name': 'B', 'score': None, 'position': 2, 'next_assignment': 'Next', 'next_action': 'Start Next'},
            {'slug': 'a', 'name': 'A', 'score': 55, 'position': 1, 'next_assignment': 'Now', 'next_action': 'Practice'},
            {'slug': 'c', 'name': 'C', 'score': 90, 'position': 3, 'next_assignment': 'Now', 'next_action': 'Stretch'},
        ]
        self.assertEqual([r['skill_slug'] for r in suggest_skills(skills)], ['a', 'b', 'c'])


if __name__ == '__main__':
    unittest.main()
