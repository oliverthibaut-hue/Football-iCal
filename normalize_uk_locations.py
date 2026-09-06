from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent

FILES = [
    "Real-Madrid.ics",
    "Malaga-CF.ics",
    "Union-Bordeaux-Begles.ics",
    "real-madrid-history.ics",
    "malaga-history.ics",
    "ubb-history.ics",
]

CITY_COUNTRIES = {
    # Angleterre
    "London": "Angleterre",
    "Liverpool": "Angleterre",
    "Manchester": "Angleterre",
    "Birmingham": "Angleterre",
    "Bristol": "Angleterre",
    "Gloucester": "Angleterre",
    "Exeter": "Angleterre",
    "Northampton": "Angleterre",
    "Leicester": "Angleterre",
    "Newcastle": "Angleterre",
    "Leeds": "Angleterre",
    "Sunderland": "Angleterre",
    "Nottingham": "Angleterre",
    "Brighton": "Angleterre",
    "Coventry": "Angleterre",
    "Hull": "Angleterre",
    "Ipswich": "Angleterre",
    "Bournemouth": "Angleterre",
    "Southampton": "Angleterre",
    "Sheffield": "Angleterre",
    "Wolverhampton": "Angleterre",
    "Derby": "Angleterre",
    "Middlesbrough": "Angleterre",
    "Oxford": "Angleterre",
    "Reading": "Angleterre",
    "Watford": "Angleterre",

    # Écosse
    "Glasgow": "Écosse",
    "Edinburgh": "Écosse",
    "Édimbourg": "Écosse",
    "Aberdeen": "Écosse",
    "Dundee": "Écosse",

    # Pays de Galles
    "Cardiff": "Pays de Galles",
    "Swansea": "Pays de Galles",
    "Newport": "Pays de Galles",

    # Irlande du Nord
    "Belfast": "Irlande du Nord",
}

UK_LABELS = {
    "Royaume-Uni",
    "United Kingdom",
    "UK",
    "Grande-Bretagne",
    "Great Britain",
    "England",
    "Scotland",
    "Wales",
    "Northern Ireland",
}

LOCATION_RE = re.compile(
    r"^(LOCATION(?:;[^:]*)?:)(.*)$",
    re.IGNORECASE,
)


def normalize_location_line(line):
    match = LOCATION_RE.match(line)

    if not match:
        return line, False

    prefix, value = match.groups()

    # Les valeurs LOCATION peuvent être échappées en iCalendar.
    for city, country in CITY_COUNTRIES.items():
        pattern = re.compile(
            rf"^({re.escape(city)})\s+\(([^)]+)\)(.*)$",
            re.IGNORECASE,
        )

        city_match = pattern.match(value)

        if not city_match:
            continue

        existing_country = city_match.group(2).strip()

        if existing_country not in UK_LABELS:
            # Si le pays est déjà correct (Angleterre, Écosse, etc.),
            # on ne touche à rien.
            if existing_country == country:
                return line, False
            continue

        new_value = (
            f"{city_match.group(1)} "
            f"({country})"
            f"{city_match.group(3)}"
        )

        return prefix + new_value, True

    return line, False


def normalize_file(path):
    if not path.exists():
        return 0

    raw = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    changes = 0
    output = []

    for line in lines:
        new_line, changed = normalize_location_line(line)
        output.append(new_line)

        if changed:
            changes += 1

    path.write_text(
        newline.join(output),
        encoding="utf-8",
    )

    return changes


def main():
    print()
    print("NORMALISATION DES LIEUX - ROYAUME-UNI")
    print()

    total = 0

    for filename in FILES:
        path = BASE_DIR / filename

        if not path.exists():
            print(f"{filename} : absent, ignoré")
            continue

        changes = normalize_file(path)
        total += changes

        print(
            f"{filename} : "
            f"{changes} localisation(s) corrigée(s)"
        )

    print()
    print(f"Total : {total} localisation(s) corrigée(s)")
    print()


if __name__ == "__main__":
    main()
