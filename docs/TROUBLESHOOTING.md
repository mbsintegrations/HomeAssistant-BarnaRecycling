# Troubleshooting, updates and removal

## Connection or authentication

Check normal HTTPS portal access from your network. Do not repeatedly retry a rejected PIN. Source/transport failures have different categories from invalid credentials. Saved data stays visible with **Data stale** and its last-successful timestamp.

Use **Reconfigure** or native reauthentication to update the same account's credentials. Changing account identity requires a separate entry. Duplicates are rejected. OTP-required data is unsupported; no browser cookies or OTP workaround are used.

## Calendar status

- `missing`: no usable calendar link supplied.
- `unsupported`: PDF could not be interpreted safely.
- `exhausted`: supported calendar has no future date left.

Check the source portal. Do not extrapolate a schedule. Report unknown formats with a **sanitized** example only; remove account/address/route details. Valid account/history data can still work.

## Missing/old cards or history

Refresh the browser and check the single [module resource](CARDS.md). YAML resources may need manual registration. Select Collection summary, not a per-bin sensor. For missing full history, check that the read-only history action exists and the entry is loaded.

## Updating

Back up HA; update through HACS; restart HA; refresh dashboard browsers. Check sync freshness and calendar status. Keep the previous release ZIP for rollback. Do not downgrade across future storage migrations without a backup.

## Removal

Delete the Barna entry in Devices & services; this deletes its private saved snapshot. Remove your cards and reminder automations. Remove the frontend resource if no Barna account still uses it. Uninstall via HACS (or remove the custom component directory), then restart HA. Imported blueprints, recorder history and old backups are separate and are not automatically deleted.

## Issues

Supply HA/integration versions, error category, calendar status and reproduction steps. Diagnostics deliberately omit credentials, routes, balances and weights. Review attachments. Never attach raw .storage, portal HTML, browser exports or private account screenshots.
