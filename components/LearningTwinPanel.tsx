"use client";

import { motion } from "framer-motion";
import { Activity, ArrowRight, BookOpenCheck, BrainCircuit, ChevronRight, ClipboardCheck, Eye, RefreshCw, ShieldCheck, Sparkles, Target } from "lucide-react";

export type SkillEvidence = {
  assignment_slug: string;
  assignment_title: string;
  commit: string;
  dimension: "tests" | "defence" | "quality";
  metric: string;
  score: number;
  weight: number;
  source: "instructor_review" | "independent_grader";
  reviewed_at: string;
};
export type TwinSkill = {
  slug: string;
  name: string;
  description: string;
  category: string;
  position: number;
  score: number | null;
  status: "not_assessed" | "needs_practice" | "developing" | "strong_evidence";
  evidence_strength: "none" | "initial" | "growing" | "repeated";
  evidence_count: number;
  projects_count: number;
  next_assignment: string | null;
  next_action: string;
  evidence: SkillEvidence[];
};
export type TwinProfile = {
  username: string;
  methodology: string;
  overview: { skills_total: number; skills_assessed: number; reviewed_projects: number; evidence_items: number };
  skills: TwinSkill[];
  recommendations: { skill_slug: string; skill_name: string; action: string; reason: string }[];
};

const labels = {
  not_assessed: "Not yet assessed",
  needs_practice: "Needs practice",
  developing: "Developing",
  strong_evidence: "Strong observed result",
} as const;
const strengths = {
  none: "No assessed project yet",
  initial: "Initial evidence · 1 project",
  growing: "Growing evidence · 2–3 projects",
  repeated: "Repeated evidence · 4+ projects",
} as const;

function ScoreBar({ score }: { score: number | null }) {
  return (
    <div className="twin-score-meter" role={score === null ? undefined : "progressbar"}
      aria-label="Observed rubric performance" aria-valuemin={0} aria-valuemax={100}
      aria-valuenow={score === null ? undefined : score}>
      <motion.div className="twin-score-fill" initial={{ width: 0 }}
        animate={{ width: `${score ?? 0}%` }} transition={{ duration: .75, ease: "easeOut" }}/>
    </div>
  );
}

export default function LearningTwinPanel({ profile, loading, error, authenticated, onRefresh }:
  { profile: TwinProfile | null; loading: boolean; error: string; authenticated: boolean; onRefresh: () => void }) {
  return <section id="learning-twin" className="learning-twin-panel" aria-labelledby="learning-twin-heading">
    <div className="learning-twin-heading">
      <div>
        <div className="twin-eyebrow"><BrainCircuit size={16}/> SAIRE LEARNING TWIN · V8</div>
        <h2 id="learning-twin-heading">Your engineering evidence, <span>made visible.</span></h2>
        <p>A practical skills profile built from reviewed code—not guesses about your intelligence.</p>
      </div>
      {authenticated && <button className="twin-refresh" type="button" disabled={loading} onClick={onRefresh}>
        <RefreshCw size={16} className={loading ? "twin-spin" : undefined}/> Refresh evidence
      </button>}
    </div>
    {!authenticated ? <div className="twin-empty">
      <ShieldCheck size={28}/>
      <h3>Private to each learner</h3>
      <p>Sign in above to view your verified assessment evidence, skills to practise, and recommended next steps.</p>
    </div> : loading && !profile ? <div className="twin-empty" role="status"><Activity size={26}/><p>Loading your assessment evidence…</p></div>
      : error && !profile ? <div className="twin-empty" role="alert"><h3>Unable to load your Learning Twin</h3><p>{error}</p><button className="twin-refresh" onClick={onRefresh}>Try again</button></div>
      : profile ? <>
        {error && <p className="twin-error" role="alert">{error}</p>}
        <div className="twin-metrics">
          <div><BookOpenCheck size={21}/><strong>{profile.overview.skills_assessed}<small> / {profile.overview.skills_total}</small></strong><span>Skills with evidence</span></div>
          <div><ClipboardCheck size={21}/><strong>{profile.overview.reviewed_projects}</strong><span>Projects reviewed</span></div>
          <div><Eye size={21}/><strong>{profile.overview.evidence_items}</strong><span>Rubric observations</span></div>
        </div>
        {profile.overview.reviewed_projects === 0 && <div className="twin-first-step">
          <Target size={24}/><div><h3>Your first assessment starts your profile</h3>
          <p>Complete an original coding project, submit your Git commit, and receive an instructor review. Local self-reported test counts and mentor conversations never create skill scores.</p></div>
        </div>}
        <div className="twin-subsection-title"><h3>Skill evidence</h3><span>Scores are observed rubric results, not mastery certificates</span></div>
        <div className="twin-skills-grid">
          {profile.skills.map((skill) => <div className="twin-skill" key={skill.slug}>
            <div className="twin-skill-head"><div><span className="twin-skill-category">{skill.category.replaceAll("_", " ")}</span><h4>{skill.name}</h4></div>
              <div className="twin-score">{skill.score === null ? "—" : `${skill.score}%`}</div>
            </div>
            <p>{skill.description}</p>
            <ScoreBar score={skill.score}/>
            <div className="twin-skill-meta"><span className={`twin-status status-${skill.status}`}>{labels[skill.status]}</span><span>{strengths[skill.evidence_strength]}</span></div>
            <details className="twin-evidence-details">
              <summary><Eye size={14}/> View supporting evidence <ChevronRight size={14}/></summary>
              {skill.evidence.length ? skill.evidence.map((evidence, index) => <div key={`${evidence.assignment_slug}-${evidence.dimension}-${index}`} className="twin-evidence-item">
                <strong>{evidence.assignment_title}</strong>
                <span>{evidence.metric}: {evidence.score}% · {evidence.source === "independent_grader" ? "Independently graded" : "Instructor review"}</span>
                <small>Commit {evidence.commit} · {new Date(evidence.reviewed_at).toLocaleDateString()} · rubric weight {evidence.weight}</small>
              </div>) : <p className="twin-no-evidence">This skill hasn't been assessed through a mapped, reviewed project yet.</p>}
            </details>
          </div>)}
        </div>
        <div className="twin-recommendations"><div className="twin-subsection-title"><h3><Sparkles size={17}/> Recommended next steps</h3><span>Based on the available evidence</span></div>
          {profile.recommendations.length ? profile.recommendations.map((item, index) => <div key={item.skill_slug} className="twin-recommendation">
            <span className="twin-step-num">{String(index+1).padStart(2,"0")}</span><div><strong>{item.skill_name}</strong><small>{item.reason}</small><p>{item.action}</p></div><ArrowRight size={18}/>
          </div>) : <p>Once instructors map and review assessments, suitable practice steps will appear here.</p>}
        </div>
        <p className="twin-methodology"><ShieldCheck size={16}/>{profile.methodology}</p>
      </> : <div className="twin-empty"><p>No Learning Twin information is available yet.</p></div>}
  </section>;
}
