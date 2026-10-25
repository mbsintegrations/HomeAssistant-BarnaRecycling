"""Pure data transformations, shared by entities and tests."""
from datetime import date, datetime
import math

from .const import STREAMS


def validate_snapshot(data):
    try:
        if not isinstance(data, dict) or not math.isfinite(data["balance"]) or data["balance_status"] not in {"credit", "debit"}:
            return False
        if data["calendar_status"] not in {"ok", "missing", "unsupported"}:
            return False
        date.fromisoformat(data["history_from"])
        sync = datetime.fromisoformat(data["last_successful_sync"])
        if sync.tzinfo is None:
            return False
        if not isinstance(data["lifts"], list) or len(data["lifts"]) > 2000:
            return False
        for row in data["lifts"]:
            date.fromisoformat(row["date"])
            if row["stream"] not in (*STREAMS, "other") or not isinstance(row["weight"], (int, float)) or not 0 <= row["weight"] <= 100000:
                return False
            if not all(isinstance(row[k], str) for k in ("vehicle", "description")):
                return False
            if row["bin_litres"] is not None and not isinstance(row["bin_litres"], int):
                return False
            if row["ewc"] is not None and not isinstance(row["ewc"], str):
                return False
        if not isinstance(data["collections"], list) or len(data["collections"]) > 1464:
            return False
        for row in data["collections"]:
            date.fromisoformat(row["date"])
            if not row["streams"] or not set(row["streams"]) <= set(STREAMS):
                return False
        for key in ("alerts", "calendar_advisories", "calendar_sources"):
            if not isinstance(data[key], list) or len(data[key]) > 30 or not all(isinstance(x, str) and len(x) <= 2000 for x in data[key]):
                return False
        if not isinstance(data["calendar_years"], list) or not all(isinstance(x, int) and 2000 <= x <= 2099 for x in data["calendar_years"]):
            return False
        return True
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def next_collection(data, today, stream=None):
    return next((x for x in sorted(data.get("collections", []), key=lambda x: x["date"])
                 if x["date"] >= today.isoformat() and (stream is None or stream in x["streams"])), None)


def stream_summary(data, stream):
    rows = sorted((x for x in data.get("lifts", []) if x["stream"] == stream), key=lambda x: x["date"], reverse=True)
    return {"last": rows[0] if rows else None, "count": len(rows),
            "total_weight": round(sum(x["weight"] for x in rows), 2)}
