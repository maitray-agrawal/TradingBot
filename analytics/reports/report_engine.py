"""Reporting engine orchestrator for PrimeTrade AI.

Integrates analytical and statistical findings into Markdown, HTML, and PDF report formats.
"""

from pathlib import Path
from typing import Any, Dict

from analytics.reports.html_compiler import HTMLReportCompiler
from analytics.reports.markdown_compiler import MarkdownReportCompiler
from analytics.reports.pdf_compiler import PDFReportCompiler
from config.paths import REPORTS_OUTPUT_DIR
from utils.logger import analytics_logger


class ReportingEngine:
    """Orchestrates generation of markdown, HTML, and PDF reports for PrimeTrade AI."""

    def __init__(self, output_dir: Path = REPORTS_OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        analytics_logger.info(f"Initialized Reporting Engine with output directory: {self.output_dir}")

    def run_reporting(
        self, analytics_res: Dict[str, Any], statistics_res: Dict[str, Any]
    ) -> Dict[str, Dict[str, Path]]:
        """Generates all reports (Executive, Technical, Business) in MD, HTML, and PDF formats.

        Args:
            analytics_res: Dictionary results from the AnalyticsEngine.
            statistics_res: Dictionary results from the StatisticsEngine.

        Returns:
            A nested dictionary mapping report key (executive_summary, technical_summary,
            business_report) to another dictionary mapping format (md, html, pdf) to the
            respective output file Path.
        """
        analytics_logger.info("Executing PrimeTrade AI reporting compilation...")
        results: Dict[str, Dict[str, Path]] = {}

        # 1. Compile Markdown Reports
        analytics_logger.info("Compiling Markdown reports...")
        md_reports = MarkdownReportCompiler.compile_all(analytics_res, statistics_res)
        for name, md_content in md_reports.items():
            file_path = self.output_dir / f"{name}.md"
            try:
                file_path.write_text(md_content, encoding="utf-8")
                results.setdefault(name, {})["md"] = file_path
                analytics_logger.info(f"Successfully saved Markdown report: {file_path}")
            except Exception as e:
                analytics_logger.error(f"Failed to save Markdown report {name}: {e}")

        # 2. Compile HTML Reports
        analytics_logger.info("Compiling HTML reports...")
        html_reports = HTMLReportCompiler.compile_all(analytics_res, statistics_res)
        for name, html_content in html_reports.items():
            file_path = self.output_dir / f"{name}.html"
            try:
                file_path.write_text(html_content, encoding="utf-8")
                results.setdefault(name, {})["html"] = file_path
                analytics_logger.info(f"Successfully saved HTML report: {file_path}")
            except Exception as e:
                analytics_logger.error(f"Failed to save HTML report {name}: {e}")

        # 3. Compile PDF Reports
        analytics_logger.info("Compiling PDF reports...")
        pdf_reports = PDFReportCompiler.compile_all(analytics_res, statistics_res)
        for name, pdf_instance in pdf_reports.items():
            file_path = self.output_dir / f"{name}.pdf"
            try:
                pdf_instance.output(str(file_path))
                results.setdefault(name, {})["pdf"] = file_path
                analytics_logger.info(f"Successfully saved PDF report: {file_path}")
            except Exception as e:
                analytics_logger.error(f"Failed to save PDF report {name}: {e}")

        analytics_logger.info("PrimeTrade AI reporting compilation complete.")
        return results
