from django.core.management.base import BaseCommand
from progression.models import LessonIteration
from progression.services import expire


class Command(BaseCommand):
    help = 'Materialise expired iterations. Schedule every minute; request-time checks still enforce deadlines.'

    def handle(self, *args, **kwargs):
        for iteration in LessonIteration.objects.filter(status__in=['active', 'failed', 'supplementary']).iterator():
            expire(iteration)
        self.stdout.write('Iteration deadlines checked.')
