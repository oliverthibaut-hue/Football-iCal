#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import os
import re
import unicodedata

BASE=Path(__file__).resolve().parent
CURRENT=BASE / "Formula-1.ics"
HISTORY=BASE / "formula1-history.ics"
SEASON=int(os.getenv("F1_SEASON",datetime.now(timezone.utc).year))


def unfold(text):
    out=[]
    for line in text.replace("\r\n","\n").replace("\r","\n").split("\n"):
        if line.startswith((" ","\t")) and out:
            out[-1]+=line[1:]
        else:
            out.append(line)
    return out


def extract_events(path):
    if not path.exists():
        return []
    events=[]
    cur=None
    for line in unfold(path.read_text(encoding="utf-8",errors="replace")):
        if line == "BEGIN:VEVENT":
            cur=[]
        elif line == "END:VEVENT" and cur is not None:
            events.append(cur)
            cur=None
        elif cur is not None:
            cur.append(line)
    return events


def prop(ev,name):
    for line in ev:
        if line.startswith(name+":") or line.startswith(name+";"):
            return line.split(":",1)[1]
    return ""


def event_date(ev):
    m=re.search(r"(\d{8})",prop(ev,"DTSTART"))
    return m.group(1) if m else "99999999"


def event_year(ev):
    d=event_date(ev)
    return int(d[:4]) if d[:4].isdigit() else 9999


def normalized_summary(ev):
    s=prop(ev,"SUMMARY").strip().casefold()
    s=s.replace(" - sprint - "," sprint - ")
    s=s.replace("grande bretagne","grande-bretagne")
    return " ".join(unicodedata.normalize("NFKC",s).split())


def key(ev):
    return (event_date(ev),normalized_summary(ev))


def write_history(events):
    events=sorted(events,key=lambda ev:(event_date(ev),prop(ev,"SUMMARY")))
    lines=[
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Oliver Thibaut//Formula 1 History//FR",
        "X-WR-CALNAME:Formula 1 History",
        "X-WR-TIMEZONE:Europe/Paris",
    ]
    for ev in events:
        lines.append("BEGIN:VEVENT")
        lines.extend(ev)
        lines.append("END:VEVENT")
    lines += ["END:VCALENDAR",""]
    HISTORY.write_text("\r\n".join(lines),encoding="utf-8")


def main():
    history=extract_events(HISTORY)
    current=extract_events(CURRENT)

    candidates=history + [ev for ev in current if event_year(ev) < SEASON]
    merged=[]
    seen=set()
    for ev in candidates:
        k=key(ev)
        if k in seen:
            continue
        seen.add(k)
        merged.append(ev)

    write_history(merged)
    print(f"Saison courante : {SEASON}")
    print(f"Historique conservé : {len(merged)} événement(s)")


if __name__ == "__main__":
    main()
