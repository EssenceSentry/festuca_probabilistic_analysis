"""Safety and determinism checks for the one-time XLSX migration."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from festuca_analysis.workbook import migrate_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT_ROOT / "sources" / "Datos_Ema_Serrana_INN.xlsx"


class WorkbookMigrationTests(unittest.TestCase):
    def test_migration_is_deterministic_and_checkable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "data"
            migrate_workbook(WORKBOOK, output)
            migrate_workbook(WORKBOOK, output, check=True)
            with self.assertRaises(FileExistsError):
                migrate_workbook(WORKBOOK, output)

    def test_migration_rejects_an_open_excel_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            workbook = temporary / WORKBOOK.name
            shutil.copy2(WORKBOOK, workbook)
            workbook.with_name(f"~${workbook.name}").touch()
            with self.assertRaisesRegex(RuntimeError, "Close Microsoft Excel"):
                migrate_workbook(workbook, temporary / "data")


if __name__ == "__main__":
    unittest.main()
