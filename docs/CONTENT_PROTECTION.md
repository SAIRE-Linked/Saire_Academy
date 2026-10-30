# SAIRE-Linked Academy — Content Protection: honest safeguards and limits

## Implemented in this v3 source

- **Print-only course view:** A `@media print` rule hides the published lesson article and displays a learner-friendly licensed-material notice. Only the active classroom view is affected; other pages remain printable.
- **Ctrl/Cmd+S deterrent:** While in the classroom, a keyboard handler intercepts the common shortcut and shows a non-blocking notice. Browser menus, DevTools and other saving methods may bypass it.
- **Visible copyright watermark:** The active lesson displays a small licensed-material marker. It is not a forensic screenshot watermark.
- **Code samples remain copyable** for assignments. Do not disable context menus globally or block text selection; accessibility and learning matter.

## Not achievable reliably from a normal webpage

- Prevent operating system screenshots, external cameras, recording extensions, or someone transcribing displayed text.
- Keep curriculum private if it is shipped in the Next.js JavaScript bundle or the demo fallback `data/curriculum.ts`.
- Restrict distribution by relying on CSS, JavaScript, copy blocking, keyboard shortcuts or obfuscation alone.

## Production prerequisites (NOT implemented in this release)

1. Replace local-only learner profiles with Django authentication and verified enrolments.
2. Enforce object-level permission checks on every content API response; never rely solely on frontend route guards.
3. Never bundle paid lesson text, hidden grading tests or private solutions into client JavaScript. Fetch only authorised content after login.
4. Add per-learner rate limits, reasonable caching, abuse monitoring and audit logs.
5. Add optional dynamic watermarks (short pseudonymous learner ID and session timestamp), with transparent privacy notices and proportional retention.
6. Use expiring URLs for downloadable assets; keep private instructor tests in isolated grading workers.
7. Give paying learners accessible note-taking, code copying, accessible transcripts, and permitted authorised downloads. Provide reasonable accommodations.
8. Maintain an original-content register, licensing metadata and takedown process; do not publish third-party starter code without permission.

## Risk posture

Treat print and save deterrence as **visible reminders**, not DRM or a guarantee of copy protection. Test in Chrome/Firefox/Edge on Windows and macOS; keyboard and print behaviour varies.

Source: MDN, Printing — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing
Source: MDN, Screen Capture API — https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API
