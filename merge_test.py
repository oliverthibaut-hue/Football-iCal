import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UTC = ZoneInfo("UTC")
PARIS = ZoneInfo("Europe/Paris")

SEASON_START = datetime(2026, 7, 1).date()
SEASON_END = datetime(2027, 6, 30).date()


SOURCES = {
    "Real Madrid CF": "real-madrid-source.ics",
    "Málaga CF": "malaga-source.ics",
    "Arsenal FC": "arsenal-source.ics",
}


# ============================================================
# NORMALISATION DES ÉQUIPES
# ============================================================

TEAM_NAMES = {

    # Clubs suivis
    "Real Madrid": "Real Madrid CF",
    "Real Madrid CF": "Real Madrid CF",

    "Malaga": "Málaga CF",
    "Malaga CF": "Málaga CF",
    "Málaga": "Málaga CF",
    "Málaga CF": "Málaga CF",

    # Arsenal / Premier League
    "Arsenal": "Arsenal FC",
    "Arsenal FC": "Arsenal FC",

    "Chelsea": "Chelsea FC",
    "Chelsea FC": "Chelsea FC",

    "Manchester City": "Manchester City",
    "Manchester City FC": "Manchester City",

    "Manchester United": "Manchester United",
    "Manchester United FC": "Manchester United",

    "Liverpool": "Liverpool FC",
    "Liverpool FC": "Liverpool FC",

    "Tottenham Hotspur": "Tottenham Hotspur",
    "Tottenham Hotspur FC": "Tottenham Hotspur",

    "Aston Villa": "Aston Villa",
    "Aston Villa FC": "Aston Villa",

    "Newcastle United": "Newcastle United",
    "Newcastle United FC": "Newcastle United",

    "Brighton & Hove Albion": "Brighton & Hove Albion",
    "Brighton & Hove Albion FC": "Brighton & Hove Albion",

    "Nottingham Forest": "Nottingham Forest",
    "Nottingham Forest FC": "Nottingham Forest",

    "Everton": "Everton",
    "Everton FC": "Everton",

    "Fulham": "Fulham FC",
    "Fulham FC": "Fulham FC",

    "Crystal Palace": "Crystal Palace",
    "Crystal Palace FC": "Crystal Palace",

    "Brentford": "Brentford FC",
    "Brentford FC": "Brentford FC",

    "AFC Bournemouth": "AFC Bournemouth",

    "Leeds United": "Leeds United",
    "Leeds United FC": "Leeds United",

    "Sunderland": "Sunderland AFC",
    "Sunderland AFC": "Sunderland AFC",

    "Coventry City": "Coventry City",
    "Coventry City FC": "Coventry City",

    "Hull City": "Hull City",
    "Hull City AFC": "Hull City",

    "Ipswich Town": "Ipswich Town",
    "Ipswich Town FC": "Ipswich Town",

    # Adversaires européens Arsenal
    "SSC Napoli": "SSC Napoli",
    "Napoli": "SSC Napoli",

    "LOSC Lille": "LOSC Lille",
    "Lille": "LOSC Lille",

    "FC Bayern München": "Bayern Munich",
    "Bayern München": "Bayern Munich",
    "Bayern Munich": "Bayern Munich",

    "SK Slavia Praha": "Slavia Prague",
    "Slavia Praha": "Slavia Prague",
    "Slavia Prague": "Slavia Prague",

    "Borussia Dortmund": "Borussia Dortmund",
    "B. Dortmund": "Borussia Dortmund",

    "Sabah FK": "Sabah FK",
    "Sabah": "Sabah FK",

    "Girona FC": "Girona FC",
    "Como": "Como 1907",
    "Como 1907": "Como 1907",

    # Espagne
    "Real Betis": "Real Betis Balompié",
    "Real Betis Balompié": "Real Betis Balompié",

    "Club Atlético de Madrid": "Atlético Madrid",
    "Atlético Madrid": "Atlético Madrid",

    "RC Deportivo La Coruña": "Deportivo La Coruña",
    "Deportivo la Coruna": "Deportivo La Coruña",
    "Deportivo La Coruña": "Deportivo La Coruña",

    "RC Celta de Vigo": "Celta de Vigo",
    "Celta de Vigo": "Celta de Vigo",

    "Villarreal": "Villarreal CF",
    "Villarreal CF": "Villarreal CF",

    "Levante": "Levante UD",
    "Levante UD": "Levante UD",

    "RCD Espanyol de Barcelona": "Espanyol",
    "Espanyol": "Espanyol",

    "Real Sociedad de Fútbol": "Real Sociedad",
    "Real Sociedad": "Real Sociedad",

    "Getafe": "Getafe CF",
    "Getafe CF": "Getafe CF",

    "Athletic de Bilbao": "Athletic Club",
    "Athletic Club": "Athletic Club",

    "Valencia": "Valencia CF",
    "Valencia CF": "Valencia CF",

    "Rayo Vallecano de Madrid": "Rayo Vallecano",
    "Rayo Vallecano": "Rayo Vallecano",

    "FC Barcelona": "FC Barcelona",

    "Sevilla FC": "Sevilla FC",

    "CA Osasuna": "CA Osasuna",

    "Deportivo Alavés": "Deportivo Alavés",

    "Elche CF": "Elche CF",

    "Real Racing Club de Santander": "Racing de Santander",
    "Racing de Santander": "Racing de Santander",

    # Champions League
    "FC Internazionale Milano": "Inter Milan",
    "Inter": "Inter Milan",
    "Inter Milan": "Inter Milan",

    "AS Roma": "AS Roma",

    "RB Leipzig": "RB Leipzig",

    "PAE AEK": "AEK Athènes",
    "AEK Athènes": "AEK Athènes",

    "PSV": "PSV Eindhoven",
    "PSV Eindhoven": "PSV Eindhoven",

    "Arsenal": "Arsenal FC",
    "Arsenal FC": "Arsenal FC",

    "LASK Linz": "LASK Linz",

    "FK Shakhtar Donetsk": "Shakhtar Donetsk",
    "Shakhtar Donetsk": "Shakhtar Donetsk",

    # Amicaux
    "Fiorentina": "Fiorentina",
    "Ferencvarosi": "Ferencvarosi",

    "FC Schalke 04": "FC Schalke 04",

    "Leicester City": "Leicester City",

    "Al Ittihad": "Al Ittihad",

    "Al Arabi": "Al Arabi",

    "AD Ceuta FC": "AD Ceuta FC",

    "Fulham": "Fulham FC",
    "Fulham FC": "Fulham FC",
}


