import unittest
from unittest.mock import patch

import generate_calendars as calendars
import merge_test as merger


class ChampionsTitlesTests(unittest.TestCase):
    # Noms et métadonnées du match 575346 dans champions-2026.json.
    def setUp(self):
        self.date = merger.parse_json_date("2026-10-13T19:00:00Z")
        self.api_match = {
            "utcDate": "2026-10-13T19:00:00Z",
            "matchday": 2,
            "stage": "LEAGUE_STAGE",
            "homeTeam": {"name": "Arsenal FC"},
            "awayTeam": {"name": "Lille OSC"},
        }
        self.event = (
            "UID:arsenal-lille-regression\n"
            "DTSTART:20261013T190000Z\n"
            "SUMMARY:Arsenal - Lille [CL]\n"
            "LOCATION:Emirates\n"
            "SEQUENCE:0\n"
        )

    def official_matches(self):
        def load(filename):
            return {"matches": [self.api_match] if filename == "champions-2026.json" else []}

        with patch.object(merger, "load_json", side_effect=load):
            return merger.load_official_matches()

    def test_lille_aliases_converge(self):
        for name in ("Lille", "Lille OSC", "LOSC Lille", " Lille OSC "):
            with self.subTest(name=name):
                self.assertEqual(merger.normalize_team(name), "LOSC Lille")

    def test_real_provider_names_match_and_produce_j2(self):
        matches = self.official_matches()
        home, away = merger.parse_fixture_teams("Arsenal - Lille [CL]")
        match = merger.find_official_match(self.date, home, away, matches)
        self.assertIs(match, matches[0])
        result = merger.build_title("Arsenal - Lille [CL]", self.date, match)
        self.assertEqual(result, "UEFA Champions League | J2 - Arsenal FC - LOSC Lille")

    def test_generated_event_preserves_identity_time_and_score(self):
        event = self.event.replace("Lille [CL]", "Lille [CL] (2-1)")
        result = merger.unfold_ics(calendars.build_vevent(event, self.official_matches()))
        self.assertEqual(merger.get_field(result, "SUMMARY"),
                         "UEFA Champions League | J2 - Arsenal FC 2 - 1 LOSC Lille")
        self.assertEqual(merger.get_field(result, "UID"), "arsenal-lille-regression")
        self.assertEqual(merger.get_field(result, "DTSTART"), "20261013T190000Z")
        self.assertEqual(merger.get_field(result, "SEQUENCE"), "0")

    def test_missing_match_stays_unknown(self):
        result = merger.unfold_ics(calendars.build_vevent(self.event, []))
        self.assertIn("Tour à définir", merger.get_field(result, "SUMMARY"))

    def test_different_date_or_opponent_does_not_match(self):
        for date, away in (("2026-10-14T19:00:00Z", "LOSC Lille"),
                           ("2026-10-13T19:00:00Z", "Chelsea FC")):
            with self.subTest(date=date, away=away):
                self.assertIsNone(merger.find_official_match(
                    merger.parse_json_date(date), "Arsenal FC", away, self.official_matches()))

    def test_knockout_stage_takes_precedence_over_matchday(self):
        self.api_match["stage"] = "QUARTER_FINALS"
        result = merger.unfold_ics(calendars.build_vevent(self.event, self.official_matches()))
        self.assertEqual(merger.get_field(result, "SUMMARY"),
                         "UEFA Champions League | 4rt de Final - Arsenal FC - LOSC Lille")


if __name__ == "__main__":
    unittest.main()
