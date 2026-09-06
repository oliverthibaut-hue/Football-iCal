from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "ubb-history.ics"
AUTO_FILE = BASE_DIR / "Union-Bordeaux-Begles.ics"
OUTPUT_FILE = AUTO_FILE

def unfold(text):
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result = []
    for line in raw:
        if line.startswith((" ", "\t")) and result:
            result[-1] += line[1:]
        else:
            result.append(line)
    return result

def extract_events(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = unfold(text)
    events = []
    cur = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            cur = ["BEGIN:VEVENT"]
        elif line == "END:VEVENT" and cur is not None:
            cur.append("END:VEVENT")
            events.append(cur)
            cur = None
        elif cur is not None:
            cur.append(line)
    return events

def prop(event, name):
    for line in event:
        if line.startswith(name + ":") or line.startswith(name + ";"):
            return line
    return ""

def event_key(event):
    uid = prop(event, "UID")
    if uid:
        return ("uid", uid)
    return (
        "fallback",
        prop(event, "DTSTART"),
        prop(event, "SUMMARY"),
    )

def main():
    if not HISTORY_FILE.exists():
        raise SystemExit(f"Historique introuvable : {HISTORY_FILE}")
    if not AUTO_FILE.exists():
        raise SystemExit(f"Calendrier automatique introuvable : {AUTO_FILE}")

    history = extract_events(HISTORY_FILE)
    automatic = extract_events(AUTO_FILE)

    merged = []
    seen = set()

    for event in history + automatic:
        key = event_key(event)
        if key in seen:
            continue
        seen.add(key)
        merged.append(event)

    output = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//Oliver Thibaut//UBB Calendar//FR",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Union Bordeaux Bègles",
        "X-WR-TIMEZONE:Europe/Paris",
    ]

    for event in merged:
        output.extend(event)

    output.append("END:VCALENDAR")

    OUTPUT_FILE.write_text(
        "\r\n".join(output) + "\r\n",
        encoding="utf-8",
    )

    print()
    print("FUSION HISTORIQUE UBB")
    print(f"Historique : {len(history)} événements")
    print(f"Automatique : {len(automatic)} événements")
    print(f"Total publié : {len(merged)} événements")
    print(f"Sortie : {OUTPUT_FILE}")
    print()

if __name__ == "__main__":
    main()
