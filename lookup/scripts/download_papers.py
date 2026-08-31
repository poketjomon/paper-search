#!/usr/bin/env python3
"""Download paper PDFs from arXiv to a local directory.

Usage:
    python3 download_papers.py 2303.04137 https://arxiv.org/abs/2401.12345
    python3 download_papers.py --input-file papers.txt --out ~/Downloads/papers

Accepts the same inputs as alphaxiv_lookup.py: plain arXiv ids (with or
without version), arXiv URLs, and alphaXiv URLs. Reuses its input parsing
so behavior stays consistent across the subskill.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from alphaxiv_lookup import InputFileError, expand_cli_inputs, normalize_input  # noqa: E402

REQUEST_GAP_SECONDS = 3.0  # courtesy gap between arXiv downloads
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"


def pdf_url_for(paper_id: str) -> str:
    return f"https://arxiv.org/pdf/{paper_id}"


def split_comma_separated(papers: List[str]) -> List[str]:
    """Allow both space-separated and comma-separated paper lists."""
    result: List[str] = []
    for paper in papers:
        for part in paper.split(","):
            part = part.strip()
            if part:
                result.append(part)
    return result


def download_one(paper: str, out_dir: Path, timeout: int) -> dict:
    """Download one paper PDF; never raises, always returns a result dict."""
    try:
        info = normalize_input(paper)
    except ValueError as err:
        return {"input": paper, "ok": False, "error": str(err)}

    paper_id = info["paper_id"]
    target = out_dir / f"{paper_id}.pdf"
    req = urllib.request.Request(pdf_url_for(paper_id), headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower():
                return {"input": paper, "ok": False, "paper_id": paper_id,
                        "error": f"unexpected content type: {content_type}"}
            data = resp.read()
        if not data.startswith(b"%PDF"):
            return {"input": paper, "ok": False, "paper_id": paper_id,
                    "error": "response is not a PDF (possibly a rate-limit page)"}
        target.write_bytes(data)
        return {"input": paper, "ok": True, "paper_id": paper_id,
                "path": str(target), "bytes": len(data)}
    except urllib.error.HTTPError as err:
        detail = f"HTTP {err.code}"
        if err.code == 404:
            detail += " (paper not found)"
        return {"input": paper, "ok": False, "paper_id": paper_id, "error": detail}
    except Exception as err:
        return {"input": paper, "ok": False, "paper_id": paper_id,
                "error": f"{type(err).__name__}: {err}"}


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Download paper PDFs from arXiv to a local directory.")
    parser.add_argument("paper", nargs="*",
                        help="arXiv ids, arXiv URLs, or alphaXiv URLs")
    parser.add_argument("--input-file", action="append", default=[], metavar="PATH",
                        help="Read paper ids/URLs from PATH (txt: one per line; CSV/TSV: use --column)")
    parser.add_argument("--column",
                        help="CSV/TSV column holding the paper id/URL")
    parser.add_argument("--out", default=".",
                        help="Output directory (default: current directory)")
    parser.add_argument("--timeout", type=int, default=60,
                        help="HTTP timeout in seconds (default: 60)")
    args = parser.parse_args(argv)

    try:
        papers = expand_cli_inputs(argv, input_column=args.column)
    except (InputFileError, OSError) as err:
        parser.error(str(err))

    papers = split_comma_separated(papers)

    if not papers:
        parser.error("provide at least one paper id / URL or --input-file PATH")

    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    ok_count = 0
    fail_count = 0
    for index, paper in enumerate(papers):
        if index:
            time.sleep(REQUEST_GAP_SECONDS)
        result = download_one(paper, out_dir, args.timeout)
        if result["ok"]:
            ok_count += 1
            print(f"OK {result['paper_id']} -> {result['path']} ({result['bytes']} bytes)")
        else:
            fail_count += 1
            print(f"FAIL {result.get('input')}: {result['error']}", file=sys.stderr)

    print(f"\nDownloaded {ok_count}/{ok_count + fail_count} PDF(s) to {out_dir}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
