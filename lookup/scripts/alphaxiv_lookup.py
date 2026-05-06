#!/usr/bin/env python3
import argparse
import csv
import html
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"


ALPHAXIV_STATUS_VALUES = {
    "available",
    "thin",
    "no_report",
    "rate_limited",
    "not_found",
    "upstream_error",
    "http_error",
    "network_error",
    "unavailable",
}


ARXIV_STATUS_VALUES = {"available", "unavailable", "unknown"}


SUMMARY_SOURCE_VALUES = {
    "alphaxiv_report",
    "alphaxiv_description",
    "arxiv_abstract",
    "none",
}


PROBLEM_HINTS = (
    "problem",
    "challenge",
    "task",
    "goal",
    "aim",
    "focus",
    "gap",
    "bottleneck",
    "limitation",
    "existing",
    "address",
    "solve",
)


METHOD_HINTS = (
    "we propose",
    "we present",
    "we introduce",
    "our method",
    "our approach",
    "framework",
    "method",
    "approach",
    "algorithm",
    "model",
    "system",
    "pipeline",
    "architecture",
    "uses",
    "combines",
    "consists of",
    "built on",
    "trained",
)


RESULT_HINTS = (
    "results",
    "show",
    "demonstrate",
    "outperform",
    "improve",
    "achieve",
    "benchmark",
    "evaluation",
    "ablation",
    "experiment",
)


OBVIOUS_INPUT_COLUMN_NAMES = {
    "paper",
    "paperid",
    "paperurl",
    "arxiv",
    "arxivid",
    "arxivurl",
    "url",
    "link",
}


