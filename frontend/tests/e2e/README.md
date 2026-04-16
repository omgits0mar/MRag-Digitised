# E2E Scaffold

Playwright is configured in `frontend/playwright.config.ts` so downstream features can add
browser coverage without changing the workspace layout.

Current status:

- No end-to-end specs ship in Feature 005.
- Use `npm run test:e2e` from inside the activated `mrag` conda environment once Feature 007
  adds specs.
- The default base URL is `http://127.0.0.1:4173`, matching `npm run preview`.