# ============================================================
# PHASES À ÉLIMINATION DIRECTE
# ============================================================

KNOCKOUT_STAGES = {

    "ROUND_OF_32": "16ème de Final",
    "LAST_32": "16ème de Final",

    "ROUND_OF_16": "8ème de Final",
    "LAST_16": "8ème de Final",

    "QUARTER_FINALS": "4rt de Final",
    "QUARTER_FINAL": "4rt de Final",

    "SEMI_FINALS": "2mi Final",
    "SEMI_FINAL": "2mi Final",

    "FINAL": "Finale",

    "PLAYOFFS": "Barrage",
    "KNOCKOUT_ROUND_PLAY_OFFS": "Barrage",
}


# ============================================================
# COPA DEL REY
# ============================================================

COPA_ROUNDS_2026 = [

    (
        datetime(2026, 10, 28).date(),
        "1er Tour"
    ),

    (
        datetime(2026, 12, 2).date(),
        "2ème Tour"
    ),

    (
        datetime(2026, 12, 16).date(),
        "16ème de Final"
    ),

    (
        datetime(2027, 1, 6).date(),
        "8ème de Final"
    ),

    (
        datetime(2027, 1, 13).date(),
        "4rt de Final"
    ),

    (
        datetime(2027, 2, 10).date(),
        "2mi Final"
    ),

    (
        datetime(2027, 3, 3).date(),
        "2mi Final"
    ),

    (
        datetime(2027, 4, 24).date(),
        "Finale"
    ),
]


# ============================================================
# JSON
# ============================================================

def load_json(filename):

    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# LIEUX
# ============================================================

VENUES = load_json("venues.json")

