#!/usr/bin/env python3

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "Formula-1.ics"

SEASON = int(os.getenv("F1_SEASON", datetime.now(timezone.utc).year))

API_URL = (
    f"https://api.jolpi.ca/ergast/f1/"
    f"{SEASON}/races.json?limit=100"
)

USER_AGENT = "Football-iCal-F1/1.0"

GRAND_PRIX_DURATION = timedelta(hours=2, minutes=30)
SPRINT_DURATION = timedelta(hours=1)

GP_NAMES = {
    "Australian Grand Prix": ("Grand Prix d'Australie", "🇦🇺"),
    "Chinese Grand Prix": ("Grand Prix de Chine", "🇨🇳"),
    "Japanese Grand Prix": ("Grand Prix du Japon", "🇯🇵"),
    "Bahrain Grand Prix": ("Grand Prix de Bahreïn", "🇧🇭"),
    "Bahrain Grand Prix in Malaysia": ("Grand Prix de Bahreïn", "🇧🇭"),
    "Saudi Arabian Grand Prix": ("Grand Prix d'Arabie saoudite", "🇸🇦"),
    "Miami Grand Prix": ("Grand Prix de Miami", "🇺🇸"),
    "Canadian Grand Prix": ("Grand Prix du Canada", "🇨🇦"),
    "Monaco Grand Prix": ("Grand Prix de Monaco", "🇲🇨"),
    "Spanish Grand Prix": ("Grand Prix d'Espagne", "🇪🇸"),
    "Barcelona-Catalunya Grand Prix": ("Grand Prix de Barcelona-Catalunya", "🇪🇸"),
    "Austrian Grand Prix": ("Grand Prix d'Autriche", "🇦🇹"),
    "British Grand Prix": ("Grand Prix de Grande-Bretagne", "🇬🇧"),
    "Belgian Grand Prix": ("Grand Prix de Belgique", "🇧🇪"),
    "Hungarian Grand Prix": ("Grand Prix de Hongrie", "🇭🇺"),
    "Dutch Grand Prix": ("Grand Prix des Pays-Bas", "🇳🇱"),
    "Italian Grand Prix": ("Grand Prix d'Italie", "🇮🇹"),
    "Azerbaijan Grand Prix": ("Grand Prix d'Azerbaïdjan", "🇦🇿"),
    "Singapore Grand Prix": ("Grand Prix de Singapour", "🇸🇬"),
    "United States Grand Prix": ("Grand Prix des États-Unis", "🇺🇸"),
    "Mexico City Grand Prix": ("Grand Prix de Mexico", "🇲🇽"),
    "São Paulo Grand Prix": ("Grand Prix de São Paulo", "🇧🇷"),
    "Sao Paulo Grand Prix": ("Grand Prix de São Paulo", "🇧🇷"),
    "Las Vegas Grand Prix": ("Grand Prix de Las Vegas", "🇺🇸"),
    "Qatar Grand Prix": ("Grand Prix du Qatar", "🇶🇦"),
    "Abu Dhabi Grand Prix": ("Grand Prix d'Abou Dabi", "🇦🇪"),
}

COUNTRY_NAMES = {
    "Australia": "Australie",
    "China": "Chine",
    "Japan": "Japon",
    "Bahrain": "Bahreïn",
    "Saudi Arabia": "Arabie saoudite",
    "USA": "États-Unis",
    "United States": "États-Unis",
    "Canada": "Canada",
    "Monaco": "Monaco",
    "Spain": "Espagne",
    "Austria": "Autriche",
    "UK": "Angleterre",
    "United Kingdom": "Angleterre",
    "Belgium": "Belgique",
    "Hungary": "Hongrie",
    "Netherlands": "Pays-Bas",
    "Italy": "Italie",
    "Azerbaijan": "Azerbaïdjan",
    "Singapore": "Singapour",
    "Mexico": "Mexique",
    "Brazil": "Brésil",
    "Qatar": "Qatar",
    "UAE": "Émirats arabes unis",
    "United Arab Emirates": "Émirats arabes unis",
    "Malaysia": "Malaisie",
}

CITY_NAMES = {
    "Melbourne": "Melbourne",
    "Shanghai": "Shanghai",
    "Suzuka": "Suzuka",
    "Sakhir": "Sakhir",
    "Jeddah": "Djeddah",
    "Miami": "Miami",
    "Montreal": "Montréal",
    "Montréal": "Montréal",
    "Monte-Carlo": "Monte-Carlo",
    "Barcelona": "Barcelona",
    "Madrid": "Madrid",
    "Spielberg": "Spielberg",
    "Silverstone": "Silverstone",
    "Spa": "Spa-Francorchamps",
    "Spa-Francorchamps": "Spa-Francorchamps",
    "Budapest": "Budapest",
    "Zandvoort": "Zandvoort",
    "Monza": "Monza",
    "Baku": "Baku",
    "Singapore": "Singapour",
    "Austin": "Austin",
    "Mexico City": "Mexico",
    "São Paulo": "São Paulo",
    "Sao Paulo": "São Paulo",
    "Las Vegas": "Las Vegas",
    "Lusail": "Lusail",
    "Abu Dhabi": "Abou Dabi",
    "Kuala Lumpur": "Kuala Lumpur",
}

