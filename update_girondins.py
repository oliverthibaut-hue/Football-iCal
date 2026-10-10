from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from urllib.request import Request, urlopen

SOURCE = Path("girondins-source.html")
HISTORY = Path("girondins-history.ics")
OUTPUT = Path("Girondins-de-Bordeaux.ics")

COMPETITIONS = {
    "39747": "Régional 1",
    "39935": "Coupe de France",
    "39890": "Friendly",
}

def resolve(obj, cache, depth=0):
    if depth > 15:
        return obj

    if isinstance(obj, dict):
        if obj.get("type") == "id" and "id" in obj:
            target = cache.get(obj["id"])
            if target is not None:
                return resolve(target, cache, depth + 1)

        return {
            k: resolve(v, cache, depth + 1)
            for k, v in obj.items()
            if k != "__typename"
        }

    if isinstance(obj, list):
        return [resolve(v, cache, depth + 1) for v in obj]

    return obj

def escape(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )

def fold(line):
    result = []
    current = ""

    for char in line:
        if len((current + char).encode("utf-8")) > 73:
            result.append(current)
            current = " " + char
        else:
            current += char

    if current:
        result.append(current)

    return result

def team_name(value, cache):
    data = resolve(value, cache)

    try:
        name = data["entity"]["fieldClubName"]
    except (KeyError, TypeError):
        return "Équipe inconnue"

    if name == "Bordeaux":
        return "FC Girondins de Bordeaux"

    return name.strip()

def main():
    for path in (SOURCE, HISTORY):
        if not path.exists():
            raise SystemExit(f"Fichier manquant : {path}")

    url = "https://www.girondins.com/fr/team/equipe-premiere/calendar-results"

    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Football-iCal/1.0"}
    )

    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    if len(html) < 10000:
        raise RuntimeError("Réponse HTML anormalement courte")

    SOURCE.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")

    script = soup.find("script", id="__NEXT_DATA__")
    if script is None:
        raise SystemExit("Impossible de trouver __NEXT_DATA__")

    data = json.loads(script.string)
    cache = data["props"]["apolloState"]["data"]

    matches = [
        value
        for key, value in cache.items()
        if re.search(r"\.entities\.\d+$", key)
        and isinstance(value, dict)
        and "fieldHomeTeam" in value
        and "fieldAwayTeam" in value
    ]

    # Historique validé jusqu'au 27 septembre 2026 inclus.
    cutoff = datetime(2026, 9, 28, tzinfo=timezone.utc)
    stamp = "20261010T000000Z"

    historical = HISTORY.read_text(encoding="utf-8")
    history_events = historical.split("BEGIN:VEVENT")[1:]

    events = [
        "BEGIN:VEVENT" + event.split("END:VEVENT")[0] + "END:VEVENT"
        for event in history_events
        if "END:VEVENT" in event
    ]

    existing_uids = set()

    for event in events:
        for line in event.splitlines():
            if line.startswith("UID:"):
                existing_uids.add(line[4:].strip())

    added = 0

    for match in matches:
        date_data = resolve(match.get("fieldDate"), cache)

        if not isinstance(date_data, dict) or not date_data.get("date"):
            continue

        start = datetime.strptime(
            date_data["date"], "%Y-%m-%d %H:%M:%S UTC"
        ).replace(tzinfo=timezone.utc)

        if start < cutoff:
            continue

        end = start + timedelta(minutes=105)

        home = team_name(match.get("fieldHomeTeam"), cache)
        away = team_name(match.get("fieldAwayTeam"), cache)

        competition = resolve(match.get("fieldMatchCompetition"), cache)
        competition_id = ""

        if isinstance(competition, dict):
            entity = competition.get("entity") or {}
            if isinstance(entity, dict):
                competition_id = str(entity.get("entityId") or "")

        category = COMPETITIONS.get(competition_id, "Friendly")

        hs = match.get("fieldHomeScore")
        aws = match.get("fieldAwayScore")

        if hs is not None and aws is not None:
            summary = f"{category} | {home} {hs} - {aws} {away}"
        else:
            summary = f"{category} | {home} - {away}"

        match_id = str(match.get("entityId") or "")
        if not match_id:
            match_id = hashlib.sha1(
                f"{start.isoformat()}|{home}|{away}".encode()
            ).hexdigest()[:16]

        uid = f"girondins-{match_id}@oliverthibaut-football-ical"

        if uid in existing_uids:
            events = [
                event
                for event in events
                if f"UID:{uid}" not in event
            ]

        existing_uids.add(uid)

        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            "DTSTART:" + start.strftime("%Y%m%dT%H%M%SZ"),
            "DTEND:" + end.strftime("%Y%m%dT%H%M%SZ"),
            "SUMMARY:" + escape(summary),
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
        ]

        venue = match.get("fieldVenue")
        if isinstance(venue, str) and venue.strip():
            lines.append("LOCATION:" + escape(venue.strip()))

        lines.append("END:VEVENT")

        events.append("\r\n".join(lines))
        added += 1

    if len(matches) == 0:
        raise SystemExit(
            "Aucun match détecté sur Girondins.com. "
            "Publication annulée par sécurité."
        )

    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Football-iCal//Girondins//FR",
        "X-WR-CALNAME:FC Girondins de Bordeaux",
        "X-WR-TIMEZONE:Europe/Paris",
        "X-APPLE-CALENDAR-COLOR:#0D1D4A",
    ]

    result = "\r\n".join(header) + "\r\n"

    for event in events:
        unfolded = event.replace("\r\n ", "").replace("\n ", "")
        lines = unfolded.replace("\r\n", "\n").split("\n")

        for line in lines:
            if line:
                result += "\r\n".join(fold(line)) + "\r\n"

    result += "END:VCALENDAR\r\n"
    OUTPUT.write_text(result, encoding="utf-8")

    print(f"Historique : {len(history_events)} matchs")
    print(f"Source officielle : {len(matches)} matchs")
    print(f"Nouveaux matchs ajoutés : {added}")
    print(f"Total : {len(events)} événements")
    print(f"Fichier créé : {OUTPUT}")

if __name__ == "__main__":
    main()
