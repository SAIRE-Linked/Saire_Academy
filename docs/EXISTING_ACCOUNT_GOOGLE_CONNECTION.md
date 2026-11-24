# Existing Academy account: connect Google or GitHub

## What this page means

Google has returned to the Academy. This is different from the earlier Google redirect_uri_mismatch. The Academy found an existing account using the email address, and this provider identity is not linked to it. The existing account must be authenticated before adding a new sign-in method.

## Recover access now

1. Open http://localhost:3000/accounts/login/?next=/accounts/3rdparty/ .
2. Sign in with the username/password of your existing Academy account, or a provider already connected to it. This is your Academy password, not your Google password. Never enter your Google password into the Academy form.
3. On the connected sign-in methods page, choose **Connect Google** (or **Connect GitHub**), then continue through the confirmation and provider steps. Use the provider account you intended to link.
4. Confirm that the provider is listed, then return to your dashboard. Future sign-ins with that provider use the same learner record and progress.

Use one hostname consistently. If you use 127.0.0.1 rather than localhost, use that hostname in the links and keep its callback registered as explained in the earlier callback guide. The installed allauth version uses /accounts/3rdparty/ as its canonical connections URL; /accounts/social/connections/ redirects there for compatibility.

If you have forgotten the Academy password, use http://localhost:3000/accounts/password/reset/ . Password reset requires working outgoing email configuration; if email delivery is not configured, arrange recovery through the administrator. Do not create another learner account with another email to work around this, because it would have separate progress. No password, email, provider connection or user record is changed by installing this UI patch.

## This update

- The social signup page explains the difference between an existing learner and a new account. It includes a **Sign in to my existing account** link with the connections page as its next destination, plus a password recovery link.
- The connections page uses the existing Academy style and lists the current account, connected providers, explicit Connect Google/GitHub actions and a dashboard link. Existing disconnect validation is retained.
- Server-generated named URLs are used in the templates. Provider connect still runs through allauth's authenticated, state-protected and CSRF-protected flow. GET shows confirmation; it does not add a connection.
- Automatic account linking by matching email remains disabled. Duplicate-email signup remains rejected. A new, unique learner can still complete the normal signup form.

Extract this upgrade outside your project. Run **Check upgrade.cmd**, then **Apply upgrade.cmd** if compatible. The launcher finds the installer independently of your terminal's current folder and targets Documents/Saire_Academy. Conflicting local files stop the update before writing. Previous affected files are backed up; keep your normal full backup too. Restart Django so the templates are refreshed. No migration, seed, frontend build, dependency installation or OAuth credential change is needed.

## Verification and boundaries

The Django regression suite passed 128 tests, including seven new account-connection tests. These cover duplicate-email rejection with the recovery link, existing-password login and continuation, authentication for connections, CSRF/GET protection, Google/GitHub connection followed by a later provider login using the original user ID, rejection of an identity already connected elsewhere, and normal new-learner signup without administrator privileges. Provider responses are mocked in these tests; real Google/GitHub consent must still be completed by the account owner. This update does not connect any real account on their behalf. The package also passed guarded check/apply/repeat, conflict rejection with zero writes, exact Git patch application and ZIP integrity checks on separate fixtures.

Official references: https://docs.allauth.org/en/latest/socialaccount/configuration.html and https://docs.allauth.org/en/latest/socialaccount/templates.html .
