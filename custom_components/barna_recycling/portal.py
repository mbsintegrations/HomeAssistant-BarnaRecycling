"""Read-only, bounded portal client. No OTP, payment or profile endpoints."""
from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit

from .const import BASE_URL


class PortalError(Exception):
    """Fixed, non-sensitive failure reason safe for logs."""


class AuthenticationError(PortalError):
    """Account number/PIN not accepted."""


class OTPRequired(PortalError):
    """This endpoint now requires an unsupported interactive challenge."""


class Node:
    def __init__(self, tag="root", attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def text(self):
        return " ".join(" ".join(c.text if isinstance(c, Node) else c for c in self.children).split())

    def find(self, tag=None, **attrs):
        found = []
        for c in self.children:
            if isinstance(c, Node):
                if (tag is None or c.tag == tag) and all(c.attrs.get(k) == v for k, v in attrs.items()):
                    found.append(c)
                found.extend(c.find(tag, **attrs))
        return found


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        if self.current.tag not in {"script", "style"}:
            self.current.children.append(data)


def is_login(html):
    return bool(Document(html).root.find("input", name="Password"))


def checked_document(html):
    doc = Document(html).root
    if "App Authentication" in doc.text or "one-time passcode" in doc.text.lower():
        raise OTPRequired("This page requires OTP; interactive access is not supported")
    if is_login(html):
        raise AuthenticationError("Re-enter the account number and PIN")
    return doc


def parse_date(value):
    value = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", value.strip())
    for fmt in ("%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise PortalError("Unrecognised lift date")


def number(value):
    if not re.fullmatch(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?", value.strip()):
        raise PortalError("Unrecognised numeric value")
    try:
        result = Decimal(value.replace(",", ""))
        if not result.is_finite():
            raise InvalidOperation
        return float(result)
    except InvalidOperation as err:
        raise PortalError("Invalid numeric value") from err


def parse_account(html):
    doc = checked_document(html)
    headings = [n.text for n in doc.find("h3") if "Current balance:" in n.text]
    if len(headings) != 1:
        raise PortalError("Account balance was not found")
    match = re.fullmatch(r"Current balance:\s*€\s*([\d,.]+)\s*(.*?)\s*\((DR|CR)\)", headings[0])
    if not match:
        raise PortalError("Unrecognised balance format")
    balance = number(match[1])
    status = "debit" if match[3] == "DR" else "credit"
    alerts = []
    for n in doc.find():
        if "alerts" in n.attrs.get("class", "").split():
            # Text only; no HTML or payment link is ever exposed as an action.
            text = n.text
            if text:
                alerts.append(text[:2000])
    return {"balance": balance if status == "debit" else -balance,
            "balance_status": status, "balance_label": match[2].strip(), "alerts": alerts}


def parse_lifts(html):
    doc = checked_document(html)
    tables = doc.find("table", id="datatable")
    if len(tables) != 1:
        raise PortalError("Lift history table was not found")
    table = tables[0]
    headers = table.find("thead")
    if not headers or not all(x in headers[0].text for x in ("Lift Date", "Vehicle Reg", "Bin Type", "Weight")):
        raise PortalError("Lift history columns changed")
    body = table.find("tbody")
    if len(body) != 1:
        raise PortalError("Lift history body was not found")
    lifts = []
    for row in body[0].find("tr"):
        cells = [c.text for c in row.children if isinstance(c, Node) and c.tag == "td"]
        if len(cells) == 1 and (not cells[0] or "no data" in cells[0].lower() or "no records" in cells[0].lower()):
            continue
        if len(cells) != 4:
            raise PortalError("Lift history row changed")
        description = cells[2]
        match = re.fullmatch(r"(\d+)\s+(Waste|Recycling|Compost)\s+EWC\s*(\d{6})", description, re.I)
        # Retain unknown streams as records without inventing a bin mapping.
        stream = match[2].lower() if match else "other"
        weight = number(cells[3])
        if weight < 0 or weight > 100000:
            raise PortalError("Lift weight is outside supported bounds")
        lifts.append({"date": parse_date(cells[0]), "vehicle": cells[1].strip(),
                      "description": description, "stream": stream, "weight": weight,
                      "bin_litres": int(match[1]) if match else None,
                      "ewc": match[3] if match else None})
    if len(lifts) > 2000:
        raise PortalError("Lift history exceeds the safety limit")
    headings = [n.text for n in doc.find("h4") if n.text.startswith("Lift Service From ")]
    if len(headings) != 1:
        raise PortalError("Lift history coverage was not found")
    return {"lifts": sorted(lifts, key=lambda x: x["date"], reverse=True),
            "history_from": parse_date(headings[0].removeprefix("Lift Service From "))}


def safe_url(value, *, pdf=False):
    url = urljoin(BASE_URL, value)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "cportal.barnarecycling.com" or parts.port not in (None, 443) or parts.username or parts.password:
        raise PortalError("Portal returned an unexpected destination")
    if pdf and not re.fullmatch(r"/api/calendars/\d{4}/[A-Za-z0-9_\-]+\.pdf", parts.path):
        raise PortalError("Calendar download address changed")
    if pdf and (parts.query or parts.fragment):
        raise PortalError("Calendar download address changed")
    return url


def parse_calendar_links(html):
    doc = checked_document(html)
    links = []
    for a in doc.find("a"):
        href = a.attrs.get("href", "")
        if ".pdf" in href.lower():
            # The portal publishes legacy HTTP links, but the files support
            # HTTPS. Upgrade only this exact host; never send cookies via HTTP.
            if href.startswith("http://cportal.barnarecycling.com/api/calendars/"):
                href = "https://" + href.removeprefix("http://")
            links.append(safe_url(href, pdf=True))
    return sorted(set(links))


class BarnaPortal:
    def __init__(self, session, account, pin, executor=None):
        self.session, self.account, self.pin = session, account, pin
        self.authenticated = False
        self.lock = asyncio.Lock()
        self.pdf_cache = {}
        self.executor = executor or asyncio.to_thread

    async def _request(self, path, data=None, pdf=False):
        url = safe_url(path, pdf=pdf)
        for _ in range(5):
            async with self.session.request("POST" if data is not None else "GET", url, data=data,
                                            allow_redirects=False) as response:
                if response.status in {301, 302, 303}:
                    location = response.headers.get("Location")
                    if not location:
                        raise PortalError("Portal redirect is missing its destination")
                    url = safe_url(urljoin(url, location), pdf=pdf)
                    data = None  # Never forward credentials to a redirect.
                    continue
                if response.status != 200:
                    raise PortalError(f"Portal returned HTTP {response.status}")
                limit = 10_000_000 if pdf else 2_000_000
                chunks, size = [], 0
                async for chunk in response.content.iter_chunked(65536):
                    size += len(chunk)
                    if size > limit:
                        raise PortalError("Portal response exceeds the safety limit")
                    chunks.append(chunk)
                payload = b"".join(chunks)
                if pdf:
                    if not payload.startswith(b"%PDF-"):
                        raise PortalError("Calendar response is not a PDF")
                    return payload
                return payload.decode("utf-8", errors="replace")
        raise PortalError("Too many portal redirects")

    async def login(self):
        self.session.cookie_jar.clear()
        html = await self._request("auth_user.php", {"Username": self.account, "Password": self.pin})
        doc = checked_document(html)
        if not any("id=99" in a.attrs.get("href", "") for a in doc.find("a")):
            raise AuthenticationError("Re-enter the account number and PIN")
        self.authenticated = True

    async def page(self, path):
        html = await self._request(path)
        if is_login(html):
            self.authenticated = False
            await self.login()
            html = await self._request(path)
        checked_document(html)
        return html

    async def fetch(self):
        async with self.lock:
            if not self.authenticated:
                await self.login()
            data = parse_account(await self.page("index.php"))
            data.update(parse_lifts(await self.page("index.php?id=4&liftperiod=last12month")))
            data.update({"collections": [], "calendar_advisories": [], "calendar_status": "missing",
                         "calendar_years": [], "calendar_sources": []})
            try:
                links = parse_calendar_links(await self.page("index.php?id=6"))
                if len(links) > 4:
                    raise PortalError("Too many calendar files")
                parsed = []
                for link in links:
                    payload = await self._request(link, pdf=True)
                    digest = sha256(payload).hexdigest()
                    if digest not in self.pdf_cache:
                        result = await self.executor(parse_pdf_in_executor, payload)
                        self.pdf_cache = {**dict(list(self.pdf_cache.items())[-3:]), digest: result}
                    parsed.append(self.pdf_cache[digest])
                for result in parsed:
                    data["collections"].extend(result["collections"])
                    data["calendar_advisories"].extend(result["advisories"])
                    data["calendar_years"].append(result["year"])
                data["collections"] = sorted({x["date"]: x for x in data["collections"]}.values(), key=lambda x: x["date"])
                data["calendar_advisories"] = sorted(set(data["calendar_advisories"]))
                data["calendar_years"] = sorted(set(data["calendar_years"]))
                data["calendar_sources"] = links
                data["calendar_status"] = "ok" if parsed else "missing"
            except (AuthenticationError, OTPRequired):
                raise
            except (PortalError, OSError, ValueError):
                # Unsupported calendars never create guessed collection events.
                data["calendar_status"] = "unsupported"
                data["collections"] = []
            return data


def parse_pdf_in_executor(payload):
    # First import also performs library I/O, so keep it off the event loop.
    from .pdf_calendar import parse_calendar_pdf
    return parse_calendar_pdf(payload)