class InputFileError(ValueError):
    pass


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = text.replace("\r", "")
    text = re.sub(r"\\n", "\n", text)
    text = strip_html_tags(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_alpha_description(text: Optional[str]) -> str:
    text = clean_text(text)
    if not text:
        return ""
    text = re.sub(r"^View recent discussion\.?\s*", "", text, flags=re.I)
    text = re.sub(r"^Abstract:\s*", "", text, flags=re.I)
    text = re.sub(r"^Summary:\s*", "", text, flags=re.I)
    return text.strip()


def unique_preserve(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def sentence_key(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def sentence_candidates(text: Optional[str]) -> List[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    cleaned = re.sub(r"[•·▪◦]", "\n", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    candidates: List[str] = []
    for block in cleaned.split("\n"):
        block = block.strip(" -*\t")
        if not block:
            continue
        parts = re.split(r"(?<=[.!?])\s+|;\s+(?=[A-Z0-9])", block)
        for part in parts:
            part = clean_text(part)
            part = re.sub(r"^(abstract|summary|overview)\s*:\s*", "", part, flags=re.I)
            part = part.strip(" -*\t")
            if part:
                candidates.append(part)
    return unique_preserve(candidates)


def truncate_text(text: str, max_chars: int) -> str:
    text = clean_text(text)
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    if len(text) <= max_chars:
        return text
    clipped = text[: max_chars + 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return (clipped or text[:max_chars].rstrip(" ,;:")) + "…"


def pick_matching_sentence(sentences: List[str], used: set, hints: Tuple[str, ...]) -> str:
    for sentence in sentences:
        key = sentence_key(sentence)
        if key in used:
            continue
        lowered = sentence.lower()
        if any(hint in lowered for hint in hints):
            used.add(key)
            return sentence
    return ""


def pick_unused_sentence(sentences: List[str], used: set, skip_hints: Tuple[str, ...] = ()) -> str:
    for sentence in sentences:
        key = sentence_key(sentence)
        if key in used:
            continue
        lowered = sentence.lower()
        if skip_hints and any(hint in lowered for hint in skip_hints):
            continue
        used.add(key)
        return sentence
    return ""


def brief_sentence_pool(result: Dict[str, object]) -> List[str]:
    texts = [
        str(result.get("best_summary", "")),
        str(result.get("arxiv_abstract", "")),
        str(result.get("alphaxiv_report", "")),
        str(result.get("alphaxiv_description", "")),
    ]
    sentences: List[str] = []
    seen = set()
    for text in texts:
        for sentence in sentence_candidates(text):
            key = sentence_key(sentence)
            if key and key not in seen:
                seen.add(key)
                sentences.append(sentence)
    return sentences


def brief_takeaway(result: Dict[str, object], sentences: List[str]) -> str:
    if sentences:
        return truncate_text(sentences[0], 180)
    if result.get("title"):
        return "Only title-level metadata was retrieved; no summary text was available."
    return "No usable paper summary was retrieved."


def brief_problem(result: Dict[str, object], sentences: List[str], used: set) -> str:
    sentence = pick_matching_sentence(sentences, used, PROBLEM_HINTS) or pick_unused_sentence(sentences, used)
    if sentence:
        return truncate_text(sentence, 200)
    if result.get("best_summary"):
        return truncate_text(str(result.get("best_summary", "")), 200)
    return "Not clearly stated in the retrieved source text."


def brief_method_points(sentences: List[str], used: set) -> List[str]:
    selected: List[str] = []
    selected_keys = set()

    def add_sentence(sentence: str) -> None:
        key = sentence_key(sentence)
        if not sentence or key in selected_keys:
            return
        selected.append(truncate_text(sentence, 160))
        selected_keys.add(key)

    for sentence in sentences:
        if len(selected) >= 4:
            break
        key = sentence_key(sentence)
        if key in used:
            continue
        lowered = sentence.lower()
        if any(hint in lowered for hint in METHOD_HINTS):
            used.add(key)
            add_sentence(sentence)

    for sentence in sentences:
        if len(selected) >= 2:
            break
        key = sentence_key(sentence)
        if key in used:
            continue
        lowered = sentence.lower()
        if any(hint in lowered for hint in RESULT_HINTS):
            continue
        used.add(key)
        add_sentence(sentence)

    for sentence in sentences:
        if len(selected) >= 2:
            break
        key = sentence_key(sentence)
        if key in used:
            continue
        used.add(key)
        add_sentence(sentence)

    return selected


def brief_reading_verdict(result: Dict[str, object]) -> str:
    summary_source = str(result.get("summary_source", "none"))
    alphaxiv_status = str(result.get("alphaxiv_status", "unavailable"))
    if summary_source == "alphaxiv_report":
        return "Yes for fast triage; a detailed alphaXiv report is available."
    if summary_source == "alphaxiv_description" and result.get("arxiv_abstract"):
        return "Maybe; alphaXiv is thin, but the arXiv abstract fills in the basics."
    if summary_source == "arxiv_abstract":
        if alphaxiv_status in {"thin", "no_report"}:
            return "Abstract-first; alphaXiv was thin, so this brief relies on arXiv."
        return "Abstract-first; this brief relies on the arXiv fallback."
    if result.get("best_summary"):
        return "Maybe; there is enough text here for a quick first pass."
    return "Hard to judge; only limited metadata was retrieved."


def brief_source_line(result: Dict[str, object]) -> str:
    summary_source = str(result.get("summary_source", "none"))
    alphaxiv_status = str(result.get("alphaxiv_status", "unavailable"))
    arxiv_status = str(result.get("arxiv_status", "unknown"))

    if summary_source == "alphaxiv_report":
        return "Source: alphaXiv report. Confidence: higher."
    if summary_source == "alphaxiv_description":
        if arxiv_status == "available":
            return f"Source: alphaXiv overview + arXiv abstract cross-check. Confidence: medium (alphaXiv: {alphaxiv_status})."
        return f"Source: alphaXiv overview only. Confidence: medium (alphaXiv: {alphaxiv_status})."
    if summary_source == "arxiv_abstract":
        return f"Source: arXiv abstract fallback. Confidence: basic (alphaXiv: {alphaxiv_status})."
    return "Source: metadata only. Confidence: low."


def extract_meta(html_text: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]*)"',
        rf'<meta[^>]+property="{re.escape(name)}"[^>]+content="([^"]*)"',
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.I | re.S)
        if m:
            return clean_text(m.group(1))
    return ""


def extract_meta_many(html_text: str, name: str) -> List[str]:
    values: List[str] = []
    patterns = [
        rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]*)"',
        rf'<meta[^>]+property="{re.escape(name)}"[^>]+content="([^"]*)"',
    ]
    for pat in patterns:
        for value in re.findall(pat, html_text, re.I | re.S):
            value = clean_text(value)
            if value:
                values.append(value)
    return unique_preserve(values)


def extract_title(html_text: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html_text, re.I | re.S)
    return clean_text(m.group(1) if m else "")


def extract_jsonld_article(html_text: str) -> Dict[str, str]:
    results: Dict[str, str] = {}
    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html_text, re.I | re.S):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "ScholarlyArticle":
                results["headline"] = clean_text(item.get("headline", ""))
                results["abstract"] = clean_text(item.get("abstract", ""))
                author = item.get("author")
                if isinstance(author, list):
                    names = []
                    for x in author:
                        if isinstance(x, dict) and x.get("name"):
                            names.append(clean_text(x["name"]))
                        elif isinstance(x, str):
                            names.append(clean_text(x))
                    results["authors"] = ", ".join([x for x in names if x])
                elif isinstance(author, dict) and author.get("name"):
                    results["authors"] = clean_text(author["name"])
                elif isinstance(author, str):
                    results["authors"] = clean_text(author)
                break
    return results


def extract_reports(html_text: str) -> List[Tuple[str, str]]:
    reports: List[Tuple[str, str]] = []
    for m in re.finditer(r'([A-Za-z]+Report):"((?:\\.|[^"\\])*)"', html_text, re.S):
        key, raw = m.group(1), m.group(2)
        try:
            text = json.loads('"' + raw + '"')
        except Exception:
            continue
        text = clean_text(text)
        if len(text) >= 200:
            reports.append((key, text))
    reports.sort(key=lambda x: len(x[1]), reverse=True)
    return reports


def classify_http_error(err: urllib.error.HTTPError, body: str) -> Tuple[str, str]:
    lowered = body.lower()
    detail = f"HTTP {err.code}"
    if err.code == 404:
        return "not_found", detail + " (paper not found)"
    if err.code == 429 or "http 429" in body or "rate limit" in lowered or "api error (http 429)" in lowered:
        return "rate_limited", detail + " (rate limited upstream)"
    if 500 <= err.code < 600:
        return "upstream_error", detail + " (upstream service error)"
    return "http_error", detail


def fetch_with_classification(url: str, timeout: int = 25) -> Tuple[Optional[str], str, Optional[str]]:
    try:
        return fetch(url, timeout=timeout), "available", None
    except urllib.error.HTTPError as err:
        try:
            body = err.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        status, detail = classify_http_error(err, body)
        return None, status, f"{url}: {detail}"
    except Exception as err:
        return None, "network_error", f"{url}: {type(err).__name__}: {err}"


def normalize_input(raw: str) -> Dict[str, str]:
    s = raw.strip()
    s = s.strip("<>")
    s = s.replace("https://alphaxiv.org/", "https://www.alphaxiv.org/")

    patterns = [
        r"arxiv\.org/(?:abs|pdf|html)/([^/?#]+)",
        r"alphaxiv\.org/(?:overview|paper|abs)/([^/?#]+)",
    ]
    for pat in patterns:
        m = re.search(pat, s, re.I)
        if m:
            paper_id = m.group(1)
            paper_id = re.sub(r"\.pdf$", "", paper_id, flags=re.I)
            return build_urls(paper_id, s)

    if re.fullmatch(r"[A-Za-z0-9._\-/]+", s):
        return build_urls(s, raw)

    raise ValueError(f"Could not parse arXiv/alphaXiv identifier from: {raw}")


def build_urls(paper_id: str, raw: str) -> Dict[str, str]:
    paper_id = paper_id.strip()
    paper_id = re.sub(r"\.pdf$", "", paper_id, flags=re.I)
    canonical_id = paper_id
    canonical_id_no_version = re.sub(r"v\d+$", "", canonical_id)
    return {
        "input": raw,
        "paper_id": canonical_id,
        "paper_id_no_version": canonical_id_no_version,
        "alphaxiv_overview_url": f"https://www.alphaxiv.org/overview/{canonical_id}",
        "alphaxiv_overview_url_no_version": f"https://www.alphaxiv.org/overview/{canonical_id_no_version}",
        "arxiv_abs_url": f"https://arxiv.org/abs/{canonical_id}",
        "arxiv_abs_url_no_version": f"https://arxiv.org/abs/{canonical_id_no_version}",
    }


def fetch_arxiv_abstract(urls: Dict[str, str], timeout: int = 25) -> Dict[str, object]:
    candidates = unique_preserve([urls["arxiv_abs_url"], urls["arxiv_abs_url_no_version"]])
    errors: List[str] = []
    for url in candidates:
        try:
            page = fetch(url, timeout=timeout)
            title = (
                extract_meta(page, "citation_title")
                or extract_meta(page, "og:title")
                or extract_meta(page, "twitter:title")
                or extract_title(page)
            )
            title = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()
            authors = ", ".join(extract_meta_many(page, "citation_author"))
            abstract = (
                extract_meta(page, "citation_abstract")
                or extract_meta(page, "og:description")
                or extract_meta(page, "twitter:description")
            )
            if not abstract:
                m = re.search(r"Abstract:\s*(.*?)\s*(?:Comments:|Subjects:|Cite as:|$)", page, re.S | re.I)
                abstract = clean_text(m.group(1) if m else "")
            if title or abstract or authors:
                return {
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "url": url,
                    "status": "available",
                }
        except urllib.error.HTTPError as err:
            try:
                body = err.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            _, detail = classify_http_error(err, body)
            errors.append(f"{url}: {detail}")
        except Exception as err:
            errors.append(f"{url}: {type(err).__name__}: {err}")
    return {
        "title": "",
        "abstract": "",
        "authors": "",
        "url": candidates[0],
        "status": "unavailable",
        "errors": unique_preserve(errors),
    }


def infer_source_used(result: Dict[str, object]) -> str:
    has_alpha = bool(result.get("alphaxiv_report") or result.get("alphaxiv_description"))
    has_arxiv = bool(result.get("arxiv_abstract"))
    if has_alpha and has_arxiv:
        return "alphaxiv+arxiv"
    if has_alpha:
        return "alphaxiv"
    if has_arxiv:
        return "arxiv"
    return "unknown"


def choose_best_summary(result: Dict[str, object]) -> Tuple[str, str]:
    if result.get("alphaxiv_report"):
        return "alphaxiv_report", str(result["alphaxiv_report"])
    if result.get("alphaxiv_status") == "available" and result.get("alphaxiv_description"):
        return "alphaxiv_description", str(result["alphaxiv_description"])
    if result.get("arxiv_abstract"):
        return "arxiv_abstract", str(result["arxiv_abstract"])
    if result.get("alphaxiv_description"):
        return "alphaxiv_description", str(result["alphaxiv_description"])
    return "none", ""


def summarize_status(title: str, best_summary: str) -> str:
    if title and best_summary:
        return "ok"
    if title or best_summary:
        return "partial"
    return "error"


def as_markdown(result: Dict[str, object]) -> str:
    lines = []
    lines.append(f"# {result.get('title') or result.get('paper_id')}")
    lines.append("")
    lines.append(f"- Paper ID: `{result.get('paper_id')}`")
    lines.append(f"- Status: `{result.get('status')}`")
    lines.append(f"- Source used: `{result.get('source_used')}`")
    lines.append(f"- Best summary: `{result.get('summary_source')}`")
    lines.append(f"- alphaXiv status: `{result.get('alphaxiv_status')}`")
    lines.append(f"- arXiv status: `{result.get('arxiv_status')}`")
    lines.append(f"- alphaXiv: {result.get('resolved_alphaxiv_url')}")
    lines.append(f"- arXiv: {result.get('resolved_arxiv_url') or result.get('arxiv_abs_url')}")
    if result.get("authors"):
        lines.append(f"- Authors: {result['authors']}")
    lines.append("")
    if result.get("best_summary"):
        lines.append("## Best available summary")
        lines.append("")
        lines.append(str(result["best_summary"]))
        lines.append("")
    if result.get("alphaxiv_report"):
        lines.append(f"## alphaXiv detailed report ({result.get('alphaxiv_report_key')})")
        lines.append("")
        lines.append(str(result["alphaxiv_report"]))
        lines.append("")
    elif result.get("alphaxiv_description"):
        lines.append("## alphaXiv quick overview")
        lines.append("")
        lines.append(str(result["alphaxiv_description"]))
        lines.append("")
    if result.get("arxiv_abstract") and result.get("summary_source") != "arxiv_abstract":
        lines.append("## arXiv abstract")
        lines.append("")
        lines.append(str(result["arxiv_abstract"]))
        lines.append("")
    warnings = result.get("warnings") or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    errors = result.get("errors") or []
    if errors:
        lines.append("## Errors")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def as_text(result: Dict[str, object]) -> str:
    lines = []
    lines.append(f"Title: {result.get('title') or result.get('paper_id')}")
    lines.append(f"Paper ID: {result.get('paper_id')}")
    lines.append(f"Status: {result.get('status')}")
    lines.append(f"Source used: {result.get('source_used')}")
    lines.append(f"Best summary source: {result.get('summary_source')}")
    lines.append(f"alphaXiv status: {result.get('alphaxiv_status')}")
    lines.append(f"arXiv status: {result.get('arxiv_status')}")
    if result.get("authors"):
        lines.append(f"Authors: {result.get('authors')}")
    lines.append(f"alphaXiv URL: {result.get('resolved_alphaxiv_url')}")
    lines.append(f"arXiv URL: {result.get('resolved_arxiv_url') or result.get('arxiv_abs_url')}")
    if result.get("best_summary"):
        lines.append("")
        lines.append("Best available summary:")
        lines.append(str(result["best_summary"]))
    warnings = result.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    errors = result.get("errors") or []
    if errors:
        lines.append("")
        lines.append("Errors:")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines).strip() + "\n"


