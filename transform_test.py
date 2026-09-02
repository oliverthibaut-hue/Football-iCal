import re
from datetime import datetime


FILES = {
    "Real Madrid CF": "real-madrid-source.ics",
    "Málaga CF": "malaga-source.ics",
}


TEAM_NAMES = {
    "Real Madrid": "Real Madrid CF",
    "Malaga": "Málaga CF",
    "Inter": "Inter Milan",
    "Real Betis": "Real Betis Balompié",
}


def clean_ics_value(value):
    return (
        value
        .replace("\\:", ":")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .strip()
    )


def get_field(event, field):
    pattern = rf"^{field}(?:;[^:]*)?\\?:(.*)$"

    match = re.search(
        pattern,
        event,
        flags=re.MULTILINE
    )

    if match:
        return clean_ics_value(match.group(1))

    return None


def normalize_team(name):
    return TEAM_NAMES.get(name.strip(), name.strip())


def parse_summary(summary):
    # Suppression d'un éventuel score final
    summary = re.sub(r"\s+\(\d+\-\d+\)$", "", summary)

    competition = "LaLiga EA Sports"

    if "[CL]" in summary:
        competition = "UEFA Champions League"
        summary = summary.replace("[CL]", "").strip()

    home, away = summary.split(" - ", 1)

    home = normalize_team(home)
    away = normalize_team(away)

    return competition, home, away


def parse_date(value):
    if len(value) == 8:
        # Date sans heure : YYYYMMDD
        return datetime.strptime(value, "%Y%m%d")

    return datetime.strptime(value, "%Y%m%dT%H%M%SZ")


def read_events(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read().replace("\r\n", "\n")

    return content.split("BEGIN:VEVENT")[1:]


for club, filename in FILES.items():

    print("\n" + "=" * 70)
    print(club.upper())
    print("=" * 70)

    events = read_events(filename)

    liga_counter = 0
    champions_counter = 0

    for event in events:

        dtstart = get_field(event, "DTSTART")
        summary = get_field(event, "SUMMARY")
        location = get_field(event, "LOCATION")

        if not dtstart or not summary:
            continue

        date = parse_date(dtstart)

        # Seulement saison 2026-2027
        if date.year < 2026:
            continue

        # Ignore les amicaux avant le début de saison
        if date.year == 2026 and date.month < 8:
            continue

        competition, home, away = parse_summary(summary)

        # On ne garde que les matchs impliquant le club suivi
        if club not in {home, away}:
            continue

        if competition == "LaLiga EA Sports":
            liga_counter += 1
            round_name = f"J{liga_counter}"

        elif competition == "UEFA Champions League":
            champions_counter += 1
            round_name = f"J{champions_counter}"

        else:
            round_name = "?"

        title = (
            f"{competition} | {round_name} - "
            f"{home} - {away}"
        )

        print()
        print(date.strftime("%d/%m/%Y %H:%M UTC"))
        print(title)
        print(f"Stade : {location or 'Non renseigné'}")
