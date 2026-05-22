---
name: feedback-playwright-testing
description: Gotchas for Playwright-driven testing of app.html — webkit, HTTP not HTTPS, mock delay requirements
metadata:
  type: feedback
---

Use **HTTP on port 8080** (plain `python3 -m http.server 8080` from the html dir), not the HTTPS dev server on 8000. WebKit rejects the self-signed cert even with `--ignore-https-errors`.

To test the upload progress screen, inject a `window.fetch` mock with a **30s+ delay** before any navigation. Shorter delays (even 8s) resolve before Playwright tool round-trips can capture an intermediate screenshot — each tool call takes 2-3s.

**Why:** Frame uploads happen during recording (best-effort, in parallel). On localhost they complete in milliseconds. By the time Playwright clicks Finish and takes a screenshot, all promises are already settled and the progress screen has transitioned to done.

**How to apply:** When asked to verify upload/progress UI, always inject the fetch mock immediately after `browser_navigate` to the fresh page, before clicking Get Started. Use `browser_wait_for` with the expected label text (e.g. "Uploading images") after clicking Finish, then screenshot immediately.

Also: do NOT re-click `#btn-record` to "reset" recording state — it toggles, so a second click stops recording rather than restarting it. Navigate fresh to reset all state.