def as_brief(result: Dict[str, object]) -> str:
    lines = []
    title = str(result.get("title") or result.get("paper_id") or "Unknown paper")
    paper_id = str(result.get("paper_id") or "unknown")
    sentences = brief_sentence_pool(result)
    takeaway = brief_takeaway(result, sentences)

    used = set()
    if sentences:
        used.add(sentence_key(sentences[0]))

    problem = brief_problem(result, sentences, used)
    method_points = brief_method_points(sentences, used)

    lines.append(f"Paper: {title} ({paper_id})")
    lines.append(f"Takeaway: {takeaway}")
    lines.append(f"Problem solved: {problem}")
    if len(method_points) >= 2:
        lines.append("Core method:")
        for point in method_points[:4]:
            lines.append(f"- {point}")
    elif method_points:
        lines.append(f"Core method: {method_points[0]}")
    else:
        lines.append("Core method: Method details are not surfaced in the retrieved summary.")
    lines.append(f"Worth reading? {brief_reading_verdict(result)}")
    lines.append(brief_source_line(result))
    return "\n".join(lines).strip() + "\n"


def brief_reading_verdict_zh(result: Dict[str, object]) -> str:
    summary_source = str(result.get("summary_source", "none"))
    alphaxiv_status = str(result.get("alphaxiv_status", "unavailable"))
    if summary_source == "alphaxiv_report":
        return "值得先读；alphaXiv 有较完整的长报告。"
    if summary_source == "alphaxiv_description" and result.get("arxiv_abstract"):
        return "值得快速略读；alphaXiv 偏薄，但 arXiv 摘要补足了基础信息。"
    if summary_source == "arxiv_abstract":
        if alphaxiv_status in {"thin", "no_report"}:
            return "先看摘要即可；alphaXiv 信息偏薄，这版主要依赖 arXiv。"
        return "先看摘要即可；这版主要依赖 arXiv fallback。"
    if result.get("best_summary"):
        return "可以先快速过一遍；现有文本足够做首轮判断。"
    return "暂时不好判断；目前只拿到了有限元数据。"


