import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build as b  # noqa: E402

ALLOWED = ("https://doi.org/", "https://openalex.org/")  # <a href> 링크용. 페이지가 직접 불러오지는 않음


def built(today):
    with tempfile.TemporaryDirectory() as d:
        html = b.build(today, Path(d) / "index.html")
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S).group(1))
    return html, data


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html, cls.data = built("2026-11-03")

    def test_no_external_requests(self):
        for bad in ("<script src", "<link", "@import", "fetch(", "XMLHttpRequest", "<img", "<iframe"):
            self.assertNotIn(bad, self.html)
        urls = re.findall(r"https?://[^\s\"'<>`$)]*", self.html)
        self.assertEqual([u for u in urls if not u.startswith(ALLOWED)], [])

    def test_no_fixed_overlay_or_history_api(self):
        self.assertIsNone(re.search(r"position:\s*(fixed|sticky)\s*[;}]", self.html))
        self.assertIsNone(re.search(r"replaceState|pushState", self.html))

    def test_every_professor_present(self):
        profs = json.loads((b.DATA / "professors.json").read_text())
        self.assertEqual({p["id"] for p in self.data["profs"]}, {p["id"] for p in profs})

    def test_tags_are_computed(self):
        self.assertTrue(any(w["k"] for w in self.data["papers"]))
        keys = {c["key"] for p in self.data["profs"] for c in p["cats"]}
        self.assertTrue(all(k in keys for w in self.data["papers"] for k in w["k"]))

    def test_new_status_follows_build_date(self):
        _, later = built("2026-12-31")
        self.assertFalse(any(w["n"] for w in later["papers"]))

    def test_no_bom_in_text(self):
        self.assertNotIn("﻿", self.html)


if __name__ == "__main__":
    unittest.main()
