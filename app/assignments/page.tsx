"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, BookOpen, BrainCircuit, CalendarClock, CheckCircle2, Code2, Download, Github, Lightbulb, LockKeyhole, LogIn, LogOut, ShieldCheck, Terminal, Trophy } from "lucide-react";
import { LMS_API_URL } from "@/lib/lms-api";
import AcademyNavigation from "@/components/AcademyNavigation";
import { count } from "@/lib/academy-display";
import AccountControls from '@/components/AccountControls';
import { endBrowserSession, watchSessionEnd, SIGN_IN_URL } from '@/lib/browser-session';
import CodeDefenceRoom from "@/components/CodeDefenceRoom";
import LearningTwinPanel, { type TwinProfile } from "@/components/LearningTwinPanel";
import "./proofloop.css";
import "./learning-twin.css";

type Assignment = {
  locked?:boolean;
  slug:string;title:string;brief:string;course_slug:string;phase:number;module:string;
  duration_days?:number;has_starter:boolean;test_command:string;learning_outcomes:string[];
  review_questions:string[];grading:Record<string,number>;template_url:string;
};
type Review = {final_score:string;feedback:string;question_scores:number[];verified_test_score:number};
type Grading = {status:"awaiting_approval"|"queued"|"running"|"complete"|"error";github_commit_verified:boolean;verified_test_score:number|null;passed:number;failed:number;errors:number;failure_reason:string;completed_at:string|null};
type Submission = {id:number;commit_sha:string;status:string;submitted_at:string;late_days:number;defence_status?:"unstarted"|"draft"|"submitted";review:Review|null;grading:Grading|null};
type Attempt = {id:string;started_at:string;due_at:string;submissions:Submission[]};
type MentorMessage = { role:"mentor"|"learner"; text:string };
type MentorMode = "preview"|"ai"|"unconfigured";
const mentorWelcome: MentorMessage = { role:"mentor", text:"Hi, I’m the SAIRE Socratic Mentor. I’ll guide your thinking with questions and small hints rather than giving away the complete solution." };

const fade={initial:{opacity:0,y:15},animate:{opacity:1,y:0},transition:{duration:.4}};

function buildMentorReply(input:string, assignment?:Assignment){
  const text=input.trim().toLowerCase();
  const title=assignment?.title ?? "this assignment";
  if(!text){
    return "Start by telling me where you feel stuck. For example: understanding the brief, planning the functions, debugging a failing test, or preparing for your code defence.";
  }
  if(/start|begin|where do i start|first step|overview/.test(text)){
    return `Let's break ${title} into smaller steps. 1) Restate the problem in your own words. 2) List the inputs, outputs, and rules. 3) Write one small function first. 4) Run the visible tests. Which one of those four steps feels least clear right now?`;
  }
  if(/test|failing|error|bug|wrong|debug/.test(text)){
    return "Don't jump to the whole fix yet. Choose one failing example and trace it carefully: what input did you use, what output did you expect, what output did you actually get, and at which line does the behaviour stop matching your expectation?";
  }
  if(/function|logic|algorithm|calculate|discount|negative|validation/.test(text)){
    return "Good. Focus on the rule before the code. What should your function accept, what must it return, and which invalid inputs must it reject? Try writing that as plain English or a short docstring first, then check whether your implementation follows it.";
  }
  if(/submit|commit|repo|repository|github|sha/.test(text)){
    return "For the workflow, ask yourself three things: 1) Have you pushed the latest code to GitHub? 2) Does the commit SHA come from that pushed commit? 3) Can someone else clone the repo and run the visible tests successfully? If one of those is uncertain, fix that first.";
  }
  if(/review|defence|explain|question/.test(text)){
    return "For the code defence, prepare to explain decisions, not just outcomes. Why did you structure the solution that way? How does a key function work step by step? What edge case did you guard against? If requirements changed slightly, what would you refactor first?";
  }
  return "Let's reason it through together. Describe the exact part you're working on, what you expected to happen, and what actually happened. I’ll respond with hints and guiding questions instead of giving away the solution.";
}

