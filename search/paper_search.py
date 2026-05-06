import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

KNOWN_VENUES = ["AAAI", "ACL", "AI4X", "EMNLP", "ICCV", "ICLR", "ICML", "IJCAI", "KDD", "NIPS", "WWW"]
DEFAULT_LIMIT = 5
PATH_PATTERN = re.compile(r"journal/([^/]+)/\1(\d{4})\.json$", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
GENERIC_QUERY_TERMS = {
    "find",
    "search",
    "paper",
    "papers",
    "related",
    "about",
    "论文",
    "相关论文",
}
STOPWORDS = {"the", "a", "an", "for", "of", "and", "or", "to", "in", "on", "at", "by"}
CONCEPT_ALIAS_GROUPS = [
    ["large language model", "language model", "foundation model", "llm"],
    ["benchmark", "evaluation"],
    ["question answering", "qa"],
    ["vision language action", "vla"],
    ["vision language model", "vlm"],
]
GENERIC_CONCEPT_LABELS = {
    "large language model",
    "language model",
    "foundation model",
    "llm",
    "benchmark",
    "evaluation",
    "question answering",
    "qa",
}
TERM_EXPANSIONS = {
    "seismology": ["seismic", "geophysics", "earth science", "earthquake"],
    "earthquake": ["seismic", "seismology", "geophysics"],
    "geoscience": ["earth science", "geophysics", "subsurface"],
    "geophysical": ["geophysics", "earth science", "seismic"],
    "vla": ["vision language action"],
    "vlm": ["vision language model"],
    "qa": ["question answering"],
    "medical": ["medicine", "clinical", "healthcare"],
}
WEAK_SCORE_THRESHOLD = 8
BUNDLE_SCORE_BONUS = 3
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_MAX_RETRIES = 3
ARXIV_RETRY_BASE_SECONDS = 1.0
ARXIV_QUERY_CACHE_TTL_SECONDS = 1800
ARXIV_QUERY_CACHE: dict[tuple[str, int], tuple[float, list[dict[str, Any]]]] = {}
FallbackSearch = Callable[[str, int], list[dict[str, Any]]]


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_whitespace(value.lower())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def parse_paper_search_query(raw_query: str) -> dict[str, Any]:
    warnings: list[str] = []
    working = normalize_whitespace(raw_query)
    working = normalize_whitespace(URL_PATTERN.sub(" ", working))
    year_start = None
    year_end = None

    range_match = re.search(r"\b(19\d{2}|20\d{2})\s*[-–—]\s*(19\d{2}|20\d{2})\b", working, re.IGNORECASE)
    if range_match:
        year_start = int(range_match.group(1))
        year_end = int(range_match.group(2))
        working = normalize_whitespace(working.replace(range_match.group(0), " "))
    else:
        exact_year_match = re.search(r"\b(19\d{2}|20\d{2})\b", working)
        if exact_year_match:
            year_start = int(exact_year_match.group(1))
            year_end = year_start
            working = normalize_whitespace(working.replace(exact_year_match.group(0), " "))

    venues: list[str] = []
    for venue in KNOWN_VENUES:
        if re.search(rf"\b{re.escape(venue)}\b", working, re.IGNORECASE):
            venues.append(venue)
            working = normalize_whitespace(re.sub(rf"\b(?:from|in)?\s*{re.escape(venue)}\b", " ", working, flags=re.IGNORECASE))

    has_code = bool(re.search(r"\b(with|has)\s+code\b", working, re.IGNORECASE))
    if has_code:
        working = normalize_whitespace(re.sub(r"\b(with|has)\s+code\b", " ", working, flags=re.IGNORECASE))

    has_pdf = bool(re.search(r"\b(with|has)\s+pdf\b", working, re.IGNORECASE))
    if has_pdf:
        working = normalize_whitespace(re.sub(r"\b(with|has)\s+pdf\b", " ", working, flags=re.IGNORECASE))

    tokens = [token for token in working.split() if token.lower() not in GENERIC_QUERY_TERMS]
    working = normalize_whitespace(" ".join(tokens))

    if not working:
        warnings.append("Query text was empty after parsing filters.")

    return {
        "rawQuery": raw_query,
        "query": working,
        "venues": venues,
        "yearStart": year_start,
        "yearEnd": year_end,
        "hasCode": has_code,
        "hasPdf": has_pdf,
        "warnings": warnings,
    }


def infer_venue_year_from_path(file_path: str) -> tuple[str, int]:
    normalized = file_path.replace("\\", "/")
    match = PATH_PATTERN.search(normalized)
    if not match:
        raise ValueError(f"Unable to infer venue/year from path: {file_path}")
    return match.group(1).upper(), int(match.group(2))


def split_author_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    delimiter = ";" if ";" in value else ","
    return [item.strip() for item in value.split(delimiter) if item.strip()]


def split_semicolon_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def as_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("github.com/"):
        return f"https://{value}"
    return value


def first_url(record: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = normalize_url(as_string(record.get(key)))
        if value:
            return value
    return None


def canonical_id(record: dict[str, Any], venue: str, year: int) -> str:
    return (
        as_string(record.get("id"))
        or as_string(record.get("pid"))
        or as_string(record.get("ssid"))
        or as_string(record.get("psid"))
        or f"{venue}-{year}-{as_string(record.get('title')) or 'unknown'}"
    )


def normalize_paper_record(record: dict[str, Any], file_path: str) -> dict[str, Any]:
    venue, year = infer_venue_year_from_path(file_path)
    paper_url = first_url(record, ["site", "oa", "url_paper", "openreview", "proceeding", "url"])
    pdf_url = first_url(record, ["pdf", "pdf_url"])
    code_url = first_url(record, ["github", "code", "code_url"])
    project_url = first_url(record, ["project", "project_url"])
    supplementary_url = first_url(record, ["supplementary_material", "supp"])

    return {
        "id": canonical_id(record, venue, year),
        "title": as_string(record.get("title")) or "Untitled Paper",
        "abstract": as_string(record.get("abstract")) or "",
        "authors": split_author_list(record.get("author") or record.get("authors")),
        "venue": venue,
        "year": year,
        "paperUrl": paper_url,
        "pdfUrl": pdf_url,
        "codeUrl": code_url,
        "projectUrl": project_url,
        "supplementaryUrl": supplementary_url,
        "source": "paperlists",
        "keywords": split_semicolon_list(record.get("keywords")),
        "primaryArea": as_string(record.get("primary_area")),
        "hasPdf": pdf_url is not None,
        "hasCode": code_url is not None,
        "hasProject": project_url is not None,
        "raw": record,
    }


def dedupe_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for paper in papers:
        key = f"{paper['venue']}:{paper['year']}:{paper['title'].strip().lower()}"
        existing = deduped.get(key)
        if not existing:
            deduped[key] = paper
            continue
        deduped[key] = {
            **existing,
            "paperUrl": existing["paperUrl"] or paper["paperUrl"],
            "pdfUrl": existing["pdfUrl"] or paper["pdfUrl"],
            "codeUrl": existing["codeUrl"] or paper["codeUrl"],
            "projectUrl": existing["projectUrl"] or paper["projectUrl"],
            "supplementaryUrl": existing["supplementaryUrl"] or paper["supplementaryUrl"],
            "raw": {**existing["raw"], **paper["raw"]},
        }
    return list(deduped.values())


def load_all_papers(journal_root: str | None = None) -> list[dict[str, Any]]:
    root = Path(journal_root) if journal_root else Path(__file__).resolve().parent / "journal"
    papers: list[dict[str, Any]] = []
    for file_path in sorted(root.rglob("*.json")):
        records = json.loads(file_path.read_text(encoding="utf-8"))
        papers.extend(normalize_paper_record(record, str(file_path)) for record in records)
    return dedupe_papers(papers)


def tokenize(query: str) -> list[str]:
    return [token.strip() for token in query.lower().split() if token.strip()]


def field_includes(value: str | None, token: str) -> bool:
    return token in (value or "").lower()


def list_includes(values: list[str], token: str) -> bool:
    return any(token in value.lower() for value in values)


def is_preprint_venue(venue: str) -> bool:
    return venue.upper() in {"ARXIV", "PREPRINT"}


def expand_query_terms(query: str) -> tuple[list[str], set[str], set[str]]:
    base_tokens = tokenize(query)
    expanded_tokens = list(base_tokens)
    domain_tokens: set[str] = set()
    generic_tokens: set[str] = set()
    seen = set(base_tokens)
    query_lower = query.lower()

    for term, expansions in TERM_EXPANSIONS.items():
        if term not in query_lower and term not in seen:
            continue
        domain_tokens.add(term)
        for expansion in expansions:
            if expansion not in seen:
                expanded_tokens.append(expansion)
                seen.add(expansion)
            domain_tokens.add(expansion)

    for token in base_tokens:
        if token in GENERIC_QUERY_TERMS or token in STOPWORDS:
            continue
        if token in {"benchmark", "evaluation", "qa", "dataset"}:
            generic_tokens.add(token)
        else:
            domain_tokens.add(token)

    return expanded_tokens, domain_tokens, generic_tokens


def extract_query_concepts(query: str) -> list[dict[str, Any]]:
    working = normalize_whitespace(query.lower())
    concepts: list[dict[str, Any]] = []

    for group in CONCEPT_ALIAS_GROUPS:
        present = [phrase for phrase in group if re.search(rf"\b{re.escape(phrase)}\b", working)]
        if not present:
            continue
        primary = max(present, key=len)
        concepts.append({
            "label": primary,
            "original": [primary],
            "searchTerms": dedupe_strings([primary, *group]),
        })
        for phrase in group:
            working = re.sub(rf"\b{re.escape(phrase)}\b", " ", working)
        working = normalize_whitespace(working)

    for token in tokenize(working):
        if token in GENERIC_QUERY_TERMS or token in STOPWORDS:
            continue
        concepts.append({
            "label": token,
            "original": [token],
            "searchTerms": dedupe_strings([token, *TERM_EXPANSIONS.get(token, [])]),
        })

    deduped: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for concept in concepts:
        if concept["label"] in seen_labels:
            continue
        seen_labels.add(concept["label"])
        deduped.append(concept)
    return deduped


def build_query_bundles(query: str, concepts: list[dict[str, Any]]) -> list[str]:
    bundles = [normalize_whitespace(query)] if normalize_whitespace(query) else []
    canonical_terms = [concept["searchTerms"][0] for concept in concepts if concept["searchTerms"]]
    canonical = normalize_whitespace(" ".join(canonical_terms))
    if canonical and canonical not in bundles:
        bundles.append(canonical)

    for index, concept in enumerate(concepts):
        for variant in concept["searchTerms"][1:3]:
            terms = canonical_terms[:]
            terms[index] = variant
            bundle = normalize_whitespace(" ".join(terms))
            if bundle and bundle not in bundles:
                bundles.append(bundle)

    return bundles[:8]


def build_remote_query_bundles(query: str, concepts: list[dict[str, Any]]) -> list[str]:
    bundles = build_query_bundles(query, concepts)
    remote_terms = []
    for concept in concepts:
        search_terms = concept.get("searchTerms") or []
        if "llm" in search_terms:
            remote_terms.append("llm")
        elif "benchmark" in search_terms:
            remote_terms.append("benchmark")
        elif search_terms:
            remote_terms.append(search_terms[0])

    compact_bundle = normalize_whitespace(" ".join(remote_terms))
    if compact_bundle and compact_bundle not in bundles:
        bundles.insert(0, compact_bundle)
    return bundles[:10]


def score_paper(paper: dict[str, Any], tokens: list[str], filters: dict[str, Any]) -> int:
    score = 0
    for token in tokens:
        if field_includes(paper["title"], token):
            score += 6
        if list_includes(paper["keywords"], token):
            score += 4
        if field_includes(paper["abstract"], token):
            score += 2
        if field_includes(paper.get("primaryArea"), token):
            score += 2
        if field_includes(paper["venue"], token):
            score += 1
    if filters.get("venues") and paper["venue"] in filters["venues"]:
        score += 12
    if filters.get("yearStart") and filters.get("yearEnd") and filters["yearStart"] == filters["yearEnd"] and paper["year"] == filters["yearStart"]:
        score += 8
    if is_preprint_venue(paper["venue"]):
        score -= 8
    return score


def build_explanation(paper: dict[str, Any], tokens: list[str], filters: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if filters.get("venues") and paper["venue"] in filters["venues"]:
        reasons.append("venue match")
    if filters.get("yearStart") and filters.get("yearEnd") and filters["yearStart"] == filters["yearEnd"] and paper["year"] == filters["yearStart"]:
        reasons.append("year match")
    if any(field_includes(paper["title"], token) for token in tokens):
        reasons.append("title match")
    if any(list_includes(paper["keywords"], token) for token in tokens):
        reasons.append("keyword match")
    if any(field_includes(paper["abstract"], token) for token in tokens):
        reasons.append("abstract match")
    if any(field_includes(paper.get("primaryArea"), token) for token in tokens):
        reasons.append("primary area match")
    return reasons


def matches_filters(paper: dict[str, Any], filters: dict[str, Any]) -> bool:
    if filters.get("venues") and paper["venue"] not in filters["venues"]:
        return False
    if filters.get("yearStart") and paper["year"] < filters["yearStart"]:
        return False
    if filters.get("yearEnd") and paper["year"] > filters["yearEnd"]:
        return False
    if filters.get("hasCode") and not paper["hasCode"]:
        return False
    if filters.get("hasPdf") and not paper["hasPdf"]:
        return False
    return True


def paper_text_fields(paper: dict[str, Any]) -> dict[str, str]:
    return {
        "title": (paper.get("title") or "").lower(),
        "abstract": (paper.get("abstract") or "").lower(),
        "primaryArea": (paper.get("primaryArea") or "").lower(),
        "keywords": " ".join(paper.get("keywords") or []).lower(),
        "venue": (paper.get("venue") or "").lower(),
    }


def paper_matches_terms(paper: dict[str, Any], terms: list[str]) -> bool:
    fields = paper_text_fields(paper)
    searchable = [fields["title"], fields["abstract"], fields["primaryArea"], fields["keywords"]]
    return any(any(term in value for value in searchable) for term in terms)


def matches_non_generic_concept(paper: dict[str, Any], concepts: list[dict[str, Any]]) -> bool:
    non_generic_concepts = [concept for concept in concepts if concept["label"] not in GENERIC_CONCEPT_LABELS]
    if not non_generic_concepts:
        return True
    return any(
        paper_matches_terms(paper, concept.get("searchTerms") or concept.get("original") or [])
        for concept in non_generic_concepts
    )


def classify_local_result(result: dict[str, Any], concepts: list[dict[str, Any]]) -> str:
    if result["score"] < WEAK_SCORE_THRESHOLD:
        return "weak"

    paper_fields = paper_text_fields(result["paper"])
    matched_groups = 0
    matched_domain_groups = 0
    for concept in concepts:
        search_terms = concept.get("searchTerms") or concept.get("original") or []
        if not search_terms:
            continue

        title_or_keywords_match = any(
            term in paper_fields["title"] or term in paper_fields["keywords"]
            for term in search_terms
        )
        abstract_or_area_match = any(
            term in paper_fields["abstract"] or term in paper_fields["primaryArea"]
            for term in search_terms
        )

        if title_or_keywords_match:
            matched_groups += 1
            if concept["label"] not in GENERIC_CONCEPT_LABELS:
                matched_domain_groups += 1
            continue

        if abstract_or_area_match and concept["label"] not in GENERIC_CONCEPT_LABELS:
            matched_groups += 1
            matched_domain_groups += 1

    required_groups = min(len(concepts), 3) if concepts else 1
    if matched_groups < required_groups:
        return "weak"
    if any(concept["label"] not in GENERIC_CONCEPT_LABELS for concept in concepts) and matched_domain_groups == 0:
        return "weak"
    return "strong"


def merge_query_result(existing: dict[str, Any] | None, candidate: dict[str, Any], bundle: str) -> dict[str, Any]:
    if not existing:
        return {
            "paper": candidate["paper"],
            "score": candidate["score"],
            "whyMatched": list(candidate["whyMatched"]),
            "matchedQueries": [bundle],
        }

    return {
        "paper": candidate["paper"],
        "score": existing["score"] + candidate["score"],
        "whyMatched": list(dict.fromkeys(existing["whyMatched"] + candidate["whyMatched"])),
        "matchedQueries": existing["matchedQueries"] + ([bundle] if bundle not in existing["matchedQueries"] else []),
    }


def search_bundle_once(papers: list[dict[str, Any]], filters: dict[str, Any], bundle: str, concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bundle_filters = {**filters, "query": bundle}
    tokens = tokenize(bundle)
    results = []
    for paper in papers:
        if not matches_filters(paper, bundle_filters):
            continue
        if not matches_non_generic_concept(paper, concepts):
            continue
        score = score_paper(paper, tokens, bundle_filters)
        if score <= 0:
            continue
        results.append({"paper": paper, "score": score, "whyMatched": build_explanation(paper, tokens, bundle_filters)})
    return results


def search_papers(papers: list[dict[str, Any]], filters: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    concepts = extract_query_concepts(filters["query"])
    bundles = build_query_bundles(filters["query"], concepts)
    combined: dict[str, dict[str, Any]] = {}

    for bundle in bundles:
        for candidate in search_bundle_once(papers, filters, bundle, concepts):
            paper_id = candidate["paper"]["id"]
            combined[paper_id] = merge_query_result(combined.get(paper_id), candidate, bundle)

    strong_results = []
    weak_results = []
    for merged in combined.values():
        result = {
            "paper": merged["paper"],
            "score": merged["score"] + len(merged["matchedQueries"]) * BUNDLE_SCORE_BONUS,
            "whyMatched": merged["whyMatched"] + ([f"matched {len(merged['matchedQueries'])} query bundles"] if len(merged["matchedQueries"]) > 1 else []),
        }
        if classify_local_result(result, concepts) == "strong":
            strong_results.append(result)
        else:
            weak_results.append(result)

    sorter = lambda result: (-result["score"], -result["paper"]["year"], result["paper"]["venue"] == "ARXIV")
    return {
        "strong": sorted(strong_results, key=sorter),
        "weak": sorted(weak_results, key=sorter),
    }


def merge_remote_result(existing: dict[str, Any] | None, candidate: dict[str, Any], bundle: str) -> dict[str, Any]:
    if not existing:
        return {
            "paper": candidate["paper"],
            "score": candidate.get("score", 0),
            "whyMatched": list(candidate.get("whyMatched", [])),
            "matchedQueries": [bundle],
        }

    return {
        "paper": existing["paper"],
        "score": max(existing["score"], candidate.get("score", 0)),
        "whyMatched": list(dict.fromkeys(existing["whyMatched"] + candidate.get("whyMatched", []))),
        "matchedQueries": existing["matchedQueries"] + ([bundle] if bundle not in existing["matchedQueries"] else []),
    }


def score_remote_result(result: dict[str, Any], concepts: list[dict[str, Any]]) -> int:
    concept_matches = 0
    non_generic_matches = 0
    llm_alias_match = 0
    compact_semantic_query_match = 0

    for concept in concepts:
        search_terms = concept.get("searchTerms") or concept.get("original") or []
        if not search_terms or not paper_matches_terms(result["paper"], search_terms):
            continue
        concept_matches += 1
        if concept["label"] not in GENERIC_CONCEPT_LABELS:
            non_generic_matches += 1
        if "llm" in search_terms and paper_matches_terms(result["paper"], ["llm"]):
            llm_alias_match = 1

    non_generic_labels = [concept["label"] for concept in concepts if concept["label"] not in GENERIC_CONCEPT_LABELS]
    for query in result.get("matchedQueries", []):
        normalized = query.strip().lower()
        if "llm" in normalized and any(label in normalized for label in non_generic_labels):
            compact_semantic_query_match = 1
            break

    base_score = result.get("score", 0)
    return base_score + concept_matches * 10 + non_generic_matches * 20 + llm_alias_match * 7 + compact_semantic_query_match * 15


def run_remote_fallback_search(
    query: str,
    limit: int,
    fallback_search: FallbackSearch,
) -> list[dict[str, Any]]:
    concepts = extract_query_concepts(query)
    bundles = build_remote_query_bundles(query, concepts)
    combined: dict[str, dict[str, Any]] = {}

    for bundle in bundles:
        for candidate in fallback_search(bundle, limit):
            paper = candidate.get("paper") or {}
            paper_id = paper.get("id") or paper.get("paperUrl") or paper.get("title")
            if not paper_id:
                continue
            combined[paper_id] = merge_remote_result(combined.get(paper_id), candidate, bundle)

    ranked = []
    for merged in combined.values():
        ranked.append(
            {
                "paper": merged["paper"],
                "score": score_remote_result(merged, concepts) + len(merged["matchedQueries"]) * BUNDLE_SCORE_BONUS,
                "whyMatched": merged["whyMatched"] + ([f"matched {len(merged['matchedQueries'])} query bundles"] if len(merged["matchedQueries"]) > 1 else []),
            }
        )

    sorter = lambda result: (-result["score"], -result["paper"].get("year", 0), result["paper"].get("venue") == "ARXIV")
    return sorted(ranked, key=sorter)[:limit]


def default_arxiv_fallback_search(query: str, limit: int) -> list[dict[str, Any]]:
    cache_key = (normalize_whitespace(query.lower()), limit)
    now = time.time()
    cached = ARXIV_QUERY_CACHE.get(cache_key)
    if cached and now - cached[0] <= ARXIV_QUERY_CACHE_TTL_SECONDS:
        return cached[1]

    encoded = urllib.parse.quote(query)
    url = f"{ARXIV_API_URL}?search_query=all:{encoded}&start=0&max_results={limit}"

    payload = None
    for attempt in range(ARXIV_MAX_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                payload = response.read()
            break
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < ARXIV_MAX_RETRIES - 1:
                time.sleep(ARXIV_RETRY_BASE_SECONDS * (2**attempt))
                continue
            ARXIV_QUERY_CACHE[cache_key] = (time.time(), [])
            return []
        except Exception:
            ARXIV_QUERY_CACHE[cache_key] = (time.time(), [])
            return []

    if payload is None:
        ARXIV_QUERY_CACHE[cache_key] = (time.time(), [])
        return []

    root = ET.fromstring(payload)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    results: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", namespace):
        entry_id = (entry.findtext("atom:id", default="", namespaces=namespace) or "").strip()
        title = normalize_whitespace(entry.findtext("atom:title", default="", namespaces=namespace) or "Untitled Paper")
        summary = normalize_whitespace(entry.findtext("atom:summary", default="", namespaces=namespace) or "")
        published = (entry.findtext("atom:published", default="", namespaces=namespace) or "")[:4]
        pdf_url = None
        for link in entry.findall("atom:link", namespace):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")
                break
        results.append(
            {
                "paper": {
                    "id": entry_id or title,
                    "title": title,
                    "abstract": summary,
                    "authors": [],
                    "venue": "ARXIV",
                    "year": int(published) if published.isdigit() else 0,
                    "paperUrl": entry_id or None,
                    "pdfUrl": pdf_url,
                    "codeUrl": None,
                    "projectUrl": None,
                    "source": "arxiv-fallback",
                    "keywords": [],
                    "primaryArea": None,
                    "hasPdf": pdf_url is not None,
                    "hasCode": False,
                    "hasProject": False,
                    "raw": {},
                },
                "score": 1,
                "whyMatched": ["remote fallback match"],
            }
        )

    ARXIV_QUERY_CACHE[cache_key] = (time.time(), results)
    return results


def run_paper_search(
    raw_query: str,
    papers: list[dict[str, Any]],
    limit: int = DEFAULT_LIMIT,
    fallback_search: FallbackSearch | None = None,
) -> dict[str, Any]:
    applied_filters = parse_paper_search_query(raw_query)
    local_results = search_papers(papers, applied_filters) if applied_filters["query"] else {"strong": [], "weak": []}
    strong_results = local_results["strong"]
    weak_results = local_results["weak"]
    warnings = list(applied_filters["warnings"])
    fallback_used = False
    local_status = "strong" if strong_results else "weak"
    final_results = strong_results[:limit] if strong_results else weak_results[:limit]

    if not strong_results and fallback_search and applied_filters["query"]:
        fallback_results = run_remote_fallback_search(raw_query, limit, fallback_search)
        if fallback_results:
            fallback_used = True
            warnings.append("Local coverage appears weak for this query; showing arXiv fallback results.")
            final_results = fallback_results
        else:
            warnings.append("Local coverage is weak and remote fallback returned no results (possibly rate-limited).")

    return {
        "appliedFilters": applied_filters,
        "total": len(final_results),
        "results": final_results,
        "strongLocalResults": strong_results[:limit],
        "weakLocalResults": weak_results[:limit],
        "truncated": (len(strong_results) if strong_results else len(weak_results)) > limit,
        "warnings": warnings,
        "localStatus": local_status,
        "fallbackUsed": fallback_used,
    }


def format_filters(response: dict[str, Any]) -> str:
    filters: list[str] = []
    applied_filters = response["appliedFilters"]
    if applied_filters["venues"]:
        filters.append(f"venue={','.join(applied_filters['venues'])}")
    if applied_filters["yearStart"] and applied_filters["yearEnd"]:
        if applied_filters["yearStart"] == applied_filters["yearEnd"]:
            filters.append(f"year={applied_filters['yearStart']}")
        else:
            filters.append(f"year={applied_filters['yearStart']}-{applied_filters['yearEnd']}")
    if applied_filters["hasCode"]:
        filters.append("hasCode=yes")
    if applied_filters["hasPdf"]:
        filters.append("hasPdf=yes")
    return f"Filters: {'; '.join(filters)}" if filters else "Filters: none"


def markdown_escape(value: str) -> str:
    return normalize_whitespace(value).replace("|", "\\|")


def truncate_text(value: str, limit: int = 180) -> str:
    text = normalize_whitespace(value)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def best_paper_link(paper: dict[str, Any]) -> str:
    return paper.get("paperUrl") or paper.get("pdfUrl") or ""


def format_paper_search_results(response: dict[str, Any]) -> str:
    query = response["appliedFilters"]["query"]
    summary = f"Found {response['total']} paper{'s' if response['total'] != 1 else ''}{f' for: {query}' if query else ''}"
    warnings = f"Warnings: {'; '.join(response['warnings'])}" if response["warnings"] else None
    local_status = f"Local status: {response['localStatus']}" if "localStatus" in response else None
    fallback = "Fallback: arXiv" if response.get("fallbackUsed") else None

    if response["results"]:
        rows = [
            "| Year | Venue | Title | Abstract | Link | Why |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for result in response["results"]:
            paper = result["paper"]
            year = str(paper.get("year") or "")
            venue = markdown_escape(str(paper.get("venue") or ""))
            title = markdown_escape(str(paper.get("title") or ""))
            abstract = markdown_escape(truncate_text(str(paper.get("abstract") or ""), 180))
            link = best_paper_link(paper)
            link_text = f"[link]({link})" if link else ""
            why = markdown_escape(", ".join(result.get("whyMatched") or ["score match"]))
            rows.append(f"| {year} | {venue} | {title} | {abstract} | {link_text} | {why} |")
        results = "\n".join(rows)
    else:
        results = "No matching papers found."

    return "\n\n".join(part for part in [summary, format_filters(response), local_status, fallback, warnings, results] if part)


def write_markdown_report(markdown_output: str) -> Path:
    output_path = Path(__file__).resolve().parent / "outputs" / "latest_search_results.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown_output + "\n", encoding="utf-8")
    return output_path


def run_cli(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    journal_root = None
    query_parts: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--journal-root":
            index += 1
            if index >= len(args):
                raise ValueError("--journal-root requires a value.")
            journal_root = args[index]
        else:
            query_parts.append(arg)
        index += 1

    query = " ".join(query_parts).strip()
    if not query:
        raise ValueError("A natural-language paper search query is required.")

    output = format_paper_search_results(
        run_paper_search(
            query,
            load_all_papers(journal_root),
            fallback_search=default_arxiv_fallback_search,
        )
    )
    report_path = write_markdown_report(output)
    sys.stdout.write(f"{output}\n\nSaved markdown report: {report_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
