# Dashboard cards

The integration serves its own frontend and registers one JavaScript module in storage-mode Lovelace. Select your actual **Collection summary** sensor; entity IDs vary by installation.

| Type | Layout | Interaction |
| --- | --- | --- |
| `custom:barna-recycling-card` | Collection overview and latest lifts | Calendar and Lift history buttons |
| `custom:barna-recycling-card-with-links` | Overview with quick links | Same popups plus Customer portal |
| `custom:barna-recycling-card-compact` | Tiny 94px-high card sized to its contents | Tap card for details |
| `custom:barna-recycling-card-compact-buttons` | Full-width 94px row, larger bins/date | Calendar and Lift history on the right |

Both tabs open **inside Home Assistant**. The calendar has month navigation and published collection markers. History retrieves all cached records through a read-only HA action without another portal request. If this fails, the recent-record fallback is explicitly labelled. Last successful sync appears in readable text in the popup.

## Examples

Replace the sample entity ID with yours.

```yaml
type: custom:barna-recycling-card
entity: sensor.barna_recycling_collection_summary
title: Barna Recycling
highlight_time: "18:00"
```

```yaml
type: custom:barna-recycling-card-with-links
entity: sensor.barna_recycling_collection_summary
show_balance: true
```

```yaml
type: custom:barna-recycling-card-compact
entity: sensor.barna_recycling_collection_summary
highlight_time: "17:30"
```

```yaml
type: custom:barna-recycling-card-compact-buttons
entity: sensor.barna_recycling_collection_summary
highlight_time: "17:30"
```

Settings are also available in the visual editor. `show_balance` defaults false; `show_history` defaults true and controls the full card's history button. Compact popups always offer both tabs. `show_links` adds the external portal link. `compact` and `compact_buttons` override layout; choosing a preset is simpler.

## Highlighting, themes and sizing

`highlight_time` is `HH:MM` in **HA's configured time zone**. The date turns red at that time on the previous day and stays red on collection day. Midnight entity updates and a 30-second card timer handle day changes. This does not schedule notifications.

HA theme colours are used automatically. Original local bin artwork is black / blue / brown. Cards omit notice banners; source notices remain in entities. Give the compact-with-buttons card a full phone-width section. The tiny compact intentionally fits its contents.

## Manual resource / YAML dashboard

If the picker does not show the cards after refreshing, register this module once:

```yaml
resources:
  - url: /barna_recycling/frontend/barna-recycling-card.js?v=0.1.0b1-release1
    type: module
```

Storage dashboards: **Settings → Dashboards → ⋮ → Resources**, with advanced mode enabled. Remove duplicate/obsolete Barna resources and refresh. YAML resource collections require manual registration. Use the current release version after updates; do not add a second copy under `/local/`.
