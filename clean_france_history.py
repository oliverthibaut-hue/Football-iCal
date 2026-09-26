#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import re


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "france-original.ics"
OUTPUT_FILE = BASE_DIR / "equipe-de-france-history.ics"

# Tout ce qui commence avant le 26 septembre 2026
# appartient à l'historique.
CUTOFF = datetime(
    2026, 9, 26, 0, 0,
    tzinfo=ZoneInfo("Europe/Paris")
)


def unfold(text):
    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    output = []

    for line in text.split("\n"):

        if line.startswith((" ", "\t")) and output:
            output[-1] += line[1:]

        else:
            output.append(line)

    return output


def fold_line(line, limit=73):

    if len(line.encode("utf-8")) <= limit:
        return [line]

    parts = []
    current = ""
    continuation = False

    for char in line:

        prefix = " " if continuation else ""

        candidate = prefix + current + char

        if (
            current
            and len(candidate.encode("utf-8")) > limit
        ):
            parts.append(prefix + current)
            current = char
            continuation = True

        else:
            current += char

    prefix = " " if continuation else ""

    if current:
        parts.append(prefix + current)

    return parts


def parse_events(lines):

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


def find_property(event, name):

    name = name.upper()

    for line in event:

        left = line.split(":", 1)[0].upper()

        if (
            left == name
            or left.startswith(name + ";")
        ):
            return line

    return None


def property_value(event, name):

    line = find_property(event, name)

    if not line or ":" not in line:
        return ""

    return line.split(":", 1)[1].strip()


def parse_datetime_property(line):

    if not line:
        return None

    left, value = line.split(":", 1)

    value = value.strip()

    if "VALUE=DATE" in left.upper():
        return None

    if value.endswith("Z"):

        return datetime.strptime(
            value,
            "%Y%m%dT%H%M%SZ"
        ).replace(
            tzinfo=timezone.utc
        )

    match = re.search(
        r"TZID=([^;:]+)",
        left,
        flags=re.IGNORECASE
    )

    timezone_name = (
        match.group(1)
        if match
        else "Europe/Paris"
    )

    try:
        tz = ZoneInfo(timezone_name)

    except Exception:
        tz = ZoneInfo("Europe/Paris")

    dt = datetime.strptime(
        value,
        "%Y%m%dT%H%M%S"
    )

    return dt.replace(
        tzinfo=tz
    ).astimezone(
        timezone.utc
    )


def escape_ics(value):

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def clean_event(event):

    start = parse_datetime_property(
        find_property(event, "DTSTART")
    )

    if start is None:
        return None

    # Les matchs futurs ne font pas encore partie
    # de l'historique.
    if start >= CUTOFF.astimezone(timezone.utc):
        return None

    end = parse_datetime_property(
        find_property(event, "DTEND")
    )

    if end is None:
        end = start + timedelta(
            hours=1,
            minutes=45
        )

    summary = property_value(
        event,
        "SUMMARY"
    ).strip()

    location = property_value(
        event,
        "LOCATION"
    ).strip()

    if not summary:
        return None

    # UID propre et stable :
    # aucune information Outlook / personnelle.
    uid_source = (
        start.isoformat()
        + "|"
        + summary
    )

    uid_hash = hashlib.sha1(
        uid_source.encode("utf-8")
    ).hexdigest()[:20]

    uid = (
        f"france-history-{uid_hash}"
        "@oliverthibaut-football-ical"
    )

    output = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        (
            "DTSTAMP:"
            + datetime.now(timezone.utc)
            .strftime("%Y%m%dT%H%M%SZ")
        ),
        (
            "DTSTART:"
            + start.strftime(
                "%Y%m%dT%H%M%SZ"
            )
        ),
        (
            "DTEND:"
            + end.strftime(
                "%Y%m%dT%H%M%SZ"
            )
        ),
        "SEQUENCE:0",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        "CLASS:PUBLIC",
        (
            "SUMMARY:"
            + escape_ics(summary)
        ),
    ]

    if location:

        output.append(
            "LOCATION:"
            + escape_ics(location)
        )

    output.append(
        "END:VEVENT"
    )

    return start, output


def main():

    if not INPUT_FILE.exists():

        raise SystemExit(
            "Fichier introuvable : "
            "france-original.ics"
        )

    raw = INPUT_FILE.read_text(
        encoding="utf-8",
        errors="replace"
    )

    events = parse_events(
        unfold(raw)
    )

    cleaned = []

    for event in events:

        result = clean_event(event)

        if result:
            cleaned.append(result)

    cleaned.sort(
        key=lambda item: item[0]
    )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        (
            "PRODID:"
            "-//Football-iCal//"
            "Equipe de France History//FR"
        ),
        (
            "X-WR-CALNAME:"
            "Équipe de France 🇫🇷"
        ),
        "X-APPLE-CALENDAR-COLOR:#0055A4",
    ]

    for _, event_lines in cleaned:
        lines.extend(event_lines)

    lines.append(
        "END:VCALENDAR"
    )

    folded = []

    for line in lines:
        folded.extend(
            fold_line(line)
        )

    OUTPUT_FILE.write_text(
        "\r\n".join(folded)
        + "\r\n",
        encoding="utf-8"
    )

    print()
    print(
        "NETTOYAGE HISTORIQUE "
        "ÉQUIPE DE FRANCE"
    )
    print()

    print(
        f"Événements dans l'original : "
        f"{len(events)}"
    )

    print(
        f"Matchs conservés : "
        f"{len(cleaned)}"
    )

    print(
        f"Matchs futurs exclus : "
        f"{len(events) - len(cleaned)}"
    )

    print(
        f"Sortie : "
        f"{OUTPUT_FILE}"
    )

    print()


if __name__ == "__main__":
    main()
