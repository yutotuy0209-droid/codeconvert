from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from code_to_svg import analyze
from project_mapper import build_file_relations, generate_mermaid, generate_relationship_svg


class ProjectRelationshipMapTest(unittest.TestCase):
    def _project_items(self, root: Path):
        result = {}
        for path in sorted(root.rglob("*.py")):
            if path.name.startswith("test_"):
                continue
            funcs = analyze(path)
            result[path.relative_to(root).as_posix()] = funcs
        return result

    def test_cross_file_import_and_call_resolve_to_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "worker.py").write_text(
                "def calculate(x):\n    return x * 2\n",
                encoding="utf-8",
            )
            (root / "main.py").write_text(
                "from worker import calculate\n\n"
                "def run():\n"
                "    return calculate(3)\n",
                encoding="utf-8",
            )

            items = self._project_items(root)
            relations, ambiguities = build_file_relations(root, items)
            triples = {(r.source, r.target, r.relation) for r in relations}

            self.assertIn(("main.py", "worker.py", "import"), triples)
            self.assertIn(("main.py", "worker.py", "call"), triples)
            self.assertEqual(ambiguities, [])

            mermaid = generate_mermaid(items, relations)
            self.assertIn("main.py", mermaid)
            self.assertIn("worker.py", mermaid)
            self.assertIn("CALL", mermaid)

            svg = generate_relationship_svg(items, relations)
            self.assertIn("Project File Relationship Map", svg)
            self.assertIn("caller/importer", svg)

    def test_ambiguous_called_symbol_is_reported_not_guessed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("def calculate():\n    return 1\n", encoding="utf-8")
            (root / "b.py").write_text("def calculate():\n    return 2\n", encoding="utf-8")
            (root / "main.py").write_text(
                "def run():\n"
                "    return calculate()\n",
                encoding="utf-8",
            )

            items = self._project_items(root)
            relations, ambiguities = build_file_relations(root, items)

            call_edges = [r for r in relations if r.relation == "call"]
            self.assertEqual(call_edges, [])
            self.assertEqual(len(ambiguities), 1)
            self.assertEqual(ambiguities[0]["symbol"], "calculate")
            self.assertEqual(ambiguities[0]["candidates"], ["a.py", "b.py"])


if __name__ == "__main__":
    unittest.main()
