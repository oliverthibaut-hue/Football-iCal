import json
import os
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")


# ============================================================
# TÉLÉCHARGEMENT GÉNÉRIQUE
# ============================================================

def download(url, filename, headers=None):

    request_headers = {
        "User-Agent": "Football-iCal/1.0",
    }

    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        url,
        headers=request_headers,
    )

    print(f"Téléchargement : {filename}")

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        content = response.read()

    if not content:
        raise RuntimeError(
            f"Réponse vide pour {filename}"
        )

    return content


# ============================================================
# SAUVEGARDE ICS
# ============================================================

def download_ics(url, filename):

    content = download(
        url,
        filename
    )

    text = content.decode(
        "utf-8",
        errors="replace"
    )

    if "BEGIN:VCALENDAR" not in text:
        raise RuntimeError(
            f"{filename} ne semble pas être "
            "un calendrier ICS valide."
        )

    path = BASE_DIR / filename

    path.write_bytes(content)

    print(f"✓ Mis à jour : {filename}")


# ============================================================
# SAUVEGARDE JSON FOOTBALL-DATA
# ============================================================

def download_football_data(
    url,
    filename
):

    if not FOOTBALL_DATA_TOKEN:
        raise RuntimeError(
            "FOOTBALL_DATA_TOKEN absent."
        )

    content = download(
        url,
        filename,
        headers={
            "X-Auth-Token":
                FOOTBALL_DATA_TOKEN
        }
    )

    try:

        data = json.loads(
            content.decode("utf-8")
        )

    except json.JSONDecodeError:

        raise RuntimeError(
            f"{filename} n'est pas "
            "un JSON valide."
        )


    # football-data.org renvoie normalement
    # une clé "matches" pour ces endpoints.

    if "matches" not in data:

        message = data.get(
            "message",
            "Réponse inattendue"
        )

        raise RuntimeError(
            f"Erreur football-data.org : "
            f"{message}"
        )


    path = BASE_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"✓ Mis à jour : {filename}")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 60)
    print("MISE À JOUR FOOTBALL-iCAL")
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # 1. FIXTUR.ES - REAL MADRID
    # --------------------------------------------------------

    download_ics(
        (
            "https://ics.fixtur.es/v2/"
            "real-madrid.ics"
            "?ab27517f4a3919b0"
        ),
        "real-madrid-source.ics"
    )


    # --------------------------------------------------------
    # 2. FIXTUR.ES - MÁLAGA
    # --------------------------------------------------------

    download_ics(
        (
            "https://ics.fixtur.es/v2/"
            "malaga.ics"
        ),
        "malaga-source.ics"
    )


    # --------------------------------------------------------
    # 3. FOOTBALL-DATA - LALIGA
    # --------------------------------------------------------

    download_football_data(
        (
            "https://api.football-data.org/v4/"
            "competitions/PD/matches"
            "?season=2026"
        ),
        "laliga-2026.json"
    )


    # --------------------------------------------------------
    # 4. FOOTBALL-DATA - CHAMPIONS LEAGUE
    # --------------------------------------------------------

    download_football_data(
        (
            "https://api.football-data.org/v4/"
            "competitions/CL/matches"
            "?season=2026"
        ),
        "champions-2026.json"
    )


    # --------------------------------------------------------
    # 5. GÉNÉRATION DES CALENDRIERS FINAUX
    # --------------------------------------------------------

    print()
    print("Génération des calendriers...")
    print()

    import generate_calendars

    generate_calendars.main()


    print()
    print("=" * 60)
    print("MISE À JOUR TERMINÉE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
