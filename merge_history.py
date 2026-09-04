#!/usr/bin/env python3
"""Fusionne l'historique Real Madrid avec le calendrier automatique courant.

Le fichier historique est statique et nettoyé. Le fichier automatique est régénéré
à chaque exécution. Le résultat remplace Real-Madrid.ics.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "real-madrid-history.ics"
CURRENT_FILE = BASE_DIR / "Real-Madrid.ics"
CUTOFF = datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc)


def unfold(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for line in text.split("\n"):
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def fold_line(line: str, limit: int = 73) -> list[str]:
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


def parse_events(path: Path) -> list[list[str]]:
    lines = unfold(path.read_text(encoding="utf-8", errors="replace"))
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


def prop(event: list[str], name: str) -> str | None:
    name = name.upper()
    for line in event:
        upper = line.upper()
        if upper.startswith(name + ":") or upper.startswith(name + ";"):
            return line.split(":", 1)[1].strip()
    return None


def event_start(event: list[str]) -> datetime:
    value = prop(event, "DTSTART")
    if not value:
        return datetime.max.replace(tzinfo=timezone.utc)
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    # Les deux fichiers fusionnés sont normalement déjà en UTC. Ce fallback ne
    # sert qu'à garder un tri déterministe en cas de fichier ancien atypique.
    digits = re.sub(r"\D", "", value)
    if len(digits) >= 14:
        return datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return datetime.max.replace(tzinfo=timezone.utc)


def event_key(event: list[str]) -> str:
    uid = prop(event, "UID")
    if uid:
        return "UID:" + uid
    return "FALLBACK:" + "|".join([
        prop(event, "DTSTART") or "",
        prop(event, "SUMMARY") or "",
    ])


def write_calendar(events: list[list[str]], path: Path) -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Football-iCal//Real Madrid Combined//FR",
        "X-WR-CALNAME:Real Madrid CF",
    ]

    for event in sorted(events, key=event_start):
        lines.append("BEGIN:VEVENT")
        lines.extend(event)
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(fold_line(line))

    path.write_text("\r\n".join(folded) + "\r\n", encoding="utf-8")


def main() -> None:
    if not HISTORY_FILE.exists():
        raise SystemExit(f"Historique introuvable : {HISTORY_FILE}")
    if not CURRENT_FILE.exists():
        raise SystemExit(f"Calendrier automatique introuvable : {CURRENT_FILE}")

    history = [e for e in parse_events(HISTORY_FILE) if event_start(e) < CUTOFF]
    current = [e for e in parse_events(CURRENT_FILE) if event_start(e) >= CUTOFF]

    combined: dict[str, list[str]] = {}
    for event in history:
        combined[event_key(event)] = event
    for event in current:
        combined[event_key(event)] = event

    write_calendar(list(combined.values()), CURRENT_FILE)

    print("FUSION HISTORIQUE REAL MADRID")
    print(f"Historique : {len(history)} événements")
    print(f"Automatique : {len(current)} événements")
    print(f"Total publié : {len(combined)} événements")
    print(f"Sortie : {CURRENT_FILE}")


if __name__ == "__main__":
    main()