def brief_source_line_zh(result: Dict[str, object]) -> str:
    summary_source = str(result.get("summary_source", "none"))
    alphaxiv_status = str(result.get("alphaxiv_status", "unavailable"))
    arxiv_status = str(result.get("arxiv_status", "unknown"))

    if summary_source == "alphaxiv_report":
        return "来源：alphaXiv 长报告。可信度：较高。"
    if summary_source == "alphaxiv_description":
        if arxiv_status == "available":
            return f"来源：alphaXiv 概览 + arXiv 摘要交叉补充。可信度：中等（alphaXiv: {alphaxiv_status}）。"
        return f"来源：alphaXiv 概览。可信度：中等（alphaXiv: {alphaxiv_status}）。"
    if summary_source == "arxiv_abstract":
        return f"来源：arXiv 摘要 fallback。可信度：基础（alphaXiv: {alphaxiv_status}）。"
    return "来源：仅元数据。可信度：较低。"


def as_brief_zh(result: Dict[str, object]) -> str:
    lines = []
    title = str(result.get("title") or result.get("paper_id") or "未知论文")
    paper_id = str(result.get("paper_id") or "unknown")
    sentences = brief_sentence_pool(result)
    takeaway = brief_takeaway(result, sentences)

    used = set()
    if sentences:
        used.add(sentence_key(sentences[0]))

    problem = brief_problem(result, sentences, used)
    method_points = brief_method_points(sentences, used)

    lines.append(f"论文：{title}（{paper_id}）")
    lines.append(f"一句话结论：{takeaway}")
    lines.append(f"解决什么问题：{problem}")
    if len(method_points) >= 2:
        lines.append("核心方法：")
        for point in method_points[:4]:
            lines.append(f"- {point}")
    elif method_points:
        lines.append(f"核心方法：{method_points[0]}")
    else:
        lines.append("核心方法：当前检索到的摘要里没有足够的方法细节。")
    lines.append(f"值不值得读：{brief_reading_verdict_zh(result)}")
    lines.append(brief_source_line_zh(result))
    return "\n".join(lines).strip() + "\n"


