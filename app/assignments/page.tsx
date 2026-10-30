"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, BookOpen, CalendarClock, CheckCircle2, Code2, Download, Github, LockKeyhole, LogIn, LogOut, ShieldCheck, Terminal, Trophy } from "lucide-react";
import { LMS_API_URL } from "@/lib/lms-api";
import "./proofloop.css";

type Assignment = {
  slug:string;title:string;brief:string;course_slug:string;phase:number;module:string;
  duration_days:number;has_starter:boolean;test_command:string;learning_outcomes:string[];
  review_questions:string[];grading:Record<string,number>;template_url:string;
};
type Review = {final_score:string;feedback:string;question_scores:number[];verified_test_score:number};
type Submission = {id:number;commit_sha:string;status:string;submitted_at:string;late_days:number;review:Review|null};
type Attempt = {id:string;started_at:string;due_at:string;submissions:Submission[]};

const fade={initial:{opacity:0,y:15},animate:{opacity:1,y:0},transition:{duration:.4}};

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

  const request=useCallback(async<T,>(url:string, body?:object, auth=token):Promise<T>=>{
    const res=await fetch(`${LMS_API_URL}${url}`,{
      method:body?"POST":"GET",cache:"no-store",
      headers:{"Accept":"application/json",...(body?{"Content-Type":"application/json"}:{}),...(auth?{"Authorization":`Token ${auth}`}:{})},
      ...(body?{body:JSON.stringify(body)}:{})
    });
    if(!res.ok){
      const details=await res.json().catch(()=>({detail:res.statusText}));
      throw new Error(typeof details.detail==="string"?details.detail:`Request failed (${res.status}).`);
    }
    return res.json() as Promise<T>;
  },[token]);

  useEffect(()=>{
    let live=true;
    request<Assignment[]>("/assignments/",undefined,"").then(items=>{if(live){setList(items);setChosen(items[0]?.slug??"");}})
      .catch(()=>{if(live)setError("Django API is offline. Start the backend to view live assignments.");});
    return()=>{live=false;};
  },[request]);
  const selected=list.find(a=>a.slug===chosen);

  const refresh=useCallback(async(slug:string,auth=token)=>{
    try{const data=await request<Attempt>(`/assignments/${slug}/mine/`,undefined,auth);setAttempt(data);}
    catch{setAttempt(null);}
  },[request,token]);

  async function login(e:FormEvent){
    e.preventDefault();setLoading(true);setError("");
    try{
      const out=await request<{username:string;token:string}>("/auth/login/",{username,password},"");
      setToken(out.token);setLearner(out.username);setPassword("");setMessage("Signed in. Your token is held only for this page session.");
      await refresh(chosen,out.token);
    }catch(err){setError(err instanceof Error?err.message:"Login failed.");}
    finally{setLoading(false);}
  }
  async function logout(){
    try{await request("/auth/logout/",{},token);}catch{/* token still cleared locally */}
    setToken("");setAttempt(null);setLearner("");setMessage("Signed out.");
  }
  async function begin(){
    if(!selected)return;setLoading(true);setError("");
    try{
      const data=await request<{attempt:Attempt;created:boolean}>(`/assignments/${selected.slug}/start/`,{});
      setAttempt(data.attempt);setMessage(data.created?"Assignment started. Your deadline is now fixed.":"Your existing attempt and deadline are unchanged.");
    }catch(err){setError(err instanceof Error?err.message:"Could not start assignment.");}
    finally{setLoading(false);}
  }
  async function starter(){
    if(!selected||!token)return;setLoading(true);setError("");
    try{
      const response=await fetch(`${LMS_API_URL}/assignments/${selected.slug}/starter/`,{headers:{Authorization:`Token ${token}`}});
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
      setMessage("Commit recorded. Independent tests and instructor review are still pending.");
      setRepo("");setSha("");await refresh(selected.slug);
    }catch(err){setError(err instanceof Error?err.message:"Submission failed.");}
    finally{setLoading(false);}
  }
  function pick(slug:string){setChosen(slug);setMessage("");setError("");setAttempt(null);if(token)void refresh(slug);}

  return <main className="proofloop-page">
    <div className="proofloop-back"><a href="/"><ArrowLeft size={16}/> Back to Academy</a><span>SAIRE-LINKED / PROOFLOOP v0.1</span></div>
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
        {list.length?list.map(a=><button key={a.slug} className={`proofloop-choice ${chosen===a.slug?"active":""}`} onClick={()=>pick(a.slug)}>
          <span>PHASE {String(a.phase).padStart(2,"0")} · {a.duration_days} DAYS</span><strong>{a.title}</strong><small>{a.module}</small><ArrowRight size={18}/>
        </button>):<div className="proofloop-empty">Assignments appear here when Django is running and the starter assignment has been seeded.</div>}
        <div className="proofloop-sidehint"><Terminal size={19}/><div><strong>Prefer your terminal?</strong><small>Install our CLI and run <code>saire list</code>, <code>saire start</code> and <code>saire submit</code>.</small></div></div>
      </motion.section>
      <motion.section {...fade} className="proofloop-panel proofloop-detail">
        {selected?<>
          <div className="proofloop-tag"><BookOpen size={15}/> {selected.module} / Phase {selected.phase}</div>
          <h2>{selected.title}</h2><p>{selected.brief}</p>
          <h3>You'll demonstrate</h3>
          <ul className="proofloop-list">{selected.learning_outcomes.map(x=><li key={x}><CheckCircle2 size={17}/>{x}</li>)}</ul>
          <div className="proofloop-data"><span><CalendarClock size={17}/> {selected.duration_days}-day window after starting</span><span><Trophy size={17}/> 50% tests · 30% defence · 10% quality · 10% deadline</span></div>
          {!token?<form className="proofloop-login" onSubmit={login}>
            <h3><LockKeyhole size={18}/> Sign in to start</h3><p>For this pilot, an instructor creates your learner account in Django Admin.</p>
            <label htmlFor="pl-username">Username</label><input id="pl-username" required autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)}/>
            <label htmlFor="pl-password">Password</label><input id="pl-password" required type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/>
            <button className="proofloop-primary" disabled={loading}><LogIn size={17}/> Sign in to ProofLoop</button>
          </form>:<div className="proofloop-workspace">
            <div className="proofloop-user"><span>Signed in as <strong>{learner}</strong></span><button onClick={logout}><LogOut size={15}/> Sign out</button></div>
            {!attempt?<button className="proofloop-primary" disabled={loading} onClick={begin}><Code2 size={18}/> Start project and set deadline</button>:<>
              <div className="proofloop-deadline"><CalendarClock size={19}/><div><small>YOUR PROJECT DEADLINE</small><strong>{new Date(attempt.due_at).toLocaleString()}</strong></div></div>
              <div className="proofloop-actions"><button className="proofloop-primary" onClick={starter} disabled={!selected.has_starter||loading}><Download size={18}/> Download starter</button><button className="proofloop-secondary" onClick={()=>refresh(selected.slug)} disabled={loading}>Refresh status</button></div>
              <h3>Submit a pushed GitHub commit</h3><p>Use the CLI for the easiest experience. This web form records a commit, but does not verify test correctness.</p>
              <form className="proofloop-submit" onSubmit={submit}>
                <label htmlFor="pl-repo">GitHub repository URL</label><input id="pl-repo" required placeholder="https://github.com/you/project" value={repo} onChange={e=>setRepo(e.target.value)}/>
                <label htmlFor="pl-sha">40-character Git commit SHA</label><input id="pl-sha" required minLength={40} maxLength={40} placeholder="git rev-parse HEAD" value={sha} onChange={e=>setSha(e.target.value)}/>
                <button className="proofloop-primary" disabled={loading}><Github size={17}/> Submit commit for review</button>
              </form>
              {attempt.submissions.length>0&&<div className="proofloop-history"><h3>Your submissions</h3>{attempt.submissions.map(s=><div className="proofloop-submission" key={s.id}>
                <div><code>{s.commit_sha.slice(0,12)}</code><small>{new Date(s.submitted_at).toLocaleString()} · {s.late_days===0?"On time":`${s.late_days} late day(s)`}</small></div>
                <strong>{s.review?`${s.review.final_score}% · Reviewed`:"Review pending"}</strong>{s.review?.feedback&&<p>{s.review.feedback}</p>}
              </div>)}</div>}
            </>}
          </div>}
          <div className="proofloop-questions"><h3>Five code defence questions</h3><ol>{selected.review_questions.map(q=><li key={q}>{q}</li>)}</ol></div>
        </>:<div className="proofloop-empty">Choose a published assignment to get started.</div>}
      </motion.section>
    </div>
    <div className="proofloop-footnote"><ShieldCheck size={17}/> Local test reports are untrusted learner evidence. Official scores are published only after an instructor verifies results and completes a code review. Learner code is never executed by this Django API.</div>
  </main>;
}