UNKNOWN_VENUES = set()


def format_location(raw_stadium):

    if not raw_stadium:
        return None

    raw_stadium = raw_stadium.strip()

    venue = VENUES.get(raw_stadium)

    if venue:

        return (
            f'{venue["city"]} '
            f'({venue["country"]}) - '
            f'{venue["stadium"]}'
        )

    UNKNOWN_VENUES.add(raw_stadium)

    return raw_stadium


# ============================================================
# LECTURE ICS
# ============================================================

def unfold_ics(content):

    lines = (
        content
        .replace("\r\n", "\n")
        .split("\n")
    )

    unfolded = []

    for line in lines:

        if (
            line.startswith(" ")
            or line.startswith("\t")
        ):

            if unfolded:
                unfolded[-1] += line[1:]

        else:
            unfolded.append(line)

    return "\n".join(unfolded)


def clean_ics_value(value):

    return (
        value
        .replace("\\:", ":")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\n", "\n")
        .strip()
    )


def get_field(event, field):

    pattern = (
        rf"^{re.escape(field)}"
        rf"(?:;[^:]*)?"
        rf"\\?:"
        rf"(.*)$"
    )

    match = re.search(
        pattern,
        event,
        flags=re.MULTILINE
    )

    if not match:
        return None

    return clean_ics_value(
        match.group(1)
    )


def read_ics(filename):

    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Fichier ICS introuvable : {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        content = unfold_ics(
            file.read()
        )

    return content.split(
        "BEGIN:VEVENT"
    )[1:]


# ============================================================
# DATES
# ============================================================

def parse_ics_date(value):

    if len(value) == 8:

        return datetime.strptime(
            value,
            "%Y%m%d"
        ).replace(
            tzinfo=UTC
        )

    if value.endswith("Z"):

        return datetime.strptime(
            value,
            "%Y%m%dT%H%M%SZ"
        ).replace(
            tzinfo=UTC
        )

    return datetime.strptime(
        value,
        "%Y%m%dT%H%M%S"
    ).replace(
        tzinfo=UTC
    )


def parse_json_date(value):

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00"
        )
    )


# ============================================================
# ÉQUIPES
# ============================================================

def normalize_team(name):

    if not name:
        return ""

    name = name.strip()

    return TEAM_NAMES.get(
        name,
        name
    )


# ============================================================
# SCORE
# ============================================================

def extract_fixture_score(summary):
    """
    Exemple :

    Real Madrid - Barcelona (3-1)

    retourne :

    (3, 1)
    """

    if not summary:
        return None

    match = re.search(
        r"\((\d+)\s*-\s*(\d+)\)\s*$",
        summary
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        int(match.group(2))
    )


# ============================================================
# NETTOYAGE DU SUMMARY
# ============================================================

def clean_fixture_summary(summary):

    if not summary:
        return ""

    # Supprime le score final
    summary = re.sub(
        r"\s+\(\d+\s*-\s*\d+\)\s*$",
        "",
        summary
    )

    # Supprime les marqueurs Fixtur.es
    summary = summary.replace(
        "[CL]",
        ""
    )

    summary = summary.replace(
        "[Copa]",
        ""
    )

    # Autres marqueurs Fixtur.es :
    # [League Cup], [FA Cup], [Community Shield], etc.
    summary = re.sub(
        r"\[[^\]]+\]",
        "",
        summary
    )

    return summary.strip()


def parse_fixture_teams(summary):

    cleaned = clean_fixture_summary(
        summary
    )

    if " - " not in cleaned:

        return (
            normalize_team(cleaned),
            ""
        )

    home, away = cleaned.split(
        " - ",
        1
    )

    return (
        normalize_team(home),
        normalize_team(away)
    )


# ============================================================
# FOOTBALL-DATA
# ============================================================

