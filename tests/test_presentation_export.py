from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from presentation_export import export_pptx, export_motion_storyboard, load_project_summary


class PresentationExportTest(unittest.TestCase):
    def _write_minimal_map_dir(self, root: Path) -> Path:
        map_dir = root / "map"
        map_dir.mkdir()
        (map_dir / "repo_map.json").write_text(
            json.dumps(
                {
                    "main.py": [
                        {"name": "run", "qualified_name": "run", "lines": [1, 3], "calls": ["calculate"], "summary": "entry"}
                    ],
                    "worker.hpp": [
                        {"name": "calculate", "qualified_name": "calculate", "lines": [10, 12], "calls": [], "summary": "worker"}
                    ],
                    "worker.cpp": [
                        {"name": "calculate", "qualified_name": "calculate", "lines": [4, 8], "calls": [], "summary": "impl"}
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (map_dir / "file_relationships.json").write_text(
            json.dumps(
                {
                    "relations": [
                        {"source": "main.py", "target": "worker.hpp", "relation": "include", "labels": ["worker.hpp"]},
                        {"source": "main.py", "target": "worker.cpp", "relation": "call", "labels": ["calculate"]},
                    ],
                    "ambiguities": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return map_dir

    def test_load_project_summary_keeps_nodes_and_relations(self):
        with tempfile.TemporaryDirectory() as td:
            map_dir = self._write_minimal_map_dir(Path(td))
            summary = load_project_summary(map_dir)
            self.assertEqual(len(summary.nodes), 3)
            self.assertEqual(len(summary.relations), 2)
            self.assertEqual(summary.nodes["main.py"].function_count, 1)

    def test_export_pptx_creates_powerpoint_zip_with_diagram_slide(self):
        with tempfile.TemporaryDirectory() as td:
            map_dir = self._write_minimal_map_dir(Path(td))
            out = Path(td) / "relationship_deck.pptx"
            export_pptx(map_dir, out)
            self.assertTrue(out.exists())
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
                self.assertIn("ppt/presentation.xml", names)
                self.assertIn("ppt/slides/slide1.xml", names)
                self.assertIn("ppt/slides/slide2.xml", names)
                slide2 = zf.read("ppt/slides/slide2.xml").decode("utf-8")
                self.assertIn("main.py", slide2)
                self.assertIn("worker.cpp", slide2)
                self.assertIn("CALL", slide2)

    def test_export_motion_storyboard_creates_html_and_svg_frames(self):
        with tempfile.TemporaryDirectory() as td:
            map_dir = self._write_minimal_map_dir(Path(td))
            out_dir = Path(td) / "motion"
            result = export_motion_storyboard(map_dir, out_dir)
            self.assertTrue((out_dir / "motion_storyboard.html").exists())
            self.assertTrue((out_dir / "frames" / "frame_001.svg").exists())
            html = (out_dir / "motion_storyboard.html").read_text(encoding="utf-8")
            self.assertIn("Code relationship motion storyboard", html)
            self.assertIn("frame_001.svg", html)
            self.assertIn("html", result["format"])


if __name__ == "__main__":
    unittest.main()
