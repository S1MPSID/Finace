"""
Generate formal regulatory compliance report PDF from analysis payload.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings
from reports.page_template import make_page_callbacks
from reports.pdf_styles import build_pdf_styles
from reports.sections.core_sections import (
    REPORT_KIND_LABELS,
    append_certification,
    append_compliance_determination,
    append_cover,
    append_document_control,
    append_evaluator_amendments,
    append_gaps_and_actions,
    append_regulatory_schedule,
    append_scope,
    append_table_of_contents,
    append_upgrade_record,
    append_workflow_appendix,
    infer_report_kind,
)


def generate_report_pdf(
    analysis: dict,
    report_id: str,
    org_name: str,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or (settings.data_dir / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report_id}.pdf"

    styles = build_pdf_styles()
    story = []

    report_kind = append_cover(story, styles, analysis, report_id, org_name)
    append_table_of_contents(story, styles, report_kind)
    append_document_control(story, styles, analysis, report_id, report_kind)
    append_scope(story, styles, analysis)
    append_compliance_determination(story, styles, analysis)
    append_gaps_and_actions(story, styles, analysis)
    append_regulatory_schedule(story, styles, analysis)
    if report_kind == "upgrade":
        append_upgrade_record(story, styles, analysis)
    append_evaluator_amendments(story, styles, analysis)
    append_certification(story, styles, analysis)
    append_workflow_appendix(story, styles, analysis)

    on_first, on_later = make_page_callbacks(report_id, REPORT_KIND_LABELS.get(report_kind, "Compliance Report"))

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=72,
        bottomMargin=54,
        title=f"Compliance Report {report_id}",
        author="Finace Autonomous Compliance Engine",
        subject=REPORT_KIND_LABELS.get(report_kind, "Compliance Report"),
    )
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate compliance PDF report")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--report-id", required=True)
    parser.add_argument("--org-name", required=True)
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    analysis = payload.get("analysis", payload)
    if "workflow_input" not in analysis and "workflow_input" in payload:
        analysis["workflow_input"] = payload["workflow_input"]

    print(str(generate_report_pdf(analysis, report_id=args.report_id, org_name=args.org_name)))


if __name__ == "__main__":
    main()