CIRCUIT_NAMES = {
    "Albert Park Grand Prix Circuit": "Albert Park Grand Prix Circuit",
    "Shanghai International Circuit": "Shanghai International Circuit",
    "Suzuka Circuit": "Suzuka International Racing Course",
    "Bahrain International Circuit": "Bahrain International Circuit",
    "Jeddah Corniche Circuit": "Jeddah Corniche Circuit",
    "Miami International Autodrome": "Miami International Autodrome",
    "Circuit Gilles Villeneuve": "Circuit Gilles-Villeneuve",
    "Circuit de Monaco": "Circuit de Monaco",
    "Circuit de Barcelona-Catalunya": "Circuit de Barcelona-Catalunya",
    "Madring": "Madring",
    "Red Bull Ring": "Red Bull Ring",
    "Silverstone Circuit": "Silverstone Circuit",
    "Circuit de Spa-Francorchamps": "Circuit de Spa-Francorchamps",
    "Hungaroring": "Hungaroring",
    "Circuit Zandvoort": "Circuit Zandvoort",
    "Autodromo Nazionale di Monza": "Autodromo Nazionale Monza",
    "Baku City Circuit": "Baku City Circuit",
    "Marina Bay Street Circuit": "Marina Bay Street Circuit",
    "Circuit of the Americas": "Circuit of the Americas",
    "Autódromo Hermanos Rodríguez": "Autódromo Hermanos Rodríguez",
    "Autódromo José Carlos Pace": "Autódromo José Carlos Pace",
    "Las Vegas Strip Street Circuit": "Las Vegas Strip Circuit",
    "Losail International Circuit": "Lusail International Circuit",
    "Yas Marina Circuit": "Yas Marina Circuit",
    "Sepang International Circuit": "Sepang International Circuit",
}

def escape_ical(value):
    if value is None:
        return ""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )

def fold_line(line):
    # Les SUMMARY restent sur une seule ligne afin
    # de ne jamais couper un emoji/drapeau Unicode.
    if line.startswith("SUMMARY:"):
        return [line]

    if len(line.encode("utf-8")) <= 74:
        return [line]

    output = []
    current = ""

    for char in line:
        candidate = current + char

        if len(candidate.encode("utf-8")) > 73:
            output.append(current)
            current = " " + char
        else:
            current = candidate

    if current:
        output.append(current)

    return output

def add_line(lines, value):
    lines.extend(fold_line(value))

def fetch_schedule():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    print(f"Source : {API_URL}")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()

    if not payload:
        raise RuntimeError("La réponse Jolpica est vide.")

    data = json.loads(payload.decode("utf-8"))
    races = (
        data.get("MRData", {})
        .get("RaceTable", {})
        .get("Races", [])
    )

    if not races:
        raise RuntimeError(f"Aucune course trouvée pour {SEASON}.")
    return races

def gp_display_name(race):
    race_name = race.get("raceName", "").strip()

    if race_name in GP_NAMES:
        return GP_NAMES[race_name]

    circuit = race.get("Circuit", {})
    location = circuit.get("Location", {})

    country = location.get("country", "")
    locality = location.get("locality", "")
    circuit_name = circuit.get("circuitName", "")

    # Deux Grands Prix en Espagne en 2026
    if country == "Spain":

        if (
            "Barcelona" in locality
            or "Barcelona" in circuit_name
        ):
            return (
                "Grand Prix de Barcelona-Catalunya",
                "🇪🇸"
            )

        if (
            "Madrid" in locality
            or "Madring" in circuit_name
        ):
            return (
                "Grand Prix d'Espagne",
                "🇪🇸"
            )

    country_fr = COUNTRY_NAMES.get(
        country,
        country
    )

    if country_fr:
        return (
            f"Grand Prix de {country_fr}",
            "🏁"
        )

    cleaned = race_name.replace(
        " Grand Prix",
        ""
    )

    return (
        f"Grand Prix de {cleaned}",
        "🏁"
    )

def format_location(race):
    circuit = race.get("Circuit", {})
    location = circuit.get("Location", {})

    locality_raw = location.get("locality", "")
    country_raw = location.get("country", "")
    circuit_raw = circuit.get("circuitName", "")

    city = CITY_NAMES.get(locality_raw, locality_raw)
    country = COUNTRY_NAMES.get(country_raw, country_raw)
    circuit_name = CIRCUIT_NAMES.get(circuit_raw, circuit_raw)

    parts = []

    if city and country:
        parts.append(f"{city} ({country})")
    elif city:
        parts.append(city)
    elif country:
        parts.append(country)

    if circuit_name:
        parts.append(circuit_name)

    return " - ".join(parts)

def parse_datetime(date_value, time_value):
    if not date_value or not time_value:
        return None

    time_iso = time_value.replace("Z", "+00:00")
    return datetime.fromisoformat(f"{date_value}T{time_iso}")