def compact_payload(result: Dict[str, object]) -> Dict[str, object]:
    return {
        "paper_id": result.get("paper_id"),
        "title": result.get("title"),
        "authors": result.get("authors"),
        "status": result.get("status"),
        "source_used": result.get("source_used"),
        "summary_source": result.get("summary_source"),
        "best_summary": result.get("best_summary"),
        "alphaxiv_status": result.get("alphaxiv_status"),
        "arxiv_status": result.get("arxiv_status"),
        "resolved_alphaxiv_url": result.get("resolved_alphaxiv_url"),
        "resolved_arxiv_url": result.get("resolved_arxiv_url"),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
    }


def render_one(result: Dict[str, object], output_format: str) -> str:
    if output_format == "markdown":
        return as_markdown(result)
    if output_format == "text":
        return as_text(result)
    if output_format == "brief":
        return as_brief(result)
    if output_format == "brief-zh":
        return as_brief_zh(result)
    if output_format == "json-compact":
        return json.dumps(compact_payload(result), ensure_ascii=False, separators=(",", ":")) + "\n"
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def render_many(results: List[Dict[str, object]], output_format: str) -> str:
    if output_format == "json":
        payload = {"count": len(results), "results": results}
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format == "json-compact":
        return "".join(json.dumps(compact_payload(r), ensure_ascii=False, separators=(",", ":")) + "\n" for r in results)
    if output_format == "markdown":
        return "\n---\n\n".join(as_markdown(r).rstrip() for r in results) + "\n"

    blocks = []
    for i, result in enumerate(results, 1):
        title = str(result.get("title") or result.get("paper_id") or f"paper-{i}")
        header = f"[{i}/{len(results)}] {title}"
        if output_format == "text":
            body = as_text(result).rstrip()
        elif output_format == "brief":
            body = as_brief(result).rstrip()
        elif output_format == "brief-zh":
            body = as_brief_zh(result).rstrip()
        else:
            body = render_one(result, output_format).rstrip()
        blocks.append(header + "\n" + body)
    return ("\n\n" + ("=" * 80) + "\n\n").join(blocks) + "\n"


