# HACS installation and catalogue status

Repository: `mbsintegrations/HomeAssistant-BarnaRecycling`  
Category: **Integration**  
Minimum HA: **2026.10.0**  
Region: **Ireland**

## Default catalogue installation

Barna Recycling was accepted into the default HACS catalogue on **3 November 2026**. Maintainers merged [submission #12619](https://github.com/hacs/default/pull/12619), and the repository is listed in the official [integration catalogue](https://github.com/hacs/default/blob/master/integration).

Open **HACS → search for Barna Recycling → Download → restart Home Assistant**. Then go to **Settings → Devices & services → Add integration → Barna Recycling** and enter your account number and PIN. See the [complete installation steps](../README.md#install-with-hacs).

The README also includes a [custom-repository fallback](../README.md#custom-repository-fallback) if the entry is not yet visible locally and [manual installation](../README.md#manual-installation) using the release ZIP, checksum and correct directory structure. Existing HACS installations do not need to be reinstalled or reconfigured because of catalogue acceptance.

## Bundled files and updates

All runtime files, brand icons and cards are inside `custom_components/barna_recycling`. HACS installs that directory. The release ZIP is for manual extraction into `custom_components`. No separate HACS dashboard repository is needed. Import the [notification blueprint](REMINDERS.md) separately.

The current normal release remains **0.1.1**. Catalogue acceptance and these documentation changes do not change runtime code or require a new integration release. For an older installation, update through HACS, restart Home Assistant and refresh dashboard browsers. No account reconfiguration or card changes are required. See [updates and removal](TROUBLESHOOTING.md#updating).

Release 0.1.1 fixes repeated HTML parsing on Home Assistant's event loop. Every response is parsed once in the executor, including login and OTP checks. [Release validation](TESTING.md) covers HACS installation, exact package comparison and native setup checks.

## Maintaining the listing

Official HACS validation and Hassfest run without ignores. Keep repository metadata, `hacs.json`, the integration manifest and documentation accurate, and publish matching normal releases for integration updates. Local icons follow [integration requirements](https://www.hacs.xyz/docs/publish/integration/). The catalogue submission is merged; no duplicate submission is needed.

This remains a custom integration distributed through HACS. Catalogue inclusion does not make it a Home Assistant Core integration or imply endorsement by Barna Recycling.
