from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import hashlib
import re
import subprocess

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit(
        "\nBeautifulSoup n'est pas installé.\n"
        "Lance : python3 -m pip install beautifulsoup4\n"
    )

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "Union-Bordeaux-Begles.ics"
DEBUG_FILE = BASE_DIR / "ubb-debug.txt"

SOURCE_URL = (
    "https://www.ubb.link/equipes/equipe-premiere/"
    "calendrier-resultats.html"
)

PARIS = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")

MONTHS = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

WEEKDAYS = {
    "lundi", "mardi", "mercredi", "jeudi",
    "vendredi", "samedi", "dimanche"
}

TEAM_ALIASES = {
    "ubb": "Union Bordeaux Bègles",
    "union bordeaux bègles": "Union Bordeaux Bègles",
    "union bordeaux-bègles": "Union Bordeaux Bègles",
    "union bordeaux begles": "Union Bordeaux Bègles",
    "union bordeaux begles rugby": "Union Bordeaux Bègles",
    "union bordeaux bègles rugby": "Union Bordeaux Bègles",
    "bordeaux-bègles": "Union Bordeaux Bègles",
    "bordeaux-begles": "Union Bordeaux Bègles",

    "racing 92": "Racing 92",

    "stade toulousain": "Stade Toulousain",
    "toulouse": "Stade Toulousain",

    "stade français": "Stade Français Paris",
    "stade français paris": "Stade Français Paris",
    "stade francais": "Stade Français Paris",
    "stade francais paris": "Stade Français Paris",

    "perpignan": "USA Perpignan",
    "usa perpignan": "USA Perpignan",

    "lyon": "LOU Rugby",
    "lou": "LOU Rugby",
    "lou rugby": "LOU Rugby",

    "clermont": "ASM Clermont Auvergne",
    "asm clermont": "ASM Clermont Auvergne",
    "asm clermont auvergne": "ASM Clermont Auvergne",

    "la rochelle": "Stade Rochelais",
    "stade rochelais": "Stade Rochelais",

    "bayonne": "Aviron Bayonnais",
    "aviron bayonnais": "Aviron Bayonnais",

    "vannes": "RC Vannes",
    "rc vannes": "RC Vannes",

    "montpellier": "Montpellier Hérault Rugby",
    "montpellier hérault rugby": "Montpellier Hérault Rugby",
    "montpellier herault rugby": "Montpellier Hérault Rugby",

    "toulon": "RC Toulon",
    "rc toulon": "RC Toulon",

    "pau": "Section Paloise",
    "section paloise": "Section Paloise",

    "castres": "Castres Olympique",
    "castres olympique": "Castres Olympique",

    "gloucester": "Gloucester Rugby",
    "gloucester rugby": "Gloucester Rugby",

    "stormers": "DHL Stormers",
    "dhl stormers": "DHL Stormers",

    "munster": "Munster Rugby",
    "munster rugby": "Munster Rugby",

    "bristol": "Bristol Bears",
    "bristol bears": "Bristol Bears",
}

VENUES_BY_HOME = {
    "Union Bordeaux Bègles":
        "Bordeaux (France) - Stade Chaban-Delmas",
    "Racing 92":
        "Nanterre (France) - Paris La Défense Arena",
    "Stade Toulousain":
        "Toulouse (France) - Stade Ernest-Wallon",
    "Stade Français Paris":
        "Paris (France) - Stade Jean-Bouin",
    "USA Perpignan":
        "Perpignan (France) - Stade Aimé-Giral",
    "LOU Rugby":
        "Lyon (France) - Matmut Stadium Gerland",
    "ASM Clermont Auvergne":
        "Clermont-Ferrand (France) - Stade Marcel-Michelin",
    "Stade Rochelais":
        "La Rochelle (France) - Stade Marcel-Deflandre",
    "Aviron Bayonnais":
        "Bayonne (France) - Stade Jean-Dauger",
    "RC Vannes":
        "Vannes (France) - Stade de la Rabine",
    "Montpellier Hérault Rugby":
        "Montpellier (France) - Septeo Stadium",
    "RC Toulon":
        "Toulon (France) - Stade Mayol",
    "Section Paloise":
        "Pau (France) - Stade du Hameau",
    "Castres Olympique":
        "Castres (France) - Stade Pierre-Fabre",
    "Gloucester Rugby":
        "Gloucester (Royaume-Uni) - Kingsholm Stadium",
    "DHL Stormers":
        "Le Cap (Afrique du Sud) - DHL Stadium",
    "Munster Rugby":
        "Limerick (Irlande) - Thomond Park",
    "Bristol Bears":
        "Bristol (Royaume-Uni) - Ashton Gate Stadium",
}