def load_official_matches():

    official_matches = []


    # --------------------------------------------------------
    # PREMIER LEAGUE
    # --------------------------------------------------------

    premier = load_json(
        "premier-league-2026.json"
    )

    for match in premier.get(
        "matches",
        []
    ):

        official_matches.append({

            "competition":
                "Premier League",

            "matchday":
                match.get("matchday"),

            "stage":
                match.get("stage"),

            "date":
                parse_json_date(
                    match["utcDate"]
                ),

            "home":
                normalize_team(
                    match["homeTeam"]["name"]
                ),

            "away":
                normalize_team(
                    match["awayTeam"]["name"]
                ),
        })


    # --------------------------------------------------------
    # LALIGA
    # --------------------------------------------------------

    liga = load_json(
        "laliga-2026.json"
    )

    for match in liga.get(
        "matches",
        []
    ):

        official_matches.append({

            "competition":
                "LaLiga EA Sports",

            "matchday":
                match.get("matchday"),

            "stage":
                match.get("stage"),

            "date":
                parse_json_date(
                    match["utcDate"]
                ),

            "home":
                normalize_team(
                    match["homeTeam"]["name"]
                ),

            "away":
                normalize_team(
                    match["awayTeam"]["name"]
                ),
        })


    # --------------------------------------------------------
    # CHAMPIONS LEAGUE
    # --------------------------------------------------------

    champions = load_json(
        "champions-2026.json"
    )

    for match in champions.get(
        "matches",
        []
    ):

        official_matches.append({

            "competition":
                "UEFA Champions League",

            "matchday":
                match.get("matchday"),

            "stage":
                match.get("stage"),

            "date":
                parse_json_date(
                    match["utcDate"]
                ),

            "home":
                normalize_team(
                    match["homeTeam"]["name"]
                ),

            "away":
                normalize_team(
                    match["awayTeam"]["name"]
                ),
        })


    return official_matches


# ============================================================
# RECHERCHE MATCH OFFICIEL
# ============================================================

def find_official_match(
    fixture_date,
    fixture_home,
    fixture_away,
    official_matches
):

    # Recherche exacte
    for match in official_matches:

        if (
            match["date"].date()
            != fixture_date.date()
        ):
            continue

        if (
            match["home"] == fixture_home
            and
            match["away"] == fixture_away
        ):

            return match


    # Fallback sur la date + équipes communes
    candidates = []

    fixture_teams = {
        fixture_home,
        fixture_away
    }

    for match in official_matches:

        if (
            match["date"].date()
            != fixture_date.date()
        ):
            continue

        official_teams = {
            match["home"],
            match["away"]
        }

        if fixture_teams == official_teams:

            candidates.append(
                match
            )


    if len(candidates) == 1:
        return candidates[0]

    return None


# ============================================================
# JOURNÉE / PHASE
# ============================================================

def get_round_name(match):

    competition = match[
        "competition"
    ]

    stage = match.get(
        "stage"
    )

    matchday = match.get(
        "matchday"
    )


    if competition in {
        "LaLiga EA Sports",
        "Premier League",
    }:

        return f"J{matchday}"


    if competition == "UEFA Champions League":

        if stage == "LEAGUE_STAGE":

            return f"J{matchday}"

        if stage in KNOCKOUT_STAGES:

            return KNOCKOUT_STAGES[
                stage
            ]

        if matchday:

            return f"J{matchday}"


    if matchday:

        return f"J{matchday}"


    return "Tour à définir"


# ============================================================
# TOUR COPA
# ============================================================

def get_copa_round(fixture_date):

    match_date = fixture_date.date()

    best_round = None
    best_distance = None

    for (
        official_date,
        round_name
    ) in COPA_ROUNDS_2026:

        distance = abs(
            (
                match_date
                - official_date
            ).days
        )

        if distance <= 7:

            if (
                best_distance is None
                or
                distance < best_distance
            ):

                best_distance = distance
                best_round = round_name


    return (
        best_round
        or
        "Tour à définir"
    )


# ============================================================
# COUPES ANGLAISES 2026-27
# ============================================================

CARABAO_ROUNDS_2026 = [
    (datetime(2026, 9, 9).date(), "3ème Tour"),
    (datetime(2026, 9, 16).date(), "3ème Tour"),
    (datetime(2026, 10, 28).date(), "4ème Tour"),
    (datetime(2026, 12, 16).date(), "4rt de Final"),
    (datetime(2027, 1, 13).date(), "2mi Final - Aller"),
    (datetime(2027, 2, 3).date(), "2mi Final - Retour"),
    (datetime(2027, 3, 21).date(), "Finale"),
]

