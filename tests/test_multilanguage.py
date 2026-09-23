import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from code_to_svg import analyze
from renderer import render_module_svg


class MultiLanguageTest(unittest.TestCase):
    def test_python(self):
        items = analyze(ROOT / "tests" / "fixtures" / "sample.py")
        self.assertGreaterEqual(len(items), 2)

    def test_cpp(self):
        items = analyze(ROOT / "tests" / "fixtures" / "sample.cpp")
        self.assertEqual([x.name for x in items], ["mean", "rms"])
        self.assertIn("mean", items[1].calls)

    def test_matlab(self):
        items = analyze(ROOT / "tests" / "fixtures" / "sample.m")
        self.assertEqual([x.name for x in items], ["analyze_values", "normalize_values"])
        self.assertIn("normalize_values", items[0].calls)

    def test_shared_renderer(self):
        items = analyze(ROOT / "tests" / "fixtures" / "sample.cpp")
        svg = render_module_svg(items, "sample.cpp")
        self.assertIn("<svg", svg)
        self.assertIn("C++", svg)


if __name__ == "__main__":
    unittest.main()
