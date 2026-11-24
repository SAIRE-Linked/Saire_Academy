"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import {
  ArrowLeft, ArrowRight, ArrowUpRight, BarChart3, BookOpen, Bot, BrainCircuit, CalendarDays,
  Check, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, ClipboardCheck, Clock3, Code2,
  Copy, Database, Download, ExternalLink, FileCode2, FileText, GraduationCap, Layers3, LayoutDashboard,
  Lightbulb, ListChecks, LockKeyhole, Menu, Network, Play, Rocket, Search, Settings2,
  ShieldCheck, Sparkles, Terminal, Trophy, X, Zap, type LucideIcon
} from "lucide-react";
import { stack, resources, weekOne, baseSchedule, type Phase } from "@/data/curriculum";
import { DEFAULT_COURSE_SLUG, demoCourse, type CmsLesson, type QuizQuestion } from "@/lib/lms-api";

import { api } from '@/lib/session-api';
import AcademyHub, { type HubSection } from './AcademyHub';
import ClassroomGate from './ClassroomGate';
import AcademyNavigation from './AcademyNavigation';
import DashboardWorkspace from './DashboardWorkspace';
import { count, timeframe } from '@/lib/academy-display';
import AccountControls from './AccountControls';
import PythonPractice from './PythonPractice';
import { FormativePanel, GuidedLesson, ResourceLinks, type LessonGuide, type Resource } from './LessonStudyTools';
import type { LiveClassroom, Iteration } from './LiveLearningPlatform';

type LessonDetail = Pick<CmsLesson, 'id' | 'objective' | 'sections' | 'challenge'> & {
  quiz: QuizQuestion[];
  passing_count: number;
  guide: LessonGuide | null;
  resources: Resource[];
};

type View = "overview" | "roadmap" | "classroom" | "projects" | "planner" | "resources" | "academy";
type Saved = { completed: string[]; notes: Record<string, string>; minutes: number[]; quizBest: number; quizBests: Record<string, number>; phase: number; lesson: string };
const STORAGE = "saire-linked-lms-v1"; // Original key retained for first-course progress migration.
const defaults: Saved = { completed: [], notes: {}, minutes: baseSchedule.map(d => d.minutes), quizBest: 0, quizBests: {}, phase: 1, lesson: "p1-l1" };
const icons: Record<string, LucideIcon> = { code: Code2, brain: BrainCircuit, layers: Layers3, database: Database, sigma: BarChart3, chart: BarChart3, network: Network, spark: Sparkles, bot: Bot, shield: ShieldCheck, cpu: Zap, rocket: Rocket };
const ease = [0.22, 1, 0.36, 1] as const;
const motionProps = { initial: {opacity:0,y:14}, animate: {opacity:1,y:0}, exit:{opacity:0,y:-12}, transition:{duration:0.33,ease} };

const categoryName: Record<string,string> = {foundations:"Engineering foundations",intelligence:"AI intelligence",agents:"Agent engineering"};

function Brand({ compact=false }: {compact?:boolean}) {
  return <div className="brand"><div className="brandmark"><img src="/brand/saire-symbol.webp" alt="SAIRE-Linked symbol" /></div>{!compact && <div className="brandname"><strong>SAIRE-Linked</strong><small>DIGITAL LEARNING</small></div>}</div>;
}
function Chip({children,variant="muted"}: {children:React.ReactNode; variant?:"muted"|"green"|"blue"|"purple"}) { return <span className={`chip chip-${variant}`}>{children}</span> }
function SectionHeading({eyebrow,title,description,right}: {eyebrow:string;title:string;description?:string;right?:React.ReactNode}) { return <div className="section-header"><div><div className="eyebrow"><span className="eyebrow-dot"/>{eyebrow}</div><h2>{title}</h2>{description && <p>{description}</p>}</div>{right}</div> }
function CodePanel({code,language="Python"}: {code:string;language?:string}) {
 const [copied,setCopied]=useState(false);
 function copy(){ if(typeof navigator!=="undefined" && navigator.clipboard){navigator.clipboard.writeText(code).then(()=>{setCopied(true);setTimeout(()=>setCopied(false),1700)}).catch(()=>{});} }
 return <div className="code-panel"><div className="code-header"><span className="code-dots"><i/><i/><i/></span><span>{language} <span className="code-filename">· snippet</span></span><button type="button" className="copy-btn" onClick={copy} aria-label="Copy code">{copied?<Check size={14}/>:<Copy size={14}/>} {copied?"Copied":"Copy"}</button></div><pre><code>{code}</code></pre></div>
}
function Stat({icon:Icon,value,label,note}: {icon:LucideIcon; value:string;label:string;note:string}) {return <div className="stat"><div className="stat-icon"><Icon size={19}/></div><strong>{value}</strong><span>{label}</span><small>{note}</small></div>}

function LessonNotes({collapse, children}: {collapse: boolean; children: React.ReactNode}) {
 return collapse ? <details className="study-panel"><summary>Detailed lesson notes and examples</summary>{children}</details> : <>{children}</>;
}

