# Headless Chrome Plan

## Why we need a headless browser

- Most major news sites now block or delay responses from simple / scrapers. Landing pages either return empty HTML, captcha challenges, or bot-detection interstitials.
- Playwright-driven Chromium renders the full page, waits for DOM content, and lets us interact (scroll, hover, wait for selectors) so we reliably capture the canonical article body.
- This repository already uses a  service, so the headless plan plugs in at the same extraction layer without touching the downstream AI cleaning/translation logic.

## Technical approach

1. **Install Playwright** – the new dependency in  triggers  during deployment or local setup. The extractor still falls back to  if Playwright cannot launch.
2. **Expose configuration** –  now has , , and  so operators can toggle Chromium rendering per environment. Defaults include the Railway-safe .
3. **Content extraction flow** –  decisions:
   - Try Playwright when  is enabled.
   - Render a page with the configured viewport and user agent, wait for , then grab .
   - If headless navigation fails (timeout, telemetry), log the failure and fallback to the familiar HTTP/Readability path.
4. **Processor wiring** –  pulls the same flag from , so turning on headless globally or per-task is a single toggle.

## Railway deployment notes

- Chromium needs  and  because Railway’s containers do not run as root; the extractor already supplies these via the default args.
- To keep the browser downloads in the app directory (), set  in Railway’s Environment Variables. Without it, Playwright tries to download to a HOME directory that might not be writable.
- Add a Railway start command or job such as:
  
  (or the equivalent script you already use). Installing Chromium during the build ensures the runtime step does not attempt to download when the container lacks network access.
- Limit concurrency and close pages/browsers immediately after extraction to keep memory/CPU in check—the new extractor closes the Playwright browser inside every request.

## Validation steps

1. Run  locally and flip  in your .
2. Execute a single task (e.g., ) and confirm log lines like  only appear when needed.
3. On Railway, inspect the build logs to ensure Chromium downloads and the runtime logs for “Playwright” lines; lack of sandbox errors means the default args are working.

This headless plan should keep the existing AI pipeline intact while giving us a stealthier fetch path that satisfies Railway’s constraints.
