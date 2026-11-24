# Existing-account Google/GitHub connection — v10.6.2

Google has returned successfully but the Academy already has this email on an unconnected account. First sign in to your existing Academy account at http://localhost:3000/accounts/login/?next=/accounts/3rdparty/ then connect your provider. See files/docs/EXISTING_ACCOUNT_GOOGLE_CONNECTION.md.

This update adds clearer signup recovery links and a branded connected-accounts page. It preserves the secure existing-account linking policy. It does not connect or modify a real account, reset any password, merge users or change progress.

Extract outside the project. Run Check upgrade.cmd then Apply upgrade.cmd if compatible. Both target Documents/Saire_Academy and locate the installer correctly. Conflicts stop all changes before writing; existing affected files are backed up. Keep a full backup. Restart Django. No migration, seed, frontend build, dependency or credential change is needed. Use either the installer or Git patch, not both.
