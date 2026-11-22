#!/usr/bin/env python3
"""Fetch the Airbnb and Booking.com iCal feeds and write availability.json.

Only date ranges are written. Summaries, descriptions, guest names and
reservation links in the feeds are never copied to the public file.

Usage:
    python3 tools/update_availability.py            # uses private/ical_sources.json
    python3 tools/update_availability.py --dry-run  # print, do not write

private/ical_sources.json (never publish this file, the URLs are secret keys):
    {"sources": [
        {"name": "airbnb",  "url": "https://www.airbnb.com/calendar/ical/...ics?s=..."},
        {"name": "booking", "url": "https://ical.booking.com/v1/export?t=..."}
    ]}

If any source fails, the existing availability.json is left untouched and the
script exits with status 1, so a temporary outage never shows dates as free.
"""
import datetime as dt
import json
import os
import ssl
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "private", "ical_sources.json")
OUT = os.path.join(ROOT, "availability.json")
TZ = dt.timezone(dt.timedelta(hours=1))  # only used for the "updated" stamp


def ssl_context():
    # python.org builds on macOS ship without root certificates; use certifi or
    # the system bundle when available. Linux (e.g. a Raspberry Pi) needs neither.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for path in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return ssl.create_default_context()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "forellen-availability/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as r:
        return r.read().decode("utf-8", errors="replace")


def unfold(text):
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line[:1] in (" ", "\t") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def parse_date(value):
    v = value.strip()[:8]
    return dt.date(int(v[0:4]), int(v[4:6]), int(v[6:8]))


def events(text):
    """Yield (start, end) dates; end is the check-out day (exclusive)."""
    start = end = None
    inside = False
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            inside, start, end = True, None, None
        elif line == "END:VEVENT":
            if inside and start:
                yield start, end or start + dt.timedelta(days=1)
            inside = False
        elif inside and ":" in line:
            key, val = line.split(":", 1)
            name = key.split(";", 1)[0].upper()
            if name == "DTSTART":
                start = parse_date(val)
            elif name == "DTEND":
                end = parse_date(val)


def merge(ranges):
    out = []
    for s, e in sorted(ranges):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def main():
    dry = "--dry-run" in sys.argv
    with open(SOURCES) as f:
        sources = json.load(f)["sources"]
    if not sources:
        print("ERROR: no iCal sources configured", file=sys.stderr)
        return 1
    today = dt.date.today()
    ranges, counts = [], {}
    for src in sources:
        try:
            text = fetch(src["url"])
            if "BEGIN:VCALENDAR" not in text:
                raise ValueError("not an iCal feed")
            evs = list(events(text))
        except Exception as exc:  # keep the old file on any failure
            print(f"ERROR {src['name']}: {exc.__class__.__name__} {exc}"[:200], file=sys.stderr)
            return 1
        counts[src["name"]] = len(evs)
        ranges += [(s, e) for s, e in evs if e > today]
    merged = merge(ranges)
    data = {
        "updated": dt.datetime.now(TZ).isoformat(timespec="minutes"),
        "booked": [[s.isoformat(), e.isoformat()] for s, e in merged],
    }
    for name, n in counts.items():
        print(f"{name}: {n} events")
    print(f"{len(merged)} booked ranges from today")
    for s, e in merged[:12]:
        print(f"  {s} -> {e}")
    if dry:
        return 0
    fd, tmp = tempfile.mkstemp(dir=ROOT, prefix=".availability.", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=1)
    os.chmod(tmp, 0o644)
    os.replace(tmp, OUT)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
