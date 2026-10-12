import datetime
import unittest

from scripts.gym_note import build_note, extract_exercises, group_columns


class GymNoteTests(unittest.TestCase):
    def test_single_column_heading_preserves_scheme_and_full_weights(self):
        cases = [
            ("[4x8]", "4x8"),
            (
                "[4x8, chwyt naturalny, kciuk do góry, przerwa na górze]",
                "4x8",
            ),
            ("[5x5, 0/7.5/12.5/0/7.5]", "5x5, 0/7.5/12.5/0/7.5"),
            (
                "[5x5, 0/7.5/12.5/0/7.5, chwyt naturalny, przerwa na górze]",
                "5x5, 0/7.5/12.5/0/7.5",
            ),
            (
                "[4x8,17.5/22.5/27.5/32.5]",
                "4x8,17.5/22.5/27.5/32.5",
            ),
        ]
        note_date = datetime.date(2026, 10, 18)
        for annotation, summary in cases:
            with self.subTest(annotation=annotation):
                raw = f"0/7.5/12.5/0/7.5 (5/5/5/5/5) <10/8/5/2/0> {annotation}"
                rows = [["Data", "Podciąganie"], ["18.10.2026", raw]]
                exercises = extract_exercises(
                    rows, 1, group_columns(rows[0]), note_date, "A"
                )
                self.assertEqual(exercises, [(f"Podciąganie {summary}", raw, "", "")])
                note = build_note(note_date, "A", exercises)
                self.assertIn(f"1. Podciąganie {summary}\n", note)
                self.assertIn(f'cell_data="{raw}"', note)