def format_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def timed_event(uid, title, location, start, duration, dtstamp):
    lines = []
    add_line(lines, "BEGIN:VEVENT")
    add_line(lines, f"UID:{uid}")
    add_line(lines, f"DTSTAMP:{dtstamp}")
    add_line(lines, "CLASS:PUBLIC")
    add_line(lines, "STATUS:CONFIRMED")
    add_line(lines, "TRANSP:OPAQUE")
    add_line(lines, f"DTSTART:{format_utc(start)}")
    add_line(lines, f"DTEND:{format_utc(start + duration)}")
    add_line(lines, f"SUMMARY:{escape_ical(title)}")
    if location:
        add_line(lines, f"LOCATION:{escape_ical(location)}")
    add_line(lines, "END:VEVENT")
    return lines

def all_day_event(uid, title, location, date_value, dtstamp):
    start_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=1)

    lines = []
    add_line(lines, "BEGIN:VEVENT")
    add_line(lines, f"UID:{uid}")
    add_line(lines, f"DTSTAMP:{dtstamp}")
    add_line(lines, "CLASS:PUBLIC")
    add_line(lines, "STATUS:TENTATIVE")
    add_line(lines, "TRANSP:TRANSPARENT")
    add_line(lines, "DTSTART;VALUE=DATE:" + start_date.strftime("%Y%m%d"))
    add_line(lines, "DTEND;VALUE=DATE:" + end_date.strftime("%Y%m%d"))
    add_line(lines, f"SUMMARY:{escape_ical(title)}")
    if location:
        add_line(lines, f"LOCATION:{escape_ical(location)}")
    add_line(lines, "END:VEVENT")
    return lines

def main():
    print()
    print("=" * 64)
    print("MISE À JOUR CALENDRIER FORMULA 1")
    print("=" * 64)
    print()

    races = fetch_schedule()
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    events = []
    gp_count = 0
    sprint_count = 0
    missing_times = []

    for race in races:
        round_number = race.get("round", "0")
        gp_name, flag = gp_display_name(race)
        location = format_location(race)

        sprint = race.get("Sprint")

        if sprint:
            sprint_title = (
                "Formula 1 | 🏎️ SPRINT - "
                f"{gp_name} {flag}"
            )
            sprint_date = sprint.get("date")
            sprint_time = sprint.get("time")
            sprint_start = parse_datetime(sprint_date, sprint_time)

            sprint_uid = (
                f"formula1-{SEASON}-r{round_number}-sprint"
                "@oliverthibaut-football-ical"
            )

            if sprint_start:
                events.extend(
                    timed_event(
                        sprint_uid,
                        sprint_title,
                        location,
                        sprint_start,
                        SPRINT_DURATION,
                        dtstamp,
                    )
                )
            else:
                events.extend(
                    all_day_event(
                        sprint_uid,
                        sprint_title,
                        location,
                        sprint_date,
                        dtstamp,
                    )
                )
                missing_times.append(sprint_title)

            sprint_count += 1

        gp_title = (
            "Formula 1 | 🏎️ - "
            f"{gp_name} {flag}"
        )
        race_date = race.get("date")
        race_time = race.get("time")
        race_start = parse_datetime(race_date, race_time)

        gp_uid = (
            f"formula1-{SEASON}-r{round_number}-race"
            "@oliverthibaut-football-ical"
        )

        if race_start:
            events.extend(
                timed_event(
                    gp_uid,
                    gp_title,
                    location,
                    race_start,
                    GRAND_PRIX_DURATION,
                    dtstamp,
                )
            )
        else:
            events.extend(
                all_day_event(
                    gp_uid,
                    gp_title,
                    location,
                    race_date,
                    dtstamp,
                )
            )
            missing_times.append(gp_title)

        gp_count += 1

    calendar = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Oliver Thibaut//Formula 1 Calendar//FR",
        "X-WR-CALNAME:Formula 1",
        "X-WR-TIMEZONE:Europe/Paris",
        *events,
        "END:VCALENDAR",
        "",
    ]

    OUTPUT_FILE.write_text(
        "\r\n".join(calendar),
        encoding="utf-8"
    )

    print()
    print(f"Saison : {SEASON}")
    print(f"Grands Prix : {gp_count}")
    print(f"SPRINTs : {sprint_count}")
    print(f"Total événements : {gp_count + sprint_count}")
    print(f"Sortie : {OUTPUT_FILE}")

    if missing_times:
        print()
        print(f"Horaires encore inconnus : {len(missing_times)}")
        for title in missing_times:
            print(f" - {title}")

    print()
    print("Premiers événements :")
    for race in races[:3]:
        gp_name, flag = gp_display_name(race)
        if race.get("Sprint"):
            print(f" - Formula 1 | 🏎️ SPRINT - {gp_name} {flag}")
        print(f" - Formula 1 | 🏎️ - {gp_name} {flag}")
    print()

if __name__ == "__main__":
    main()
