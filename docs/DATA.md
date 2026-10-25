# Entities and data coverage

| Shared sensor | Data |
| --- | --- |
| Collection summary | Next published date; collections, stream summaries and latest 12 lift rows in attributes |
| Account balance | EUR; positive = debit owed, negative = credit |
| Balance status | `debit` or `credit` |
| Account alerts | Count; source messages in attributes |
| Calendar status | `ok`, `missing`, `unsupported`, or `exhausted` when no future dates remain |
| Last successful sync | Timestamp |
| Lift history | All cached rows; disabled by default |

Each of **waste, recycling and compost** has next collection, last lift date, last lift weight (kg), recorded weight (kg) and recorded lift count. The last two are disabled by default. Totals cover returned source history, not lifetime consumption. Identical source rows are preserved because separate lifts may match.

Total: **22 sensors**, **2 binary sensors** (Data stale, Account notice) and **4 calendars** (All / Waste / Recycling / Compost). Seven sensors are disabled by default: full history and each stream's total/count. Enable these in the device entity list if needed.

## Calendars

All-day events end exclusively on the following day. Per-bin calendars filter the combined calendar. Interval boundaries use the HA time zone, including daylight saving. Source advisories are retained in event descriptions; cached schedules are labelled.

Only the inspected combined three-bin vector PDF format is supported initially. All date cells and the legend are validated before highlights are interpreted. Unknown layouts, ambiguous colours and corrupt PDFs fail closed. No route/address is entered in YAML.

## Complete history action

`barna_recycling.get_lift_history` is response-only and reads the existing cache:

```yaml
action: barna_recycling.get_lift_history
data:
  entity_id: sensor.barna_recycling_collection_summary
response_variable: barna_history
```

The selected entity must belong to the desired loaded Barna entry. The response contains `records`, `history_from`, `last_successful_sync` and `data_stale`. Records contain `date`, `stream`, `description`, `weight`, `vehicle`, `bin_litres` and `ewc` where supplied. Unknown descriptions are retained as `other`, without adding them to a known stream's totals.

## Refresh and failures

Polling is every six hours. Ordinary login is reused; expired sessions trigger bounded relogin. A private, validated account-bound snapshot survives restarts. Failed refreshes retain saved data with freshness/error attributes. Invalid credentials request native reauthentication. Without a usable cache, setup retries or requests credentials as appropriate.

Missing/unsupported calendars do not prevent valid financial/history data from loading. OTP is never requested or bypassed. Payments, card details, profile changes, support messages and OTP-gated pages are outside scope. These fields cover useful data found on the inspected ordinary-login pages; other account types may differ.
