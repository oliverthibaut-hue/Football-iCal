#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILE = BASE_DIR / "france-source.ics"
OUTPUT_FILE = BASE_DIR / "Equipe-de-France.ics"

# Le 25/09/2026 est déjà intégré à notre historique.
CUTOFF = datetime(
    2026, 9, 26,
    0, 0, 0,
    tzinfo=timezone.utc,
)


# ============================================================
# NOMS DES PAYS
# ============================================================

COUNTRIES = {
    "France": ("France", "🇫🇷"),
    "Belgium": ("Belgique", "🇧🇪"),
    "Belgique": ("Belgique", "🇧🇪"),
    "Italy": ("Italie", "🇮🇹"),
    "Italie": ("Italie", "🇮🇹"),
    "Turkey": ("Turquie", "🇹🇷"),
    "Türkiye": ("Turquie", "🇹🇷"),
    "Turquie": ("Turquie", "🇹🇷"),

    "Germany": ("Allemagne", "🇩🇪"),
    "Allemagne": ("Allemagne", "🇩🇪"),

    "Spain": ("Espagne", "🇪🇸"),
    "Espagne": ("Espagne", "🇪🇸"),

    "England": ("Angleterre", "🏴"),
    "Angleterre": ("Angleterre", "🏴"),

    "Portugal": ("Portugal", "🇵🇹"),
    "Netherlands": ("Pays-Bas", "🇳🇱"),
    "Pays-Bas": ("Pays-Bas", "🇳🇱"),

    "Croatia": ("Croatie", "🇭🇷"),
    "Croatie": ("Croatie", "🇭🇷"),

    "Brazil": ("Brésil", "🇧🇷"),
    "Brésil": ("Brésil", "🇧🇷"),

    "Colombia": ("Colombie", "🇨🇴"),
    "Colombie": ("Colombie", "🇨🇴"),

    "Morocco": ("Maroc", "🇲🇦"),
    "Maroc": ("Maroc", "🇲🇦"),

    "Senegal": ("Sénégal", "🇸🇳"),
    "Sénégal": ("Sénégal", "🇸🇳"),

    "Iraq": ("Irak", "🇮🇶"),
    "Irak": ("Irak", "🇮🇶"),

    "Norway": ("Norvège", "🇳🇴"),
    "Norvège": ("Norvège", "🇳🇴"),

    "Sweden": ("Suède", "🇸🇪"),
    "Suède": ("Suède", "🇸🇪"),

    "Paraguay": ("Paraguay", "🇵🇾"),

    "Ivory Coast": ("Côte-d'Ivoire", "🇨🇮"),
    "Côte d’Ivoire": ("Côte-d'Ivoire", "🇨🇮"),
    "Côte-d'Ivoire": ("Côte-d'Ivoire", "🇨🇮"),

    "Northern Ireland": ("Irlande du Nord", "🏴"),
    "Irlande du Nord": ("Irlande du Nord", "🏴"),

    "Iceland": ("Islande", "🇮🇸"),
    "Islande": ("Islande", "🇮🇸"),

    "Ukraine": ("Ukraine", "🇺🇦"),

    "Azerbaijan": ("Azerbaïdjan", "🇦🇿"),
    "Azerbaïdjan": ("Azerbaïdjan", "🇦🇿"),
}


# ============================================================
# NATIONS LEAGUE 2026
# ============================================================

NATIONS_LEAGUE = {
    "20260928": {
        "round": 2,
        "location":
            "Bruxelles (Belgique) - Stade Roi Baudouin",
    },

    "20261002": {
        "round": 3,
        "location":
            "Saint-Denis (France) - Stade de France",
    },

    "20261005": {
        "round": 4,
        "location":
            "Saint-Denis (France) - Stade de France",
    },

    "20261112": {
        "round": 5,
        "location":
            "Rome (Italie) - Stadio Olimpico",
    },

    "20261115": {
        "round": 6,
        "location":
            "Bordeaux (France) - Stade Atlantique",
    },
}


# ============================================================
# ICS
# ============================================================

def unfold(text: str) -> list[str]:

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