FA_CUP_ROUNDS_2026 = [
    (datetime(2027, 1, 9).date(), "3ème Tour"),
    (datetime(2027, 2, 13).date(), "4ème Tour"),
    (datetime(2027, 3, 6).date(), "8ème de Final"),
    (datetime(2027, 4, 3).date(), "4rt de Final"),
    (datetime(2027, 4, 24).date(), "2mi Final"),
    (datetime(2027, 5, 22).date(), "Finale"),
]


def nearest_round(
    fixture_date,
    rounds,
    max_days=7
):

    target = fixture_date.date()
    best = None
    best_distance = None

    for official_date, label in rounds:

        distance = abs(
            (target - official_date).days
        )

        if (
            distance <= max_days
            and (
                best_distance is None
                or distance < best_distance
            )
        ):
            best = label
            best_distance = distance

    return best or "Tour à définir"


# ============================================================
# PLACEHOLDER FIXTUR.ES
# ============================================================

def is_stale_placeholder(
    fixture_date,
    summary,
    location,
    official_matches
):

    # Un stade est renseigné :
    # ce n'est pas notre placeholder suspect.
    if location:
        return False


    # Le faux événement observé était à minuit UTC.
    if (
        fixture_date.hour != 0
        or
        fixture_date.minute != 0
    ):
        return False


    # Ne pas éliminer automatiquement
    # un match de coupe identifié.
    if (
        "[CL]" in summary
        or
        "[Copa]" in summary
    ):
        return False


    home, away = parse_fixture_teams(
        summary
    )


    # Recherche d'un vrai match officiel
    # avec les mêmes équipes dans les 7 jours.
    for match in official_matches:

        if (
            match["home"] != home
            or
            match["away"] != away
        ):
            continue

        distance = abs(
            (
                match["date"].date()
                - fixture_date.date()
            ).days
        )

        if distance <= 7:
            return True


    return False


# ============================================================
# FORMAT DU MATCH
# ============================================================

def format_match_teams(
    home,
    away,
    score
):
    """
    Sans score :

    Real Madrid CF - FC Barcelona

    Avec score :

    Real Madrid CF 3 - 1 FC Barcelona
    """

    if score:

        home_score, away_score = score

        return (
            f"{home} "
            f"{home_score} - "
            f"{away_score} "
            f"{away}"
        )

    return (
        f"{home} - {away}"
    )


# ============================================================
# CONSTRUCTION DU TITRE
# ============================================================

