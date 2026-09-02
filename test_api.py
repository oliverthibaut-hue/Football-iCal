import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta


API_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"

TEAMS = {
    541: "Real Madrid CF",
    535: "Málaga CF",
}


def get_fixtures(team_id, days=90):
    today = datetime.now().date()
    end_date = today + timedelta(days=days)

    params = {
        "team": team_id,
	"season": 2026,
        "from": today.isoformat(),
        "to": end_date.isoformat(),
        "timezone": "Europe/Paris",
    }

    url = f"{BASE_URL}/fixtures?{urllib.parse.urlencode(params)}"

    request = urllib.request.Request(
        url,
        headers={
            "x-apisports-key": API_KEY,
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))

        remaining = response.headers.get(
            "x-ratelimit-requests-remaining",
            "inconnu"
        )

        return data, remaining


def display_fixture(match):
    fixture = match["fixture"]
    league = match["league"]
    teams = match["teams"]

    date = datetime.fromisoformat(fixture["date"])

    venue = fixture.get("venue") or {}
    stadium = venue.get("name") or "Stade non renseigné"
    city = venue.get("city") or "Ville non renseignée"

    print()
    print(f"Fixture ID : {fixture['id']}")
    print(date.strftime("%d/%m/%Y %H:%M"))
    print(f'{league["name"]} | {league["round"]}')
    print(f'{teams["home"]["name"]} - {teams["away"]["name"]}')
    print(f'{city} - {stadium}')


def main():
    if not API_KEY:
        print("ERREUR : clé API absente.")
        print('Utilise : export API_FOOTBALL_KEY="ta_cle"')
        return

    for team_id, team_name in TEAMS.items():

        print()
        print("=" * 60)
        print(team_name.upper())
        print("=" * 60)

        data, remaining = get_fixtures(team_id)

        if data.get("errors"):
            print("Erreur API :", data["errors"])
            continue

        fixtures = data.get("response", [])

        print(f"{len(fixtures)} matchs récupérés")
        print(f"Requêtes restantes aujourd'hui : {remaining}")

        for match in fixtures:
            display_fixture(match)


if __name__ == "__main__":
    main()