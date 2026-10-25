# Collection notifications

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmbsintegrations%2FHomeAssistant-BarnaRecycling%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbarna_collection_reminder.yaml)

Alternatively copy `blueprints/automation/barna_collection_reminder.yaml` into `/config/blueprints/automation/barna_recycling/`, reload blueprints/automations and create an automation from it. Blueprints are imported separately from HACS installation.

1. Select **Collection summary**.
2. Choose a local notification time (default **18:00**).
3. Select 0–7 days before collection (default **1**).
4. Decide whether to allow saved schedules after a failed refresh (default **off**).
5. Choose notification actions and use `{{ reminder_title }}` and `{{ reminder_message }}`.

Example, replacing the phone action with yours:

```yaml
action: notify.mobile_app_your_phone
data:
  title: "{{ reminder_title }}"
  message: "{{ reminder_message }}"
```

Multiple phones/providers can be selected. There is no bundled device target. The blueprint uses actual published dates; it skips unavailable/unsupported/no-date states and stale data unless explicitly allowed. Saved schedules are labelled, and source calendar advisories are included.

HA must run at the selected time; there is no catch-up notification. Test your own notification action manually: validating the blueprint does not prove phone delivery or notification permissions.

**Date colour is separate:** set `highlight_time: "18:00"` on each card. It turns red the previous day at that time and remains red on collection day.
