"""Repository hygiene: personal data must not be committed."""

import ast
import shutil
import subprocess
import unittest
from pathlib import Path

PY_APP = Path(__file__).resolve().parents[1]


def _git_ignores(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", str(path)],
        cwd=PY_APP, capture_output=True, check=False,
    )
    return result.returncode == 0


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class TestGitIgnore(unittest.TestCase):
    def test_training_history_is_ignored(self):
        # The rule `data/training_sessions.json.gzip` only matched at the
        # repository root, not under py_app/.
        for name in ("training_sessions.json.gzip", "training_sessions.json"):
            with self.subTest(name=name):
                self.assertTrue(_git_ignores(PY_APP / "data" / name))

    def test_session_backups_are_ignored(self):
        self.assertTrue(_git_ignores(PY_APP / "data" / "training_sessions.json.gzip.corrupt-20250301-090000"))


class TestManualScripts(unittest.TestCase):
    def test_collecting_the_tests_does_not_run_them(self):
        # pytest imports every test_*.py file, and test_ui.py then started the trainer.
        for name in ("test_ui.py", "test_two_back.py"):
            with self.subTest(name=name):
                tree = ast.parse((PY_APP / name).read_text(encoding="utf-8"))
                for node in tree.body:
                    self.assertIsInstance(node, (ast.Expr, ast.Import, ast.ImportFrom, ast.FunctionDef, ast.If))
                    if isinstance(node, ast.Expr):
                        self.assertIsInstance(node.value, ast.Constant, "only a docstring may run on import")


if __name__ == "__main__":
    unittest.main()
