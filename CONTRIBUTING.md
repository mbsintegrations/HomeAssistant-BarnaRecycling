# Contributing

Use a focused pull request against main. Explain the source behaviour and resulting change. Run:

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
npm test
python scripts/build_release.py
```

Python tests use synthetic portal/PDF fixtures and small HA interface substitutes for unit-level lifecycle checks. Native HA testing is separate. Frontend logic uses Node's built-in test runner.

For visual review, serve the repository with `python -m http.server 8766 --bind 127.0.0.1`, then visit `http://127.0.0.1:8766/preview/`. This uses the actual card module with synthetic HA state/history. Parameters: `?theme=dark`, `?mobile=1`, `?focus=buttons` (also standard, links, compact, balance, reminder). Check both popup tabs, keyboard operation and phone widths in both themes.

Never commit customer data, credentials, cookies, account/route IDs, raw portal documents or live screenshots. Build fixtures from scratch. New PDF layouts require date/stream proof; reject ambiguous schedules.

Official HACS validation and Hassfest must pass without ignores. Releases need matching version/code, updated docs/screenshots and a full GitHub release with ZIP/checksum. Contributions use GPL-3.0-only.
