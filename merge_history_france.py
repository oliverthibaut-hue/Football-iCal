#!/usr/bin/env python3

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

HISTORY_FILE = (
    BASE_DIR / "equipe-de-france-history.ics"
)

CURRENT_FILE = (
    BASE_DIR / "Equipe-de-France.ics"
)


def unfold(text):

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    output = []

    for line in text.split("\n"):

        if (
            line.startswith((" ", "\t"))
            and output
        ):
            output[-1] += line[1:]

        else:
            output.append(line)

    return output


def parse_events(path):

    lines = unfold(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    events = []
    current = None

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


def prop(event, name):

    name = name.upper()

    for line in event:

        left = (
            line
            .split(":", 1)[0]
            .upper()
        )

        if (
            left == name
            or left.startswith(name + ";")
        ):
            return (
                line
                .split(":", 1)[1]
                .strip()
            )

    return ""


def event_start(event):

    value = prop(
        event,
        "DTSTART",
    )

    if not value:

        return datetime.max.replace(
            tzinfo=timezone.utc
        )

    if value.endswith("Z"):

        return datetime.strptime(
            value,
            "%Y%m%dT%H%M%SZ",
        ).replace(
            tzinfo=timezone.utc
        )

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if len(digits) >= 14:

        return datetime.strptime(
            digits[:14],
            "%Y%m%d%H%M%S",
        ).replace(
            tzinfo=timezone.utc
        )

    return datetime.max.replace(
        tzinfo=timezone.utc
    )


def event_key(event):

    uid = prop(
        event,
        "UID",
    )

    if uid:
        return "UID:" + uid

    return (
        "FALLBACK:"
        + prop(event, "DTSTART")
        + "|"
        + prop(event, "SUMMARY")
    )


def fold_line(line, limit=73):

    if len(line.encode("utf-8")) <= limit:
        return [line]

    parts = []
    current = ""
    continuation = False

    for char in line:

        prefix = (
            " "
            if continuation
            else ""
        )

        candidate = (
            prefix
            + current
            + char
        )

        if (
            current
            and len(
                candidate.encode("utf-8")
            ) > limit
        ):

            parts.append(
                prefix + current
            )

            current = char
            continuation = True

        else:
            current += char

    if current:

        prefix = (
            " "
            if continuation
            else ""
        )

        parts.append(
            prefix + current
        )

    return parts


def write_calendar(events):

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",

        (
            "PRODID:"
            "-//Football-iCal//"
            "Equipe de France Combined//FR"
        ),

        (
            "X-WR-CALNAME:"
            "Équipe de France 🇫🇷"
        ),

        "X-WR-TIMEZONE:Europe/Paris",

        "X-APPLE-CALENDAR-COLOR:#0055A4",
    ]

    for event in sorted(
        events,
        key=event_start,
    ):

        lines.append(
            "BEGIN:VEVENT"
        )

        lines.extend(
            event
        )

        lines.append(
            "END:VEVENT"
        )

    lines.append(
        "END:VCALENDAR"
    )

    folded = []

    for line in lines:

        folded.extend(
            fold_line(line)
        )

    CURRENT_FILE.write_text(
        "\r\n".join(folded)
        + "\r\n",
        encoding="utf-8",
    )


def main():

    if not HISTORY_FILE.exists():

        raise SystemExit(
            "Historique introuvable : "
            + str(HISTORY_FILE)
        )

    if not CURRENT_FILE.exists():

        raise SystemExit(
            "Calendrier courant introuvable : "
            + str(CURRENT_FILE)
        )

    history = parse_events(
        HISTORY_FILE
    )

    current = parse_events(
        CURRENT_FILE
    )

    combined = {}

    for event in history:

        combined[
            event_key(event)
        ] = event

    for event in current:

        combined[
            event_key(event)
        ] = event

    write_calendar(
        list(
            combined.values()
        )
    )

    print()
    print(
        "FUSION HISTORIQUE "
        "ÉQUIPE DE FRANCE"
    )
    print()

    print(
        f"Historique : "
        f"{len(history)} événements"
    )

    print(
        f"Automatique : "
        f"{len(current)} événements"
    )

    print(
        f"Total publié : "
        f"{len(combined)} événements"
    )

    print(
        f"Sortie : "
        f"{CURRENT_FILE}"
    )

    print()


if __name__ == "__main__":
    main()
