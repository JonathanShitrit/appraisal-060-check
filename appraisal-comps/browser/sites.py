#!/usr/bin/env python3
"""
sites.py - reads settings/sites.json, the appraiser's allowlist of sites the
browser may open in his logged-in profile (Task 6: "Read-tier browser").

A bad or missing sites.json must never let any site through (Design
Principles, "Trust": an origin allowed by default, or by a malformed
sites.json, is an anti-goal) - so load_sites() never raises. It returns
whatever sites are cleanly enabled, plus a list of problems: guard.py denies
every browser call when that list isn't empty, and launch.py refuses to
start the browser when no site is enabled.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

AccessLevel = Literal["read"]


@dataclass
class Site:
    name: str
    origin: str
    access: AccessLevel
    terms_checked_on: str
    note: str


def origin_of(url: str) -> str:
    """The normalized origin of url: "https://<host>", or "https://<host>:<port>"
    when the port isn't the https default (443). Always lowercased.

    Returns "" for anything that isn't an unambiguous https URL: a
    backslash (the WHATWG URL parser a real browser uses treats "\\" as a
    path separator; Python's urlparse doesn't), userinfo before the host
    (an "x@host" prefix can smuggle a different real host past a parser
    that stops at the first "@"), or a scheme other than https.
    """
    if "\\" in url:
        return ""
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        return ""
    if parsed.scheme != "https":
        return ""
    host = parsed.hostname
    if not host:
        return ""
    host = host.lower()
    try:
        port = parsed.port
    except ValueError:
        return ""
    if port is None or port == 443:
        return f"https://{host}"
    return f"https://{host}:{port}"


def _is_enabled_origin(origin: str) -> bool:
    """True only when origin is already in origin_of()'s own canonical
    shape: "https://<host>" or "https://<host>:<port>", lowercase, no path.
    Reusing origin_of() as the single source of truth means a blank
    origin, an http origin, a path, a trailing slash or upper case all
    fail the round trip, with no separate shape regex to keep in sync."""
    return bool(origin) and origin_of(origin) == origin


def _is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


SITE_FIELDS = ("name", "origin", "access", "terms_checked_on", "note")


def _parse_site(entry: object) -> tuple[Site | None, list[str]]:
    """entry is one element of sites.json's "sites" list - untrusted JSON,
    so every field is narrowed before use. Returns the Site when it is
    enabled, else None, plus any problem worth reporting.

    A site whose origin is blank is simply not enabled yet (a fresh
    install), so it reports nothing. A site he has started to fill in
    (a non-blank origin) that is still disabled reports why, naming it, so
    the session's BROWSER_OFF line can tell him what to fix. An entry of
    the wrong shape, and the fill tier, are always reported.
    """
    if not isinstance(entry, dict):
        return None, ["a site entry is not a JSON object"]
    name = entry.get("name")
    origin = entry.get("origin")
    access = entry.get("access")
    terms_checked_on = entry.get("terms_checked_on")
    note = entry.get("note")
    if not all(isinstance(value, str) for value in (name, origin, access, terms_checked_on, note)):
        label = name if isinstance(name, str) else "a site entry"
        return None, [f"{label}: every field ({', '.join(SITE_FIELDS)}) must be text"]

    if access == "fill":
        return None, [f"{name}: fill tier is not available in this version"]
    has_origin = origin.strip() != ""
    if access != "read":
        if has_origin:
            return None, [f'{name}: access must be "read"']
        return None, []
    if not has_origin:
        return None, []
    if not _is_enabled_origin(origin):
        return None, [f"{name}: origin {origin!r} must look like https://www.example.com "
                      "(https, lowercase, no path or trailing slash)"]
    if not _is_valid_date(terms_checked_on):
        return None, [f"{name}: terms_checked_on must be the date he checked the terms, like 2026-11-20"]
    return Site(name=name, origin=origin, access="read", terms_checked_on=terms_checked_on, note=note), []


def load_sites(path: Path) -> tuple[list[Site], list[str]]:
    """The enabled sites in path, and the problems found. Never raises:
    a missing file, invalid JSON, or the wrong shape all come back as a
    problem and no sites, so the caller can fail closed."""
    try:
        raw_text = path.read_text()
    except OSError as error:
        return [], [f"settings/sites.json could not be read: {error}"]

    try:
        payload: object = json.loads(raw_text)
    except json.JSONDecodeError as error:
        return [], [f"sites.json line {error.lineno} column {error.colno}: {error.msg}"]

    if not isinstance(payload, dict) or not isinstance(payload.get("sites"), list):
        return [], ['sites.json is not shaped like {"sites": [...]}']

    enabled: list[Site] = []
    problems: list[str] = []
    for entry in payload["sites"]:
        site, entry_problems = _parse_site(entry)
        problems.extend(entry_problems)
        if site is not None:
            enabled.append(site)
    return enabled, problems
