#!/usr/bin/env python3

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

FILES = [
    "Real-Madrid.ics",
    "Malaga-CF.ics",
    "Union-Bordeaux-Begles.ics",
    "Arsenal-FC.ics",
    "Formula-1.ics",
]

ALARM = [
    "BEGIN:VALARM",
    "ACTION:DISPLAY",
    "TRIGGER:-PT15M",
    "DESCRIPTION:Rappel - début dans 15 minutes",
    "END:VALARM",
]


def add_alarm_to_event(lines):
    # Si l'événement possède déjà une alerte exactement 15 min avant,
    # on ne fait rien.
    if any(
        line.strip() == "TRIGGER:-PT15M"
        for line in lines
    ):
        return lines, False

    output = []

    for line in lines:
        if line == "END:VEVENT":
            output.extend(ALARM)

        output.append(line)

    return output, True


def process_file(path):
    raw = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    # On conserve le type de retour à la ligne du fichier.
    newline = "\r\n" if "\r\n" in raw else "\n"

    lines = (
        raw
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )

    output = []
    event = None

    event_count = 0
    added_count = 0

    for line in lines:

        if line == "BEGIN:VEVENT":
            event = [line]
            continue

        if event is not None:

            event.append(line)

            if line == "END:VEVENT":
                event_count += 1

                updated, added = add_alarm_to_event(
                    event
                )

                output.extend(updated)

                if added:
                    added_count += 1

                event = None

            continue

        output.append(line)

    path.write_text(
        newline.join(output),
        encoding="utf-8",
    )

    return event_count, added_count


def main():

    print()
    print("AJOUT DES ALERTES -15 MIN")
    print()

    total_events = 0
    total_added = 0

    for filename in FILES:

        path = BASE_DIR / filename

        if not path.exists():
            print(
                f"{filename}: absent, ignoré"
            )
            continue

        events, added = process_file(path)

        total_events += events
        total_added += added

        print(
            f"{filename}: "
            f"{events} événement(s), "
            f"{added} alerte(s) ajoutée(s)"
        )

    print()
    print(
        f"Total : {total_events} événement(s), "
        f"{total_added} alerte(s) ajoutée(s)"
    )
    print()


if __name__ == "__main__":
    main()
