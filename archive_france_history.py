#!/usr/bin/env python3

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CURRENT_FILE = BASE_DIR / "Equipe-de-France.ics"

HISTORY_FILE = (
    BASE_DIR / "equipe-de-france-history.ics"
)


# ============================================================
# LECTURE ICS
# ============================================================

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

    if not path.exists():
        return []

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    events = []
    current = None

    for line in unfold(text):

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


# ============================================================
# DATES
# ============================================================

def parse_datetime(value):

    if not value:
        return None

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

    return None


def event_start(event):

    value = prop(
        event,
        "DTSTART",
    )

    dt = parse_datetime(value)

    if dt:
        return dt

    return datetime.max.replace(
        tzinfo=timezone.utc
    )


def event_end(event):

    value = prop(
        event,
        "DTEND",
    )

    dt = parse_datetime(value)

    if dt:
        return dt

    return event_start(event)


# ============================================================
# DÉDOUBLONNAGE
# ============================================================

def normalize_text(value):

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    value = value.casefold()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalized_summary(event):

    summary = prop(
        event,
        "SUMMARY",
    )

    # Suppression des scores :
    #
    # France 🇫🇷 2 - 1 🇮🇹 Italie
    #
    # devient comparable à :
    #
    # France 🇫🇷 - 🇮🇹 Italie

    summary = re.sub(
        r"\s+\d+\s*-\s*\d+\s+",
        " - ",
        summary,
    )

    return normalize_text(summary)


def event_key(event):

    start = event_start(event)

    date_key = start.strftime(
        "%Y%m%d"
    )

    summary = normalized_summary(
        event
    )

    return (
        date_key,
        summary,
    )


# ============================================================
# ÉCRITURE
# ============================================================

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


def write_calendar(
    path,
    events,
    history=False,
):

    if history:

        prodid = (
            "-//Football-iCal//"
            "Equipe de France History//FR"
        )

    else:

        prodid = (
            "-//Football-iCal//"
            "Equipe de France//FR"
        )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"PRODID:{prodid}",
        (
            "X-WR-CALNAME:"
            "Équipe de France 🇫🇷"
        ),
        "X-WR-TIMEZONE:Europe/Paris",
        "X-APPLE-CALENDAR-COLOR:#0055A4",
    ]

    events = sorted(
        events,
        key=event_start,
    )

    for event in events:

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

    path.write_text(
        "\r\n".join(folded)
        + "\r\n",
        encoding="utf-8",
    )


# ============================================================
# PROGRAMME
# ============================================================

def main():

    if not CURRENT_FILE.exists():

        raise SystemExit(
            "Calendrier France courant introuvable"
        )

    if not HISTORY_FILE.exists():

        raise SystemExit(
            "Historique France introuvable"
        )

    now = datetime.now(
        timezone.utc
    )

    history = parse_events(
        HISTORY_FILE
    )

    current = parse_events(
        CURRENT_FILE
    )

    history_by_key = {}

    for event in history:

        history_by_key[
            event_key(event)
        ] = event

    remaining_current = []

    archived = 0
    updated = 0

    for event in current:

        # Le match est terminé.
        if event_end(event) <= now:

            key = event_key(event)

            if key in history_by_key:

                # Si le match existe déjà,
                # on remplace l'ancienne version
                # par la version automatique,
                # par exemple avec le score final.

                history_by_key[
                    key
                ] = event

                updated += 1

            else:

                history_by_key[
                    key
                ] = event

                archived += 1

        else:

            # Match encore à venir :
            # il reste dans le calendrier courant.

            remaining_current.append(
                event
            )

    new_history = list(
        history_by_key.values()
    )

    write_calendar(
        HISTORY_FILE,
        new_history,
        history=True,
    )

    write_calendar(
        CURRENT_FILE,
        remaining_current,
        history=False,
    )

    print()
    print(
        "ARCHIVAGE ÉQUIPE DE FRANCE"
    )
    print()

    print(
        "Date UTC : "
        + now.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    print(
        f"Historique avant : "
        f"{len(history)}"
    )

    print(
        f"Calendrier courant : "
        f"{len(current)}"
    )

    print(
        f"Nouveaux matchs archivés : "
        f"{archived}"
    )

    print(
        f"Matchs historiques mis à jour : "
        f"{updated}"
    )

    print(
        f"Historique après : "
        f"{len(new_history)}"
    )

    print(
        f"Matchs encore courants/futurs : "
        f"{len(remaining_current)}"
    )

    print()


if __name__ == "__main__":
    main()