def property_line(event, name):

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
            return line

    return None


def property_value(event, name):

    line = property_line(event, name)

    if not line:
        return ""

    if ":" not in line:
        return ""

    return (
        line
        .split(":", 1)[1]
        .strip()
    )


def parse_datetime(line):

    if not line:
        return None

    value = (
        line
        .split(":", 1)[1]
        .strip()
    )

    if len(value) == 8:
        return None

    if value.endswith("Z"):

        return datetime.strptime(
            value,
            "%Y%m%dT%H%M%SZ",
        ).replace(
            tzinfo=timezone.utc
        )

    # Fixtur.es est normalement en UTC.
    # Fallback déterministe si le Z manque.
    return datetime.strptime(
        value,
        "%Y%m%dT%H%M%S",
    ).replace(
        tzinfo=timezone.utc
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


def fold_line(line, limit=73):

    if len(line.encode("utf-8")) <= limit:
        return [line]

    result = []
    current = ""
    continuation = False

    for char in line:

        prefix = " " if continuation else ""

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

            result.append(
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

        result.append(
            prefix + current
        )

    return result


# ============================================================
# MATCH
# ============================================================

def normalize_team(raw):

    raw = raw.strip()

    name, flag = COUNTRIES.get(
        raw,
        (raw, "")
    )

    return name, flag


def team_display(raw):

    name, flag = normalize_team(raw)

    # Dans ta charte :
    # France -> France 🇫🇷
    # Adversaire -> Belgique 🇧🇪
    return (
        f"{name} {flag}".strip()
    )


def parse_source_summary(summary):

    summary = (
        summary
        .replace("\\,", ",")
        .strip()
    )

    # Format Fixtur.es classique :
    #
    # France - Italy
    #
    # ou après match :
    #
    # France - Italy (2-1)

    score = None

    match = re.search(
        r"\((\d+)\s*-\s*(\d+)\)\s*$",
        summary
    )

    if match:

        score = (
            match.group(1),
            match.group(2),
        )

        summary = (
            summary[:match.start()]
            .strip()
        )

    # Nettoyage éventuel de tags
    summary = re.sub(
        r"\s*\[[^\]]+\]\s*$",
        "",
        summary,
    ).strip()

    if " - " not in summary:
        return None

    home, away = summary.split(
        " - ",
        1
    )

    return (
        home.strip(),
        away.strip(),
        score,
    )


def competition_info(start, event):

    date_key = start.strftime(
        "%Y%m%d"
    )

    # Nations League actuelle
    if date_key in NATIONS_LEAGUE:

        data = NATIONS_LEAGUE[
            date_key
        ]

        return (
            "UEFA Nations League",
            (
                f"Gr. A1 - "
                f"J{data['round']}"
            ),
            data["location"],
        )

    # Détection générique pour
    # les prochaines années.
    blob = " ".join(event).lower()

    if (
        "world cup qualification"
        in blob
        or "world cup qualifier"
        in blob
    ):
        return (
            "FIFA World Cup Qualification",
            None,
            None,
        )

    if (
        "world cup"
        in blob
    ):
        return (
            "FIFA World Cup",
            None,
            None,
        )

    if (
        "nations league"
        in blob
    ):
        return (
            "UEFA Nations League",
            None,
            None,
        )

    if (
        "friendly"
        in blob
        or "oefen-interlands"
        in blob
    ):
        return (
            "Friendly",
            None,
            None,
        )

    # On préfère ne pas inventer une compétition.
    return (
        "International",
        None,
        None,
    )


def build_summary(
    competition,
    stage,
    home,
    away,
    score,
):

    home_text = team_display(home)
    away_text = team_display(away)

    prefix = competition

    if stage:
        prefix += f" | {stage}"

    else:
        prefix += " |"

    if score:

        return (
            f"{prefix} - "
            f"{home_text} "
            f"{score[0]} - "
            f"{score[1]} "
            f"{away_text}"
        )

    return (
        f"{prefix} - "
        f"{home_text} - "
        f"{away_text}"
    )


# ============================================================
# GÉNÉRATION
# ============================================================

def make_uid(
    source_uid,
    start,
    home,
    away,
):

    if source_uid:

        clean = re.sub(
            r"[^A-Za-z0-9._-]",
            "-",
            source_uid,
        )

        return (
            "france-"
            + clean[:100]
            + "@oliverthibaut-football-ical"
        )

    raw = (
        start.isoformat()
        + "|"
        + home
        + "|"
        + away
    )

    digest = hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()[:20]

    return (
        f"france-{digest}"
        "@oliverthibaut-football-ical"
    )


def main():

    if not SOURCE_FILE.exists():

        raise SystemExit(
            "france-source.ics introuvable"
        )

    raw = SOURCE_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    source_events = parse_events(
        unfold(raw)
    )

    output_events = []

    for event in source_events:

        start = parse_datetime(
            property_line(
                event,
                "DTSTART",
            )
        )

        if not start:
            continue

        # Tout ce qui est antérieur au
        # 26/09/2026 vient de l'historique.
        if start < CUTOFF:
            continue

        source_summary = property_value(
            event,
            "SUMMARY",
        )

        parsed = parse_source_summary(
            source_summary
        )

        if not parsed:
            continue

        home, away, score = parsed

        competition, stage, fallback_location = (
            competition_info(
                start,
                event,
            )
        )

        summary = build_summary(
            competition,
            stage,
            home,
            away,
            score,
        )

        location = property_value(
            event,
            "LOCATION",
        ).strip()

        # Pour les matchs actuels,
        # nos lieux validés sont plus complets.
        if fallback_location:
            location = fallback_location

        source_uid = property_value(
            event,
            "UID",
        )

        uid = make_uid(
            source_uid,
            start,
            home,
            away,
        )

        end = start + timedelta(
            hours=1,
            minutes=45,
        )

        output_events.append({
            "start": start,
            "end": end,
            "uid": uid,
            "summary": summary,
            "location": location,
        })


    output_events.sort(
        key=lambda x: x["start"]
    )


    stamp = (
        datetime.now(timezone.utc)
        .strftime("%Y%m%dT%H%M%SZ")
    )


    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        (
            "PRODID:"
            "-//Football-iCal//"
            "Equipe de France//FR"
        ),
        (
            "X-WR-CALNAME:"
            "Équipe de France 🇫🇷"
        ),
        "X-WR-TIMEZONE:Europe/Paris",
        "X-APPLE-CALENDAR-COLOR:#0055A4",
    ]


    for item in output_events:

        lines.extend([
            "BEGIN:VEVENT",

            (
                "UID:"
                + escape_ics(
                    item["uid"]
                )
            ),

            f"DTSTAMP:{stamp}",

            (
                "DTSTART:"
                + item["start"].strftime(
                    "%Y%m%dT%H%M%SZ"
                )
            ),

            (
                "DTEND:"
                + item["end"].strftime(
                    "%Y%m%dT%H%M%SZ"
                )
            ),

            "SEQUENCE:0",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "CLASS:PUBLIC",

            (
                "SUMMARY:"
                + escape_ics(
                    item["summary"]
                )
            ),
        ])

        if item["location"]:

            lines.append(
                "LOCATION:"
                + escape_ics(
                    item["location"]
                )
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


    OUTPUT_FILE.write_text(
        "\r\n".join(folded)
        + "\r\n",
        encoding="utf-8",
    )


    print()
    print(
        "GÉNÉRATION ÉQUIPE DE FRANCE"
    )
    print()

    print(
        f"Source : "
        f"{SOURCE_FILE.name}"
    )

    print(
        f"Événements source : "
        f"{len(source_events)}"
    )

    print(
        f"Événements courants/futurs : "
        f"{len(output_events)}"
    )

    print(
        f"Sortie : "
        f"{OUTPUT_FILE.name}"
    )

    print()

    for item in output_events:

        print(
            item["start"]
            .strftime(
                "%Y-%m-%d %H:%M UTC"
            ),
            "|",
            item["summary"],
        )

    print()


if __name__ == "__main__":
    main()