def canonicalize_column_name(name: str) -> str:
    return re.sub(r"[\s_-]+", "", name.strip().lower())


def nonempty_row_values(row: List[str]) -> List[str]:
    return [cell.strip() for cell in row if cell and cell.strip()]


def is_blank_row(row: List[str]) -> bool:
    return not nonempty_row_values(row)


def is_comment_only_row(row: List[str]) -> bool:
    values = nonempty_row_values(row)
    return len(values) == 1 and values[0].startswith("#")


def visible_column_names(columns: List[str]) -> List[str]:
    return [column for column in columns if column]


def obvious_input_column_index(columns: List[str]) -> Optional[int]:
    indexed = [(idx, column) for idx, column in enumerate(columns) if column]
    if len(indexed) == 1:
        return indexed[0][0]

    matches = [
        (idx, column)
        for idx, column in indexed
        if canonicalize_column_name(column) in OBVIOUS_INPUT_COLUMN_NAMES
    ]
    if len(matches) == 1:
        return matches[0][0]
    return None


def resolve_structured_input_column(path: str, columns: List[str], column_name: Optional[str]) -> int:
    indexed = [(idx, column) for idx, column in enumerate(columns) if column]
    if not indexed:
        raise InputFileError(f"structured input file '{path}' has an empty header row")

    normalized_to_indexes: Dict[str, List[int]] = {}
    for idx, column in indexed:
        normalized_to_indexes.setdefault(canonicalize_column_name(column), []).append(idx)

    available = ", ".join(visible_column_names(columns))

    if column_name:
        requested = canonicalize_column_name(column_name)
        matches = normalized_to_indexes.get(requested, [])
        if not matches:
            raise InputFileError(
                f"structured input file '{path}' does not contain column '{column_name}'; available columns: {available}"
            )
        if len(matches) > 1:
            raise InputFileError(
                f"structured input file '{path}' has multiple columns matching '{column_name}'; available columns: {available}"
            )
        return matches[0]

    obvious_index = obvious_input_column_index(columns)
    if obvious_index is not None:
        return obvious_index

    raise InputFileError(
        f"structured input file '{path}' requires --column COLUMN_NAME; available columns: {available}"
    )


