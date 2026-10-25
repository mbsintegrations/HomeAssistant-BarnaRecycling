# HACS

Repository: `mbsintegrations/HomeAssistant-BarnaRecycling`  
Category: **Integration**  
Minimum HA: **2026.10.0**  
Region: **Ireland**

Default-catalogue submission: [hacs/default #12619](https://github.com/hacs/default/pull/12619), opened 25 October 2026. Use a custom repository while review is pending. Submission is not catalogue acceptance.

1. HACS → ⋮ → Custom repositories.
2. Add `https://github.com/mbsintegrations/HomeAssistant-BarnaRecycling` as **Integration**.
3. Download Barna Recycling **0.1.0**.
4. Restart HA, add the integration and refresh the browser.

All runtime files and brand icons are inside `custom_components/barna_recycling`. HACS installs that directory. The release ZIP is for manual extraction into custom_components. Import the blueprint separately.

The validation build was installed through HACS on HA Test 2026.10.1. All 28 installed files matched the downloaded release ZIP byte-for-byte. After restart, the entry loaded with fresh data, 26 published collection dates and 15 history records for the validation account. These counts describe that test account, not a guarantee for every customer.

Official HACS validation and Hassfest run without ignores. Submission follows [HACS inclusion requirements](https://hacs.xyz/docs/publish/include/) after successful checks and a full GitHub release. Local icons follow [integration requirements](https://hacs.xyz/docs/publish/integration/). See the linked submission for current review status; do not open duplicates.

Release **0.1.0** keeps that validated runtime unchanged apart from the version fields and frontend cache URL. It is a normal release and does not require enabling prereleases. HA Test remained stopped for this metadata-only release promotion.
