'use client';
import {useCallback,useEffect,useState} from 'react';
import {api, ApiError} from '@/lib/session-api';
import ModuleRoadmap, {type Course, type Lesson, type Iteration} from './ModuleRoadmap';
import LearningTwinPanel,{type TwinProfile} from './LearningTwinPanel';
import '@/app/assignments/learning-twin.css';
import '@/app/learner.css';
type Dashboard={username:string;admin:boolean;server_now:string;quote:string;passed:number;badges:string[];iterations:Record<string,Iteration>;projects:{assignment:string;due_at:string}[];learning_twin:TwinProfile};
type Detail={id:string;title:string;objective:string;challenge:string;iteration:Iteration|null;sections:{heading:string;body:string;code:string;note:string}[];quiz:{id:number;question:string;answers:string[]}[];passing_count:number};
export default function LearnerDashboard(){
 const [dash,setDash]=useState<Dashboard|null>(null),[courses,setCourses]=useState<Course[]>([]),[detail,setDetail]=useState<Detail|null>(null);
 const [answers,setAnswers]=useState<Record<number,number>>({}),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[ready,setReady]=useState(false);
 const refresh = useCallback(async () => {
   try {
     const dashboard = await api<Dashboard>('/dashboard/');
     const catalog = await api<{slug: string}[]>('/courses/');
     const nextCourses = await Promise.all(catalog.map(c => api<Course>(`/courses/${c.slug}/`)));
     setDash(dashboard);
     setCourses(nextCourses);
     setError('');
   } catch (cause) {
     if (cause instanceof ApiError && (cause.status === 401 || cause.status === 403)) {
       window.location.replace('/');
       return;
     }
     setError(cause instanceof Error ? cause.message : 'Could not load your dashboard.');
   } finally {
     setReady(true);
   }
 }, []);
 useEffect(() => {
   void refresh();
   const timer = setInterval(() => void refresh(), 60000);
   return () => clearInterval(timer);
 }, [refresh]);
 const openLessonId = detail?.id;
 useEffect(() => {
   if (openLessonId) document.getElementById('active-lesson')?.focus();
 }, [openLessonId]);
 async function act(lesson:Lesson,action:string){
   setBusy(true);setError('');setNotice('');
   try{if(action!=='open')await api(`/lessons/${lesson.id}/${action}/`,{});
     setDetail(await api<Detail>(`/lessons/${lesson.id}/`));setAnswers({});await refresh();
   }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 async function submit(){
   if(!detail)return;setBusy(true);setError('');
   try{const out=await api<{iteration:Iteration}>(`/lessons/${detail.id}/submit/`,{answers:detail.quiz.map(q=>answers[q.id])});
     setDetail({...detail,iteration:out.iteration});await refresh();
     setNotice(out.iteration.status==='passed'?'🎉 Lesson passed. Check your module for the next step.':'Review the lesson and try again before your deadline.');
   }catch(e){await refresh();setError((e as Error).message);}finally{setBusy(false);}
 }
 async function logout(){setBusy(true);try{await api('/auth/session-logout/',{});window.location.replace('/');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 const date=(s:string)=>new Date(s).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
 return <main className="academy">
   <header><a href="/" className="academy-brand"><img src="/brand/saire-symbol.webp" alt=""/>SAIRE-LINKED <small>ACADEMY / PROOFLOOP</small></a><nav><a href="#learning-roadmap">Roadmap</a><a href="/assignments/">Project lab & Mentor</a><a href="#learning-twin">Learning Twin</a>{dash&&<button disabled={busy} onClick={logout}>Sign out</button>}</nav></header>
   <section className="academy-hero"><p className="eyebrow">LEARN → BUILD → DEFEND → EVOLVE → PROVE</p><h1>{dash?`Welcome back, ${dash.username}.`:'Build skill. Leave proof.'}</h1><p>{dash?.quote||'One focused lesson. One honest attempt. One step closer to the engineer you are becoming.'}</p>{dash?.admin&&<strong className="badge">Administrator testing access · all content unlocked</strong>}</section>
   {error&&<p role="alert" className="academy-error">{error}</p>}{notice&&<p role="status" className="academy-notice">{notice}</p>}
   {!ready ? <p role="status">Opening your dashboard…</p> : dash ? <>
   <section className="academy-stats"><div><strong>{dash.passed}</strong><span>Lessons passed</span></div><div><strong>{Object.values(dash.iterations).filter(i=>['active','supplementary'].includes(i.status)).length}</strong><span>Active iterations</span></div><div><strong>{dash.badges.join(' · ')||'Your first proof awaits'}</strong><span>Milestones</span></div></section>
   <section className="academy-card"><h2>Your iteration rules</h2><p>14 days from starting. Passing unlocks the next lesson. A missed deadline fails the original attempt. One supplementary attempt ends on day 21 and caps credited marks at 70% (or your server’s configured cap). Quiz competence uses the published pass count. Lessons without quizzes require instructor sign-off. Exhausted attempts need instructor support; automatic resets are unavailable.</p><p>Times use your device’s time zone. Django’s clock decides acceptance. Finish a module’s lessons to open its final project. A passing project review unlocks the next module.</p></section>
   {detail&&<section id="active-lesson" tabIndex={-1} className="academy-card" aria-label="Lesson content"><button onClick={()=>setDetail(null)}>Close lesson</button><h2>{detail.title}</h2><p>{detail.objective}</p>{detail.sections.map((s,j)=><article key={j}><h3>{s.heading}</h3><p style={{whiteSpace:'pre-wrap'}}>{s.body}</p>{s.code&&<pre><code>{s.code}</code></pre>}{s.note&&<p>{s.note}</p>}</article>)}<h3>Your challenge</h3><p>{detail.challenge}</p>{detail.quiz.length?<form onSubmit={e=>{e.preventDefault();void submit();}}><h3>Knowledge check · {detail.passing_count} correct required</h3>{detail.quiz.map(q=><fieldset key={q.id}><legend>{q.question}</legend>{q.answers.map((a,j)=><label key={j}><input required type="radio" name={`q${q.id}`} value={j} checked={answers[q.id]===j} onChange={()=>setAnswers({...answers,[q.id]:j})}/>{a}</label>)}</fieldset>)}<button disabled={busy||!detail.iteration||!['active','supplementary'].includes(detail.iteration.status)}>Submit for server grading</button>{!detail.iteration&&<p>Admin preview does not create progress. Use a learner account to test iteration grading.</p>}</form>:<p>Instructor sign-off is required for completion.</p>}</section>}
   <ModuleRoadmap courses={courses} iterations={dash.iterations} busy={busy} admin={dash.admin} onLessonAction={act} />
   <section className="academy-card">
     <h2>Your project attempts</h2>
     {dash.projects.length ? dash.projects.map(project => (
       <p key={project.assignment}>{project.assignment} · due {date(project.due_at)} · <a href={`/assignments/?assignment=${encodeURIComponent(project.assignment)}`}>Open lab and grades</a></p>
     )) : <p>Your submissions and reviews will appear here.</p>}
   </section>
   <section className="academy-card">
     <h2>Study tools</h2>
     <p>Plan your week and browse the v9 resource library. Study plans are saved in this browser.</p>
     <nav aria-label="Study tools">
       <a href="/demo/?view=planner">Study planner</a>
       <a href="/demo/?view=resources">Resource library</a>
       <a href="/demo/">Sample demo</a>
     </nav>
   </section>
   <div id="learning-twin">
     <LearningTwinPanel profile={dash.learning_twin} authenticated loading={false} error="" onRefresh={() => void refresh()} />
   </div>
   </> : <button type="button" onClick={() => void refresh()}>Retry dashboard</button>}
   <footer>Live Django data · Sample demo progress never counts toward your academy record.</footer>
 </main>;
}
