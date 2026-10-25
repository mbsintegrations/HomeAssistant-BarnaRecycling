# HACS

Repository: `mbsintegrations/HomeAssistant-BarnaRecycling`  
Category: **Integration**  
Minimum HA: **2026.10.0**  
Region: **Ireland**

Use a custom repository while default-catalogue review is pending. A submitted PR is not catalogue acceptance.

1. HACS → ⋮ → Custom repositories.
2. Add `https://github.com/mbsintegrations/HomeAssistant-BarnaRecycling` as **Integration**.
3. Download Barna Recycling; enable prerelease versions for the beta if needed.
4. Restart HA, add the integration and refresh the browser.

All runtime files and brand icons are inside `custom_components/barna_recycling`. HACS installs that directory. The release ZIP is for manual extraction into custom_components. Import the blueprint separately.

Official HACS validation and Hassfest run without ignores. Submission follows [HACS inclusion requirements](https://hacs.xyz/docs/publish/include/) after successful checks and a full GitHub release. Local icons follow [integration requirements](https://hacs.xyz/docs/publish/integration/). See the linked submission for current review status; do not open duplicates.
