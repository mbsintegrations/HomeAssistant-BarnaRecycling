"""Conservative parser for Barna's combined three-bin vector calendar layout.

Other layouts are rejected instead of assigning a colour to the wrong bin.
This runs in an executor, never on Home Assistant's event loop.
"""
import calendar
from datetime import date
from io import BytesIO
import re

import pdfplumber

from .portal import PortalError


def parse_calendar_pdf(payload):
    try:
        with pdfplumber.open(BytesIO(payload)) as pdf:
            if not 1 <= len(pdf.pages) <= 4:
                raise PortalError("Unsupported calendar page count")
            return parse_page(pdf.pages[0])
    except PortalError:
        raise
    except Exception as err:
        raise PortalError("Calendar PDF could not be parsed") from err


def parse_page(page):
    words = page.extract_words()
    text = page.extract_text() or ""
    years = {int(w["text"]) for w in words if re.fullmatch(r"20\d\d", w["text"])}
    if len(years) != 1:
        raise PortalError("Calendar year is ambiguous")
    year = years.pop()
    months = [(list(calendar.month_name).index(w["text"]), w) for w in words if w["text"] in list(calendar.month_name)[1:]]
    if sorted(n for n, _ in months) != list(range(1, 13)):
        raise PortalError("Unsupported calendar month layout")
    scale = page.width / 841.89
    grid_right = max((w["x0"] + w["x1"]) / 2 for _, w in months) + 75 * scale
    legend = [w for w in words if w["x0"] > grid_right and w["text"] in ("Waste", "Recyc", "Compost")]
    if len(legend) != 3 or len({w["text"] for w in legend}) != 3 or max(w["top"] for w in legend) - min(w["top"] for w in legend) > 3 * scale:
        raise PortalError("Unsupported calendar legend")
    dates, all_dates, colours = [], set(), set()
    for word in words:
        if not word["text"].isdigit() or not 1 <= int(word["text"]) <= 31:
            continue
        x, y = (word["x0"] + word["x1"]) / 2, (word["top"] + word["bottom"]) / 2
        if x > grid_right:
            continue
        candidates = [(n, w) for n, w in months if w["top"] < word["top"] and abs((w["x0"] + w["x1"]) / 2 - x) < 70 * scale]
        if not candidates:
            continue
        month, anchor = max(candidates, key=lambda pair: pair[1]["top"])
        if y - anchor["top"] > 140 * scale:
            raise PortalError("Unsupported calendar grid")
        try:
            day = date(year, month, int(word["text"])).isoformat()
        except ValueError as err:
            raise PortalError("Invalid calendar date") from err
        if day in all_dates:
            raise PortalError("Duplicate calendar date")
        all_dates.add(day)
        cells = [r for r in page.rects if r.get("fill") and r["x0"] <= x <= r["x1"] and r["top"] <= y <= r["bottom"]]
        if not cells:
            raise PortalError("Calendar cell has no vector fill")
        colour = tuple(cells[-1].get("non_stroking_color") or ())
        if colour != (1.0, 1.0, 1.0):
            colours.add(colour)
            dates.append(day)
    if len(all_dates) != (366 if calendar.isleap(year) else 365) or len(colours) != 1 or not dates:
        raise PortalError("Unsupported calendar date or colour layout")
    colour = next(iter(colours))
    swatches = [r for r in page.rects if r.get("fill") and tuple(r.get("non_stroking_color") or ()) == colour
                and r["x0"] > grid_right and 0 < min(w["top"] for w in legend) - r["top"] < 100 * scale
                and abs(r["width"] - r["height"]) < 2 * scale]
    if len(swatches) != 1:
        raise PortalError("Collection colour does not match a single combined legend")
    advisories = [line.strip() for line in text.splitlines() if any(k in line.lower() for k in ("christmas", "confirm", "bank holiday", "subject to", "night before"))]
    return {"year": year, "collections": [{"date": d, "streams": ["waste", "recycling", "compost"]} for d in sorted(dates)], "advisories": advisories}
