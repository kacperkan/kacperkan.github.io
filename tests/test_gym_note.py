import datetime
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.gym_note as gym_note
from scripts.gym_note import (
    build_note,
    extract_exercises,
    find_unnoted_row,
    group_columns,
    group_columns_for_rows,
    load_queue,
    save_queue,
)


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

    def test_group_columns_for_rows_includes_trailing_merged_column(self):
        rows = [
            ["Data", "Przysiad", "", "Rumuński martwy ciąg"],
            ["02.10.2026", "60/80 (5/5)", "60 80x5", "50/60 (8/8)", "50 60x8"],
        ]
        groups = group_columns_for_rows(rows)
        self.assertEqual(
            groups,
            [("Przysiad", [1, 2]), ("Rumuński martwy ciąg", [3, 4])],
        )

    def test_find_unnoted_row_tracks_partial_and_complete_rows(self):
        rows = [
            ["Data", "Ex1", "", "Ex2"],
            ["03.10.2026", "60/70 (5/5) @1@", "60 70x5", "40/50 (8/8) @2@"],
            ["", "", "65 75x5", "[4x8]"],
        ]
        groups = group_columns_for_rows(rows)
        seen = {"60/70 (5/5)", "40/50 (8/8)"}

        # Row 1 is already seen; row 2 has only plan helpers (0/2 logged)
        self.assertEqual(find_unnoted_row(rows, groups, seen), (2, 0, 2))

        # Partially logged row 2 (1/2 logged)
        rows[2][1] = "65/75 (5/5) @1@"
        self.assertEqual(find_unnoted_row(rows, groups, seen), (2, 1, 2))

        # Fully logged row 2 (2/2 logged)
        rows[2][3] = "42.5/52.5 (8/8) [4x8] @2@"
        self.assertEqual(find_unnoted_row(rows, groups, seen), (2, 2, 2))

    def test_queue_persistence_and_run_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            queue_file = tmp_path / "queue.json"
            gym_dir = tmp_path / "gym"
            gym_dir.mkdir()

            with (
                mock.patch.object(gym_note, "CONFIG_DIR", tmp_path),
                mock.patch.object(gym_note, "QUEUE_PATH", queue_file),
                mock.patch.object(gym_note, "ROOT", tmp_path),
                mock.patch.object(gym_note, "GYM_DIR", gym_dir),
            ):
                target = datetime.date(2026, 10, 10)
                save_queue([target])
                self.assertEqual(load_queue(), [target])

                # Pre-create A and B as already published
                for letter in ("A", "B"):
                    d = gym_dir / f"2026.10.10 {letter}"
                    d.mkdir()
                    (d / "index.md").write_text('cell_data="seen"\n', encoding="utf-8")

                tabs = [
                    {"sheetId": 1, "title": "A", "index": 0},
                    {"sheetId": 2, "title": "B", "index": 1},
                    {"sheetId": 3, "title": "C", "index": 2},
                ]
                c_rows = [
                    ["Data", "Squat", "Bench"],
                    ["09.10.2026", "100/110 (5/5) @1@", "80/90 (5/5) @2@"],
                ]
                values = {1: [], 2: [], 3: c_rows}

                with (
                    mock.patch.object(gym_note, "get_credentials", return_value=object()),
                    mock.patch.object(gym_note, "fetch_spreadsheet_tabs", return_value=(tabs, values, None)),
                    mock.patch.object(gym_note, "save_posters", return_value=True),
                    mock.patch.object(gym_note, "git_publish") as mock_publish,
                ):
                    gym_note.run_queue(tmp_path / "creds.json", push=True)

                self.assertTrue((gym_dir / "2026.10.10 C" / "index.md").exists())
                mock_publish.assert_called_once()
                # All A, B, C now exist, so queue should be automatically cleared
                self.assertEqual(load_queue(), [])

