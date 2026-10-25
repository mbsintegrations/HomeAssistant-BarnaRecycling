# Validation and limitations

Release candidate: **0.1.0b1**, checked 25 October 2026.

## Automated regression checks

- **37 Python tests:** synthetic account/history parsing, debit/credit, malformed/duplicate rows, authentication and OTP handling, expired-session relogin, redirect origin/body protection, bounded downloads and corrupt/unsupported PDFs.
- Synthetic full-year vector PDFs cover leap years, year boundaries, legend ambiguity and multiple colours.
- Runtime tests execute the actual integration methods with small HA interface adapters: private cache identity/schema, network/auth/OTP failures, recovery, disk-save failure, six-hour interval, midnight updates, entity defaults, diagnostics allowlist, setup/unload/removal and history service routing.
- Config-flow tests cover masking, trimming, invalid inputs, duplicate accounts, same-account reauthentication/reconfiguration and safe error categories.
- **11 Node tests:** HA time zone, DST, highlighting boundaries, invalid/missing dates, unavailable states, HTML escaping, preset selection, history response/fallback, calendar popup content and history invalidation.
- These unit tests do not replace native Home Assistant lifecycle testing. CI also runs official Hassfest and HACS validation without ignores.

## Native Home Assistant Test

Tested on **Home Assistant 2026.10.1** with an isolated container and one real customer account:

- Account/PIN setup submitted through the native masked form.
- Unattended server login and live account/history/calendar reads.
- Loaded entry, supported calendar, 15 source lift rows and all-day calendar API events with next-day exclusive end.
- Read-only full-history response action.
- Blueprint accepted by HA's blueprint schema.
- Six inert blueprint runs verified through execution traces: matching fresh date runs; wrong date, stale-by-default, unsupported calendar and unavailable state skip; explicitly allowed stale data runs.
- Temporary fixture sensor and automation removed after validation. No phone notification or household action was sent.
- Resource registration and existing dashboard presets visually checked.

HACS release installation and final restart checks are recorded in the release validation note once completed.

## Visual checks

18 sample-data screenshots cover light/dark galleries, overview, quick links, tiny compact, compact with buttons, red reminder date, calendar, history and phone layouts. Actual card code is used in the preview harness. Month navigation, compact-card Enter access and Escape dismissal were checked in Chrome. No horizontal card overflow at 320, 360 or 390px viewport widths after the narrow-screen fix.

## Practical limits

One real account and the combined three-bin vector PDF layout are verified. Other accounts, route formats and future portal changes are not proven compatible. There has not yet been a multi-week soak test or real collection-day notification delivery test. Notification-provider delivery and device permissions are the user's responsibility. The portal can publish late changes or stop providing future dates; the integration reports stale/unsupported/exhausted data instead of predicting collections.

Reproduce local tests with the commands in [Contributing](../CONTRIBUTING.md).
