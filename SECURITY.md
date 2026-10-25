# Security and privacy

Credentials are entered in a masked HA form and stored in private HA config-entry storage. HA configuration/backups are **not a credential vault**: protect administrator access, host files and backups. This integration adds no independent credential encryption.

The private last-good snapshot contains account/history data. Its schema/account identity are validated before reuse. Entry removal deletes it; recorder data and backup copies follow your own retention policy.

Account information is exposed through HA entities/service responses. Summary attributes include balance and recent history even when the card hides them. Do not publish live entity snapshots or public dashboards containing this data.

HTTPS requests have bounded payloads/timeouts, an in-memory cookie jar and same-origin redirects. Only the known legacy calendar path is upgraded from HTTP before requesting it. PDF parsing runs in an executor; ambiguous formats do not create dates.

No analytics, telemetry, frontend CDN or paid API is used. No payment/profile/OTP-request/support-message operation is implemented. Errors use stable categories and diagnostics use an allowlist.

Report vulnerabilities privately through GitHub **Security → Report a vulnerability** when available. Do not place secrets in public issues. Only the latest release is actively supported.