def build_title(
    summary,
    fixture_date,
    official_match
):

    fixture_home, fixture_away = (
        parse_fixture_teams(
            summary
        )
    )

    score = extract_fixture_score(
        summary
    )


    # --------------------------------------------------------
    # MATCH OFFICIEL
    # --------------------------------------------------------

    if official_match:

        competition = (
            official_match[
                "competition"
            ]
        )

        round_name = (
            get_round_name(
                official_match
            )
        )

        home = official_match[
            "home"
        ]

        away = official_match[
            "away"
        ]

        fixture_text = (
            format_match_teams(
                home,
                away,
                score
            )
        )

        return (
            f"{competition} | "
            f"{round_name} - "
            f"{fixture_text}"
        )


    # --------------------------------------------------------
    # COPA DEL REY
    # --------------------------------------------------------

    if "[Copa]" in summary:

        round_name = (
            get_copa_round(
                fixture_date
            )
        )

        fixture_text = (
            format_match_teams(
                fixture_home,
                fixture_away,
                score
            )
        )

        return (
            f"Copa del Rey | "
            f"{round_name} - "
            f"{fixture_text}"
        )


    # --------------------------------------------------------
    # CHAMPIONS LEAGUE NON MATCHÉE
    # --------------------------------------------------------

    if "[CL]" in summary:

        fixture_text = (
            format_match_teams(
                fixture_home,
                fixture_away,
                score
            )
        )

        return (
            "UEFA Champions League | "
            "Tour à définir - "
            f"{fixture_text}"
        )


    # --------------------------------------------------------
    # COUPES ANGLAISES
    # --------------------------------------------------------

    summary_lower = summary.lower()

    if (
        "community shield" in summary_lower
        or "fa community shield" in summary_lower
    ):

        fixture_text = format_match_teams(
            fixture_home,
            fixture_away,
            score
        )

        return (
            "FA Community Shield | Finale - "
            f"{fixture_text}"
        )


    if (
        "[lc]" in summary_lower
        or "league cup" in summary_lower
        or "carabao" in summary_lower
        or "efl cup" in summary_lower
    ):

        round_name = nearest_round(
            fixture_date,
            CARABAO_ROUNDS_2026
        )

        fixture_text = format_match_teams(
            fixture_home,
            fixture_away,
            score
        )

        return (
            f"Carabao Cup | {round_name} - "
            f"{fixture_text}"
        )


    if "fa cup" in summary_lower:

        round_name = nearest_round(
            fixture_date,
            FA_CUP_ROUNDS_2026
        )

        fixture_text = format_match_teams(
            fixture_home,
            fixture_away,
            score
        )

        return (
            f"FA Cup | {round_name} - "
            f"{fixture_text}"
        )


    if "emirates cup" in summary_lower:

        fixture_text = format_match_teams(
            fixture_home,
            fixture_away,
            score
        )

        return (
            "Emirates Cup | Finale - "
            f"{fixture_text}"
        )

    # --------------------------------------------------------
    # FA COMMUNITY SHIELD 2026
    # --------------------------------------------------------

    if (
        fixture_date.date()
        == datetime(2026, 8, 16).date()
        and
        {
            fixture_home,
            fixture_away
        }
        == {
            "Arsenal FC",
            "Manchester City"
        }
    ):

        fixture_text = format_match_teams(
            fixture_home,
            fixture_away,
            score
        )

        return (
            "FA Community Shield | Finale - "
            f"{fixture_text}"
        )

    # --------------------------------------------------------
    # FRIENDLY
    # --------------------------------------------------------

    fixture_text = (
        format_match_teams(
            fixture_home,
            fixture_away,
            score
        )
    )

    return (
        f"Friendly | "
        f"{fixture_text}"
    )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    official_matches = (
        load_official_matches()
    )


    for (
        club,
        filename
    ) in SOURCES.items():


        print()
        print("=" * 80)
        print(club.upper())
        print("=" * 80)


        events = read_ics(
            filename
        )


        for event in events:


            dtstart = get_field(
                event,
                "DTSTART"
            )

            summary = get_field(
                event,
                "SUMMARY"
            )

            location = get_field(
                event,
                "LOCATION"
            )


            if (
                not dtstart
                or
                not summary
            ):
                continue


            fixture_date = (
                parse_ics_date(
                    dtstart
                )
            )


            # Saison uniquement
            if (
                fixture_date.date()
                < SEASON_START
            ):
                continue

            if (
                fixture_date.date()
                > SEASON_END
            ):
                continue


            # Placeholders obsolètes
            if is_stale_placeholder(
                fixture_date,
                summary,
                location,
                official_matches
            ):
                continue


            fixture_home, fixture_away = (
                parse_fixture_teams(
                    summary
                )
            )


            official_match = (
                find_official_match(
                    fixture_date,
                    fixture_home,
                    fixture_away,
                    official_matches
                )
            )


            title = build_title(
                summary,
                fixture_date,
                official_match
            )


            formatted_location = (
                format_location(
                    location
                )
            )


            paris_date = (
                fixture_date
                .astimezone(
                    PARIS
                )
            )


            print()

            print(
                paris_date.strftime(
                    "%d/%m/%Y %H:%M"
                )
            )

            print(title)

            print(
                "Lieu : "
                f"{formatted_location or 'Non renseigné'}"
            )


    # ========================================================
    # STADES MANQUANTS
    # ========================================================

    if UNKNOWN_VENUES:

        print()
        print("=" * 80)
        print(
            "STADES À AJOUTER "
            "DANS venues.json"
        )
        print("=" * 80)

        for stadium in sorted(
            UNKNOWN_VENUES
        ):
            print(stadium)


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()