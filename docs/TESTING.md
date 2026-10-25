# Validation and limitations

Release: **0.1.0**, checked 25 October 2026.

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

The validation build was installed through HACS. All **28 installed files** matched a freshly downloaded release ZIP byte-for-byte. The ZIP's SHA-256 also matched its published checksum. After restarting Home Assistant, Barna loaded with fresh data, 26 published dates, 15 history records and one correctly versioned frontend resource. There were 28 registered entities, 21 enabled and seven disabled by default. No Barna-specific startup errors were found; HA emitted its standard custom-integration warning.

The validated runtime commit passed [all four official CI jobs](https://github.com/mbsintegrations/HomeAssistant-BarnaRecycling/actions/runs/40157585823), including HACS and Hassfest without ignores. The [catalogue submission](https://github.com/hacs/default/pull/12619) is separate from maintainer acceptance.

## Visual checks

18 sample-data screenshots cover light/dark galleries, overview, quick links, tiny compact, compact with buttons, red reminder date, calendar, history and phone layouts. Actual card code is used in the preview harness. Month navigation, compact-card Enter access and Escape dismissal were checked in Chrome. No horizontal card overflow at 320, 360 or 390px viewport widths after the narrow-screen fix.

## Practical limits

One real account and the combined three-bin vector PDF layout are verified. Other accounts, route formats and future portal changes are not proven compatible. There has not yet been a multi-week soak test or real collection-day notification delivery test. Notification-provider delivery and device permissions are the user's responsibility. The portal can publish late changes or stop providing future dates; the integration reports stale/unsupported/exhausted data instead of predicting collections.

Reproduce local tests with the commands in [Contributing](../CONTRIBUTING.md).

## Version promotion

Release **0.1.0** uses the same validated runtime, with only the manifest version, shared version constant and derived frontend cache URL changed. Python/Node regression checks and official CI are rerun for this release. The final metadata-only promotion was not separately reinstalled in Home Assistant.