def read_structured_input_file(path: str, delimiter: str, column_name: Optional[str]) -> List[str]:
    papers: List[str] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)

        columns: Optional[List[str]] = None
        for row in reader:
            if is_blank_row(row) or is_comment_only_row(row):
                continue
            columns = [cell.strip() for cell in row]
            break

        if columns is None:
            return papers

        column_index = resolve_structured_input_column(path, columns, column_name)

        for row in reader:
            if is_blank_row(row) or is_comment_only_row(row):
                continue
            value = row[column_index].strip() if column_index < len(row) else ""
            if not value or value.startswith("#"):
                continue
            papers.append(value)

    return papers


def read_input_file(path: str, column_name: Optional[str] = None) -> List[str]:
    lowered_path = path.lower()
    if lowered_path.endswith(".csv"):
        return read_structured_input_file(path, ",", column_name)
    if lowered_path.endswith(".tsv"):
        return read_structured_input_file(path, "\t", column_name)

    papers: List[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            papers.append(line)
    return papers


def expand_cli_inputs(argv: List[str], input_column: Optional[str] = None) -> List[str]:
    papers: List[str] = []
    index = 0

    while index < len(argv):
        token = argv[index]

        if token == "--":
            papers.extend(arg.strip() for arg in argv[index + 1 :] if arg.strip())
            break

        if token == "--input-file":
            index += 1
            if index >= len(argv):
                break
            papers.extend(read_input_file(argv[index], input_column))
            index += 1
            continue

        if token.startswith("--input-file="):
            papers.extend(read_input_file(token.split("=", 1)[1], input_column))
            index += 1
            continue

        if token in {"--column", "--format", "--timeout"}:
            index += 2
            continue

        if token.startswith("--column=") or token.startswith("--format=") or token.startswith("--timeout="):
            index += 1
            continue

        if token.startswith("-"):
            index += 1
            continue

        papers.append(token)
        index += 1

    return papers


def lookup(raw: str, timeout: int = 25) -> Dict[str, object]:
    urls = normalize_input(raw)
    candidates = unique_preserve([urls["alphaxiv_overview_url"], urls["alphaxiv_overview_url_no_version"]])
    alpha_page = ""
    alpha_url = candidates[0]
    alpha_errors: List[str] = []
    alpha_status = "unavailable"

    for url in candidates:
        page, fetch_status, error = fetch_with_classification(url, timeout=timeout)
        if page is not None:
            alpha_page = page
            alpha_url = url
            alpha_status = "available"
            break
        alpha_status = fetch_status
        if error:
            alpha_errors.append(error)

    alpha_errors = unique_preserve(alpha_errors)

    result: Dict[str, object] = {
        **urls,
        "resolved_alphaxiv_url": alpha_url,
        "resolved_arxiv_url": urls["arxiv_abs_url"],
        "status": "error",
        "source_used": "unknown",
        "summary_source": "none",
        "best_summary": "",
        "alphaxiv_available": bool(alpha_page),
        "alphaxiv_status": alpha_status,
        "alphaxiv_errors": alpha_errors,
        "arxiv_status": "unknown",
        "title": "",
        "alphaxiv_description": "",
        "alphaxiv_report": "",
        "alphaxiv_report_key": "",
        "authors": "",
        "arxiv_abstract": "",
        "notes": [],
        "warnings": [],
        "errors": list(alpha_errors),
    }

    if alpha_page:
        meta_title = extract_meta(alpha_page, "og:title") or extract_meta(alpha_page, "twitter:title") or extract_title(alpha_page)
        meta_desc = extract_meta(alpha_page, "description") or extract_meta(alpha_page, "og:description") or extract_meta(alpha_page, "twitter:description")
        jsonld = extract_jsonld_article(alpha_page)
        reports = extract_reports(alpha_page)
        title = jsonld.get("headline") or meta_title.replace("| alphaXiv", "").strip()
        result["title"] = clean_text(title)
        result["alphaxiv_description"] = clean_alpha_description(meta_desc)
        result["authors"] = clean_text(jsonld.get("authors", ""))
        result["arxiv_abstract"] = clean_text(jsonld.get("abstract", ""))
        if reports:
            result["alphaxiv_report_key"] = reports[0][0]
            result["alphaxiv_report"] = reports[0][1]
            result["alphaxiv_status"] = "available"
        elif result["alphaxiv_description"]:
            result["alphaxiv_status"] = "thin"
            result["notes"].append("AlphaXiv page fetched, but only a short overview was available.")
        else:
            result["alphaxiv_status"] = "no_report"
            result["notes"].append("AlphaXiv page fetched, but no summary/report field was found.")
    else:
        if result["alphaxiv_status"] == "rate_limited":
            result["notes"].append("AlphaXiv appears rate-limited; falling back to arXiv abstract.")
        elif result["alphaxiv_status"] == "not_found":
            result["notes"].append("AlphaXiv overview page was not found; falling back to arXiv abstract.")
        elif result["alphaxiv_status"] == "upstream_error":
            result["notes"].append("AlphaXiv upstream returned a server error; falling back to arXiv abstract.")
        else:
            result["notes"].append("AlphaXiv overview fetch failed; falling back to arXiv abstract.")

    if not result["title"] or not result["arxiv_abstract"] or not result["authors"]:
        arxiv = fetch_arxiv_abstract(urls, timeout=timeout)
        result["resolved_arxiv_url"] = arxiv.get("url", urls["arxiv_abs_url"])
        result["arxiv_status"] = arxiv.get("status", "unknown")
        if not result["title"]:
            result["title"] = str(arxiv.get("title", ""))
        if not result["arxiv_abstract"]:
            result["arxiv_abstract"] = str(arxiv.get("abstract", ""))
        if not result["authors"]:
            result["authors"] = str(arxiv.get("authors", ""))
        if arxiv.get("errors"):
            result["errors"] = unique_preserve(list(result["errors"]) + list(arxiv["errors"]))
            result["notes"].append("arXiv fallback had errors: " + "; ".join(arxiv["errors"]))
    else:
        result["arxiv_status"] = "available"

    result["source_used"] = infer_source_used(result)
    result["summary_source"], result["best_summary"] = choose_best_summary(result)
    result["status"] = summarize_status(str(result.get("title", "")), str(result.get("best_summary", "")))
    result["notes"] = unique_preserve(list(result["notes"]))
    result["warnings"] = list(result["notes"])
    result["errors"] = unique_preserve(list(result["errors"]))
    return result


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Look up arXiv papers via alphaXiv and extract structured overview fields.")
    parser.add_argument("paper", nargs="*", help="One or more arXiv ids, arXiv URLs, or alphaXiv URLs")
    parser.add_argument(
        "--input-file",
        action="append",
        default=[],
        metavar="PATH",
        help="Read paper ids or URLs from PATH. Text files stay line-based; CSV/TSV files support header-based column selection.",
    )
    parser.add_argument(
        "--column",
        help="For CSV/TSV --input-file values, read paper ids or URLs from COLUMN_NAME. If omitted, an obvious structured column is used only when it can be chosen unambiguously.",
    )
    parser.add_argument("--format", choices=["json", "json-compact", "markdown", "text", "brief", "brief-zh"], default="json")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout in seconds (default: 25)")
    args = parser.parse_args(argv)

    try:
        papers = expand_cli_inputs(argv, input_column=args.column)
    except (InputFileError, OSError) as err:
        path = err.filename or "<unknown>"
        if isinstance(err, OSError):
            parser.error(f"unable to read input file '{path}': {err.strerror or err}")
        parser.error(str(err))

    if not papers:
        parser.error("provide at least one paper id / URL or --input-file PATH")

    results: List[Dict[str, object]] = []
    had_error = False
    for paper in papers:
        try:
            results.append(lookup(paper, timeout=args.timeout))
        except urllib.error.HTTPError as err:
            try:
                body = err.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            _, detail = classify_http_error(err, body)
            results.append({"input": paper, "status": "error", "error": f"HTTP {err.code}", "detail": detail})
            had_error = True
        except Exception as err:
            results.append({"input": paper, "status": "error", "error": type(err).__name__, "detail": str(err)})
            had_error = True

    if len(results) == 1:
        sys.stdout.write(render_one(results[0], args.format))
    else:
        sys.stdout.write(render_many(results, args.format))
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
