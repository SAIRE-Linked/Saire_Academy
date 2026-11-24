import AcademyNavigation from '@/components/AcademyNavigation';
import AcademySignIn from '@/components/AcademySignIn';
import AccountControls from '@/components/AccountControls';
import '@/public/academy-auth.css';

export default function Home() {
  return (
    <main className="academy-entry">
      <header className="entry-header">
        <a className="entry-brand" href="/">
          <img src="/brand/saire-symbol.webp" alt="" />
          <span>SAIRE-Linked Academy</span>
        </a>
        <AcademyNavigation compact />
        <a href="/pathways/">Explore learning pathways</a>
        <a href="/demo/">Explore the demo</a>
        <AccountControls />
      </header>
      <section className="entry-hero" aria-labelledby="academy-title">
        <div className="entry-intro">
          <p className="entry-eyebrow">ENGINEERING LEARNING PLATFORM</p>
          <h1 id="academy-title">Learn AI engineering by building real projects.</h1>
          <p>SAIRE-Linked Academy takes you from programming foundations to AI and agentic systems. Follow a structured roadmap, practise with hands-on lessons, and prove what you can build through reviewed projects.</p>
          <dl className="entry-steps">
            <div><dt>Learn</dt><dd>Work through guided lessons in order.</dd></div>
            <div><dt>Build</dt><dd>Apply what you learn to a module project.</dd></div>
            <div><dt>Advance</dt><dd>Pass the project to unlock the next module.</dd></div>
          </dl>
        </div>
        <AcademySignIn />
      </section>
      <footer>SAIRE-Linked Academy · Powered by ProofLoop</footer>
    </main>
  );
}
