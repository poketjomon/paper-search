import pathlib
import sys
import unittest
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from paper_search import (
    classify_local_result,
    default_arxiv_fallback_search,
    format_paper_search_results,
    parse_paper_search_query,
    run_paper_search,
)


class ParsePaperSearchQueryTest(unittest.TestCase):
    def test_extracts_exact_year_venue_and_has_code_filters(self):
        self.assertEqual(
            parse_paper_search_query("find 2024 diffusion policy papers from CORL with code"),
            {
                "rawQuery": "find 2024 diffusion policy papers from CORL with code",
                "query": "diffusion policy",
                "venues": ["CORL"],
                "yearStart": 2024,
                "yearEnd": 2024,
                "hasCode": True,
                "hasPdf": False,
                "warnings": [],
            },
        )

    def test_strips_arxiv_links_but_keeps_local_search_intent(self):
        self.assertEqual(
            parse_paper_search_query("find 2024 CORL papers about diffusion policy https://arxiv.org/abs/2401.12345"),
            {
                "rawQuery": "find 2024 CORL papers about diffusion policy https://arxiv.org/abs/2401.12345",
                "query": "diffusion policy",
                "venues": ["CORL"],
                "yearStart": 2024,
                "yearEnd": 2024,
                "hasCode": False,
                "hasPdf": False,
                "warnings": [],
            },
        )


