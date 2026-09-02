import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# DOSSIER DU PROJET
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PARIS = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")


# ============================================================
# SAISON À TRAITER
# ============================================================

SEASON_START = datetime(2026, 7, 1).date()
SEASON_END = datetime(2027, 6, 30).date()


# ============================================================
# SOURCES FIXTUR.ES
# ============================================================

SOURCES = {
    "Real Madrid CF": "real-madrid-source.ics",
    "Málaga CF": "malaga-source.ics",
}


# ============================================================
# NORMALISATION DES NOMS D'ÉQUIPES
# ============================================================

TEAM_NAMES = {

    # Clubs suivis
    "Real Madrid": "Real Madrid CF",
    "Real Madrid CF": "Real Madrid CF",

    "Malaga": "Málaga CF",
    "Malaga CF": "Málaga CF",
    "Málaga": "Málaga CF",
    "Málaga CF": "Málaga CF",

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
    "AEK Athene": "AEK Athènes",
    "AEK Athènes": "AEK Athènes",

    "PSV": "PSV Eindhoven",
    "PSV Eindhoven": "PSV Eindhoven",

    "Arsenal": "Arsenal FC",
    "Arsenal FC": "Arsenal FC",

    "LASK Linz": "LASK Linz",

    "FK Shakhtar Donetsk": "Shakhtar Donetsk",
    "Shakhtar Donetsk": "Shakhtar Donetsk",

    # Friendlies
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
# DATES COPA DEL REY 2026-2027
#
# football-data.org Free ne donne pas accès à la Copa.
# Fixtur.es fournit en revanche le marqueur [Copa].
#
# Le tour est donc estimé à partir de la date.
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
# LECTURE JSON
# ============================================================

def load_json(filename):

    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"\nFichier introuvable : {path}\n"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# STADES / LIEUX
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

    # Si le stade n'est pas dans venues.json,
    # on conserve malgré tout son nom brut.
    return raw_stadium


# ============================================================
# OUTILS ICS
# ============================================================

def unfold_ics(content):
    """
    Recolle les lignes ICS qui sont coupées
    sur plusieurs lignes.
    """

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
    """
    Accepte aussi bien :

    SUMMARY:...
    SUMMARY\\:...

    LOCATION:...
    LOCATION\\:...
    """

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

    if match:
        return clean_ics_value(
            match.group(1)
        )

    return None


def read_ics(filename):

    path = BASE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"\nFichier ICS introuvable : {path}\n"
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

    # Exemple :
    # 20270202
    if len(value) == 8:

        return datetime.strptime(
            value,
            "%Y%m%d"
        ).replace(
            tzinfo=UTC
        )

    # Exemple :
    # 20260904T190000Z
    if value.endswith("Z"):

        return datetime.strptime(
            value,
            "%Y%m%dT%H%M%SZ"
        ).replace(
            tzinfo=UTC
        )

    # Sécurité si un jour Fixtur.es
    # fournit une date sans Z.
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
# NOMS D'ÉQUIPES
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
# NETTOYAGE DU SUMMARY FIXTUR.ES
# ============================================================

def clean_fixture_summary(summary):

    # Supprime le score final :
    # Real Madrid - Malaga (3-0)
    # devient
    # Real Madrid - Malaga

    summary = re.sub(
        r"\s+\(\d+\-\d+\)$",
        "",
        summary
    )

    # Supprime les tags de compétition
    summary = summary.replace(
        "[CL]",
        ""
    )

    summary = summary.replace(
        "[Copa]",
        ""
    )

    return summary.strip()


def parse_fixture_teams(summary):

    cleaned = clean_fixture_summary(
        summary
    )

    if " - " not in cleaned:

        return (
            cleaned,
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
# FOOTBALL-DATA.ORG
# ============================================================

def load_official_matches():

    official_matches = []


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
    # UEFA CHAMPIONS LEAGUE
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
# RECHERCHE D'UN MATCH OFFICIEL
# ============================================================

def find_official_match(
    fixture_date,
    fixture_home,
    fixture_away,
    official_matches
):

    candidates = []

    for match in official_matches:

        # On compare d'abord la date.
        # Cela permet de ne pas dépendre d'un horaire
        # provisoire à 00:00 dans football-data.org.

        if (
            match["date"].date()
            != fixture_date.date()
        ):
            continue


        # Puis les équipes après normalisation.

        if (
            match["home"] == fixture_home
            and
            match["away"] == fixture_away
        ):

            candidates.append(
                match
            )


    if len(candidates) == 1:
        return candidates[0]


    # Fallback :
    # si les noms ne correspondent pas exactement
    # mais qu'un seul match avec le club suivi
    # existe à cette date.

    date_candidates = []

    for match in official_matches:

        if (
            match["date"].date()
            != fixture_date.date()
        ):
            continue

        fixture_teams = {
            fixture_home,
            fixture_away
        }

        official_teams = {
            match["home"],
            match["away"]
        }

        if fixture_teams & official_teams:

            date_candidates.append(
                match
            )


    if len(date_candidates) == 1:
        return date_candidates[0]


    return None


# ============================================================
# NOM DE LA JOURNÉE / PHASE
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


    # --------------------------------------------------------
    # LALIGA
    # --------------------------------------------------------

    if (
        competition
        == "LaLiga EA Sports"
    ):

        return f"J{matchday}"


    # --------------------------------------------------------
    # CHAMPIONS LEAGUE
    # --------------------------------------------------------

    if (
        competition
        == "UEFA Champions League"
    ):

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
# COPA DEL REY
# ============================================================

def get_copa_round(
    fixture_date
):

    match_date = (
        fixture_date.date()
    )

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

        # Tolérance de 7 jours
        # autour de chaque date prévue.

        if distance <= 7:

            if (
                best_distance is None
                or
                distance < best_distance
            ):

                best_distance = distance
                best_round = round_name


    if best_round:
        return best_round


    return "Tour à définir"


# ============================================================
# SUPPRESSION DES PLACEHOLDERS FIXTUR.ES
# ============================================================

def is_stale_placeholder(
    fixture_date,
    summary,
    location,
    official_matches
):
    """
    Détecte les faux événements provisoires
    comme :

    02/02/2027 00:00 UTC
    Real Sociedad - Real Madrid
    sans lieu

    alors que le vrai match officiel
    existe quelques jours plus tard.
    """


    # Un vrai lieu est renseigné :
    # on ne supprime pas.
    if location:
        return False


    # Le placeholder doit être à minuit UTC.
    if (
        fixture_date.hour != 0
        or
        fixture_date.minute != 0
    ):
        return False


    # On ne supprime jamais automatiquement
    # un match identifié comme Coupe ou C1.
    if (
        "[CL]" in summary
        or
        "[Copa]" in summary
    ):
        return False


    fixture_home, fixture_away = (
        parse_fixture_teams(
            summary
        )
    )


    for match in official_matches:

        if (
            match["home"]
            != fixture_home
        ):
            continue

        if (
            match["away"]
            != fixture_away
        ):
            continue


        distance = abs(
            (
                match["date"].date()
                -
                fixture_date.date()
            ).days
        )


        # Si le vrai match officiel existe
        # dans la semaine suivante/précédente,
        # le placeholder est ignoré.

        if distance <= 7:
            return True


    return False


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


    # --------------------------------------------------------
    # MATCH OFFICIEL IDENTIFIÉ
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


        return (
            f"{competition} | "
            f"{round_name} - "
            f"{home} - {away}"
        )


    # --------------------------------------------------------
    # COPA DEL REY
    # --------------------------------------------------------

    if "[Copa]" in summary:

        copa_round = (
            get_copa_round(
                fixture_date
            )
        )

        return (
            f"Copa del Rey | "
            f"{copa_round} - "
            f"{fixture_home} - "
            f"{fixture_away}"
        )


    # --------------------------------------------------------
    # CHAMPIONS LEAGUE NON TROUVÉE
    # DANS FOOTBALL-DATA
    # --------------------------------------------------------

    if "[CL]" in summary:

        return (
            "UEFA Champions League | "
            "Tour à définir - "
            f"{fixture_home} - "
            f"{fixture_away}"
        )


    # --------------------------------------------------------
    # FRIENDLY
    # --------------------------------------------------------

    return (
        f"Friendly | "
        f"{fixture_home} - "
        f"{fixture_away}"
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


            # ------------------------------------------------
            # CHAMPS ICS
            # ------------------------------------------------

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


            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            fixture_date = (
                parse_ics_date(
                    dtstart
                )
            )


            # ------------------------------------------------
            # SAISON 2026-2027 UNIQUEMENT
            # ------------------------------------------------

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


            # ------------------------------------------------
            # PLACEHOLDERS
            # ------------------------------------------------

            if is_stale_placeholder(
                fixture_date,
                summary,
                location,
                official_matches
            ):
                continue


            # ------------------------------------------------
            # ÉQUIPES FIXTUR.ES
            # ------------------------------------------------

            fixture_home, fixture_away = (
                parse_fixture_teams(
                    summary
                )
            )


            # ------------------------------------------------
            # RECHERCHE MATCH OFFICIEL
            # ------------------------------------------------

            official_match = (
                find_official_match(
                    fixture_date,
                    fixture_home,
                    fixture_away,
                    official_matches
                )
            )


            # ------------------------------------------------
            # TITRE
            # ------------------------------------------------

            title = build_title(
                summary,
                fixture_date,
                official_match
            )


            # ------------------------------------------------
            # LIEU
            # ------------------------------------------------

            formatted_location = (
                format_location(
                    location
                )
            )


            # ------------------------------------------------
            # HEURE PARIS POUR LE TEST
            # ------------------------------------------------

            paris_date = (
                fixture_date
                .astimezone(
                    PARIS
                )
            )


            # ------------------------------------------------
            # AFFICHAGE
            # ------------------------------------------------

            print()

            print(
                paris_date.strftime(
                    "%d/%m/%Y %H:%M"
                )
            )

            print(
                title
            )

            print(
                "Lieu : "
                f"{formatted_location or 'Non renseigné'}"
            )


    # ========================================================
    # STADES NON CONNUS
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