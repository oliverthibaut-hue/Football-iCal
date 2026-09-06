#!/usr/bin/env python3
from pathlib import Path
import json
import shutil

BASE = Path(__file__).resolve().parent

REQUIRED = [
    "update_all.py",
    "merge_test.py",
    "generate_calendars.py",
    "venues.json",
    ".github/workflows/update-calendars.yml",
]

for name in REQUIRED:
    if not (BASE / name).exists():
        raise SystemExit(f"Fichier requis introuvable : {name}")


def backup(path):
    bak = path.with_suffix(path.suffix + ".bak-arsenal")
    if not bak.exists():
        shutil.copy2(path, bak)


def replace_once(text, old, new, label):
    if new in text:
        print(f"✓ {label} déjà présent")
        return text

    if old not in text:
        raise SystemExit(
            f"\nImpossible de modifier : {label}\n"
            "Le bloc attendu n'a pas été trouvé."
        )

    print(f"✓ {label}")
    return text.replace(old, new, 1)


# ============================================================
# update_all.py
# ============================================================

path = BASE / "update_all.py"
backup(path)
text = path.read_text(encoding="utf-8")

anchor = '''    # --------------------------------------------------------
    # 3. FOOTBALL-DATA - LALIGA
    # --------------------------------------------------------
'''

arsenal_source_block = '''    # --------------------------------------------------------
    # 3. FIXTUR.ES - ARSENAL
    # --------------------------------------------------------

    try:
        download_ics(
            (
                "https://ics.fixtur.es/v2/"
                "arsenal.ics"
            ),
            "arsenal-source.ics"
        )
    except Exception:
        print(
            "Source directe Arsenal indisponible, "
            "essai du flux Google public Fixtur.es..."
        )

        download_ics(
            (
                "https://calendar.google.com/calendar/ical/"
                "eka2uomkdqfhu5bk6hbdc7a4d4%40group.calendar.google.com/"
                "public/basic.ics"
            ),
            "arsenal-source.ics"
        )


    # --------------------------------------------------------
    # 4. FOOTBALL-DATA - PREMIER LEAGUE
    # --------------------------------------------------------

    download_football_data(
        (
            "https://api.football-data.org/v4/"
            "competitions/PL/matches"
            "?season=2026"
        ),
        "premier-league-2026.json"
    )


    # --------------------------------------------------------
    # 5. FOOTBALL-DATA - LALIGA
    # --------------------------------------------------------
'''

text = replace_once(
    text,
    anchor,
    arsenal_source_block,
    "source Arsenal + Premier League",
)

text = text.replace(
    "# 4. FOOTBALL-DATA - CHAMPIONS LEAGUE",
    "# 6. FOOTBALL-DATA - CHAMPIONS LEAGUE",
)
text = text.replace(
    "# 5. GÉNÉRATION DES CALENDRIERS FINAUX",
    "# 7. GÉNÉRATION DES CALENDRIERS FINAUX",
)

path.write_text(text, encoding="utf-8")


# ============================================================
# merge_test.py
# ============================================================

path = BASE / "merge_test.py"
backup(path)
text = path.read_text(encoding="utf-8")

old = '''SOURCES = {
    "Real Madrid CF": "real-madrid-source.ics",
    "Málaga CF": "malaga-source.ics",
}
'''

new = '''SOURCES = {
    "Real Madrid CF": "real-madrid-source.ics",
    "Málaga CF": "malaga-source.ics",
    "Arsenal FC": "arsenal-source.ics",
}
'''

text = replace_once(
    text,
    old,
    new,
    "Arsenal dans SOURCES",
)

marker = '''    # Espagne
'''

aliases = '''    # Arsenal / Premier League
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
'''

text = replace_once(
    text,
    marker,
    aliases,
    "aliases Arsenal/Premier League",
)

old = '''    summary = summary.replace(
        "[Copa]",
        ""
    )

    return summary.strip()
'''

new = '''    summary = summary.replace(
        "[Copa]",
        ""
    )

    # Autres marqueurs Fixtur.es :
    # [League Cup], [FA Cup], [Community Shield], etc.
    summary = re.sub(
        r"\\[[^\\]]+\\]",
        "",
        summary
    )

    return summary.strip()
'''

text = replace_once(
    text,
    old,
    new,
    "nettoyage des marqueurs Fixtur.es",
)

