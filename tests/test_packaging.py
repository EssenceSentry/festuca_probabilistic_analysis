"""Packaging checks for the installed command-line surface."""

from __future__ import annotations

import importlib
import tomllib
import unittest
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_project_script_targets_are_importable(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            configuration = tomllib.load(handle)

        project = cast(dict[str, object], configuration["project"])
        scripts = cast(dict[str, str], project["scripts"])
        for name, target in scripts.items():
            module_name, attribute_name = target.split(":", maxsplit=1)
            module = importlib.import_module(module_name)
            self.assertTrue(
                callable(getattr(module, attribute_name, None)),
                msg=f"{name} targets a missing callable: {target}",
            )


if __name__ == "__main__":
    unittest.main()
