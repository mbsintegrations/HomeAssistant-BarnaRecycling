# Changelog

## Documentation — 2026-11-03

Accepted into the default HACS catalogue. Installation now starts with searching for Barna Recycling in HACS. Retains a custom-repository fallback and expands manual installation and update instructions, including ZIP checksums and directory layout. Existing installations do not need to be reconfigured. Runtime code, release files and version 0.1.1 are unchanged.

## 0.1.1 — 2026-11-02

Fix portal HTML parsing blocking Home Assistant's event loop during setup, reauthentication and six-hour refreshes. Each HTML response is now parsed once in the executor, including login detection, OTP checks and account/history/calendar-link extraction.

Expired sessions still retry once; OTP and changed page layouts do not trigger repeated logins. A failed login clears the authenticated state. Existing entities, calendars, cards, history, polling interval and private cache are unchanged.

Adds regression coverage for worker-thread execution, one DOM per response, responsiveness with a near-2 MB/2,000-row fixture, retry bounds and both Home Assistant entry points. Updates the pinned Hassfest validation action.

Update through HACS, restart Home Assistant, then refresh dashboard browsers. No account reconfiguration is required.

## 0.1.0 — 2026-10-25

First public release: native account/PIN setup, duplicate protection, reauthentication, six-hour polling, private cache, account/history entities and four published collection calendars.

Includes combined three-bin vector PDF parsing, four theme-aware card presets, calendar/history popups, original black/blue/brown bins, adjustable reminder blueprint, local brand assets and documentation.

Initial real-world validation covers one customer account and one calendar layout. Additional layouts require testing.