anchor = '''    # --------------------------------------------------------
    # LALIGA
    # --------------------------------------------------------
'''

pl_block = '''    # --------------------------------------------------------
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
'''

text = replace_once(
    text,
    anchor,
    pl_block,
    "Premier League dans les matchs officiels",
)

old = '''    if competition == "LaLiga EA Sports":

        return f"J{matchday}"
'''

new = '''    if competition in {
        "LaLiga EA Sports",
        "Premier League",
    }:

        return f"J{matchday}"
'''

text = replace_once(
    text,
    old,
    new,
    "journées Premier League",
)

anchor = '''# ============================================================
# PLACEHOLDER FIXTUR.ES
# ============================================================
'''

helpers = '''# ============================================================
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
'''

text = replace_once(
    text,
    anchor,
    helpers,
    "tours Carabao Cup / FA Cup",
)

anchor = '''    # --------------------------------------------------------
    # FRIENDLY
    # --------------------------------------------------------
'''

cup_titles = '''    # --------------------------------------------------------
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
        "league cup" in summary_lower
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
    # FRIENDLY
    # --------------------------------------------------------
'''

text = replace_once(
    text,
    anchor,
    cup_titles,
    "titres des coupes anglaises",
)

path.write_text(text, encoding="utf-8")


# ============================================================
# generate_calendars.py
# ============================================================

path = BASE / "generate_calendars.py"
backup(path)
text = path.read_text(encoding="utf-8")

old = '''OUTPUTS = {
    "Real Madrid CF": "Real-Madrid.ics",
    "Málaga CF": "Malaga-CF.ics",
}
'''

new = '''OUTPUTS = {
    "Real Madrid CF": "Real-Madrid.ics",
    "Málaga CF": "Malaga-CF.ics",
    "Arsenal FC": "Arsenal-FC.ics",
}
'''

text = replace_once(
    text,
    old,
    new,
    "Arsenal dans OUTPUTS",
)

path.write_text(text, encoding="utf-8")


# ============================================================
# venues.json
# ============================================================

path = BASE / "venues.json"
backup(path)

with path.open(
    "r",
    encoding="utf-8"
) as f:
    venues = json.load(f)

new_venues = {
    "Emirates": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Emirates Stadium",
    },
    "Emirates Stadium": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Emirates Stadium",
    },
    "Stamford Bridge": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Stamford Bridge",
    },
    "Villa Park": {
        "city": "Birmingham",
        "country": "Angleterre",
        "stadium": "Villa Park",
    },
    "Stadium of Light": {
        "city": "Sunderland",
        "country": "Angleterre",
        "stadium": "Stadium of Light",
    },
    "Amex Stadium": {
        "city": "Brighton",
        "country": "Angleterre",
        "stadium": "Amex Stadium",
    },
    "The American Express Community Stadium": {
        "city": "Brighton",
        "country": "Angleterre",
        "stadium": "Amex Stadium",
    },
    "City Ground": {
        "city": "Nottingham",
        "country": "Angleterre",
        "stadium": "City Ground",
    },
    "Anfield": {
        "city": "Liverpool",
        "country": "Angleterre",
        "stadium": "Anfield",
    },
    "MKM Stadium": {
        "city": "Hull",
        "country": "Angleterre",
        "stadium": "MKM Stadium",
    },
    "St James' Park": {
        "city": "Newcastle",
        "country": "Angleterre",
        "stadium": "St James' Park",
    },
    "Etihad Stadium": {
        "city": "Manchester",
        "country": "Angleterre",
        "stadium": "Etihad Stadium",
    },
    "Gtech Community Stadium": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Gtech Community Stadium",
    },
    "Tottenham Hotspur Stadium": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Tottenham Hotspur Stadium",
    },
    "Vitality Stadium": {
        "city": "Bournemouth",
        "country": "Angleterre",
        "stadium": "Vitality Stadium",
    },
    "Old Trafford": {
        "city": "Manchester",
        "country": "Angleterre",
        "stadium": "Old Trafford",
    },
    "Selhurst Park": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Selhurst Park",
    },
    "Craven Cottage": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Craven Cottage",
    },
    "Portman Road": {
        "city": "Ipswich",
        "country": "Angleterre",
        "stadium": "Portman Road",
    },
    "Elland Road": {
        "city": "Leeds",
        "country": "Angleterre",
        "stadium": "Elland Road",
    },
    "Hill Dickinson Stadium": {
        "city": "Liverpool",
        "country": "Angleterre",
        "stadium": "Hill Dickinson Stadium",
    },
    "Coventry Building Society Arena": {
        "city": "Coventry",
        "country": "Angleterre",
        "stadium": "Coventry Building Society Arena",
    },
    "Wembley": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Wembley Stadium",
    },
    "Wembley Stadium": {
        "city": "London",
        "country": "Angleterre",
        "stadium": "Wembley Stadium",
    },
    "Stadio Diego Armando Maradona": {
        "city": "Napoli",
        "country": "Italie",
        "stadium": "Stadio Diego Armando Maradona",
    },
    "Diego Armando Maradona Stadium": {
        "city": "Napoli",
        "country": "Italie",
        "stadium": "Stadio Diego Armando Maradona",
    },
    "Allianz Arena": {
        "city": "München",
        "country": "Allemagne",
        "stadium": "Allianz Arena",
    },
    "Fortuna Arena": {
        "city": "Praha",
        "country": "République tchèque",
        "stadium": "Fortuna Arena",
    },
    "Estadio Benito Villamarín": {
        "city": "Sevilla",
        "country": "Espagne",
        "stadium": "Estadio Benito Villamarín",
    },
    "Benito Villamarín Stadium": {
        "city": "Sevilla",
        "country": "Espagne",
        "stadium": "Estadio Benito Villamarín",
    },
    "Estadi Montilivi": {
        "city": "Girona",
        "country": "Espagne",
        "stadium": "Estadi Montilivi",
    },
}

