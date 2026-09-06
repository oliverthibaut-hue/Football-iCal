#!/usr/bin/env python3
from pathlib import Path

path = Path(".github/workflows/update-calendars.yml")

if not path.exists():
    raise SystemExit("Workflow introuvable.")

text = path.read_text(encoding="utf-8")

old_block = (
    "          python merge_history_ubb.py\n"
    "          python update_f1.py\n"
    "          python normalize_uk_locations.py\n"
)

new_block = (
    "          python merge_history_ubb.py\n"
    "          python archive_f1_history.py\n"
    "          python update_f1.py\n"
    "          python merge_history_f1.py\n"
    "          python normalize_uk_locations.py\n"
)

if "python archive_f1_history.py" not in text:
    if old_block not in text:
        raise SystemExit(
            "Bloc F1 attendu introuvable dans le workflow. "
            "Aucune modification effectuée."
        )
    text = text.replace(old_block, new_block, 1)

old_add = (
    "git add Real-Madrid.ics Malaga-CF.ics "
    "Union-Bordeaux-Begles.ics Arsenal-FC.ics Formula-1.ics"
)
new_add = old_add + " formula1-history.ics"

if "formula1-history.ics" not in text:
    if old_add not in text:
        raise SystemExit(
            "Ligne git add attendue introuvable. "
            "Aucune modification effectuée."
        )
    text = text.replace(old_add, new_add, 1)

path.write_text(text, encoding="utf-8")

print("✓ archive F1 avant génération")
print("✓ fusion historique F1 après génération")
print("✓ formula1-history.ics ajouté au commit automatique")
