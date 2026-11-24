'use client';

export type Lesson = {
  id: string;
  title: string;
  phaseId: number;
  locked: boolean;
  minutes: number;
};

export type Iteration = {
  status: string;
  due_at: string;
  supplementary_due_at: string | null;
  raw_score: number | null;
  credited_score: number | null;
  grade_cap: number;
};

type ModuleStatus = 'locked' | 'coming_soon' | 'lessons' | 'awaiting_project' | 'final_project' | 'completed' | 'admin_preview';
type ProjectStatus = 'ready' | 'awaiting_review' | 'needs_revision' | 'passed';

type Module = {
  id: number;
  name: string;
  desc: string;
  topics: string[];
  progress: {
    status: ModuleStatus;
    project_unlocked: boolean;
    final_project: { slug: string; title: string; pass_score: number; status: ProjectStatus } | null;
  };
};

export type Course = {
  slug: string;
  title: string;
  phases: Module[];
  lessons: Lesson[];
  projects: { id: string; name: string; phase: number; locked: boolean; description?: string }[];
};

const moduleLabels: Record<ModuleStatus, string> = {
  locked: 'Locked',
  coming_soon: 'Content coming soon',
  lessons: 'Lessons in progress',
  awaiting_project: 'Final project coming soon',
  final_project: 'Final project required',
  completed: 'Module complete',
  admin_preview: 'Admin preview',
};
const projectLabels: Record<ProjectStatus, string> = {
  ready: 'Ready to start',
  awaiting_review: 'Awaiting instructor review',
  needs_revision: 'Below the pass mark. Revise and submit another commit.',
  passed: 'Passed',
};

function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export default function ModuleRoadmap({ courses, iterations, busy, admin, onLessonAction }: {
  courses: Course[];
  iterations: Record<string, Iteration>;
  busy: boolean;
  admin: boolean;
  onLessonAction: (lesson: Lesson, action: 'open' | 'start' | 'supplement') => void;
}) {
  return (
    <div id="learning-roadmap">
      <h2>Learning roadmap</h2>
      {!courses.length && <p>No courses have been published yet.</p>}
      {courses.map(course => (
        <section key={course.slug} className="academy-card">
          <h2>{course.title}</h2>
          {course.phases.map(module => {
            const { status, final_project: final, project_unlocked: projectUnlocked } = module.progress;
            const lessons = course.lessons.filter(lesson => lesson.phaseId === module.id);
            const ideas = course.projects.filter(project => project.phase === module.id && !project.locked);
            return (
              <article className="academy-module" key={module.id}>
                <div className="academy-module-heading">
                  <h3>Module {module.id} · {module.name}</h3>
                  <span className="academy-module-status">{moduleLabels[status]}</span>
                </div>
                <p>{module.desc}</p>
                {status === 'locked' && <p>Complete the earlier modules and pass their final projects to unlock this module.</p>}
                {module.topics.length > 0 && (
                  <details>
                    <summary>View syllabus</summary>
                    <ul>{module.topics.map((topic, index) => <li key={index}>{topic}</li>)}</ul>
                  </details>
                )}
                {lessons.length > 0 && (
                  <ol className="academy-roadmap">
                    {lessons.map((lesson, index) => {
                      const iteration = iterations[lesson.id];
                      const open = admin || Boolean(iteration);
                      const statusLabel = lesson.locked ? 'Locked' : iteration?.status.replaceAll('_', ' ') || 'Ready to start';
                      return (
                        <li key={lesson.id}>
                          <span className="lesson-number" aria-hidden="true">{lesson.locked ? '🔒' : iteration?.status === 'passed' ? '✓' : index + 1}</span>
                          <div>
                            <h4>{lesson.title}</h4>
                            <p>{lesson.minutes} min · {statusLabel}</p>
                            {iteration && !lesson.locked && (
                              <p>Deadline {formatDate(iteration.supplementary_due_at || iteration.due_at)}
                                {iteration.credited_score !== null && ` · Credited ${iteration.credited_score}% (raw ${iteration.raw_score}%)`}
                              </p>
                            )}
                            {iteration?.status === 'failed' && !lesson.locked && (
                              <p>Supplementary window ends {formatDate(new Date(Date.parse(iteration.due_at) + 7 * 86400000).toISOString())} · {iteration.grade_cap}% cap</p>
                            )}
                          </div>
                          {!lesson.locked && (
                            <div className="academy-actions">
                              <button disabled={busy} onClick={() => onLessonAction(lesson, open ? 'open' : 'start')}>
                                {open ? 'Open lesson' : 'Start 14-day lesson'}
                              </button>
                              {iteration?.status === 'failed' && (
                                <button disabled={busy} onClick={() => onLessonAction(lesson, 'supplement')}>Begin supplementary</button>
                              )}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                )}
                {final && (
                  <div className="academy-capstone">
                    <h4>Final project · {final.title}</h4>
                    <p>Pass mark {final.pass_score}% · {projectUnlocked ? projectLabels[final.status] : status === 'locked' ? 'Module locked' : 'Finish the required lessons first'}</p>
                    {projectUnlocked && <a href={`/assignments/?assignment=${encodeURIComponent(final.slug)}`}>Open final project →</a>}
                  </div>
                )}
                {status === 'awaiting_project' && <p>This module’s lessons are complete. Progression resumes when its final project is published.</p>}
                {ideas.length > 0 && (
                  <details>
                    <summary>Additional project ideas</summary>
                    <ul>{ideas.map(idea => <li key={idea.id}><strong>{idea.name}</strong>{idea.description && ` · ${idea.description}`}</li>)}</ul>
                  </details>
                )}
              </article>
            );
          })}
        </section>
      ))}
    </div>
  );
}
