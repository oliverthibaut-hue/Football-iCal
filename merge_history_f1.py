#!/usr/bin/env python3
from pathlib import Path
import re
import unicodedata

BASE = Path(__file__).resolve().parent
HISTORY = BASE / "formula1-history.ics"
CURRENT = BASE / "Formula-1.ics"


def unfold(text):
    out=[]
    for line in text.replace("\r\n","\n").replace("\r","\n").split("\n"):
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def extract_events(path):
    if not path.exists():
        return []
    lines=unfold(path.read_text(encoding="utf-8",errors="replace"))
    events=[]
    cur=None
    for line in lines:
        if line == "BEGIN:VEVENT":
            cur=[]
        elif line == "END:VEVENT" and cur is not None:
            events.append(cur)
            cur=None
        elif cur is not None:
            cur.append(line)
    return events


def prop(ev, name):
    for line in ev:
        if line.startswith(name + ":") or line.startswith(name + ";"):
            return line.split(":",1)[1]
    return ""


def event_date(ev):
    value=prop(ev,"DTSTART")
    m=re.search(r"(\d{8})",value)
    return m.group(1) if m else "99999999"


def normalized_summary(ev):
    s=prop(ev,"SUMMARY").strip().casefold()
    s=s.replace(" - sprint - ", " sprint - ")
    s=s.replace("grande bretagne", "grande-bretagne")
    s=unicodedata.normalize("NFKC",s)
    return " ".join(s.split())


def key(ev):
    return (event_date(ev), normalized_summary(ev))


def write_calendar(events):
    events=sorted(events,key=lambda ev:(event_date(ev),prop(ev,"SUMMARY")))
    lines=[
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Oliver Thibaut//Formula 1 Calendar//FR",
        "X-WR-CALNAME:Formula 1",
        "X-WR-TIMEZONE:Europe/Paris",
    ]
    for ev in events:
        lines.append("BEGIN:VEVENT")
        lines.extend(ev)
        lines.append("END:VEVENT")
    lines += ["END:VCALENDAR",""]
    CURRENT.write_text("\r\n".join(lines),encoding="utf-8")


def main():
    history=extract_events(HISTORY)
    current=extract_events(CURRENT)

    merged=[]
    seen=set()
    for ev in history + current:
        k=key(ev)
        if k in seen:
            continue
        seen.add(k)
        merged.append(ev)

    write_calendar(merged)
    print(f"Historique : {len(history)}")
    print(f"Saison auto : {len(current)}")
    print(f"Total fusionné : {len(merged)}")


if __name__ == "__main__":
    main()
