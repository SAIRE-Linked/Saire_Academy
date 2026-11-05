"""Private learning conversations. Do not store hidden tests, grading secrets or code here."""
from django.conf import settings
from django.db import models


class MentorMessage(models.Model):
    LEARNER = 'learner'
    MENTOR = 'mentor'
    ROLES = ((LEARNER, 'Learner'), (MENTOR, 'Socratic Mentor'))

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saire_mentor_messages')
    assignment = models.ForeignKey('assessments.Assignment', on_delete=models.CASCADE, related_name='mentor_messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField(max_length=2400)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'pk')
        indexes = [models.Index(fields=('learner', 'assignment', 'created_at'), name='mentor_owner_history_idx')]

    def __str__(self):
        return f'{self.learner_id}/{self.assignment_id}/{self.role}'
