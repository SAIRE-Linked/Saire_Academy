import { ArrowRight, BookOpen, Clock3, Flag } from 'lucide-react';
import { count, timeframe } from '@/lib/academy-display';
import type { LiveClassroom } from './LiveLearningPlatform';
import DashboardMentor from './DashboardMentor';

const displayDate = (value: string) => new Date(value).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'});

export default function DashboardWorkspace({live, openLesson, roadmap}: {live: LiveClassroom; openLesson: (id: string) => void; roadmap: () => void}) {
  const {course, iterations} = live;
  const available = course.lessons.filter(lesson => !lesson.locked);
  const active = available.filter(lesson => ['active', 'supplementary'].includes(iterations[lesson.id]?.status));
  const next = active[0] ?? available.find(lesson => iterations[lesson.id]?.status !== 'passed');
  const passed = course.lessons.filter(lesson => iterations[lesson.id]?.status === 'passed').length;
  const authored = new Set(course.lessons.map(lesson => lesson.phaseId)).size;
  const finals = course.phases.flatMap(module => module.progress?.final_project ? [{...module.progress.final_project, unlocked: module.progress.project_unlocked}] : []);
  const projects = live.projects.filter(attempt => finals.some(project => project.slug === attempt.assignment));
  const current = projects.find(attempt => finals.some(project => project.slug === attempt.assignment && project.unlocked && project.status !== 'passed'));
  const projectTitle = (slug: string) => finals.find(project => project.slug === slug)?.title ?? slug;
  const needsOrientation = !live.admin && !live.orientation.acknowledged;
  const deadlines = active.map(lesson => ({name: lesson.title, date: iterations[lesson.id].supplementary_due_at || iterations[lesson.id].due_at}))
    .concat(projects.filter(project => !project.submissions.length).map(project => ({name: projectTitle(project.assignment), date: project.due_at})))
    .sort((a,b) => Date.parse(a.date) - Date.parse(b.date));
  return <div className="workspace-layout"><div className="workspace-main">
    <header className="workspace-heading"><p>Learner dashboard</p><h1>Welcome back, {live.username}.</h1></header>
    <section className="workspace-focus"><BookOpen aria-hidden="true"/><p>{course.title}</p>
      <h2>{needsOrientation ? 'Get ready for your first lesson' : next?.title ?? (passed && passed === course.lessons.length ? 'Your lessons are complete' : 'Explore your course roadmap')}</h2>
      {needsOrientation ? <a className="btn btn-primary" href={'/dashboard/?view=academy&section=handbook&course=' + encodeURIComponent(course.slug)}>Open the handbook <ArrowRight size={16}/></a> :
        <button className="btn btn-primary" onClick={() => next ? openLesson(next.id) : roadmap()}>{next ? active.length ? 'Resume lesson' : 'Open classroom' : 'View roadmap'} <ArrowRight size={16}/></button>}
    </section>
    <section className="workspace-panel"><h2>Course progress</h2>
      <p>{passed} of {count(course.lessons.length, 'published lesson')} passed</p>
      <progress aria-label="Published lessons passed" value={passed} max={course.lessons.length || 1}/>
      <p>{count(authored, 'module')} with lessons · {count(course.phases.length - authored, 'outline')} · {timeframe(course.estimated_months)}</p>
      <button className="link-button" onClick={roadmap}>View course roadmap →</button>
    </section>
    <section className="workspace-panel"><h2><Clock3 size={19}/> Deadlines</h2>{deadlines.length ? <ul>{deadlines.map(item =>
      <li key={item.name + item.date}><strong>{item.name}</strong><time dateTime={item.date}>{displayDate(item.date)}</time></li>)}</ul> : <p>No active deadlines in this course.</p>}</section>
    <section className="workspace-panel"><h2><Flag size={19}/> Project reviews</h2>{projects.length ? <ul>{projects.map(project =>
      <li key={project.assignment}><a href={'/assignments/?assignment=' + encodeURIComponent(project.assignment)}>{projectTitle(project.assignment)}</a>
        <span>{finals.find(final => final.slug === project.assignment)?.status.replaceAll('_', ' ')}</span></li>)}</ul> : <p>Your first project attempt will appear here after you start it.</p>}</section>
    <a className="link-button" href="/pathways/">Browse learning pathways →</a>
  </div><DashboardMentor key={current?.assignment ?? course.slug} assignment={current?.assignment} title={current && projectTitle(current.assignment)} lesson={next?.title}/></div>;
}
