import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_papers as f  # noqa: E402

PROFS = json.loads((ROOT / "data" / "professors.json").read_text())
COLORS = {"gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink"}  # red 는 신규 전용


class Professors(unittest.TestCase):
    def test_ids_unique_and_slug(self):
        ids = [p["id"] for p in PROFS]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^[a-z0-9-]+$")

    def test_category_keys_unique_across_professors(self):
        # 화면 필터와 Notion 다중 선택에서 key 로 묶으므로 교수 간에도 겹치면 안 된다
        keys = [c["key"] for p in PROFS for c in p["categories"]]
        self.assertEqual(len(keys), len(set(keys)), [k for k in keys if keys.count(k) > 1])

    def test_category_fields(self):
        for p in PROFS:
            self.assertLessEqual(len(p["categories"]), 3, p["id"])
            for c in p["categories"]:
                self.assertIn(c["color"], COLORS, (p["id"], c["key"]))
                for k in ("ko", "en", "desc"):
                    self.assertTrue(c[k], (p["id"], c["key"], k))
                for k in ("ko", "en"):
                    self.assertNotIn(",", c[k], "Notion 다중 선택 이름에는 쉼표를 쓸 수 없다")
                for m in c["match"]:
                    f.term_re(m)
                    self.assertEqual(m, m.strip().lower(), (p["id"], m))

    def test_openalex_ids(self):
        for p in PROFS:
            for a in p["openalex"]:
                self.assertRegex(a, r"^A\d+$")


if __name__ == "__main__":
    unittest.main()
