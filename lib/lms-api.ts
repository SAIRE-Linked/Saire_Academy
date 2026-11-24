import { lessons as demoLessons, phases as demoPhases, projects as demoProjects, quiz as demoQuiz, type Phase, type Lesson } from "@/data/curriculum";

export const DEFAULT_COURSE_SLUG = "ai-engineer-agentic-systems";
export const LMS_API_URL = (process.env.NEXT_PUBLIC_LMS_API_URL || "/api/v1").replace(/\/$/, "");

export type QuizQuestion = { question: string; answers: string[]; correct?: number; reason?: string };
export type CmsLesson = Lesson & { quiz?: QuizQuestion[]; passing_score?: number; locked?: boolean };
export type CmsProject = { id: string; name: string; level: string; phase: number; description: string; skills: string[]; locked?: boolean };
export type CourseSummary = {
  slug: string; title: string; subtitle: string; description: string;
  estimated_months: string; phase_count: number; lesson_count: number;
};
export type ModuleProgress = {
  status: string;
  project_unlocked: boolean;
  final_project: { slug: string; title: string; pass_score: number; status: string } | null;
};

export type ClassroomEntry = {
  kind: 'available' | 'empty' | 'sign_in' | 'prerequisite' | 'project' | 'review' | 'configuration';
  title?: string;
  message?: string;
  requirements: {module_id: number; title: string; course_slug: string; status: string}[];
  action: {label: string; href: string} | null;
};

export type CourseDetails = Omit<CourseSummary,"phase_count"|"lesson_count"> & {
  classroom_entry?: ClassroomEntry;
  updated_at?: string; phases: (Phase & { progress?: ModuleProgress; module_id?: number; setup_required?: boolean; setup_complete?: boolean })[]; lessons: CmsLesson[]; projects: CmsProject[];
};

export const demoCourse: CourseDetails = {
  slug: DEFAULT_COURSE_SLUG,
  title: "AI Engineer & Agentic Systems Mastery Programme",
  subtitle: "From programming fundamentals to production-ready AI agents",
  description: "A complete, project-based journey from programming fundamentals to production-ready AI agents. Learn deeply. Build confidently. Grow with SAIRE-Linked.",
  estimated_months: "12–18",
  phases: demoPhases,
  lessons: demoLessons.map(lesson => ({...lesson, quiz: lesson.id === "p1-l1" ? demoQuiz : [], passing_score: lesson.id === "p1-l1" ? 1 : 0})),
  projects: demoProjects,
};

async function getJson<T>(route: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${LMS_API_URL}${route}`, {signal, cache: "no-store", headers: {Accept: "application/json"}});
  if (!response.ok) throw new Error(`LMS API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export function fetchCourses(signal?: AbortSignal) {
  return getJson<CourseSummary[]>("/courses/", signal);
}
export function fetchCourse(slug: string, signal?: AbortSignal) {
  return getJson<CourseDetails>(`/courses/${encodeURIComponent(slug)}/`, signal);
}
