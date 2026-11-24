import { BookOpen, CalendarDays, ClipboardList, Compass, FileText, GraduationCap, LayoutDashboard, Map, NotebookPen, Rocket, ShieldCheck, Target, Terminal } from 'lucide-react';

const groups = [
  { title: 'Workspace', links: [
    {label: 'Dashboard', to: 'overview', icon: LayoutDashboard}, {label: 'Study planner', to: 'planner', icon: CalendarDays}] },
  { title: 'Smart Classroom', links: [
    {label: 'My classroom', to: 'classroom', icon: BookOpen}, {label: 'Course roadmap', to: 'roadmap', icon: Map},
    {label: 'Learning pathways', to: '/pathways/', icon: Compass}] },
  { title: 'Engineering Lab', links: [
    {label: 'Project briefs', to: 'projects', icon: Rocket}, {label: 'Getting ready', to: 'academy&section=setup', icon: Terminal}] },
  { title: 'ProofLoop Centre', links: [
    {label: 'Assignments & reviews', to: '/assignments/', icon: ClipboardList}] },
  { title: 'Learning Twin', links: [
    {label: 'My skill evidence', to: '/assignments/#learning-twin', icon: Target}, {label: 'Revision & milestones', to: 'academy&section=revision', icon: NotebookPen}] },
  { title: 'Support', links: [
    {label: 'Study hub', to: 'academy&section=welcome', icon: GraduationCap}, {label: 'Handbook & help', to: 'academy&section=handbook', icon: ShieldCheck},
    {label: 'Resource library', to: 'resources', icon: FileText}] },
];

export default function AcademyNavigation({active, course, compact = false, demo = false}: {active?: string; course?: string; compact?: boolean; demo?: boolean}) {
  const navigation = <nav className="academy-v11-nav" aria-label="Academy navigation">{groups.map(group =>
    <div key={group.title} className="academy-nav-group"><strong>{group.title}</strong>
      {group.links.map(({label, to, icon: Icon}) => {
        const base = demo && !to.startsWith('academy') ? '/demo/' : '/dashboard/';
        const href = to.startsWith('/') ? to : `${base}?view=${to}${course ? '&course=' + encodeURIComponent(course) : ''}`;
        return <a key={to} href={href} aria-current={to === active ? 'page' : undefined}><Icon size={16} aria-hidden="true"/>{label}</a>;
      })}
    </div>)}</nav>;
  return compact ? <details className="academy-nav-menu"><summary>Academy menu</summary>{navigation}</details> : navigation;
}