export default function LearningPlatform({live}: {live?: LiveClassroom}) {
 const [view,setView]=useState<View>('overview');
 const [hubSection, setHubSection] = useState<HubSection>('welcome');
 const [hubPhase, setHubPhase] = useState<number>();
 const [textFirst, setTextFirst] = useState(false);
 const course = live?.course ?? demoCourse;
 const courseSlug = course.slug;
 const catalog = live?.catalog ?? [];
 const storageKey = live ? `${STORAGE}:account:${encodeURIComponent(live.username)}:${courseSlug}` : `${STORAGE}:${courseSlug}`;
 const [liveDetail, setLiveDetail] = useState<LessonDetail | null>(null);
 const [lessonError, setLessonError] = useState('');
 const [busy, setBusy] = useState(false);
 const [result, setResult] = useState<Iteration | null>(null);
 const [saved,setSaved]=useState<Saved>(defaults);
 const [hydrated,setHydrated]=useState(false);
 const [menuOpen,setMenuOpen]=useState(false);
 const [search,setSearch]=useState("");
 const [category,setCategory]=useState("all");
 const [phaseOpen,setPhaseOpen]=useState<number|null>(1);
 const [projectOpen,setProjectOpen]=useState<string|null>(null);
 const [quizAnswers,setQuizAnswers]=useState<Record<number,number>>({});
 const [quizSubmitted,setQuizSubmitted]=useState(false);
 const [toast,setToast]=useState("");
 const [sidebarOpen,setSidebarOpen]=useState(true);
 // The URL follows classroom actions as well as navigation links. Refresh and
 // sign-in therefore return to the displayed course and lesson.
 useEffect(() => {
   if (!live || !hydrated) return;
   const url = new URL(window.location.href);
   url.searchParams.set('course', courseSlug);
   url.searchParams.set('view', view);
   if (view === 'academy') url.searchParams.set('section', hubSection);
   else url.searchParams.delete('section');
   if (view !== 'classroom') url.searchParams.delete('lesson');
   window.history.replaceState(window.history.state, '', url);
 }, [hydrated, courseSlug, view, hubSection]);


 // Each course has separate progress. The original course reads legacy browser data.
 useEffect(()=>{
   const empty:Saved = {...defaults, lesson:"", phase:1, completed:[], notes:{}, quizBests:{}, minutes:[...defaults.minutes]};
   try {
     const raw = localStorage.getItem(storageKey) || (!live && courseSlug===DEFAULT_COURSE_SLUG ? localStorage.getItem(STORAGE) : null);
     if(raw){const parsed=JSON.parse(raw) as Partial<Saved>;setSaved({...empty,...parsed,
       minutes:Array.isArray(parsed.minutes)&&parsed.minutes.length===7?parsed.minutes:empty.minutes,
       completed:Array.isArray(parsed.completed)?parsed.completed:[],
       quizBests:parsed.quizBests && typeof parsed.quizBests==="object"?parsed.quizBests:{}
     });} else setSaved(empty);
   }catch{setSaved(empty)}
   setHydrated(true);
 },[storageKey]);
 useEffect(() => {
   const params = new URLSearchParams(window.location.search);
   const requested = params.get('view');
   const section = params.get('section');
   if (requested === 'overview' || requested === 'roadmap' || requested === 'classroom' || requested === 'projects') setView(requested);
   if (live && requested === 'academy') {
     setView('academy');
     if (section === 'welcome' || section === 'handbook' || section === 'setup' || section === 'glossary' || section === 'notebook' || section === 'revision') setHubSection(section);
   }
   try { setTextFirst(localStorage.getItem('saire-text-first') === '1'); } catch { /* browser storage is optional */ }
   if (requested === 'planner' || requested === 'resources') setView(requested);
 }, []);
 useEffect(()=>{if(hydrated){try{localStorage.setItem(storageKey,JSON.stringify(saved))}catch{/* storage may be disabled */}}},[saved,hydrated,storageKey]);
 useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(""),3000);return ()=>clearTimeout(timer)},[toast]);
 useEffect(()=>{function onKey(e:KeyboardEvent){if(e.key==="Escape"){setProjectOpen(null);setMenuOpen(false)}}window.addEventListener("keydown",onKey);return()=>window.removeEventListener("keydown",onKey)},[]);
 // Optional educational deterrent: browser shortcuts are not a security boundary.
 // Keep code samples copyable and protect premium lessons at the Django API layer.
 useEffect(()=>{
   if(view!=="classroom") return;
   const warnSave=(e:KeyboardEvent)=>{
     const target=e.target as HTMLElement | null;
     const editing=target?.matches("input, textarea, [contenteditable='true']");
     if(!editing && (e.ctrlKey||e.metaKey) && e.key.toLowerCase()==="s") {
       e.preventDefault();
       setToast("Course saving is restricted. Use your learning notes or the provided project starter.");
     }
   };
   window.addEventListener("keydown",warnSave);
   return ()=>window.removeEventListener("keydown",warnSave);
 },[view]);
 const {phases, lessons, projects}=course;
 const totalTopics=phases.reduce((a,p)=>a+p.topics.length,0);
 const completed = live
   ? Object.keys(live.iterations).filter(id => live.iterations[id].status === 'passed')
   : saved.completed;
 const completedCount = lessons.filter(lesson => completed.includes(lesson.id)).length;
 const progress = lessons.length ? Math.round(completedCount / lessons.length * 100) : 0;
 const suggested = lessons.find(lesson => !lesson.locked && !completed.includes(lesson.id))
   ?? lessons.find(lesson => !lesson.locked);
 const selected = lessons.find(lesson => lesson.id === saved.lesson && !lesson.locked) ?? suggested;
 const iteration = selected && live?.iterations[selected.id];
 const detailAvailable = Boolean(live && selected && (iteration || live.admin));
 const selectedId = selected?.id;
 useEffect(() => {
   if (!live || !hydrated) return;
   const requested = new URLSearchParams(window.location.search).get('lesson');
   const lesson = course.lessons.find(item => item.id === requested && !item.locked);
   if (lesson) setSaved(old => ({...old, lesson: lesson.id, phase: lesson.phaseId}));
 }, [hydrated, courseSlug]);
 useEffect(() => {
   if (!selectedId || view !== 'classroom' || !detailAvailable) return;
   let active = true;
   setLessonError('');
   api<LessonDetail>(`/lessons/${encodeURIComponent(selectedId)}/`).then(
     detail => { if (active) setLiveDetail(detail); },
     cause => { if (active) setLessonError(cause.message); },
   );
   return () => { active = false; };
 }, [selectedId, view, detailAvailable]);
 const emptyLesson: CmsLesson = {
   id: '', phaseId: 1, title: 'Lessons coming soon', minutes: 0, difficulty: '',
   objective: '', sections: [], challenge: '',
 };
 const currentLesson = {
   ...(selected ?? emptyLesson),
   ...(liveDetail && liveDetail.id === selectedId ? { ...liveDetail, passing_score: liveDetail.passing_count } : {}),
 };
 const pythonSection = currentLesson.sections.find(section => section.code && /^(python|python3|py)$/i.test(section.language || "python"));
 const practiceExample = pythonSection ? (liveDetail?.id === currentLesson.id && liveDetail.guide?.example || pythonSection.code) : undefined;
 const quiz = currentLesson.quiz ?? [];
 const passingScore = currentLesson.passing_score ?? Math.ceil(quiz.length * .75);
 const quizScore = quiz.reduce((sum,q,i)=>sum+(quizAnswers[i]===q.correct?1:0),0);
 const nextLesson = selected && lessons.slice(lessons.indexOf(selected) + 1).find(lesson => !lesson.locked);
 const activeModule = phases.find(phase => phase.id === currentLesson.phaseId);
 const orientationRequired = Boolean(live && !live.admin && !live.orientation.acknowledged);
 const setupRequired = Boolean(live && !live.admin && activeModule?.setup_required && !activeModule.setup_complete);
 const openHub = (section: HubSection, phase?: number) => {
   setHubSection(section);
   setHubPhase(phase);
   navigate('academy');
 };
 function toggleTextFirst() {
   const next = !textFirst;
   setTextFirst(next);
   try { localStorage.setItem('saire-text-first', next ? '1' : '0'); } catch { /* browser storage is optional */ }
 }
 const projectLink = activeModule?.progress?.project_unlocked && activeModule.progress.final_project
   ? `/assignments/?assignment=${encodeURIComponent(activeModule.progress.final_project.slug)}`
   : null;
 const canSubmit = !live || iteration?.status === 'active' || iteration?.status === 'supplementary';
 const weekTotal=saved.minutes.reduce((a,b)=>a+b,0);
 const visiblePhases=phases.filter(p=>(category==="all"||p.category===category) && `${p.name} ${p.desc} ${p.project} ${p.topics.join(" ")}`.toLowerCase().includes(search.toLowerCase()));
 const visibleProjects=projects.filter(p=>`${p.name} ${p.description} ${p.skills.join(" ")}`.toLowerCase().includes(search.toLowerCase()));
 function navigate(target:View){setView(target);setMenuOpen(false);setSearch("");window.scrollTo({top:0,behavior:"smooth"})}
 function beginLesson(id?: string) {
   const lesson = id ? lessons.find(item => item.id === id) : suggested;
   if (!lesson || lesson.locked) {
     navigate('roadmap');
     setToast('Check the roadmap for the requirements to unlock your next lesson.');
     return;
   }
   setSaved(old => ({ ...old, lesson: lesson.id, phase: lesson.phaseId }));
   if (live) {
     const url = new URL(window.location.href);
     url.searchParams.set('lesson', lesson.id);
     window.history.replaceState(window.history.state, '', url);
   }
   setQuizAnswers({});
   setQuizSubmitted(false);
   setResult(null);
   setLessonError('');
   navigate('classroom');
 }
 async function lessonAction(action: 'start' | 'supplement' | 'submit') {
   if (!live || !selected || busy) return;
   setBusy(true);
   setLessonError('');
   try {
     const body = action === 'submit' ? { answers: quiz.map((_, i) => quizAnswers[i]) } : {};
     const response = await api<{ iteration: Iteration }>(`/lessons/${encodeURIComponent(selected.id)}/${action}/`, body);
     if (action === 'submit') {
       setResult(response.iteration);
       setQuizSubmitted(true);
       setToast(response.iteration.status === 'passed' ? 'Lesson passed. Your progress is saved.' : 'Review the lesson, then try again.');
     }
     await live.refresh();
   } catch (cause) {
     await live.refresh();
     setLessonError(cause instanceof Error ? cause.message : 'The lesson could not be updated.');
   } finally {
     setBusy(false);
   }
 }
 function finishLesson(){if(live)return;if(!currentLesson.id){setToast("No published lessons yet.");return;}if(quiz.length && (saved.quizBests[currentLesson.id]??(currentLesson.id==="p1-l1"?saved.quizBest:0))<passingScore){setToast(`Score at least ${passingScore}/${quiz.length} on the knowledge check before completing this lesson.`);document.getElementById("lesson-quiz")?.scrollIntoView({behavior:"smooth"});return;}setSaved(old=>({...old,completed:[...new Set([...old.completed,currentLesson.id])]}));setToast("Lesson completed! Your progress is saved in this browser.")}
 function submitQuiz(){if(Object.keys(quizAnswers).length!==quiz.length||!canSubmit||busy)return;if(live){void lessonAction('submit');return;}setQuizSubmitted(true);setSaved(old=>({...old,quizBest:currentLesson.id==="p1-l1"?Math.max(old.quizBest,quizScore):old.quizBest,quizBests:{...old.quizBests,[currentLesson.id]:Math.max(old.quizBests[currentLesson.id]??0,quizScore)}}));setToast(quizScore>=passingScore?"Great work! You passed the diagnostic.":"Review the explanations and try again.")}
 function exportProgress(){const blob=new Blob([JSON.stringify({product:"SAIRE-Linked Digital Learning",exportedAt:new Date().toISOString(),...saved,completed},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="saire-learning-progress.json";link.click();URL.revokeObjectURL(url);setToast("Progress exported to a JSON backup.")}
 function updateMinutes(i:number,value:number){setSaved(old=>({...old,minutes:old.minutes.map((v,j)=>i===j?value:v)}))}
 const nav:[View,LucideIcon,string][]=[["overview",LayoutDashboard,"Overview"],["roadmap",Layers3,"Learning roadmap"],["classroom",BookOpen,"My classroom"],["projects",Rocket,"Project lab"],["planner",CalendarDays,"Study planner"],["resources",FileText,"Resource library"]];
 if (live) nav.push(["academy", GraduationCap, "Study Hub"]);
 return <MotionConfig reducedMotion="user"><div className={`app-shell ${!sidebarOpen?"compact-sidebar":""} ${textFirst ? "text-first" : ""}`}>
  <aside id="academy-sidebar" className={`sidebar ${menuOpen?"mobile-open":""}`} aria-label="Primary navigation">
    <div className="sidebar-top"><Brand/><button className="icon-button mobile-close" onClick={()=>setMenuOpen(false)} aria-label="Close navigation"><X size={20}/></button></div>
    <div className="sidebar-scroll">
      <AcademyNavigation demo={!live} course={live ? courseSlug : undefined} active={view === 'academy' ? 'academy&section=' + hubSection : view} />
      <div className="sidebar-bottom-links"><a href="https://www.sairelinked.com" target="_blank" rel="noreferrer">SAIRE-Linked website</a><a href="https://www.sairelinked.com/packages/growth" target="_blank" rel="noreferrer">Explore Growth Package</a></div>
    </div>
    <div className="sidebar-footer"><div className="avatar">SL</div><div><strong>{live?.username ?? "My learning space"}</strong><small>{live ? "Academy account" : "Local browser profile"}</small></div><span className="avatar-online"/></div>
  </aside>
  <div className="sidebar-overlay" onClick={()=>setMenuOpen(false)} aria-hidden="true"/>
  <div className="main-shell">
    <header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" aria-expanded={menuOpen} aria-controls="academy-sidebar" onClick={()=>setMenuOpen(true)} aria-label="Open menu"><Menu size={20}/></button><button className="icon-button desktop-menu" onClick={()=>setSidebarOpen(v=>!v)} aria-label="Toggle sidebar"><Menu size={18}/></button><div className="breadcrumb"><span>SAIRE Academy</span><ChevronRight size={14}/><strong>{nav.find(n=>n[0]===view)?.[2]}</strong></div></div><div className="topbar-actions"><label className="course-picker-label" htmlFor="course-picker">COURSE</label><select id="course-picker" className="course-picker" value={courseSlug} onChange={e=>live?.selectCourse(e.target.value)} aria-label="Choose a course">{!live&&<option value={DEFAULT_COURSE_SLUG}>AI Engineering Mastery</option>}{catalog.map(item=><option key={item.slug} value={item.slug}>{item.title}</option>)}</select><span className="live-badge"><span className="pulse-dot"/> LEARNING IN PROGRESS</span>{live ? <AccountControls username={live.username} onLogout={live.signOut} /> : <a className="btn btn-outline" href="/#signin">Sign in</a>}</div></header>
    <main className="content">
      <div className={`api-banner ${live ? 'api-connected' : 'api-offline'}`} role="status">
        <span className="pulse-dot" />
        {live ? `Live Academy · ${live.quote}` : 'Sample demo only — progress stays in this browser.'}
        {live?.admin && <span>Administrator preview</span>}
      </div>
      {live?.refreshError && <div className="api-banner api-offline" role="alert">
        {live.refreshError} <button className="btn btn-outline" onClick={()=>void live.refresh()}>Refresh progress</button>
      </div>}
      {live && <div className="study-actions study-top-tools">
        <button className="btn btn-outline" aria-pressed={textFirst} onClick={toggleTextFirst}>Text-first mode {textFirst ? 'on' : 'off'}</button>
        {orientationRequired && <button className="btn btn-outline" onClick={()=>openHub('handbook')}>Read and acknowledge rules</button>}
      </div>}
      <AnimatePresence mode="wait">
      {view === 'academy' && live && <motion.div key="academy" {...motionProps}>
        <AcademyHub section={hubSection} select={setHubSection} modules={phases} phase={hubPhase}
          orientation={live.orientation} refresh={live.refresh} />
      </motion.div>}
      {view === "overview" && live && <DashboardWorkspace live={live} openLesson={beginLesson} roadmap={() => navigate("roadmap")}/>}
      {view==="overview"&&!live&&<motion.div key="overview" {...motionProps} className="page-content">
        <div className="hero"><div className="hero-orb hero-orb-1"/><div className="hero-orb hero-orb-2"/><div className="hero-grid"/><div className="hero-content"><span className="hero-kicker"><Sparkles size={13}/> THE FUTURE IS ENGINEERED, NOT GUESSED <span>· 2026—2027</span></span><h1>Build the mind.<br/><span>Engineer the future.</span></h1><p>{course.description}</p><div className="hero-course-tag">NOW STUDYING · {course.title}</div><div className="hero-buttons"><button className="btn btn-primary" disabled={!suggested} onClick={()=>beginLesson()}><Play size={16} fill="currentColor"/>{completedCount?"Continue learning":"Start learning"}<ArrowRight size={17}/></button><button className="btn btn-ghost" onClick={()=>navigate("roadmap")}>Explore the roadmap <ArrowUpRight size={16}/></button></div><div className="hero-bottom"><span><CheckCircle2 size={15}/> Practical first</span><span><CheckCircle2 size={15}/> Real projects</span><span><CheckCircle2 size={15}/> Career focused</span></div></div>{!textFirst && <img className="hero-logo" src="/brand/saire-pcb.webp" alt="SAIRE-Linked circuit heart emblem"/>}<div className="hero-side-tag">SAIRE-Linked / DIGITAL LEARNING PLATFORM</div></div>
        <div className="stat-grid"><Stat icon={Layers3} value={String(phases.length)} label="Learning phases" note="Foundation to expert path"/><Stat icon={BookOpen} value={String(totalTopics)} label="Curriculum topics" note={`${count(lessons.length, 'tutorial')} published`}/><Stat icon={Rocket} value={String(projects.length)} label="Portfolio projects" note="Build real-world skills"/><Stat icon={Clock3} value={timeframe(course.estimated_months)} label="Learning timeframe" note="Flexible, competence-led"/></div>
        <div className="split-section"><div className="section-main"><SectionHeading eyebrow="PICK UP WHERE YOU LEFT OFF" title="Your next step" description="Small, consistent steps lead to meaningful progress."/><div className="continue-card"><div className="continue-icon"><Terminal size={27}/></div><div className="continue-body"><Chip variant="green">PHASE {currentLesson.phaseId.toString().padStart(2,"0")} · CURRENT LESSON</Chip><h3>{currentLesson.title}</h3><p>{currentLesson.objective || "Open the classroom to begin or resume your next lesson."}</p><div className="lesson-meta"><span><Clock3 size={14}/>{currentLesson.minutes} min lesson</span><span><BookOpen size={14}/>{currentLesson.difficulty}</span></div></div><button className="circle-arrow" disabled={!selected} aria-label="Open current lesson" onClick={()=>beginLesson(currentLesson.id)}><ArrowUpRight size={23}/></button></div></div><div className="insight-card"><div className="insight-heading"><Lightbulb size={19}/><span>THE SAIRE APPROACH</span></div><h3>Understand first.<br/><em>Automate second.</em></h3><p>Master the underlying logic before relying on frameworks or AI tools. Strong foundations create engineers who can design, debug and lead.</p><button onClick={()=>navigate("planner")}>Plan your study week <ArrowRight size={16}/></button></div></div>
        <SectionHeading eyebrow="THE LEARNING JOURNEY" title={course.title} description="A carefully sequenced path from fundamentals to confident engineering." right={<button className="link-button" onClick={()=>navigate("roadmap")}>All {count(phases.length, 'phase')} <ArrowRight size={17}/></button>}/>
        <div className="phase-feature-grid">{phases.slice(0,6).map(p=>{const Icon=icons[p.icon]??Code2;return <button className="phase-feature-card" key={p.id} onClick={()=>{setPhaseOpen(p.id);navigate("roadmap")}}><span className="phase-feature-no">{String(p.id).padStart(2,"0")} / {phases.length}</span><div className={`phase-feature-icon icon-${p.category}`}><Icon size={23}/></div><h3>{p.name}</h3><p>{p.desc}</p><span className="phase-feature-bottom">{count(p.duration, 'week')} <ArrowUpRight size={17}/></span></button>})}</div>
        <div className="banner-gradient"><div><span className="eyebrow">LEARN BY BUILDING</span><h2>Real projects. Real engineering.</h2><p>Turn milestones into practical portfolio projects that demonstrate your engineering skills.</p><button className="btn btn-white" onClick={()=>navigate("projects")}>Enter the project lab <ArrowRight size={17}/></button></div><div className="banner-visual"><div className="visual-ring ring-a"/><div className="visual-ring ring-b"/><Code2 size={82}/></div></div>
        {courseSlug===DEFAULT_COURSE_SLUG&&<div className="month-section"><SectionHeading eyebrow="YOUR FIRST 30 DAYS" title="Rebuild the foundation." description="A structured first month to make your programming knowledge solid again."/><div className="month-grid">{weekOne.map(w=><div className="month-card" key={w.week}><span>WEEK {String(w.week).padStart(2,"0")}</span><h3>{w.title}</h3><p>{w.focus}</p><div><CheckCircle2 size={15}/>{w.deliverable}</div></div>)}</div></div>}
      </motion.div>}
      {view==="roadmap"&&<motion.div key="roadmap" {...motionProps} className="page-content">
        <div className="page-intro"><div className="eyebrow"><span className="eyebrow-dot"/> YOUR COMPLETE LEARNING ROADMAP</div><h1>From fundamentals <span>to mastery.</span></h1><p>Explore all {count(phases.length, 'phase')}, {totalTopics} curriculum topics and project milestones. Follow the sequence, or preview what lies ahead.</p></div>
        <p className="api-banner">{count(new Set(lessons.map(lesson => lesson.phaseId)).size, 'module')} with published lessons · {count(phases.filter(phase => !lessons.some(lesson => lesson.phaseId === phase.id)).length, 'outline')} only</p>
        <div className="filter-row"><div className="search-control"><Search size={18}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search phases, topics or projects…" aria-label="Search curriculum"/></div><div className="filter-pills">{[["all","All phases"],...Array.from(new Set(phases.map(p=>p.category))).map(key=>[key,categoryName[key]??key])].map(([key,label])=><button className={category===key?"selected":""} onClick={()=>setCategory(key)} key={key}>{label}</button>)}</div></div>
        <div className="roadmap-overview"><span><Layers3 size={17}/> {count(phases.length, 'phase')}</span><span><ListChecks size={17}/> {count(totalTopics, 'topic')}</span><span><Rocket size={17}/> {count(projects.length, 'project')}</span><span><Clock3 size={17}/> Suggested timeframe: {timeframe(course.estimated_months)}</span></div>
        <div className="roadmap-list">{visiblePhases.length?visiblePhases.map(p=>{const Icon=icons[p.icon]??Code2;const phaseLessons=lessons.filter(l=>l.phaseId===p.id);const open=phaseOpen===p.id;return <div className={`roadmap-item ${open?"open":""}`} key={p.id}><button className="roadmap-toggle" onClick={()=>setPhaseOpen(open?null:p.id)} aria-expanded={open}><div className="roadmap-count">{String(p.id).padStart(2,"0")}</div><div className={`roadmap-icon icon-${p.category}`}><Icon size={24}/></div><div className="roadmap-title"><div className="phase-category">{categoryName[p.category]??p.category} · {count(p.duration, 'week')}</div><h3>{p.name}</h3><p>{p.desc}</p></div><div className="roadmap-toggle-end"><Chip variant={phaseLessons.length?"green":"muted"}>{phaseLessons.length === 0 ? "Outline only" : p.progress?.status==="locked"?"Locked":p.progress?.status==="completed"?"Module complete":phaseLessons.length?`${count(phaseLessons.length, 'lesson')} live`:"Syllabus ready"}</Chip><ChevronDown className={open?"rotated":""} size={20}/></div></button>{open&&<div className="roadmap-details"><div className="roadmap-columns"><div><h4><BookOpen size={17}/> Course syllabus</h4><ol className="topic-list">{p.topics.map((topic,i)=><li key={i}><span>{String(i+1).padStart(2,"0")}</span>{topic}</li>)}</ol></div><div className="roadmap-sidebar"><div className="project-milestone"><Rocket size={21}/><span>END-OF-MODULE PROJECT</span>
          <h4>{p.progress?.final_project?.title ?? p.project}</h4>
          {p.progress?.final_project ? <>
            <p>{p.progress.final_project.pass_score}% to pass · {p.progress.project_unlocked ? p.progress.final_project.status.replaceAll('_', ' ') : 'Locked'}</p>
            {p.progress.project_unlocked && <a href={`/assignments/?assignment=${encodeURIComponent(p.progress.final_project.slug)}`}>Open project lab →</a>}
          </> : live ? <p>Final project details will appear when published.</p>
          : p.id === 1 ? <details><summary>View project brief</summary><p>Build a command-line business expense tracker. Record an expense with an amount and category, save entries to a file, and show a spending summary when you reopen it.</p></details>
          : <p>This milestone is outlined in the syllabus. Its detailed brief is not published in the demo.</p>}
          </div><div className="available-lessons">{live && <button className="btn btn-outline" onClick={()=>openHub("setup",p.id)}>Getting Ready and outcomes <ArrowRight size={15}/></button>}<h4>Lessons</h4>{phaseLessons.length?phaseLessons.map(l=><button key={l.id} disabled={l.locked||busy} onClick={()=>beginLesson(l.id)}><span>{l.locked?<LockKeyhole size={15}/>:completed.includes(l.id)?<CheckCircle2 size={17}/>:<Play size={15}/>}</span>{l.title}{l.locked?" · Locked":""}<ArrowRight size={15}/></button>):<p>This phase is fully mapped. Detailed lessons will be published progressively; the syllabus is not presented as completed teaching content.</p>}</div></div></div></div>}</div>}):<div className="empty-state">No phases match that search. Try a shorter keyword.</div>}</div>
      </motion.div>}
      {view==="classroom"&&<motion.div key="classroom" {...motionProps} className="page-content classroom-page">
        <div className="page-intro classroom-intro"><div className="eyebrow"><span className="eyebrow-dot"/> INTERACTIVE CLASSROOM</div><h1>Learn with <span>purpose.</span></h1><p>Read, experiment, review and apply. Your learning journey starts with real understanding.</p></div>
        <div className="classroom-layout"><div className="print-protection-notice" role="note"><strong>SAIRE-Linked Academy</strong><p>This course lesson is available in your authorised learning session. Printing is disabled in this view. Visit the Academy to study the current licensed version.</p></div><aside className="lesson-sidebar"><div className="lesson-sidebar-heading"><BookOpen size={19}/><span>Available lessons</span><Chip variant="green">{lessons.length} LIVE</Chip></div><div className="lesson-phase-label">{course.title.toUpperCase()}</div>{lessons.map((lesson,i)=><button key={lesson.id} className={`lesson-tab ${saved.lesson===lesson.id?"selected":""}`} disabled={lesson.locked||busy} onClick={()=>beginLesson(lesson.id)}><span className={`lesson-number ${completed.includes(lesson.id)?"completed":""}`}>{lesson.locked?<LockKeyhole size={14}/>:completed.includes(lesson.id)?<Check size={14}/>:String(i+1).padStart(2,"0")}</span><span><strong>{lesson.title}</strong><small><Clock3 size={12}/>{lesson.minutes} min{lesson.locked?" · Locked":""}</small></span><ChevronRight size={15}/></button>)}<div className="lesson-sidebar-foot"><Sparkles size={17}/><p>Additional in-depth lessons are being developed in sequence. The full syllabus is available in the roadmap.</p></div></aside>
        {!selected?<ClassroomGate entry={course.classroom_entry} lessonCount={lessons.length} onRoadmap={()=>navigate('roadmap')}/>
        :live && liveDetail?.id!==selected.id ? <article className="lesson-article empty-course">
          <BookOpen size={36}/><h2>{selected.title}</h2>
          {lessonError && <p role="alert">{lessonError}</p>}
          {detailAvailable ? <p role="status">{lessonError ? 'Return to the overview and reopen the classroom to retry.' : 'Opening your lesson…'}</p> : <>
            <p>Start when you’re ready. You’ll have 14 days to complete the lesson and its knowledge check.</p>
            {orientationRequired && <button className="btn btn-outline" onClick={()=>openHub('handbook')}>Read and acknowledge the rules</button>}
            {setupRequired && <button className="btn btn-outline" onClick={()=>openHub('setup',selected.phaseId)}>Complete Getting Ready</button>}
            <FormativePanel key={selected.id} lesson={selected.id} stage="before" />
            <button className="btn btn-primary" disabled={busy||orientationRequired||setupRequired}
              onClick={()=>void lessonAction('start')}>{busy?'Starting…':'Start 14-day lesson'}</button>
          </>}
        </article>:<article className="lesson-article protected-curriculum"><div className="lesson-art"><div className="lesson-art-glow"/><div className="lesson-art-label"><Chip variant="green">PHASE {String(currentLesson.phaseId).padStart(2,"0")} / LESSON {Math.max(1,lessons.findIndex(l=>l.id===currentLesson.id)+1)}</Chip><h2>{currentLesson.title}</h2><p>{currentLesson.objective}</p><div><Clock3 size={15}/> {currentLesson.minutes} MIN <span>·</span> {currentLesson.difficulty.toUpperCase()}</div></div><Terminal className="lesson-art-icon" size={140}/></div><div className="lesson-article-inner">
        {live && <div className="live-lesson-status">
          {lessonError && <p role="alert">{lessonError}</p>}
          {iteration ? <>
            <Chip variant={iteration.status === 'passed' ? 'green' : 'blue'}>{iteration.status.replaceAll('_',' ')}</Chip>
            <p>Deadline {new Date(iteration.supplementary_due_at || iteration.due_at).toLocaleString()}
              {iteration.credited_score !== null && ` · Credited ${iteration.credited_score}%`}
            </p>
            {iteration.status === 'failed' && <button className="btn btn-outline" disabled={busy} onClick={()=>void lessonAction('supplement')}>Begin supplementary attempt · {iteration.grade_cap}% cap</button>}
            {iteration.status === 'exhausted' && <p>Both attempt windows have ended. Contact the Academy for help with your next step.</p>}
          </> : <p>Administrator preview</p>}
        </div>}
        {liveDetail?.id === currentLesson.id && liveDetail.guide && <GuidedLesson guide={liveDetail.guide} />}
        {practiceExample && <PythonPractice key={`${live?.username ?? "demo"}:${currentLesson.id}`} owner={live?.username ?? "demo"} lessonId={currentLesson.id} example={practiceExample} />}
        <LessonNotes collapse={Boolean(liveDetail?.id === currentLesson.id && liveDetail.guide)}><div className="lesson-objective"><Lightbulb size={20}/><p><strong>What you'll learn</strong><br/>{currentLesson.objective}</p></div>{currentLesson.sections.map((section,i)=><section className="lesson-section" key={i}><div className="lesson-section-no">0{i+1} / {String(currentLesson.sections.length).padStart(2,"0")}</div><h3>{section.heading}</h3><p>{section.body}</p>{section.code&&<CodePanel code={section.code} language={section.language||"Python"}/>} {section.note&&<div className="lesson-note"><Lightbulb size={19}/><span>{section.note}</span></div>}</section>)}</LessonNotes><div className="challenge-box"><div className="challenge-kicker"><Zap size={18}/> YOUR INDEPENDENT CHALLENGE</div><h3>Now it's your turn.</h3><p>{currentLesson.challenge}</p><label htmlFor="reflection">Your notes / approach</label><textarea id="reflection" value={saved.notes[currentLesson.id]??""} onChange={e=>setSaved(old=>({...old,notes:{...old.notes,[currentLesson.id]:e.target.value}}))} placeholder="Write down your approach or what you learned… (saved automatically in this browser)" rows={4}/><small>Use the practice studio above or your local IDE to run code. This notes area does not execute code.</small></div>
        {live && selected && <FormativePanel key={selected.id} lesson={selected.id} stage="after" />}
        {liveDetail?.id === currentLesson.id && <ResourceLinks links={liveDetail.resources} />}
        {quiz.length>0&&<section className="quiz-block" id="lesson-quiz"><div className="quiz-title"><div><span className="eyebrow"><span className="eyebrow-dot"/> KNOWLEDGE CHECK</span><h3>Test your understanding</h3><p>Answer {count(quiz.length, 'question')}. Aim for at least {passingScore}/{quiz.length} to complete this lesson.</p></div><div className="quiz-illustration"><ClipboardCheck size={30}/></div></div>{quiz.map((q,i)=><div key={i} className="quiz-question"><h4><span>{String(i+1).padStart(2,"0")}</span>{q.question}</h4><div className="quiz-options">{q.answers.map((answer,j)=><button key={j} disabled={quizSubmitted||busy||!canSubmit} className={`quiz-option ${quizAnswers[i]===j?"chosen":""} ${!live&&quizSubmitted&&j===q.correct?"correct":""} ${!live&&quizSubmitted&&quizAnswers[i]===j&&j!==q.correct?"incorrect":""}`} onClick={()=>setQuizAnswers(a=>({...a,[i]:j}))}><span className="option-circle">{String.fromCharCode(65+j)}</span>{answer}{!live&&quizSubmitted&&j===q.correct&&<CheckCircle2 size={17}/>}</button>)}</div>{!live&&quizSubmitted&&<div className="quiz-explanation"><Lightbulb size={16}/>{q.reason}</div>}</div>)}<div className="quiz-footer">
          {live && result ? <div className="quiz-result" role="status">
            <Trophy size={23}/> Score <strong>{result.raw_score}%</strong>
            <span>{result.status === 'passed' ? 'Knowledge check passed!' : 'Review the lesson and try again.'}</span>
            {canSubmit && result.status !== 'passed' && <button className="btn btn-outline" onClick={()=>{setQuizSubmitted(false);setQuizAnswers({});setResult(null)}}>Retake quiz</button>}
          </div> : !live && quizSubmitted ? <div className="quiz-result"><Trophy size={23}/> You scored <strong>{quizScore} / {quiz.length}</strong><span>{quizScore>=passingScore?"Knowledge check passed!":"Review the explanations, then try again."}</span><button className="btn btn-outline" onClick={()=>{setQuizSubmitted(false);setQuizAnswers({})}}>Retake quiz</button></div>
          : canSubmit ? <><span>{Object.keys(quizAnswers).length} / {quiz.length} answered</span><button className="btn btn-primary" disabled={busy||Object.keys(quizAnswers).length!==quiz.length} onClick={submitQuiz}>Check my answers <ArrowRight size={16}/></button></>
          : <p>{iteration?.status === 'passed' ? 'This knowledge check is complete.' : 'An active attempt is required to submit answers.'}</p>}
        </div></section>}
        <div className="lesson-finish">
          <div><strong>{completed.includes(currentLesson.id)?"This lesson is complete!":"Ready to move forward?"}</strong>
          <p>{live && !quiz.length && !completed.includes(currentLesson.id) ? 'This lesson requires instructor sign-off.' : 'Complete the practice before continuing.'}</p></div>
          <div className="lesson-finish-actions">
            <button className="btn btn-outline" onClick={()=>navigate("roadmap")}>View roadmap</button>
            {completed.includes(currentLesson.id) && nextLesson && <button className="btn btn-primary" disabled={busy} onClick={()=>beginLesson(nextLesson.id)}>Next lesson <ArrowRight size={17}/></button>}
            {completed.includes(currentLesson.id) && !nextLesson && projectLink && <a className="btn btn-primary" href={projectLink}>Open final project <ArrowRight size={17}/></a>}
            {!live && !completed.includes(currentLesson.id) && <button className="btn btn-primary" onClick={finishLesson}>Mark lesson complete <Check size={17}/></button>}
          </div>
        </div>
        </div></article>}</div>
      </motion.div>}
      {view==="projects"&&<motion.div key="projects" {...motionProps} className="page-content"><div className="page-intro"><div className="eyebrow"><span className="eyebrow-dot"/> THE PROJECT LAB</div><h1>{live ? 'Course projects' : 'Sample project lab'}</h1><p>Real-world milestones, designed to become your engineering portfolio — and potentially SAIRE-Linked products.</p></div><div className="filter-row"><div className="search-control"><Search size={18}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search projects or technologies…" aria-label="Search projects"/></div><Chip variant="green">{projects.length} PROJECT MILESTONES</Chip>{live&&<a className="btn btn-primary" href="/assignments/">Open ProofLoop lab <ArrowRight size={16}/></a>}</div>{live && <section className="workspace-panel"><h2>Assessed final projects</h2>
        {phases.some(phase => phase.progress?.final_project) ? <ul>{phases.map(phase => {
          const final = phase.progress?.final_project;
          return final && <li key={phase.id}><strong>{final.title}</strong>{phase.progress?.project_unlocked ?
            <a href={'/assignments/?assignment=' + encodeURIComponent(final.slug)}>Open assessed brief</a> : <span>Complete module requirements to unlock</span>}</li>;
        })}</ul> : <p>No final project has been published for this course.</p>}</section>}
        {live && <h2>Additional project ideas</h2>}<div className="projects-grid">{visibleProjects.map((project,i)=><button className="project-card" key={project.id} disabled={project.locked} onClick={()=>setProjectOpen(project.id)}><div className={`project-visual visual-${project.phase%4}`}><span className="project-visual-num">{String(project.phase).padStart(2,"0")}</span><div className="project-visual-shape"><Code2 size={39}/></div><span className="project-visual-tag">PHASE {String(project.phase).padStart(2,"0")}</span></div><div className="project-card-body"><div className="project-card-top"><Chip>{project.locked?"Locked":project.level}</Chip><ArrowUpRight size={18}/></div><h3>{project.name}</h3><p>{project.locked?"Complete the required lessons and modules to unlock.":project.description}</p><div className="skill-tags">{project.skills.map(s=><span key={s}>{s}</span>)}</div></div></button>)}{!visibleProjects.length&&<div className="empty-state">No projects found.</div>}</div></motion.div>}
      {view==="planner"&&<motion.div key="planner" {...motionProps} className="page-content"><div className="page-intro"><div className="eyebrow"><span className="eyebrow-dot"/> BUILD CONSISTENCY</div><h1>Make time for <span>growth.</span></h1><p>Plan a realistic schedule around your life. Adjust the sessions and your plan will remain saved on this device.</p></div><div className="planner-grid"><div className="planner-main"><div className="planner-header"><div><h2>Weekly study planner</h2><p>A flexible plan built around focused, practical sessions.</p></div><Chip variant="blue"><CalendarDays size={13}/> MY WEEK</Chip></div><div className="planner-days">{baseSchedule.map((day,i)=><div className="planner-day" key={day.day}><div className="day-icon">{day.day}</div><div className="day-body"><div><strong>{day.full}</strong><small>{day.label}</small></div><span>{saved.minutes[i]===0?"Rest day":`${saved.minutes[i]} min`}</span><input aria-label={`${day.full} study minutes`} type="range" min="0" max="240" step="15" value={saved.minutes[i]} onChange={e=>updateMinutes(i,Number(e.target.value))} style={{background:`linear-gradient(to right, #22ce9a ${saved.minutes[i]/240*100}%, #203044 ${saved.minutes[i]/240*100}%)`}}/></div></div>)}</div><div className="planner-hint"><CircleHelp size={18}/> Consistency beats intensity. A smaller schedule you can actually maintain is better than an ambitious schedule you abandon.</div></div><div className="planner-right"><div className="hours-card"><div className="hours-card-ring"><Clock3 size={34}/></div><span>YOUR WEEKLY COMMITMENT</span><div><strong>{(weekTotal/60).toFixed(1)}</strong><em>hours / week</em></div><p>{weekTotal>=600?"A balanced pace for this programme.":weekTotal>0?"A lighter pace is fine — move according to understanding.":"Add study time to design your week."}</p></div><div className="planner-tips"><h3>Our recommended rhythm</h3><div><CheckCircle2 size={17}/> Concept before implementation</div><div><CheckCircle2 size={17}/> Code independently every week</div><div><CheckCircle2 size={17}/> Review and refactor your work</div><div><CheckCircle2 size={17}/> Build projects as you progress</div></div><div className="planner-actions"><button className="btn btn-outline" onClick={()=>{setSaved(old=>({...old,minutes:baseSchedule.map(d=>d.minutes)}));setToast("Default schedule restored.")}}>Reset schedule</button><button className="btn btn-primary" onClick={()=>setToast("Study schedule saved automatically in this browser.")}><Check size={17}/> Save my plan</button></div></div></div><div className="month-section"><SectionHeading eyebrow="MONTH ONE" title="Your first four weeks" description="The fundamentals you will rebuild before tackling more complex systems."/><div className="month-grid">{weekOne.map(w=><div className="month-card" key={w.week}><span>WEEK {String(w.week).padStart(2,"0")}</span><h3>{w.title}</h3><p>{w.focus}</p><div><CheckCircle2 size={15}/>{w.deliverable}</div></div>)}</div></div></motion.div>}
      {view==="resources"&&<motion.div key="resources" {...motionProps} className="page-content"><div className="page-intro"><div className="eyebrow"><span className="eyebrow-dot"/> YOUR ENGINEERING TOOLKIT</div><h1>Learn from the <span>best sources.</span></h1><p>Our guided tutorials are the core. Trusted documentation and courses deepen your understanding as you grow.</p></div><SectionHeading eyebrow="CORE TECHNOLOGY STACK" title="Tools you'll learn to master" description="A carefully selected stack — depth before endless framework hopping."/><div className="tech-grid">{stack.map(s=><div className="tech-card" key={s.tag}><span className="tech-num">{s.tag}</span><span className="tech-tag">{s.role}</span><h3>{s.title}</h3><p>{s.description}</p></div>)}</div><div className="resource-heading"><SectionHeading eyebrow="OFFICIAL RESOURCES" title="Recommended learning library" description="Reliable places to expand your knowledge alongside our lessons."/></div><div className="resources-grid">{resources.map(r=><a href={r.url} target="_blank" rel="noreferrer" className="resource-card" key={r.name}><div className="resource-icon"><BookOpen size={24}/></div><span>{r.category}</span><h3>{r.name}</h3><div>Explore resource <ArrowUpRight size={17}/></div></a>)}</div><div className="manifesto"><img className="manifesto-logo" src="/brand/saire-horizontal.webp" alt="SAIRE-Linked horizontal brand logo"/><div className="eyebrow">OUR LEARNING PHILOSOPHY</div><h2>Understanding before automation.</h2><p>Learn the logic behind tools. Practice without copying. Ask why a system works, how it breaks, and what makes it trustworthy. Then build things that matter.</p><button className="btn btn-primary" onClick={()=>beginLesson()}>Start with Lesson 1 <ArrowRight size={16}/></button></div></motion.div>}
    </AnimatePresence></main>
    <footer className="footer"><span>© 2026 SAIRE-Linked. Built smarter. Learn deeper.</span><span>Digital Learning Platform <i/> Growth Initiative</span><button type="button" onClick={exportProgress}><Download size={15}/> Back up progress</button></footer>
  </div>
  <AnimatePresence>{projectOpen&&(()=>{const project=projects.find(p=>p.id===projectOpen);if(!project||project.locked)return null;const phase=phases.find(p=>p.id===project.phase)??phases[0];return <motion.div className="modal-cover" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} onClick={()=>setProjectOpen(null)}><motion.div className="project-modal" role="dialog" aria-modal="true" aria-label={project.name} initial={{y:30,opacity:0,scale:.96}} animate={{y:0,opacity:1,scale:1}} exit={{y:18,opacity:0}} transition={{duration:.25}} onClick={e=>e.stopPropagation()}><div className="modal-top"><Chip variant="green">PROJECT · PHASE {String(project.phase).padStart(2,"0")}</Chip><button className="icon-button" onClick={()=>setProjectOpen(null)} aria-label="Close project"><X size={20}/></button></div><div className="modal-icon"><Rocket size={35}/></div><h2>{project.name}</h2><p>{project.description}</p><h3>What you'll practise</h3><div className="skill-tags">{project.skills.map(s=><span key={s}>{s}</span>)}</div><h3>Success criteria</h3><ul className="modal-checklist"><li>Plan the requirements and explain your design decisions.</li><li>Build a working, maintainable implementation.</li><li>Test both expected behaviour and failure cases.</li><li>Document limitations, setup steps and next improvements.</li></ul><div className="modal-note">Detailed guided project instructions are released with their respective lessons. This is the curriculum milestone specification.</div><button className="btn btn-primary" onClick={()=>{setProjectOpen(null);setPhaseOpen(phase?.id??1);navigate("roadmap")}}>Explore phase syllabus <ArrowRight size={17}/></button></motion.div></motion.div>})()}</AnimatePresence>
  <AnimatePresence>{toast&&<motion.div className="toast" initial={{y:25,opacity:0}} animate={{y:0,opacity:1}} exit={{y:15,opacity:0}} role="status"><CheckCircle2 size={19}/>{toast}</motion.div>}</AnimatePresence>
 </div></MotionConfig>;
}
