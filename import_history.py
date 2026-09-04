#!/usr/bin/env python3
"""Nettoie un export Apple Calendar du Real Madrid pour en faire un historique public.

- conserve uniquement les événements antérieurs au 1er juillet 2026 ;
- supprime ATTENDEE / ORGANIZER / DESCRIPTION / X-MICROSOFT-* et toute autre
  métadonnée non nécessaire ;
- convertit DTSTART / DTEND en UTC ;
- conserve les UID historiques ;
- harmonise quelques libellés connus.

Usage :
    python3 import_history.py "Real Madrid CF.ics" real-madrid-history.ics
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CUTOFF = datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc)
DEFAULT_TZ = "Europe/Paris"


def unfold_ics(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for line in text.split("\n"):
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def fold_ical_line(line: str, limit: int = 73) -> list[str]:
    """Plie une ligne en restant sous la limite iCalendar en octets UTF-8."""
    if len(line.encode("utf-8")) <= limit:
        return [line]

    parts: list[str] = []
    current = ""
    prefix = ""
    for ch in line:
        candidate = current + ch
        if len((prefix + candidate).encode("utf-8")) > limit:
            parts.append(prefix + current)
            current = ch
            prefix = " "
        else:
            current = candidate
    if current or not parts:
        parts.append(prefix + current)
    return parts


def parse_events(text: str) -> list[list[str]]:
    lines = unfold_ics(text)
    events: list[list[str]] = []
    current: list[str] | None = None

    for line in lines:
        if line == "BEGIN:VEVENT":
            current = []
        elif line == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
        elif current is not None:
            current.append(line)

    return events


def find_property(event: list[str], name: str) -> tuple[str | None, str | None]:
    prefix = name.upper()
    for line in event:
        upper = line.upper()
        if upper.startswith(prefix + ":") or upper.startswith(prefix + ";"):
            key, value = line.split(":", 1)
            return key, value
    return None, None


def parse_datetime_property(key: str, value: str) -> tuple[datetime, bool]:
    """Retourne (datetime UTC, all_day)."""
    params = key.split(";")[1:]
    tzid = None
    is_date = False

    for param in params:
        if param.upper().startswith("TZID="):
            tzid = param.split("=", 1)[1]
        elif param.upper() == "VALUE=DATE":
            is_date = True

    value = value.strip()

    if is_date or (len(value) == 8 and "T" not in value):
        dt = datetime.strptime(value, "%Y%m%d").replace(tzinfo=ZoneInfo(DEFAULT_TZ))
        return dt.astimezone(timezone.utc), True

    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt, False

    source_tz = ZoneInfo(tzid or DEFAULT_TZ)
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=source_tz)
    return dt.astimezone(timezone.utc), False


def utc_property(name: str, dt: datetime) -> str:
    return f"{name}:{dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def normalize_summary(summary: str) -> str:
    # Convention actuelle du calendrier automatique.
    summary = summary.replace("LaLiga EA Sport |", "LaLiga EA Sports |")

    # Correction d'une coquille présente dans l'export d'origine.
    summary = re.sub(r"\beal Madrid CF\b", "Real Madrid CF", summary)

    return summary.strip()


def build_clean_event(event: list[str]) -> tuple[datetime, list[str]] | None:
    start_key, start_value = find_property(event, "DTSTART")
    end_key, end_value = find_property(event, "DTEND")
    _, uid = find_property(event, "UID")
    _, summary = find_property(event, "SUMMARY")
    _, location = find_property(event, "LOCATION")
    _, status = find_property(event, "STATUS")
    _, last_modified = find_property(event, "LAST-MODIFIED")

    if not all([start_key, start_value, end_key, end_value, uid, summary, location]):
        return None

    start_utc, _ = parse_datetime_property(start_key, start_value)
    end_utc, _ = parse_datetime_property(end_key, end_value)

    if start_utc >= CUTOFF:
        return None

    clean = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        utc_property("DTSTART", start_utc),
        utc_property("DTEND", end_utc),
        f"SUMMARY:{normalize_summary(summary)}",
        f"LOCATION:{location.strip()}",
        f"STATUS:{(status or 'CONFIRMED').strip()}",
        "CLASS:PUBLIC",
        "TRANSP:OPAQUE",
    ]

    if last_modified:
        clean.append(f"LAST-MODIFIED:{last_modified.strip()}")

    clean.append("END:VEVENT")
    return start_utc, clean


def write_calendar(events: list[tuple[datetime, list[str]]], output: Path) -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Football-iCal//Real Madrid History//FR",
        "X-WR-CALNAME:Real Madrid CF - Historique",
    ]

    for _, event_lines in sorted(events, key=lambda item: item[0]):
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(fold_ical_line(line))

    output.write_text("\r\n".join(folded) + "\r\n", encoding="utf-8")


def privacy_check(text: str) -> list[str]:
    forbidden = [
        "ATTENDEE",
        "ORGANIZER",
        "DESCRIPTION",
        "X-MICROSOFT",
        "TEAMS.MICROSOFT",
        "MAILTO:",
        "@RWE.COM",
        "@ME.COM",
    ]
    upper = text.upper()
    return [token for token in forbidden if token in upper]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="Real Madrid CF.ics")
    parser.add_argument("output", nargs="?", default="real-madrid-history.ics")
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)

    if not source.exists():
        raise SystemExit(f"Fichier introuvable : {source}")

    source_text = source.read_text(encoding="utf-8", errors="replace")
    raw_events = parse_events(source_text)

    clean_events: list[tuple[datetime, list[str]]] = []
    skipped = 0

    for event in raw_events:
        cleaned = build_clean_event(event)
        if cleaned is None:
            skipped += 1
        else:
            clean_events.append(cleaned)

    write_calendar(clean_events, output)

    result = output.read_text(encoding="utf-8", errors="replace")
    leaks = privacy_check(result)

    if leaks:
        raise SystemExit(
            "ERREUR : métadonnées sensibles encore détectées : " + ", ".join(leaks)
        )

    print("IMPORT HISTORIQUE REAL MADRID")
    print(f"Source : {source}")
    print(f"Événements source : {len(raw_events)}")
    print(f"Événements historiques conservés : {len(clean_events)}")
    print(f"Événements ignorés : {skipped}")
    print(f"Sortie : {output}")
    print("Contrôle confidentialité : OK")


if __name__ == "__main__":
    main()
