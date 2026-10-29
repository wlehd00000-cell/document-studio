"""Fixed HTML composition and HTML-to-PPTX delivery; stdlib only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

ROUTES = {"html_report"}

def select_route(brief: dict) -> dict:
    """Use, templates and old native-quality flags cannot change HTML authoring.

    Explicit/accepted output requests can change export, never the authoring
    source. Normalized user intent is supplied by the caller; capability is not intent.
    """
    use = brief.get("document_use") or brief.get("use") or "reading"
    output = brief.get("output_format") or brief.get("requested_outputs") or "PPTX"
    if isinstance(output, list):
        if any(not isinstance(item, str) or not item.strip() for item in output):
            raise ValueError("Output formats must be nonempty text")
        output = " + ".join(output)
    if not isinstance(output, str):
        raise ValueError("Output request must be text or a list of text formats")
    normalized = output.lower()
    exporters = []
    if re.search(r"ppt|powerpoint|파워포인트|slides", normalized):
        exporters.append("html_to_pptx")
    if "pdf" in normalized:
        exporters.append("html_to_pdf")
    if "html" in normalized:
        exporters.append("html_delivery")
    if re.search(r"docx|word|워드", normalized):
        exporters.append("html_to_docx")
    if not exporters:
        exporters = ["requested_special_output"]
    return {
        "authoring_route": "html_report",
        "canonical_source": "html/index.html",
        "export_route": exporters[0],
        "export_routes": exporters,
        "requested_output": output,
        "document_use": use,
        "export_exception": exporters != ["html_to_pptx"],
        "reason": "HTML composition is fixed. HTML-to-PPTX is the default; explicit output requests determine export exceptions.",
        "capability_verified": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    args = parser.parse_args()
    print(json.dumps(select_route(json.loads(args.brief.read_text(encoding="utf-8-sig"))), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
