from pathlib import Path
from datetime import datetime, timezone
import re

CALENDAR = Path("Girondins-de-Bordeaux.ics")
HISTORY = Path("girondins-history.ics")

def extract_events(content):
    return re.findall(
        r"BEGIN:VEVENT.*?END:VEVENT",
        content,
        flags=re.DOTALL
    )

def get_value(event, field):
    match = re.search(
        rf"^{field}:(.+)$",
        event,
        flags=re.MULTILINE
    )
    return match.group(1).strip() if match else None

def main():
    if not CALENDAR.exists() or not HISTORY.exists():
        raise SystemExit("Fichier calendrier ou historique manquant")

    calendar = CALENDAR.read_text(encoding="utf-8")
    history = HISTORY.read_text(encoding="utf-8")

    historical_events = extract_events(history)
    current_events = extract_events(calendar)

    existing_uids = {
        get_value(event, "UID")
        for event in historical_events
    }

    now = datetime.now(timezone.utc)
    added = 0

    for event in current_events:
        uid = get_value(event, "UID")
        end_value = get_value(event, "DTEND")

        if not uid or not end_value:
            continue

        try:
            end = datetime.strptime(
                end_value, "%Y%m%dT%H%M%SZ"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        summary = get_value(event, "SUMMARY") or ""

        # Un score doit apparaître entre les deux équipes.
        has_final_score = bool(
            re.search(r"\s\d+\s*-\s*\d+\s", summary)
        )

        if end <= now and has_final_score and uid not in existing_uids:
            historical_events.append(event)
            existing_uids.add(uid)
            added += 1

    header = history.split("BEGIN:VEVENT")[0]

    output = header.rstrip() + "\r\n"

    for event in historical_events:
        output += event.strip() + "\r\n"

    output += "END:VCALENDAR\r\n"

    HISTORY.write_text(output, encoding="utf-8")

    print("Matchs ajoutés à l'historique :", added)
    print("Total historique :", len(historical_events))

if __name__ == "__main__":
    main()
