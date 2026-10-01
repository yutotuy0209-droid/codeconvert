import tempfile
import unittest
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from function_to_svg import analyze_python, render_function_svg, render_module_svg


class FunctionToSvgTest(unittest.TestCase):
    def setUp(self):
        self.fixture = ROOT / "tests" / "fixtures" / "sample.py"

    def test_analyze(self):
        items = analyze_python(self.fixture)
        self.assertEqual([item.name for item in items], ["normalize", "analyze"])
        self.assertIn("normalize", items[1].calls)

    def test_render_svg(self):
        items = analyze_python(self.fixture)
        single = render_function_svg(items[0], self.fixture.name)
        overview = render_module_svg(items, self.fixture.name)
        self.assertIn("<svg", single)
        self.assertIn("normalize", single)
        self.assertIn("Function Map", overview)

    def test_output_is_writable(self):
        items = analyze_python(self.fixture)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "function.svg"
            out.write_text(render_function_svg(items[0], self.fixture.name), encoding="utf-8")
            self.assertTrue(out.exists())

    def test_function_canvas_contains_all_sections(self):
        from renderer import render_function_svg as render_shared_function
        for info in analyze_python(self.fixture):
            root = ET.fromstring(render_shared_function(info, self.fixture.name))
            height = float(root.get("height"))
            for node in root:
                if node.tag.endswith("rect") and node.get("y"):
                    self.assertLessEqual(float(node.get("y")) + float(node.get("height")), height)
                if node.tag.endswith("text"):
                    self.assertLess(float(node.get("y")), height)


if __name__ == "__main__":
    unittest.main()
