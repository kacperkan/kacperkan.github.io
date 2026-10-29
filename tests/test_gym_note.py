import contextlib
import datetime
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.gym_note as gym_note
from scripts.gym_note import (
    build_note,
    extract_exercises,
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

    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        self.gym = self.root / "gym"
        self.gym.mkdir()
        stack.enter_context(mock.patch.multiple(
            gym_note, ROOT=self.root, GYM_DIR=self.gym, CONFIG_DIR=self.root,
            QUEUE_PATH=self.root / "queue.json", SYNC_PATH=self.root / "last-sync.json",
            LOG_PATH=self.root / "sync.log",
        ))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(mock.patch.object(gym_note, "get_credentials", return_value=object()))
        self.publish = stack.enter_context(mock.patch.object(gym_note, "git_publish"))
        self.posters = stack.enter_context(mock.patch.object(gym_note, "save_posters", return_value=True))
        self.tabs = [
            {"sheetId": i, "title": letter, "spreadsheet_id": "book"}
            for i, letter in enumerate(gym_note.LETTERS)
        ]
        self.rows = [
            ["Data", "Squat", "Bench", "Gotowe"],
            ["01.01.2026", "50 (5)", "40 (8)", "TRUE"],
            ["02.01.2026", "50 (5)", "40 (8)", "TRUE"],
        ]
        self.values = {0: self.rows, 1: [], 2: []}
        stack.enter_context(mock.patch.object(
            gym_note, "fetch_spreadsheet_tabs", return_value=(self.tabs, self.values, None),
        ))
        self.plan = datetime.date(2026, 1, 3)

    def import_first(self):
        source = gym_note.source_for(self.tabs[0], datetime.date(2026, 1, 1))
        return gym_note.write_note(self.plan, "A", [("Squat", "50 (5)", "", "")], source)

    def test_v1_v2_v7_repeated_results_and_row_shifts(self):
        self.import_first()
        sources, legacy = gym_note.note_sources()
        row, _, source = gym_note.select_source(self.tabs[0], self.rows, sources, legacy, "A")
        self.assertEqual((row, source["workout_date"]), (2, "2026-01-02"))
        shifted = [self.rows[0], [], *self.rows[1:]]
        self.assertEqual(gym_note.select_source(self.tabs[0], shifted, sources, legacy, "A")[0], 3)

    def test_v4_bad_and_duplicate_dates(self):
        for date in ("", "31.02.2026", "wrong", "01.01.2026"):
            with self.subTest(date=date):
                rows = [*self.rows[:2], [date, "50 (5)", "40 (8)", "TRUE"]]
                with self.assertRaisesRegex(ValueError, "row 3.*date"):
                    gym_note.select_source(self.tabs[0], rows, {}, [], "A")

    def test_v8_history_blocks_without_writing(self):
        path = self.gym / "2026.01.03 A" / "index.md"
        path.parent.mkdir()
        path.write_text('cell_data="50 (5)"')
        sources, legacy = gym_note.note_sources()
        with self.assertRaisesRegex(ValueError, "unmapped history"):
            gym_note.select_source(self.tabs[0], self.rows, sources, legacy, "A")
        self.assertEqual(path.read_text(), 'cell_data="50 (5)"')

    def test_v9_duplicate_metadata_and_title_conflict(self):
        original = self.import_first() / "index.md"
        duplicate = self.gym / "2026.01.10 A" / "index.md"
        duplicate.parent.mkdir()
        duplicate.write_text(original.read_text().replace("03.01.2026", "10.01.2026"))
        with self.assertRaisesRegex(ValueError, "assigned twice"):
            gym_note.note_sources()
        duplicate.write_text(original.read_text())
        with self.assertRaisesRegex(ValueError, "conflicts with title"):
            gym_note.note_sources()

    def test_v4_invalid_metadata(self):
        path = self.import_first() / "index.md"
        text = path.read_text()
        for invalid in ('{}', 'null', '{"sheet_id": 1}', 'not JSON'):
            with self.subTest(invalid=invalid):
                lines = ["gym_source: " + invalid if line.startswith("gym_source:") else line for line in text.splitlines()]
                path.write_text("\n".join(lines))
                with self.assertRaises(ValueError):
                    gym_note.note_sources()

    def test_v11_changed_workout_date_or_workbook_stops(self):
        self.import_first()
        sources, legacy = gym_note.note_sources()
        with self.assertRaisesRegex(ValueError, "disappeared/changed"):
            gym_note.select_source(self.tabs[0], [self.rows[0], self.rows[2]], sources, legacy, "A")
        for changed in ({"spreadsheet_id": "other"}, {"sheetId": 99}):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "workbook/tab changed"):
                gym_note.select_source(dict(self.tabs[0], **changed), self.rows, sources, legacy, "A")

    def test_v5_posters_failure_preserves_existing_note(self):
        path = self.import_first() / "index.md"
        before = path.read_bytes()
        source = gym_note.source_for(self.tabs[0], datetime.date(2026, 1, 1))
        self.posters.return_value = False
        with self.assertRaisesRegex(ValueError, "pCloud"):
            gym_note.write_note(self.plan, "A", [], source, force=True)
        with self.assertRaisesRegex(ValueError, "pCloud"):
            gym_note.write_note(datetime.date(2026, 1, 10), "A", [], source)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.gym / "2026.01.10 A").exists())
        self.assertFalse(list(self.gym.glob(".gym-note-*")))

    def test_v3_v5_earlier_incomplete_workout_blocks_later(self):
        for row in (
            ["01.01.2026", "50 (5)", "40 (8)", "FALSE"],
            ["01.01.2026", "50 (5)", "", "TRUE"],
        ):
            with self.subTest(row=row):
                self.values[0] = [self.rows[0], row, self.rows[2]]
                save_queue([self.plan])
                gym_note.run_queue(self.root / "creds", push=False)
                self.assertFalse((self.gym / "2026.01.03 A").exists())
                snapshot = json.loads(gym_note.SYNC_PATH.read_text())
                self.assertTrue(any("row 2, date 2026-01-01: waiting" in s for s in snapshot["results"]))
        self.publish.assert_not_called()

    def test_v5_missing_checkbox_and_failed_posters_block_queue(self):
        save_queue([self.plan])
        self.values[0] = [self.rows[0][:-1], self.rows[1][:-1]]
        gym_note.run_queue(self.root / "creds", push=False)
        self.assertFalse((self.gym / "2026.01.03 A").exists())
        self.assertIn("missing Gotowe", gym_note.SYNC_PATH.read_text())
        self.values[0] = self.rows
        self.posters.return_value = False
        gym_note.run_queue(self.root / "creds", push=False)
        self.assertFalse((self.gym / "2026.01.03 A").exists())
        self.assertIn("pCloud", gym_note.SYNC_PATH.read_text())
        self.publish.assert_not_called()

    def test_v8_only_unresolved_history_within_current_cycle_blocks(self):
        self.import_first()
        sources, _ = gym_note.note_sources()
        old = self.gym / "2025.12.27 A" / "index.md"
        self.assertEqual(gym_note.select_source(self.tabs[0], self.rows, sources, [old], "A")[0], 2)
        unresolved = self.gym / "2026.01.10 A" / "index.md"
        with self.assertRaisesRegex(ValueError, "unresolved historical mapping"):
            gym_note.select_source(self.tabs[0], self.rows, sources, [unresolved], "A")

    def test_v6_v9_queue_multiple_dates_and_rerun(self):
        later = datetime.date(2026, 1, 10)
        save_queue([later, self.plan])
        self.assertEqual(load_queue(), [later, self.plan])
        gym_note.run_queue(self.root / "creds", push=False)
        sources, _ = gym_note.note_sources()
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[("book", 0, "2026-01-01")].parent.name, "2026.01.03 A")
        self.assertEqual(sources[("book", 0, "2026-01-02")].parent.name, "2026.01.10 A")
        gym_note.run_queue(self.root / "creds", push=False)
        self.assertEqual(gym_note.note_sources()[0], sources)
        self.publish.assert_not_called()

    def test_queue_publishes_and_clears_completed_date(self):
        for tab in self.tabs:
            self.values[tab["sheetId"]] = self.rows[:2]
        save_queue([self.plan])
        gym_note.run_queue(self.root / "creds", push=True)
        self.publish.assert_called_once()
        self.assertEqual(len(self.publish.call_args.args[0]), 3)
        self.assertEqual(load_queue(), [])

    def test_v10_manual_force_keeps_bound_source(self):
        self.import_first()
        with mock.patch.object(sys, "argv", ["gym-note", "A", "03.01.2026", "--force"]):
            gym_note.main()
        self.assertEqual(set(gym_note.note_sources()[0]), {("book", 0, "2026-01-01")})
        with mock.patch.object(sys, "argv", ["gym-note", "A", "10.01.2026"]):
            gym_note.main()
        self.assertEqual(len(gym_note.note_sources()[0]), 2)
        self.publish.assert_not_called()

    def test_v10_autodetection_requires_one_candidate(self):
        self.values[1] = self.rows
        with mock.patch.object(sys, "argv", ["gym-note"]), self.assertRaisesRegex(SystemExit, "cannot auto-detect"):
            gym_note.main()
        self.values[1] = []
        with mock.patch.object(sys, "argv", ["gym-note", "03.01.2026"]):
            gym_note.main()
        self.assertEqual(set(gym_note.note_sources()[0]), {("book", 0, "2026-01-01")})

    def test_v7_status_without_snapshot_labels_historical_logs(self):
        gym_note.LOG_PATH.write_text("old workout log\n")
        with mock.patch.object(gym_note, "launchd_is_loaded", return_value=True), mock.patch.object(gym_note, "fetch_spreadsheet_tabs") as fetch, contextlib.redirect_stdout(io.StringIO()) as output:
            gym_note.print_status()
        self.assertIn("no sync recorded by this version", output.getvalue())
        self.assertIn("historical log", output.getvalue())
        fetch.assert_not_called()
        self.assertFalse(gym_note.SYNC_PATH.exists())

    def test_v7_snapshot_reports_time_and_reason(self):
        self.rows[1][-1] = "FALSE"
        save_queue([self.plan])
        gym_note.run_queue(self.root / "creds", push=False)
        snapshot = json.loads(gym_note.SYNC_PATH.read_text())
        self.assertIsNotNone(snapshot["finished_at"])
        with mock.patch.object(gym_note, "launchd_is_loaded", return_value=True), contextlib.redirect_stdout(io.StringIO()) as output:
            gym_note.print_status()
        self.assertIn("not live", output.getvalue())
        self.assertIn("row 2, date 2026-01-01: waiting (Gotowe is not checked)", output.getvalue())

    def test_sync_failure_is_saved(self):
        save_queue([self.plan])
        with mock.patch.object(gym_note, "fetch_spreadsheet_tabs", side_effect=RuntimeError("offline")):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                gym_note.run_queue(self.root / "creds", push=False)
        snapshot = json.loads(gym_note.SYNC_PATH.read_text())
        self.assertIsNotNone(snapshot["finished_at"])
        self.assertEqual(snapshot["results"], ["sync failed: offline"])

