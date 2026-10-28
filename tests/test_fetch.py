import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_papers as f  # noqa: E402


def work(wid="W1", title="A Study", doi=None, typ="article", venue="Journal X", cited=0,
         authors=(("A1", ["I163753206"]),), field="fields/17", year=2024):
    return {
        "id": f"https://openalex.org/{wid}", "title": title, "doi": doi and f"https://doi.org/{doi}",
        "type": typ, "publication_year": year, "publication_date": f"{year}-01-01", "cited_by_count": cited,
        "primary_location": {"source": {"display_name": venue}},
        "primary_topic": {"display_name": "Fuzzing", "field": {"id": f"https://openalex.org/{field}"}},
        "keywords": [{"display_name": "mutation testing"}],
        "authorships": [{"author": {"id": f"https://openalex.org/{a}", "display_name": a},
                         "institutions": [{"id": f"https://openalex.org/{i}"} for i in insts]} for a, insts in authors],
    }


def paper(**kw):
    p = f.to_paper(work(**kw))
    p["cats"] = []
    return p


PROF = {"id": "p1", "openalex": ["A1"], "categories": [
    {"key": "fuzz", "match": ["fuzz"]}, {"key": "db", "match": ["database"]}]}


class KeepWork(unittest.TestCase):
    def test_skips_corrections_and_errata(self):
        self.assertFalse(f.keep_work(work(title="Correction: A Study"), PROF))
        self.assertFalse(f.keep_work(work(typ="erratum"), PROF))
        self.assertTrue(f.keep_work(work(), PROF))

    def test_affiliation_filter_checks_this_author_only(self):
        prof = dict(PROF, affiliation_filter=True)
        other_at_cbnu = work(authors=(("A1", ["I999"]), ("A2", ["I163753206"])))
        self.assertFalse(f.keep_work(other_at_cbnu, prof))
        self.assertTrue(f.keep_work(work(authors=(("A1", ["I163753206"]),)), prof))

    def test_field_filter(self):
        prof = dict(PROF, field_filter=True)
        self.assertFalse(f.keep_work(work(field="fields/31"), prof))
        self.assertTrue(f.keep_work(work(field="fields/17"), prof))


class Tagging(unittest.TestCase):
    def test_matches_title_and_terms(self):
        p = paper(title="Directed Greybox FUZZING")
        self.assertEqual(f.tag(p, PROF), ["fuzz"])
        self.assertEqual(f.tag(paper(title="Nothing here"), PROF), ["fuzz"])  # 주제어 "Fuzzing"
        self.assertEqual(f.tag(paper(title="x"), {"categories": []}), [])


class Merge(unittest.TestCase):
    def test_baseline_marks_normal(self):
        out = f.merge([], {"p1": [paper()]}, "2026-10-26", baseline={"p1", "p2"})
        self.assertEqual(out[0]["status"], "normal")
        self.assertEqual(out[0]["added_at"], "2026-10-26")

    def test_new_paper_after_baseline(self):
        base = f.merge([], {"p1": [paper()]}, "2026-10-26", baseline={"p1", "p2"})
        out = f.merge(base, {"p1": [paper(), paper(wid="W2", title="Another")]}, "2026-11-02", baseline=set())
        self.assertEqual(len(out), 2)
        new = [p for p in out if p["id"] == "W2"][0]
        self.assertEqual((new["status"], new["added_at"]), ("new", "2026-11-02"))
        old = [p for p in out if p["id"] == "W1"][0]
        self.assertEqual((old["status"], old["added_at"]), ("normal", "2026-10-26"))

    def test_dedupe_by_doi_and_title(self):
        a = paper(wid="W1", doi="10.1/x")
        b = paper(wid="W9", title="Totally different title", doi="10.1/X")
        c = paper(wid="W7", title="a  study!", year=2024)
        out = f.merge([], {"p1": [a, b, c]}, "2026-10-26", baseline={"p1", "p2"})
        self.assertEqual(len(out), 1)

    def test_prefers_published_over_preprint_and_keeps_max_citations(self):
        pre = paper(wid="W1", venue="arXiv (Cornell University)", cited=9)
        pub = paper(wid="W2", venue="ICSE", cited=3)
        out = f.merge([], {"p1": [pre, pub]}, "2026-10-26", baseline={"p1", "p2"})
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0]["venue"], out[0]["cited"]), ("ICSE", 9))

    def test_coauthored_by_two_professors(self):
        out = f.merge([], {"p1": [paper()], "p2": [paper()]}, "2026-10-26", baseline={"p1", "p2"})
        self.assertEqual(out[0]["prof"], ["p1", "p2"])

    def test_existing_added_at_never_changes(self):
        base = f.merge([], {"p1": [paper(cited=1)]}, "2026-10-26", baseline={"p1", "p2"})
        out = f.merge(base, {"p1": [paper(cited=5)]}, "2026-11-02", baseline=set())
        self.assertEqual((out[0]["added_at"], out[0]["cited"]), ("2026-10-26", 5))


    def test_baseline_is_per_professor(self):
        base = f.merge([], {"p1": [paper()]}, "2026-10-26", baseline={"p1"})
        out = f.merge(base, {"p1": [paper(wid="W2", title="B")], "p9": [paper(wid="W3", title="C")]},
                      "2026-11-02", baseline={"p9"})
        st = {p["id"]: p["status"] for p in out}
        self.assertEqual(st, {"W1": "normal", "W2": "new", "W3": "normal"})


class Status(unittest.TestCase):
    def test_new_becomes_normal_after_7_days(self):
        ps = [{"status": "new", "added_at": "2026-10-26"}]
        self.assertEqual(f.refresh_status([dict(ps[0])], "2026-11-01")[0]["status"], "new")
        self.assertEqual(f.refresh_status([dict(ps[0])], "2026-11-02")[0]["status"], "normal")


if __name__ == "__main__":
    unittest.main()