changes = 0

for stadium, data in new_venues.items():
    if venues.get(stadium) != data:
        venues[stadium] = data
        changes += 1

path.write_text(
    json.dumps(
        venues,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print(
    "✓ venues.json : "
    f"{changes} entrée(s) ajoutée(s)/mise(s) à jour"
)


# ============================================================
# normalize_uk_locations.py
# ============================================================

path = BASE / "normalize_uk_locations.py"

if path.exists():
    backup(path)
    text = path.read_text(encoding="utf-8")

    if '"Arsenal-FC.ics"' not in text:
        old = '''    "Union-Bordeaux-Begles.ics",
'''
        new = '''    "Union-Bordeaux-Begles.ics",
    "Arsenal-FC.ics",
'''
        text = replace_once(
            text,
            old,
            new,
            "Arsenal dans normalize_uk_locations.py",
        )

    path.write_text(
        text,
        encoding="utf-8"
    )
else:
    print(
        "ℹ normalize_uk_locations.py absent : ignoré"
    )


# ============================================================
# GitHub Actions
# ============================================================

path = BASE / ".github/workflows/update-calendars.yml"
backup(path)
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    "git add Real-Madrid.ics Malaga-CF.ics Union-Bordeaux-Begles.ics",
    "git add Real-Madrid.ics Malaga-CF.ics Union-Bordeaux-Begles.ics Arsenal-FC.ics",
    "Arsenal dans git add du workflow",
)

text = replace_once(
    text,
    "          cp Union-Bordeaux-Begles.ics public/Union-Bordeaux-Begles.ics\n",
    "          cp Union-Bordeaux-Begles.ics public/Union-Bordeaux-Begles.ics\n"
    "          cp Arsenal-FC.ics public/Arsenal-FC.ics\n",
    "Arsenal dans GitHub Pages",
)

text = replace_once(
    text,
    "            '  <p><a href=\"Union-Bordeaux-Begles.ics\">Union Bordeaux Bègles</a></p>' \\\n",
    "            '  <p><a href=\"Union-Bordeaux-Begles.ics\">Union Bordeaux Bègles</a></p>' \\\n"
    "            '  <p><a href=\"Arsenal-FC.ics\">Arsenal FC</a></p>' \\\n",
    "lien Arsenal sur la page GitHub Pages",
)

path.write_text(
    text,
    encoding="utf-8"
)

print()
print("=" * 60)
print("INTÉGRATION ARSENAL TERMINÉE")
print("=" * 60)
print()
print("Étape suivante :")
print("python3 -u update_all.py")
print()
