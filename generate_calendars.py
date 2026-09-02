from datetime import datetime, timedelta, timezone
from pathlib import Path

from merge_test import (
    SOURCES,
    SEASON_START,
    SEASON_END,
    read_ics,
    get_field,
    parse_ics_date,
    parse_fixture_teams,
    load_official_matches,
    find_official_match,
    build_title,
    format_location,
    is_stale_placeholder,
)


BASE_DIR = Path(__file__).resolve().parent

OUTPUTS = {
    "Real Madrid CF": "Real-Madrid.ics",
    "Málaga CF": "Malaga-CF.ics",
}

MATCH_DURATION = timedelta(
    hours=1,
    minutes=45
)


# ============================================================
# ÉCHAPPEMENT ICAL
# ============================================================

def escape_ical_text(value):

    if not value:
        return ""

    return (
        value
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


# ============================================================
# PLIAGE DES LIGNES ICAL
# RFC 5545 : lignes limitées à ~75 octets
# ============================================================

def fold_ical_line(line):

    if len(line.encode("utf-8")) <= 75:
        return line

    result = []
    current = ""

    for char in line:

        candidate = current + char

        if len(candidate.encode("utf-8")) > 74:

            result.append(current)

            # Ligne suivante = continuation iCal
            current = " " + char

        else:
            current = candidate

    if current:
        result.append(current)

    return "\r\n".join(result)


def add_line(lines, line):

    lines.append(
        fold_ical_line(line)
    )


# ============================================================
# CONSTRUCTION D'UN ÉVÉNEMENT
# ============================================================

def build_vevent(
    event,
    official_matches
):

    dtstart_raw = get_field(
        event,
        "DTSTART"
    )

    summary_raw = get_field(
        event,
        "SUMMARY"
    )

    location_raw = get_field(
        event,
        "LOCATION"
    )

    uid = get_field(
        event,
        "UID"
    )

    sequence = (
        get_field(event, "SEQUENCE")
        or "0"
    )

    last_modified = get_field(
        event,
        "LAST-MODIFIED"
    )

    status = (
        get_field(event, "STATUS")
        or "CONFIRMED"
    )


    if (
        not dtstart_raw
        or
        not summary_raw
        or
        not uid
    ):
        return None


    fixture_date = parse_ics_date(
        dtstart_raw
    )


    # --------------------------------------------------------
    # SAISON
    # --------------------------------------------------------

    if (
        fixture_date.date()
        < SEASON_START
    ):
        return None

    if (
        fixture_date.date()
        > SEASON_END
    ):
        return None


    # --------------------------------------------------------
    # PLACEHOLDER OBSOLÈTE
    # --------------------------------------------------------

    if is_stale_placeholder(
        fixture_date,
        summary_raw,
        location_raw,
        official_matches
    ):
        return None


    # --------------------------------------------------------
    # ÉQUIPES
    # --------------------------------------------------------

    home, away = parse_fixture_teams(
        summary_raw
    )


    # --------------------------------------------------------
    # MATCH OFFICIEL
    # --------------------------------------------------------

    official_match = find_official_match(
        fixture_date,
        home,
        away,
        official_matches
    )


    # --------------------------------------------------------
    # TITRE FINAL
    # --------------------------------------------------------

    title = build_title(
        summary_raw,
        fixture_date,
        official_match
    )


    # --------------------------------------------------------
    # LIEU FINAL
    # --------------------------------------------------------

    location = format_location(
        location_raw
    )


    # --------------------------------------------------------
    # DURÉE FIXE 1 H 45
    # --------------------------------------------------------

    end_date = (
        fixture_date
        + MATCH_DURATION
    )


    # UTC dans le fichier ICS
    dtstart = fixture_date.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    dtend = end_date.strftime(
        "%Y%m%dT%H%M%SZ"
    )


    # --------------------------------------------------------
    # VEVENT
    # --------------------------------------------------------

    lines = []

    add_line(
        lines,
        "BEGIN:VEVENT"
    )

    add_line(
        lines,
        f"UID:{uid}"
    )

    add_line(
        lines,
        f"DTSTART:{dtstart}"
    )

    add_line(
        lines,
        f"DTEND:{dtend}"
    )

    add_line(
        lines,
        "DTSTAMP:"
        + datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    add_line(
        lines,
        f"SEQUENCE:{sequence}"
    )

    add_line(
        lines,
        f"STATUS:{status}"
    )

    add_line(
        lines,
        "TRANSP:OPAQUE"
    )

    add_line(
        lines,
        "CLASS:PUBLIC"
    )

    add_line(
        lines,
        "SUMMARY:"
        + escape_ical_text(
            title
        )
    )


    if location:

        add_line(
            lines,
            "LOCATION:"
            + escape_ical_text(
                location
            )
        )


    if last_modified:

        add_line(
            lines,
            "LAST-MODIFIED:"
            + last_modified
        )


    add_line(
        lines,
        "END:VEVENT"
    )

    return "\r\n".join(lines)


# ============================================================
# CONSTRUCTION DU CALENDRIER
# ============================================================

def generate_calendar(
    club,
    source_filename,
    output_filename,
    official_matches
):

    events = read_ics(
        source_filename
    )

    generated_events = []


    for event in events:

        vevent = build_vevent(
            event,
            official_matches
        )

        if vevent:
            generated_events.append(
                vevent
            )


    calendar_lines = [

        "BEGIN:VCALENDAR",

        "VERSION:2.0",

        "PRODID:"
        "-//Thibaut Oliver//"
        "Football Calendar//FR",

        "CALSCALE:GREGORIAN",

        "METHOD:PUBLISH",

        "X-WR-CALNAME:"
        + escape_ical_text(
            club
        ),

        "X-WR-TIMEZONE:"
        "Europe/Paris",
    ]


    content = (
        "\r\n".join(
            calendar_lines
        )
        + "\r\n"
        + "\r\n".join(
            generated_events
        )
        + "\r\n"
        + "END:VCALENDAR"
        + "\r\n"
    )


    output_path = (
        BASE_DIR
        / output_filename
    )


    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        file.write(
            content
        )


    print(
        f"{club} : "
        f"{len(generated_events)} événements"
    )

    print(
        f"→ {output_path}"
    )


# ============================================================
# PROGRAMME
# ============================================================

def main():

    official_matches = (
        load_official_matches()
    )


    print()
    print(
        "GÉNÉRATION DES CALENDRIERS"
    )
    print(
        "=" * 60
    )


    for (
        club,
        source_filename
    ) in SOURCES.items():

        output_filename = (
            OUTPUTS[club]
        )

        generate_calendar(
            club,
            source_filename,
            output_filename,
            official_matches
        )

        print()


if __name__ == "__main__":
    main()