export default function ProofLoopPage(){
  const [list,setList]=useState<Assignment[]>([]);
  const [chosen,setChosen]=useState<string>("");
  const [token,setToken]=useState<string>(""); // Memory only: deliberately not stored in localStorage.
  const [username,setUsername]=useState("");
  const [password,setPassword]=useState("");
  const [learner,setLearner]=useState("");
  const [attempt,setAttempt]=useState<Attempt|null>(null);
  const [loading,setLoading]=useState(false);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [repo,setRepo]=useState("");
  const [sha,setSha]=useState("");
  const [mentorInput,setMentorInput]=useState("");
  const [mentorMessages,setMentorMessages]=useState<MentorMessage[]>([mentorWelcome]);
  const [mentorMode,setMentorMode]=useState<MentorMode>("preview");
  const [mentorProvider,setMentorProvider]=useState<"gemini"|"openai"|null>(null);
  const [twinPersonalizationAvailable,setTwinPersonalizationAvailable]=useState(false);
  const [useTwinForMentor,setUseTwinForMentor]=useState(false);
  const [mentorLoading,setMentorLoading]=useState(false);
  const [mentorError,setMentorError]=useState("");
  const [learningTwin,setLearningTwin]=useState<TwinProfile|null>(null);
  const [twinLoading,setTwinLoading]=useState(false);
  const [twinError,setTwinError]=useState("");
  const twinRequestId=useRef(0);

  const request=useCallback(async<T,>(url:string, body?:object, auth=token):Promise<T>=>{
    let csrf='';
    if(body && auth==='session'){
      const out=await fetch('/api/v1/auth/csrf/',{credentials:'same-origin',cache:'no-store'});
      csrf=(await out.json()).csrfToken;
    }
    const res=await fetch(`${LMS_API_URL}${url}`,{
      method:body?"POST":"GET",cache:"no-store",credentials:"same-origin",
      headers:{"Accept":"application/json",...(csrf?{"X-CSRFToken":csrf}:{}),...(body?{"Content-Type":"application/json"}:{}),...(auth && auth!=="session"?{"Authorization":`Token ${auth}`}:{})},
      ...(body?{body:JSON.stringify(body)}:{})
    });
    if(!res.ok){
      const details=await res.json().catch(()=>({detail:res.statusText}));
      throw new Error(typeof details.detail==="string"?details.detail:`Request failed (${res.status}).`);
    }
    return res.json() as Promise<T>;
  },[token]);

  useEffect(()=>{
    fetch('/api/v1/auth/me/',{cache:'no-store'}).then(async res=>{if(res.ok){const me=await res.json();setToken('session');setLearner(me.username);}}).catch(()=>{});
  },[]);
  useEffect(()=>{
    let live=true;
    request<Assignment[]>("/assignments/",undefined,token).then(items=>{if(live){setList(items);setChosen(current => {
        const requested = new URLSearchParams(window.location.search).get("assignment");
        const unlocked = items.filter(assignment => !assignment.locked);
        if (requested) return requested;
        return unlocked.find(assignment => assignment.slug === current)?.slug
          ?? unlocked[0]?.slug ?? "";
      });}})
      .catch(()=>{if(live)setError("Django API is offline. Start the backend to view live assignments.");});
    return()=>{live=false;};
  },[request,token]);
  const selected=list.find(a=>a.slug===chosen && !a.locked);

  const refresh=useCallback(async(slug:string,auth=token)=>{
    try{const data=await request<Attempt>(`/assignments/${slug}/mine/`,undefined,auth);setAttempt(data);}
    catch{setAttempt(null);}
  },[request,token]);

  const loadMentor=useCallback(async(slug:string,auth=token)=>{
    if(!auth || !slug){setMentorMode("preview");return;}
    try{
      const data=await request<{mode:"ai"|"unconfigured";provider:"gemini"|"openai"|null;personalization_available:boolean;messages:MentorMessage[]}>(`/assignments/${slug}/mentor/`,undefined,auth);
      setMentorMessages(data.messages.length ? data.messages : [mentorWelcome]);
      setMentorMode(data.mode);
      setMentorProvider(data.provider ?? null);
      setTwinPersonalizationAvailable(Boolean(data.personalization_available));
      setMentorError("");
    }catch{
      // Most commonly, the learner has not started the assignment yet.
      setMentorMode("preview");
      setMentorProvider(null);setTwinPersonalizationAvailable(false);setUseTwinForMentor(false);
    }
  },[request,token]);

  const loadLearningTwin=useCallback(async(auth=token)=>{
    if(!auth) return;
    const requestId=++twinRequestId.current;
    setTwinLoading(true);setTwinError("");
    try{
      const result=await request<TwinProfile>("/learning-twin/me/",undefined,auth);
      if(twinRequestId.current===requestId)setLearningTwin(result);
    }catch(err){
      if(twinRequestId.current===requestId)setTwinError(err instanceof Error?err.message:"Unable to fetch skill evidence.");
    }finally{
      if(twinRequestId.current===requestId)setTwinLoading(false);
    }
  },[request,token]);

  useEffect(()=>{if(token==='session'){void loadLearningTwin();if(chosen){void refresh(chosen);void loadMentor(chosen);}}},[token,chosen,loadLearningTwin,refresh,loadMentor]);
  useEffect(()=>watchSessionEnd(()=>window.location.replace(SIGN_IN_URL)),[]);
  async function login(e:FormEvent){
    e.preventDefault();setLoading(true);setError("");
    try{
      const out=await request<{username:string;token:string}>("/auth/login/",{username,password},"");
      setToken(out.token);setLearner(out.username);setPassword("");setMessage("Signed in. Your token is held only for this page session.");
      await refresh(chosen,out.token);
      await loadMentor(chosen,out.token);
      await loadLearningTwin(out.token);
    }catch(err){setError(err instanceof Error?err.message:"Login failed.");}
    finally{setLoading(false);}
  }
  async function logout(){
    try{
      if(token && token!=="session") await request("/auth/logout/",{},token);
      await endBrowserSession();
    }catch(cause){setError("Could not log out. Check your connection and try again.");throw cause;}
    setToken("");setAttempt(null);setLearner("");setMessage("Signed out.");
    setMentorMode("preview");setMentorMessages([mentorWelcome]);setMentorError("");setMentorProvider(null);setTwinPersonalizationAvailable(false);setUseTwinForMentor(false);
    twinRequestId.current+=1;setLearningTwin(null);setTwinLoading(false);setTwinError("");
  }
  async function begin(){
    if(!selected)return;setLoading(true);setError("");
    try{
      const data=await request<{attempt:Attempt;created:boolean}>(`/assignments/${selected.slug}/start/`,{});
      setAttempt(data.attempt);setMessage(data.created?"Assignment started. Your deadline is now fixed.":"Your existing attempt and deadline are unchanged.");
      await loadMentor(selected.slug);
    }catch(err){setError(err instanceof Error?err.message:"Could not start assignment.");}
    finally{setLoading(false);}
  }
  async function starter(){
    if(!selected||!token)return;setLoading(true);setError("");
    try{
      const response=await fetch(`${LMS_API_URL}/assignments/${selected.slug}/starter/`,{credentials:"same-origin",headers:token==="session"?{}:{Authorization:`Token ${token}`}});
      if(!response.ok)throw new Error("Starter download failed.");
      const blob=await response.blob();const url=URL.createObjectURL(blob);
      const a=document.createElement("a");a.href=url;a.download=`${selected.slug}.zip`;document.body.appendChild(a);a.click();a.remove();
      URL.revokeObjectURL(url);setMessage("Starter ZIP downloaded. Extract it and begin coding!");
    }catch(err){setError(err instanceof Error?err.message:"Download failed.");}
    finally{setLoading(false);}
  }
  async function submit(e:FormEvent){
    e.preventDefault();if(!selected)return;setLoading(true);setError("");
    try{
      await request(`/assignments/${selected.slug}/submit/`,{repository_url:repo,commit_sha:sha,
        local_tests_passed:0,local_tests_failed:0,local_tests_errors:0});
      setMessage("Commit recorded. An instructor must approve the repository before independent grading begins.");
      setRepo("");setSha("");await refresh(selected.slug);
    }catch(err){setError(err instanceof Error?err.message:"Submission failed.");}
    finally{setLoading(false);}
  }
  function pick(slug:string){
    setChosen(slug);setMessage("");setError("");setAttempt(null);
    setMentorMessages([mentorWelcome]);setMentorMode("preview");setMentorInput("");setMentorError("");setUseTwinForMentor(false);
    if(token){void refresh(slug);void loadMentor(slug);}
  }
  async function mentorAsk(question:string){
    const trimmed=question.trim();
    if(!trimmed || mentorLoading) return;
    setMentorError("");
    setMentorInput("");
    if(mentorMode!=="ai" || !token || !attempt || !selected){
      const reply=buildMentorReply(trimmed,selected);
      setMentorMessages(old=>[...old,{role:"learner",text:trimmed},{role:"mentor",text:reply}]);
      return;
    }
    setMentorLoading(true);
    try{
      const data=await request<{learner_message:MentorMessage;mentor_message:MentorMessage}>(`/assignments/${selected.slug}/mentor/`,{message:trimmed,use_learning_twin:useTwinForMentor && twinPersonalizationAvailable});
      setMentorMessages(old=>[...old,data.learner_message,data.mentor_message]);
    }catch(err){
      setMentorInput(trimmed);
      setMentorError(err instanceof Error ? err.message : "The mentor is temporarily unavailable.");
    }finally{setMentorLoading(false);}
  }
  function askMentor(e:FormEvent){e.preventDefault();void mentorAsk(mentorInput);}
  function quickMentor(prompt:string){void mentorAsk(prompt);}
  async function clearMentor(){
    if(!selected) return;
    if(token && attempt){
      setMentorLoading(true);
      try{
        const csrf=token==='session'?(await (await fetch('/api/v1/auth/csrf/')).json()).csrfToken:'';
        const res=await fetch(`${LMS_API_URL}/assignments/${selected.slug}/mentor/`,{method:"DELETE",credentials:"same-origin",headers:token==="session"?{"X-CSRFToken":csrf}:{Authorization:`Token ${token}`}});
        if(!res.ok)throw new Error("Could not delete mentor history.");
        setMentorError("");setMentorMessages([mentorWelcome]);
      }catch(err){setMentorError(err instanceof Error?err.message:"History deletion failed.");}
      finally{setMentorLoading(false);}
    }else{setMentorMessages([mentorWelcome]);setMentorError("");}
  }

  return <main className="proofloop-page">
    <AcademyNavigation compact active="/assignments/" />
    {!token && <p><a href="/dashboard/">Personal dashboard</a> · <a href="/">Sign in with Google or GitHub</a></p>}
    <div className="proofloop-back"><a href="/"><ArrowLeft size={16}/> Back to Academy</a><span>SAIRE-LINKED / PROOFLOOP</span></div>
    <AccountControls username={token ? learner : null} onLogout={logout} />
    <p className="project-local-rule">End-of-module projects: develop and test in your local IDE, commit and push with Git, then submit through ProofLoop. The lesson practice studio does not submit or grade projects.</p>
    <motion.header {...fade} className="proofloop-hero">
      <div className="proofloop-hero-icon"><img src="/brand/saire-symbol.webp" alt="SAIRE-Linked Academy logo"/></div>
      <div><div className="proofloop-eyebrow"><span/> THE ENGINEERING APPRENTICESHIP ENGINE</div>
        <h1>Learn. Build. <em>Prove.</em></h1>
        <p>Start a real project, test your work locally, submit an exact Git commit, and defend your technical decisions in an instructor review.</p>
      </div>
      <div className="proofloop-hero-badge"><ShieldCheck size={18}/> Instructor-verified grading</div>
    </motion.header>
    {message&&<p role="status" className="proofloop-notice good">{message}</p>}
    {error&&<p role="alert" className="proofloop-notice bad">{error}</p>}
    <div className="proofloop-grid">
      <motion.section {...fade} className="proofloop-panel" aria-label="Published assignments">
        <div className="proofloop-heading"><Code2 size={20}/><h2>Assignment lab</h2></div>
        <p className="proofloop-muted">Instructor-published, original SAIRE coding challenges.</p>
        {list.length?list.map(a=><button key={a.slug} className={`proofloop-choice ${chosen===a.slug?"active":""}`} disabled={a.locked} onClick={()=>pick(a.slug)}>
          <span>PHASE {String(a.phase).padStart(2,"0")} · {a.duration_days ? count(a.duration_days, 'day').toUpperCase() : 'Duration pending'}</span><strong>{a.locked?"🔒 ":""}{a.title}</strong><small>{a.module}</small><ArrowRight size={18}/>
        </button>):<div className="proofloop-empty">Assignments appear here when Django is running and the starter assignment has been seeded.</div>}
        <div className="proofloop-sidehint"><Terminal size={19}/><div><strong>Prefer your terminal?</strong><small>Install our CLI and run <code>saire list</code>, <code>saire start</code> and <code>saire submit</code>.</small></div></div>
      </motion.section>
      <motion.section {...fade} className="proofloop-panel proofloop-detail">
        {selected?<>
          <div className="proofloop-tag"><BookOpen size={15}/> {selected.module} / Phase {selected.phase}</div>
          <h2>{selected.title}</h2><p>{selected.brief}</p>
          <h3>You'll demonstrate</h3>
          <ul className="proofloop-list">{selected.learning_outcomes.map(x=><li key={x}><CheckCircle2 size={17}/>{x}</li>)}</ul>
          <div className="proofloop-data"><span><CalendarClock size={17}/> {selected.duration_days ? `${count(selected.duration_days, 'day')} after starting` : 'Duration pending'}</span><span><Trophy size={17}/> 50% tests · 30% defence · 10% quality · 10% deadline</span></div>
          {!token?<form className="proofloop-login" onSubmit={login}>
            <h3><LockKeyhole size={18}/> Sign in to start</h3><p>For this pilot, an instructor creates your learner account in Django Admin.</p>
            <label htmlFor="pl-username">Username</label><input id="pl-username" required autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)}/>
            <label htmlFor="pl-password">Password</label><input id="pl-password" required type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/>
            <button className="proofloop-primary" disabled={loading}><LogIn size={17}/> Sign in to ProofLoop</button>
          </form>:<div className="proofloop-workspace">
            <div className="proofloop-user"><span>Signed in as <strong>{learner}</strong></span><button onClick={()=>void logout().catch(()=>{})}><LogOut size={15}/> Log out</button></div>
            {!attempt&&<p><a href="/dashboard/?view=academy&section=handbook">Review the rules and Getting Ready checklist</a> before starting.</p>}
            {!attempt?<button className="proofloop-primary" disabled={loading} onClick={begin}><Code2 size={18}/> Start project and set deadline</button>:<>
              <div className="proofloop-deadline"><CalendarClock size={19}/><div><small>YOUR PROJECT DEADLINE</small><strong>{new Date(attempt.due_at).toLocaleString()}</strong></div></div>
              <div className="proofloop-actions"><button className="proofloop-primary" onClick={starter} disabled={!selected.has_starter||loading}><Download size={18}/> Download starter</button><button className="proofloop-secondary" onClick={()=>refresh(selected.slug)} disabled={loading}>Refresh status</button></div>
              <h3>Submit a pushed GitHub commit</h3><p>Use the CLI for the easiest experience. An instructor approves your repository before a separate worker verifies the GitHub commit and runs trusted tests. You can then complete your code defence.</p>
              <form className="proofloop-submit" onSubmit={submit}>
                <label htmlFor="pl-repo">GitHub repository URL</label><input id="pl-repo" required placeholder="https://github.com/you/project" value={repo} onChange={e=>setRepo(e.target.value)}/>
                <label htmlFor="pl-sha">40-character Git commit SHA</label><input id="pl-sha" required minLength={40} maxLength={40} placeholder="git rev-parse HEAD" value={sha} onChange={e=>setSha(e.target.value)}/>
                <button className="proofloop-primary" disabled={loading}><Github size={17}/> Submit commit for review</button>
              </form>
              {attempt.submissions.length>0&&<div className="proofloop-history"><h3>Your submissions</h3>{attempt.submissions.map(s=><div className="proofloop-submission" key={s.id}>
                <div><code>{s.commit_sha.slice(0,12)}</code><small>{new Date(s.submitted_at).toLocaleString()} · {s.late_days===0?"On time":`${s.late_days} late day(s)`}</small></div>
                <strong>{s.review?`${s.review.final_score}% · Reviewed`:s.defence_status==="submitted"?"Defence handed in · Awaiting review":s.defence_status==="draft"?"Defence draft saved":"Code defence pending"}</strong>
                {s.grading&&<div className="proofloop-grade"><ShieldCheck size={15}/>
                  {s.grading.status==="awaiting_approval"&&"Waiting for instructor repository approval"}
                  {s.grading.status==="queued"&&"Approved · Waiting for isolated grader"}
                  {s.grading.status==="running"&&"Independent grading in progress"}
                  {s.grading.status==="complete"&&`GitHub commit verified · ${s.grading.verified_test_score}% tests (${s.grading.passed} passed, ${s.grading.failed} failed, ${s.grading.errors} errors)`}
                  {s.grading.status==="error"&&`Grading error · ${s.grading.failure_reason || "Ask the instructor to review"}`}
                </div>}
                {s.review?.feedback&&<p>{s.review.feedback}</p>}
                <CodeDefenceRoom assignment={selected.slug} submissionId={s.id} request={request}
                  onChanged={() => void refresh(selected.slug)} />
              </div>)}</div>}
            </>}
          </div>}
          <div className="proofloop-questions"><h3>Five code defence questions</h3><ol>{selected.review_questions.map(q=><li key={q}>{q}</li>)}</ol></div>
          <div className="proofloop-mentor" id="project-mentor">
            <div className="proofloop-mentor-top">
              <div>
                <span className="proofloop-mentor-kicker"><BrainCircuit size={15}/> SAIRE SOCRATIC MENTOR</span>
                <h3>Think before you code</h3>
              </div>
              <div className="proofloop-mentor-chip"><Lightbulb size={14}/> {mentorMode==="ai" && token && attempt ? `${mentorProvider === "gemini" ? "Gemini" : "OpenAI"} AI · Account history` : "Guided preview · Not AI"}</div>
            </div>
            <p className="proofloop-mentor-intro">{mentorMode==="ai" && token && attempt
              ? "Your messages are saved to your learner account and sent to the configured AI provider. For Gemini free-tier testing, use only fictional examples; do not share private learner information, API keys or confidential code."
              : "This is a local, rule-based guided-hint preview, not an AI model. To enable live AI, sign in, start the assignment and configure GEMINI_API_KEY on Django (or OPENAI_API_KEY if using OpenAI)."}</p>
            {mentorMode==="ai" && token && attempt && twinPersonalizationAvailable && <label className="proofloop-twin-optin">
              <input type="checkbox" checked={useTwinForMentor} onChange={event=>setUseTwinForMentor(event.target.checked)}/>
              <span><strong>Personalise hints with my Learning Twin</strong><small>Optional for this session. Share a short summary of assessed skill areas with {mentorProvider==="gemini" ? "Gemini" : "the configured AI provider"}; no numerical grades, commit IDs, review notes or hidden tests.</small></span>
            </label>}
            {mentorError && <p role="alert" className="proofloop-mentor-error">{mentorError}</p>}
            <div className="proofloop-mentor-quick">
              <button type="button" disabled={mentorLoading} onClick={()=>quickMentor("Where do I start?")}>Where do I start?</button>
              <button type="button" disabled={mentorLoading} onClick={()=>quickMentor("A test is failing.")}>A test is failing</button>
              <button type="button" disabled={mentorLoading} onClick={()=>quickMentor("Help me prepare for the review.")}>Prepare for the review</button>
            </div>
            <div className="proofloop-mentor-thread" aria-live="polite">
              {mentorMessages.map((message,index)=><div key={`${message.role}-${index}`} className={`proofloop-mentor-msg ${message.role}`}>
                <strong>{message.role === "mentor" ? "Mentor" : "You"}</strong>
                <p>{message.text}</p>
              </div>)}
            </div>
            <div className="proofloop-mentor-tools"><span>{mentorMode==="ai"&&token&&attempt ? "Signed-in conversation" : "Preview messages are not saved"}</span><button type="button" onClick={clearMentor} disabled={mentorLoading}>Clear {token&&attempt ? "saved history" : "preview"}</button></div>
            <form className="proofloop-mentor-form" onSubmit={askMentor}>
              <label htmlFor="mentor-input">Ask for a hint or describe where you are stuck</label>
              <textarea id="mentor-input" maxLength={1200} value={mentorInput} onChange={e=>setMentorInput(e.target.value)} placeholder="Example: My total is wrong when a negative discount is entered. How should I think about debugging this?" rows={4}/>
              <button className="proofloop-primary" type="submit" disabled={mentorLoading || !mentorInput.trim()}><BrainCircuit size={17}/> {mentorLoading ? "Thinking…" : "Ask the mentor"}</button>
            </form>
          </div>
        </>:<div className="proofloop-empty">{chosen ? list.some(item => item.slug === chosen && item.locked) ? 'This project is locked. Complete its prerequisites to open the brief.' : 'This project is unavailable. Choose a published assignment.' : 'Choose a published assignment to get started.'}</div>}
      </motion.section>
    </div>
    <LearningTwinPanel profile={learningTwin} loading={twinLoading} error={twinError}
      authenticated={Boolean(token)} onRefresh={()=>{void loadLearningTwin();}}/>
    <div className="proofloop-footnote"><ShieldCheck size={17}/> Local test reports are advisory. Instructor-approved submissions are tested on a separate restricted worker, never inside Django. Final grades combine those results with a human code defence and code-quality review.</div>
  </main>;
}