class RunPaperSearchTest(unittest.TestCase):
    def test_returns_ranked_results_with_match_reasons(self):
        papers = [
            {
                "id": "1",
                "title": "Diffusion Policy for Robot Manipulation",
                "abstract": "A diffusion-based approach for robot control.",
                "authors": ["A"],
                "venue": "CORL",
                "year": 2024,
                "paperUrl": "https://example.com/1",
                "pdfUrl": "https://example.com/1.pdf",
                "codeUrl": "https://github.com/example/1",
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["diffusion", "robot manipulation"],
                "primaryArea": "robotics",
                "hasPdf": True,
                "hasCode": True,
                "hasProject": False,
                "raw": {},
            },
            {
                "id": "2",
                "title": "Vision Transformers for Segmentation",
                "abstract": "Image segmentation with transformer backbones.",
                "authors": ["B"],
                "venue": "CVPR",
                "year": 2023,
                "paperUrl": "https://example.com/2",
                "pdfUrl": "https://example.com/2.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["vision", "segmentation"],
                "primaryArea": "computer vision",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
        ]

        response = run_paper_search("diffusion policy from CORL 2024 with code", papers)

        self.assertEqual(response["total"], 1)
        self.assertFalse(response["truncated"])
        self.assertEqual(response["results"][0]["paper"]["id"], "1")
        self.assertIn("title match", response["results"][0]["whyMatched"])

    def test_prefers_formal_venue_result_over_arxiv_when_query_is_local_search(self):
        papers = [
            {
                "id": "venue-paper",
                "title": "GeoLLM-Bench: Evaluating LLMs on Earth Science Data Tasks",
                "abstract": "A benchmark for LLM evaluation on earth science datasets.",
                "authors": ["A"],
                "venue": "CORL",
                "year": 2024,
                "paperUrl": "https://example.com/venue",
                "pdfUrl": "https://example.com/venue.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["earth science", "benchmark", "llm"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
            {
                "id": "arxiv-paper",
                "title": "GeoLLM-Bench for Earth Science",
                "abstract": "An arXiv preprint about benchmark datasets for LLMs.",
                "authors": ["B"],
                "venue": "ARXIV",
                "year": 2024,
                "paperUrl": "https://arxiv.org/abs/2401.12345",
                "pdfUrl": "https://arxiv.org/pdf/2401.12345.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["earth science", "benchmark", "llm"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
        ]

        response = run_paper_search(
            "find 2024 CORL earth science benchmark llm papers https://arxiv.org/abs/2401.12345",
            papers,
        )

        self.assertEqual(response["results"][0]["paper"]["id"], "venue-paper")

    def test_domain_expansion_finds_geoscience_match_from_seismology_query(self):
        papers = [
            {
                "id": "geo-1",
                "title": "GeoLLM-Bench: Evaluating Language Models for Earth Science Reasoning",
                "abstract": "We evaluate language models on geophysical and seismic reasoning tasks.",
                "authors": ["A"],
                "venue": "ICLR",
                "year": 2025,
                "paperUrl": "https://example.com/geo-1",
                "pdfUrl": "https://example.com/geo-1.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["earth science", "geophysics", "benchmark"],
                "primaryArea": "scientific reasoning",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
            {
                "id": "generic-1",
                "title": "LongGenBench: Benchmarking Long-Form Generation in LLMs",
                "abstract": "A generic benchmark for long-context language models.",
                "authors": ["B"],
                "venue": "COLING",
                "year": 2024,
                "paperUrl": "https://example.com/generic-1",
                "pdfUrl": "https://example.com/generic-1.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["llm", "benchmark"],
                "primaryArea": "language modeling",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
        ]

        response = run_paper_search("seismology large language model benchmark evaluation", papers)

        self.assertEqual(response["results"][0]["paper"]["id"], "geo-1")
        self.assertEqual(response["localStatus"], "strong")

    def test_classify_local_result_uses_eight_as_weak_cutoff(self):
        result = {
            "score": 9,
            "paper": {
                "title": "Seismology Paper",
                "abstract": "",
                "primaryArea": "",
                "keywords": [],
            },
        }
        concepts = [
            {
                "label": "seismology",
                "original": ["seismology"],
                "searchTerms": ["seismology"],
            }
        ]

        self.assertEqual(classify_local_result(result, concepts), "strong")

    def test_treats_score_above_eight_as_strong_local_match(self):
        papers = [
            {
                "id": "score-10-local",
                "title": "Seismology Foundation Models",
                "abstract": "Study of seismic modeling tasks.",
                "authors": ["A"],
                "venue": "ICLR",
                "year": 2025,
                "paperUrl": "https://example.com/score-10-local",
                "pdfUrl": "https://example.com/score-10-local.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["seismology"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            }
        ]

        response = run_paper_search("seismology", papers)

        self.assertEqual(response["results"][0]["paper"]["id"], "score-10-local")
        self.assertEqual(response["localStatus"], "strong")

    def test_marks_results_weak_when_only_domain_and_task_match_without_model_intent(self):
        papers = [
            {
                "id": "domain-task-only",
                "title": "OpenFWI: Large-scale Multi-structural Benchmark Datasets for Full Waveform Inversion",
                "abstract": "A benchmark for geophysical inversion tasks.",
                "authors": ["A"],
                "venue": "NIPS",
                "year": 2022,
                "paperUrl": "https://example.com/domain-task-only",
                "pdfUrl": "https://example.com/domain-task-only.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["geophysics", "benchmark"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            }
        ]

        response = run_paper_search("seismology large language model benchmark evaluation", papers)

        self.assertEqual(response["localStatus"], "weak")

        papers = [
            {
                "id": "bundle-hit",
                "title": "SeisBench-LM: Language Models for Seismology Question Answering",
                "abstract": "We evaluate language models on seismic benchmark and QA tasks.",
                "authors": ["A"],
                "venue": "ICLR",
                "year": 2025,
                "paperUrl": "https://example.com/bundle-hit",
                "pdfUrl": "https://example.com/bundle-hit.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["seismology", "benchmark", "llm", "qa"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
            {
                "id": "domain-only",
                "title": "Seismic Inversion with Diffusion Models",
                "abstract": "A geophysics paper about subsurface inversion.",
                "authors": ["B"],
                "venue": "ICML",
                "year": 2024,
                "paperUrl": "https://example.com/domain-only",
                "pdfUrl": "https://example.com/domain-only.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["seismic", "geophysics"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            },
        ]

        response = run_paper_search("seismology large language model benchmark evaluation", papers)

        self.assertEqual(response["results"][0]["paper"]["id"], "bundle-hit")

    def test_uses_fallback_when_query_bundle_finds_too_few_complete_local_matches(self):
        papers = [
            {
                "id": "domain-only",
                "title": "Seismic Inversion with Diffusion Models",
                "abstract": "A geophysics paper about subsurface inversion.",
                "authors": ["B"],
                "venue": "ICML",
                "year": 2024,
                "paperUrl": "https://example.com/domain-only",
                "pdfUrl": "https://example.com/domain-only.pdf",
                "codeUrl": None,
                "projectUrl": None,
                "source": "paperlists",
                "keywords": ["seismic", "geophysics"],
                "primaryArea": "earth science",
                "hasPdf": True,
                "hasCode": False,
                "hasProject": False,
                "raw": {},
            }
        ]

        def fake_fallback(query, limit):
            return [
                {
                    "paper": {
                        "id": "arxiv-1",
                        "title": "SeisBench-LM: Evaluating Language Models on Seismology Tasks",
                        "venue": "ARXIV",
                        "year": 2025,
                        "paperUrl": "https://arxiv.org/abs/2501.12345",
                        "pdfUrl": "https://arxiv.org/pdf/2501.12345.pdf",
                        "codeUrl": None,
                        "projectUrl": None,
                        "source": "arxiv-fallback",
                        "keywords": ["seismology", "benchmark"],
                        "primaryArea": "earth science",
                        "hasPdf": True,
                        "hasCode": False,
                        "hasProject": False,
                        "raw": {},
                    },
                    "score": 1,
                    "whyMatched": ["remote fallback match"],
                }
            ]

        response = run_paper_search(
            "seismology large language model benchmark evaluation",
            papers,
            fallback_search=fake_fallback,
        )

        self.assertEqual(response["localStatus"], "weak")
        self.assertTrue(response["fallbackUsed"])
        self.assertEqual(response["results"][0]["paper"]["source"], "arxiv-fallback")
        self.assertIn("Local coverage appears weak", response["warnings"][0])

    def test_remote_fallback_prefers_llm_planned_queries_over_shallow_bundle_only(self):
        papers = []
        fallback_queries = []

        def fake_fallback(query, limit):
            fallback_queries.append(query)
            normalized = query.lower()
            if all(term in normalized for term in ["seismology", "llm", "benchmark"]):
                return [
                    {
                        "paper": {
                            "id": "arxiv-seisbench-llm",
                            "title": "SeisBench-LLM: Benchmarking LLMs for Seismology",
                            "abstract": "A benchmark for large language models on seismology tasks.",
                            "venue": "ARXIV",
                            "year": 2025,
                            "paperUrl": "https://arxiv.org/abs/2501.99999",
                            "pdfUrl": "https://arxiv.org/pdf/2501.99999.pdf",
                            "codeUrl": None,
                            "projectUrl": None,
                            "source": "arxiv-fallback",
                            "keywords": ["seismology", "llm", "benchmark"],
                            "primaryArea": "earth science",
                            "hasPdf": True,
                            "hasCode": False,
                            "hasProject": False,
                            "raw": {},
                        },
                        "score": 1,
                        "whyMatched": ["remote fallback match"],
                    }
                ]
            if all(term in normalized for term in ["seismology", "large language model", "benchmark"]):
                return [
                    {
                        "paper": {
                            "id": "arxiv-seisbench-longform",
                            "title": "SeisBench-LM: Evaluating Language Models on Seismology Tasks",
                            "abstract": "Evaluation benchmark for language models in seismology.",
                            "venue": "ARXIV",
                            "year": 2025,
                            "paperUrl": "https://arxiv.org/abs/2501.12345",
                            "pdfUrl": "https://arxiv.org/pdf/2501.12345.pdf",
                            "codeUrl": None,
                            "projectUrl": None,
                            "source": "arxiv-fallback",
                            "keywords": ["seismology", "benchmark", "llm"],
                            "primaryArea": "earth science",
                            "hasPdf": True,
                            "hasCode": False,
                            "hasProject": False,
                            "raw": {},
                        },
                        "score": 1,
                        "whyMatched": ["remote fallback match"],
                    }
                ]
            return [
                {
                    "paper": {
                        "id": "arxiv-generic",
                        "title": "Generic LLM Benchmark",
                        "abstract": "A broad benchmark for language models.",
                        "venue": "ARXIV",
                        "year": 2024,
                        "paperUrl": "https://arxiv.org/abs/2400.00001",
                        "pdfUrl": "https://arxiv.org/pdf/2400.00001.pdf",
                        "codeUrl": None,
                        "projectUrl": None,
                        "source": "arxiv-fallback",
                        "keywords": ["benchmark", "llm"],
                        "primaryArea": "language modeling",
                        "hasPdf": True,
                        "hasCode": False,
                        "hasProject": False,
                        "raw": {},
                    },
                    "score": 1,
                    "whyMatched": ["remote fallback match"],
                }
            ]

        response = run_paper_search(
            "seismology large language model benchmark evaluation",
            papers,
            fallback_search=fake_fallback,
        )

        self.assertTrue(response["fallbackUsed"])
        self.assertEqual(response["results"][0]["paper"]["id"], "arxiv-seisbench-llm")
        self.assertTrue(any("llm benchmark seismology" in query.lower() for query in fallback_queries))


class ArxivFallbackBehaviorTest(unittest.TestCase):
    def test_default_arxiv_fallback_returns_empty_on_429(self):
        import paper_search

        original_urlopen = paper_search.urllib.request.urlopen

        def fake_urlopen(_url, timeout=20):
            raise urllib.error.HTTPError(_url, 429, "Too Many Requests", hdrs=None, fp=None)

        paper_search.urllib.request.urlopen = fake_urlopen
        try:
            self.assertEqual(default_arxiv_fallback_search("seismology llm benchmark", 3), [])
        finally:
            paper_search.urllib.request.urlopen = original_urlopen

    def test_reports_warning_when_remote_fallback_returns_empty(self):
        response = run_paper_search(
            "seismology large language model benchmark evaluation",
            papers=[],
            fallback_search=lambda query, limit: [],
        )

        self.assertEqual(response["localStatus"], "weak")
        self.assertFalse(response["fallbackUsed"])
        self.assertTrue(any("fallback" in warning.lower() for warning in response["warnings"]))


    def test_renders_summary_filters_and_match_reasons(self):
        output = format_paper_search_results(
            {
                "appliedFilters": {
                    "rawQuery": "diffusion policy from CORL 2024 with code",
                    "query": "diffusion policy",
                    "venues": ["CORL"],
                    "yearStart": 2024,
                    "yearEnd": 2024,
                    "hasCode": True,
                    "hasPdf": False,
                    "warnings": [],
                },
                "total": 1,
                "truncated": False,
                "warnings": [],
                "results": [
                    {
                        "score": 10,
                        "whyMatched": ["title match", "keyword match"],
                        "paper": {
                            "id": "1",
                            "title": "Diffusion Policy for Robot Manipulation",
                            "venue": "CORL",
                            "year": 2024,
                        },
                    }
                ],
            }
        )

        self.assertIn("| Year | Venue | Title | Abstract | Link |", output)
        self.assertIn("Diffusion Policy for Robot Manipulation", output)
        self.assertIn("title match, keyword match", output)

    def test_renders_local_coverage_warning_and_fallback_results(self):
        output = format_paper_search_results(
            {
                "appliedFilters": {
                    "rawQuery": "seismology large language model benchmark evaluation",
                    "query": "seismology large language model benchmark evaluation",
                    "venues": [],
                    "yearStart": None,
                    "yearEnd": None,
                    "hasCode": False,
                    "hasPdf": False,
                    "warnings": [],
                },
                "total": 1,
                "truncated": False,
                "warnings": ["Local coverage appears weak for this query; showing arXiv fallback results."],
                "localStatus": "weak",
                "fallbackUsed": True,
                "results": [
                    {
                        "score": 1,
                        "whyMatched": ["remote fallback match"],
                        "paper": {
                            "id": "arxiv-1",
                            "title": "SeisBench-LM: Evaluating Language Models on Seismology Tasks",
                            "venue": "ARXIV",
                            "year": 2025,
                            "source": "arxiv-fallback",
                        },
                    }
                ],
            }
        )

        self.assertIn("Local status: weak", output)
        self.assertIn("Fallback: arXiv", output)
        self.assertIn("Warnings: Local coverage appears weak for this query; showing arXiv fallback results.", output)


if __name__ == "__main__":
    unittest.main()
