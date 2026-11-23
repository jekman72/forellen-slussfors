#!/usr/bin/env python3
"""Short Swedish summary of yesterday's visits to forellenslussfors.se from
Cloudflare Web Analytics, for a daily push notification.

Token: a Cloudflare API token with Account > Account Analytics > Read, stored
in private/cloudflare_token (chmod 600, never published).

Usage:  python3 tools/daily_stats.py            # yesterday, print only
        python3 tools/daily_stats.py 2026-11-22 # a given day
        python3 tools/daily_stats.py --push     # also send to the ntfy topic in private/ntfy_topic
"""
import datetime as dt
import json
import os
import ssl
import sys
import urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT = "817bbf005400304d46e1f931cf574253"
HOST = "forellenslussfors.se"
TOKEN_FILE = os.path.join(ROOT, "private", "cloudflare_token")
TOPIC_FILE = os.path.join(ROOT, "private", "ntfy_topic")

COUNTRY_SV = {"SE": "Sverige", "LV": "Lettland", "LT": "Litauen", "EE": "Estland", "FI": "Finland",
              "NO": "Norge", "DE": "Tyskland", "PL": "Polen", "GB": "Storbritannien", "NL": "Nederländerna",
              "US": "USA", "DK": "Danmark", "CZ": "Tjeckien", "FR": "Frankrike"}


def ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for p in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(p):
            return ssl.create_default_context(cafile=p)
    return ssl.create_default_context()


def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"][0].get("message", "GraphQL error"))
    return out["data"]["viewer"]["accounts"][0]


Q = """query($acc: String!, $from: Date!, $to: Date!, $host: String!) {
  viewer { accounts(filter: {accountTag: $acc}) {
    days: rumPageloadEventsAdaptiveGroups(limit: 100, filter: {date_geq: $from, date_leq: $to, requestHost: $host}) {
      count sum { visits } dimensions { date } }
    detail: rumPageloadEventsAdaptiveGroups(limit: 1000, filter: {date: $to, requestHost: $host}) {
      count sum { visits } dimensions { countryName refererHost requestPath deviceType } }
  } } }"""


def push(text):
    """Send the summary to the private ntfy topic (title ASCII, body UTF-8)."""
    topic = open(TOPIC_FILE).read().strip()
    req = urllib.request.Request("https://ntfy.sh/" + topic, data=text.encode("utf-8"),
                                 headers={"Title": "Forellen", "Tags": "fishing_pole_and_fish"})
    with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
        return r.status


ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PUSH = "--push" in sys.argv


def main():
    day = dt.date.fromisoformat(ARGS[0]) if ARGS else dt.date.today() - dt.timedelta(days=1)
    token = open(TOKEN_FILE).read().strip()
    acc = gql(token, Q, {"acc": ACCOUNT, "from": (day - dt.timedelta(days=7)).isoformat(),
                         "to": day.isoformat(), "host": HOST})
    per_day = {g["dimensions"]["date"]: (g["sum"]["visits"], g["count"]) for g in acc["days"]}
    visits, views = per_day.get(day.isoformat(), (0, 0))
    prev = [per_day.get((day - dt.timedelta(days=i)).isoformat(), (0, 0))[0] for i in range(1, 8)]
    avg = sum(prev) / 7

    c_country, c_ref, c_path, c_dev = Counter(), Counter(), Counter(), Counter()
    for g in acc["detail"]:
        d, v = g["dimensions"], g["count"]  # page views, so details show even without "visits"
        c_country[COUNTRY_SV.get(d["countryName"], d["countryName"] or "?")] += v
        ref = (d["refererHost"] or "direkt").replace("www.", "")
        if HOST in ref: continue
        if "facebook" in ref or ref.startswith("l.facebook") or ref == "fb.com": ref = "Facebook"
        c_ref[ref] += v
        p = d["requestPath"] or "/"
        if p.startswith("/lv"): c_path["lettiska"] += v
        elif p.startswith("/lt"): c_path["litauiska"] += v
        elif p.startswith("/pl"): c_path["polska"] += v
        c_dev["mobil" if (d["deviceType"] or "").lower() == "mobile" else "dator"] += v

    def top(c, n=3): return ", ".join(f"{k} {v}" for k, v in c.most_common(n)) or "-"
    trend = "" if avg == 0 else f" (snitt 7 d: {avg:.1f})"
    lines = [f"{day.strftime('%-d/%-m')}: {visits} besök, {views} sidvisningar{trend}"]
    if views:
        lines.append("Länder: " + top(c_country))
        lines.append("Från: " + top(c_ref))
        extra = []
        if c_path: extra.append("via " + top(c_path, 2) + " länk")
        extra.append(top(c_dev, 2))
        lines.append(" · ".join(extra))
    text = "\n".join(lines)
    print(text)
    if PUSH:
        push(text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = ("Statistik saknas: ingen Cloudflare-nyckel" if isinstance(e, FileNotFoundError)
               else f"Statistik kunde inte hämtas ({e.__class__.__name__}: {e})")[:200]
        print(msg)
        if PUSH:
            try: push(msg)
            except Exception: pass
        sys.exit(1)
