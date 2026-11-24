import type { ClassroomEntry } from '@/lib/lms-api';

export default function ClassroomGate({entry, lessonCount, onRoadmap}: {
  entry?: ClassroomEntry; lessonCount: number; onRoadmap: () => void;
}) {
  const locked = lessonCount > 0;
  return <article className="lesson-article empty-course classroom-gate" aria-labelledby="classroom-gate-title">
    <h2 id="classroom-gate-title">{entry?.title ?? (locked ? 'Your lessons are locked by module requirements' : 'This course has no published lessons yet')}</h2>
    <p>{entry?.message ?? (locked ? 'The lessons are present. Complete the required earlier module and its reviewed final project to open them.' : 'Detailed lessons still need to be published for this course.')}</p>
    {locked && <p>{lessonCount} published {lessonCount === 1 ? 'lesson' : 'lessons'} in this course. Opening a prerequisite classroom does not start a timer; a timer starts only when you choose Start lesson.</p>}
    {!!entry?.requirements.length && <div className="study-panel">
      <h3>Required modules, in order</h3>
      <ol>{entry.requirements.map(required => <li key={required.module_id}>{required.title}</li>)}</ol>
    </div>}
    <div className="classroom-gate-actions">
      {entry?.action && <a className="btn btn-primary" href={entry.action.href}>{entry.action.label}</a>}
      <button className="btn btn-outline" onClick={onRoadmap}>View roadmap</button>
    </div>
  </article>;
}
