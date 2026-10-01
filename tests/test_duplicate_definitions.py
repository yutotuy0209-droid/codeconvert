import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DuplicateDefinitionsTest(unittest.TestCase):
    def test_repeated_name_requires_line_and_split_preserves_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "duplicate.py"
            source.write_text("def compute():\n    return 1\n\ndef compute():\n    return 2\n", encoding="utf-8")
            command = [sys.executable, str(ROOT / "src/code_to_svg.py"), str(source)]
            ambiguous = subprocess.run(command + ["--function", "compute"], capture_output=True, text=True)
            self.assertNotEqual(ambiguous.returncode, 0)
            self.assertIn("Ambiguous", ambiguous.stderr)
            selected = subprocess.run(command + ["--function", "compute", "--line", "4", "--out", str(root / "selected.svg")], capture_output=True, text=True)
            self.assertEqual(selected.returncode, 0, selected.stderr)
            svg = (root / "selected.svg").read_text(encoding="utf-8")
            self.assertIn("L4-L5", svg)
            self.assertIn("• 2", svg)
            split = subprocess.run(command + ["--split", str(root / "split")], capture_output=True, text=True)
            self.assertEqual(split.returncode, 0, split.stderr)
            self.assertEqual(sorted(p.name for p in (root / "split").glob("*.svg")), ["compute-L1.svg", "compute-L4.svg"])

    def test_line_requires_function(self):
        result = subprocess.run([sys.executable, str(ROOT / "src/code_to_svg.py"), "unused.py", "--line", "4"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --function", result.stderr)


if __name__ == "__main__":
    unittest.main()
