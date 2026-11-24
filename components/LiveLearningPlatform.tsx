'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { dashboardDestination } from '@/lib/academy-display';
import { api, ApiError } from '@/lib/session-api';
import type { CourseDetails, CourseSummary } from '@/lib/lms-api';
import LearningPlatform from './LearningPlatform';
import { endBrowserSession, watchSessionEnd, SIGN_IN_URL } from '@/lib/browser-session';

export type Iteration = {
  status: string;
  due_at: string;
  supplementary_due_at: string | null;
  raw_score: number | null;
  credited_score: number | null;
  grade_cap: number;
};

type Account = {
  username: string;
  admin: boolean;
  iterations: Record<string, Iteration>;
  projects: {assignment: string; due_at: string; submissions: {id: number}[]}[];
  quote: string;
  orientation: {version: string; acknowledged: boolean};
};

export type LiveClassroom = Account & {
  course: CourseDetails;
  catalog: CourseSummary[];
  selectCourse: (slug: string) => void;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshError: string;
};

type CourseMetadata = Omit<CourseDetails, 'lessons' | 'projects'> & {
  lessons: Omit<CourseDetails['lessons'][number], 'objective' | 'sections' | 'challenge'>[];
  projects: (Omit<CourseDetails['projects'][number], 'description' | 'skills'> &
    Partial<Pick<CourseDetails['projects'][number], 'description' | 'skills'>>)[];
};

export default function LiveLearningPlatform() {
  const [slug, setSlug] = useState('');
  const [state, setState] = useState<(Account & { course: CourseDetails; catalog: CourseSummary[] }) | null>(null);
  const [error, setError] = useState('');
  const requestVersion = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    try {
      const account = await api<Account>('/dashboard/');
      const catalog = await api<CourseSummary[]>('/courses/');
      if (version !== requestVersion.current) return;
      const requestedSlug = slug || new URLSearchParams(window.location.search).get('course');
      const selected = catalog.find(course => course.slug === requestedSlug) ?? catalog[0];
      if (!selected) {
        setState(null);
        setError('No courses are published yet. Ask the Academy administrator to publish or seed the curriculum.');
        return;
      }
      const data = await api<CourseMetadata>(`/courses/${encodeURIComponent(selected.slug)}/`);
      if (version !== requestVersion.current) return;
      const course: CourseDetails = {
        ...data,
        lessons: data.lessons.map(lesson => ({ ...lesson, objective: '', sections: [], challenge: '' })),
        projects: data.projects.map(project => ({ ...project, description: project.description ?? '', skills: project.skills ?? [] })),
      };
      setState({ ...account, course, catalog });
      if (slug && selected.slug !== slug) setSlug(selected.slug);
      setError('');
    } catch (cause) {
      if (version !== requestVersion.current) return;
      if (cause instanceof ApiError && (cause.status === 401 || cause.status === 403)) {
        const next = dashboardDestination(window.location.pathname + window.location.search + window.location.hash);
        window.location.replace('/?next=' + encodeURIComponent(next) + '#signin');
        return;
      }
      setError(cause instanceof Error ? cause.message : 'The Academy could not load.');
    }
  }, [slug]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 60_000);
    return () => {
      window.clearInterval(timer);
      requestVersion.current++;
    };
  }, [refresh]);

  useEffect(() => {
    const stop = watchSessionEnd(() => {
      requestVersion.current++; setState(null); window.location.replace(SIGN_IN_URL);
    });
    const restored = (event: PageTransitionEvent) => { if (event.persisted) { setState(null); void refresh(); } };
    window.addEventListener('pageshow', restored);
    return () => { stop(); window.removeEventListener('pageshow', restored); };
  }, [refresh]);

  async function signOut() {
    await endBrowserSession();
  }

  if (!state || (slug && state.course.slug !== slug)) {
    return (
      <main className="live-load-screen">
        <h1>SAIRE-Linked Academy</h1>
        {error ? <><p role="alert">{error}</p><button className="btn btn-primary" onClick={() => void refresh()}>Try again</button></>
          : <p role="status">Opening your learning space…</p>}
        <a href="/">Back to the Academy</a>
      </main>
    );
  }

  return <LearningPlatform key={state.course.slug} live={{ ...state, selectCourse: next => {
    const url = new URL(window.location.href);
    url.searchParams.set("course", next);
    url.searchParams.delete("lesson");
    window.history.replaceState(window.history.state, "", url);
    setSlug(next);
  }, refresh, signOut, refreshError: error }} />;
}