COMP_LINE_RE = re.compile(
    r"^(Top\s*14|Champions\s*Cup)\s*-\s*$",
    re.IGNORECASE,
)

ROUND_RE = re.compile(
    r"^(\d+)\s*(?:re|er|e|ème|eme)\s+journée$",
    re.IGNORECASE,
)

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")

ONE_LINE_DATE_RE = re.compile(
    r"^(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+"
    r"(\d{1,2})\s+"
    r"([a-zàâäéèêëîïôöùûüç]+)\s+"
    r"(\d{4})$",
    re.IGNORECASE,
)


def norm(value):
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_team(value):
    raw = norm(value).lower()
    raw = re.sub(r"^(?:image|logo)\s*:?\s*", "", raw).strip()

    if raw in TEAM_ALIASES:
        return TEAM_ALIASES[raw]

    for alias, canonical in sorted(
        TEAM_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if len(alias) >= 4 and alias in raw:
            return canonical

    return None


def fetch_page():
    command = [
        "curl",
        "-L",
        "-sS",
        "--fail",
        "-A",
        "Mozilla/5.0",
        SOURCE_URL,
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"\nERREUR curl ({exc.returncode}).\n{exc.stderr}\n"
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(
            "\nERREUR : le site UBB n'a pas répondu sous 30 secondes.\n"
        )

    html = result.stdout

    if "Top 14 -" not in html:
        raise SystemExit(
            "\nERREUR : le calendrier UBB n'est pas présent "
            "dans le HTML reçu.\n"
        )

    return html


def page_to_lines(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for img in soup.find_all("img"):
        candidates = [
            img.get("alt", ""),
            img.get("title", ""),
        ]
        label = next(
            (norm(x) for x in candidates if norm(x)),
            "",
        )

        if label:
            img.replace_with(f"\n{label}\n")
        else:
            img.decompose()

    text = soup.get_text("\n")
    return [
        norm(line)
        for line in text.splitlines()
        if norm(line)
    ]


def parse_one_line_date(line):
    match = ONE_LINE_DATE_RE.match(line)
    if not match:
        return None

    day = int(match.group(1))
    month = MONTHS.get(match.group(2).lower())
    year = int(match.group(3))

    if not month:
        return None

    return datetime(year, month, day, tzinfo=PARIS)


def parse_split_date_before(lines, comp_index):
    # Cas exact observé dans ubb-debug.txt :
    # Dimanche / 13 / septembre / 2026 / Top 14 -
    if comp_index >= 4:
        weekday = lines[comp_index - 4].lower()
        day = lines[comp_index - 3]
        month_name = lines[comp_index - 2].lower()
        year = lines[comp_index - 1]

        if (
            weekday in WEEKDAYS
            and day.isdigit()
            and month_name in MONTHS
            and year.isdigit()
        ):
            return datetime(
                int(year),
                MONTHS[month_name],
                int(day),
                tzinfo=PARIS,
            )

    # Tolère également une date sur une seule ligne.
    for offset in range(1, 7):
        idx = comp_index - offset
        if idx < 0:
            break

        parsed = parse_one_line_date(lines[idx])
        if parsed:
            return parsed

    return None


def find_teams(lines, start_index, max_scan=10):
    teams = []

    for line in lines[start_index:start_index + max_scan]:
        team = normalize_team(line)

        if team and team not in teams:
            teams.append(team)

        if len(teams) == 2:
            return teams

    return teams


def find_time(lines, start_index, max_scan=5):
    for line in lines[start_index:start_index + max_scan]:
        if line == "-":
            return None

        match = TIME_RE.match(line)

        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
            )

    return None


def parse_schedule(lines):
    fixtures = []
    seen = set()

    for idx, line in enumerate(lines):
        comp_match = COMP_LINE_RE.match(line)

        if not comp_match:
            continue

        competition = (
            "Top 14"
            if comp_match.group(1).lower().replace(" ", "") == "top14"
            else "Investec Champions Cup"
        )

        match_date = parse_split_date_before(lines, idx)

        if not match_date:
            continue

        matchday = None

        if idx + 1 < len(lines):
            round_match = ROUND_RE.match(lines[idx + 1])

            if round_match:
                matchday = int(round_match.group(1))

        if matchday is None:
            continue

        time_value = find_time(lines, idx + 2)

        teams = find_teams(lines, idx + 2)

        if len(teams) < 2:
            continue

        home, away = teams[0], teams[1]

        kickoff = None

        if time_value:
            kickoff = match_date.replace(
                hour=time_value[0],
                minute=time_value[1],
                second=0,
                microsecond=0,
            )

        fixture = {
            "date": match_date,
            "kickoff": kickoff,
            "competition": competition,
            "matchday": matchday,
            "home": home,
            "away": away,
            "score": None,
            "location": VENUES_BY_HOME.get(home),
        }

        key = (
            fixture["competition"],
            fixture["matchday"],
            fixture["home"],
            fixture["away"],
        )

        if key not in seen:
            seen.add(key)
            fixtures.append(fixture)

    return fixtures


def add_known_current_season_events(fixtures):
    # J1 Top 14 : la page UBB "Calendrier" la retire après le match.
    # La LNR officielle publie désormais le résultat 64-5.
    known_events = [
        {
            "date": datetime(2026, 9, 5, tzinfo=PARIS),
            "kickoff": datetime(2026, 9, 5, 21, 15, tzinfo=PARIS),
            "competition": "Top 14",
            "matchday": 1,
            "home": "Union Bordeaux Bègles",
            "away": "Racing 92",
            "score": (64, 5),
            "location": "Bordeaux (France) - Stade Chaban-Delmas",
        },

        # Amicaux officiels affichés par l'UBB en tête de page.
        {
            "date": datetime(2026, 8, 21, tzinfo=PARIS),
            "kickoff": datetime(2026, 8, 21, 19, 30, tzinfo=PARIS),
            "competition": "Friendly",
            "matchday": None,
            "home": "Stade Rochelais",
            "away": "Union Bordeaux Bègles",
            "score": None,
            "location": None,
        },
        {
            "date": datetime(2026, 8, 28, tzinfo=PARIS),
            "kickoff": datetime(2026, 8, 28, 19, 0, tzinfo=PARIS),
            "competition": "Friendly",
            "matchday": None,
            "home": "Union Bordeaux Bègles",
            "away": "Section Paloise",
            "score": None,
            "location": "Bordeaux (France) - Stade Chaban-Delmas",
        },
    ]

    existing = {
        (
            item["competition"],
            item["matchday"],
            item["home"],
            item["away"],
        )
        for item in fixtures
    }

    for event in known_events:
        key = (
            event["competition"],
            event["matchday"],
            event["home"],
            event["away"],
        )

        if key not in existing:
            fixtures.append(event)
            existing.add(key)

    return fixtures


def escape_ics(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def fold_ics_line(line, limit=73):
    if len(line) <= limit:
        return [line]

    parts = []
    first = True

    while line:
        chunk_size = limit if first else limit - 1
        chunk = line[:chunk_size]
        line = line[chunk_size:]
        parts.append(chunk if first else " " + chunk)
        first = False

    return parts


def make_uid(fixture):
    stable_key = (
        f'{fixture["competition"]}|'
        f'{fixture["matchday"]}|'
        f'{fixture["home"]}|'
        f'{fixture["away"]}'
    )

    digest = hashlib.sha1(
        stable_key.encode("utf-8")
    ).hexdigest()[:20]

    return f"ubb-{digest}@oliverthibaut-football-ical"


def make_title(fixture):
    if fixture["competition"] == "Friendly":
        prefix = "Friendly | 🏉"

    elif fixture["competition"] == "Top 14":
        prefix = (
            f'Top14 | 🏉 J{fixture["matchday"]}'
        )

    elif fixture["competition"] == "Investec Champions Cup":
        prefix = (
            f'Champions Cup | 🏉 J{fixture["matchday"]}'
        )

    else:
        prefix = (
            f'{fixture["competition"]} | 🏉 '
            f'J{fixture["matchday"]}'
        )

    if fixture["score"]:
        hs, as_ = fixture["score"]

        match_text = (
            f'{fixture["home"]} {hs} - '
            f'{as_} {fixture["away"]}'
        )

    else:
        match_text = (
            f'{fixture["home"]} - '
            f'{fixture["away"]}'
        )

    return f"{prefix} - {match_text}"

def event_lines(fixture):
    now_utc = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VEVENT",
        f'UID:{make_uid(fixture)}',
        f"DTSTAMP:{now_utc}",
        "CLASS:PUBLIC",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
    ]

    if fixture["kickoff"]:
        start_utc = fixture["kickoff"].astimezone(UTC)
        end_utc = start_utc + timedelta(hours=1, minutes=35)

        lines.extend([
            "DTSTART:" + start_utc.strftime("%Y%m%dT%H%M%SZ"),
            "DTEND:" + end_utc.strftime("%Y%m%dT%H%M%SZ"),
        ])
    else:
        start_date = fixture["date"].date()
        end_date = start_date + timedelta(days=1)

        lines.extend([
            "DTSTART;VALUE=DATE:" + start_date.strftime("%Y%m%d"),
            "DTEND;VALUE=DATE:" + end_date.strftime("%Y%m%d"),
        ])

    lines.append(
        "SUMMARY:" + escape_ics(make_title(fixture))
    )

    if fixture["location"]:
        lines.append(
            "LOCATION:" + escape_ics(fixture["location"])
        )

    lines.append("END:VEVENT")

    folded = []

    for line in lines:
        folded.extend(fold_ics_line(line))

    return folded


def write_calendar(fixtures):
    output = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//Oliver Thibaut//UBB Calendar//FR",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Union Bordeaux Bègles",
        "X-WR-TIMEZONE:Europe/Paris",
    ]

    for fixture in sorted(
        fixtures,
        key=lambda item: item["kickoff"] or item["date"],
    ):
        output.extend(event_lines(fixture))

    output.append("END:VCALENDAR")

    OUTPUT_FILE.write_text(
        "\r\n".join(output) + "\r\n",
        encoding="utf-8",
    )


def main():
    print()
    print("MISE À JOUR CALENDRIER UBB")
    print()
    print("Source : calendrier officiel UBB (ubb.link)")

    html = fetch_page()

    print(
        "Occurrences 'Top 14 -' dans le HTML : "
        f"{html.count('Top 14 -')}"
    )

    lines = page_to_lines(html)

    DEBUG_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    fixtures = parse_schedule(lines)
    fixtures = add_known_current_season_events(fixtures)

    if not fixtures:
        raise SystemExit(
            "\nERREUR : aucun match UBB détecté.\n"
        )

    write_calendar(fixtures)

    top14 = sum(
        1 for item in fixtures
        if item["competition"] == "Top 14"
    )

    champions = sum(
        1 for item in fixtures
        if item["competition"] == "Investec Champions Cup"
    )

    friendlies = sum(
        1 for item in fixtures
        if item["competition"] == "Friendly"
    )

    timed = sum(
        1 for item in fixtures
        if item["kickoff"] is not None
    )

    print()
    print(f"Top 14 : {top14}")
    print(f"Investec Champions Cup : {champions}")
    print(f"Friendlies : {friendlies}")
    print(f"Horaires connus : {timed}/{len(fixtures)}")
    print(f"Total : {len(fixtures)} événements")
    print(f"Sortie : {OUTPUT_FILE}")
    print()

    print("Premiers événements :")

    for fixture in sorted(
        fixtures,
        key=lambda item: item["kickoff"] or item["date"],
    )[:8]:
        when = (
            fixture["kickoff"].strftime("%d/%m/%Y %H:%M")
            if fixture["kickoff"]
            else fixture["date"].strftime("%d/%m/%Y")
            + " (horaire à confirmer)"
        )

        print(
            f"  {when} — {make_title(fixture)}"
        )


if __name__ == "__main__":
    main()
