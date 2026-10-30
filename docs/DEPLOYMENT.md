> **v2 note:** This earlier guide covers the original Next.js frontend. The added Django curriculum service needs its own deployment and PostgreSQL database. Follow `DJANGO_CMS_SETUP.md` for full-stack steps and environment variables; otherwise the frontend intentionally falls back to local demo curriculum.

# Local development and Render deployment

## Local

1. Ensure Node.js 20+ is installed (`node -v`).
2. Extract the project ZIP and open its root directory in VS Code.
3. Run `npm install` then `npm run dev`.
4. Visit `http://localhost:3000`.
5. Test all six navigation pages at desktop and mobile widths.
6. Open the classroom, complete Lesson 1, pass the quiz and mark it complete. Reload and confirm the progress persists **on this browser**.
7. Run `npm run typecheck` and `npm run build` before publishing.

## Deploy to Render as a Node.js web service

1. Create a GitHub repository and push the extracted source code. Keep `node_modules/` and `.next/` out of Git (see `.gitignore`).
2. In Render, create a **New Web Service** from the repository (or use the provided `render.yaml` blueprint if supported).
3. Set the **Build command** to `npm install && npm run build`.
4. Set the **Start command** to `npm run start`.
5. Use Node 22.x and configure Render's supplied `PORT` environment variable as normal.
6. Deploy, open the URL, and perform the same UI checks.
7. Connect a custom learning subdomain such as `learn.sairelinked.com` **only after** configuring its DNS records in your own domain provider and verifying the Render custom domain and TLS certificate.

### Domain and integration

The project is **not deployed** by this delivery. No domain, URL or Render environment has been created. The `learn.sairelinked.com` name is a deployment suggestion, not an existing website. Until you configure a custom domain, use the actual URL Render assigns.

The footer links back to SAIRE-Linked. No business data is read from the existing company's website or API. Keep this as a separate app/repository unless you intentionally choose to merge it.

## Before public production use

- Replace demo-only browser state with authenticated API-based persistence and access control.
- Validate inputs server-side; do not trust quiz grades sent from a browser.
- Set up backups, error monitoring, privacy policies and account deletion workflows.
- Author, review and publish additional content before marketing the whole programme as available.
- Integrate real enrolment and billing only after business model, security and compliance decisions.
- Add test automation, CI, performance budgets, production logs and an accessibility review.

## Troubleshooting

- **`next: command not found`**: run `npm install` in the project root.
- **Missing environment variables**: current MVP does not require any; future API keys should be server-side only.
- **Blank page or broken brand assets**: ensure the `public/brand` images were copied with the project.
- **Progress seems missing**: localStorage is browser- and origin-specific, and private browsing may clear it. The preview and deployed website may not share a web origin.
- **Animated movement feels too much**: enable reduced motion in your operating system; the interface honors that preference.
