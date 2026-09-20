"""
Unit tests for executive PDF report generation.
"""

from pathlib import Path
import pytest


def test_executive_pdf_existence_and_size():
    pdf_path = Path("relatorio_executivo_vertice.pdf")
    assert pdf_path.exists(), "The executive PDF report must be generated and exist"
    assert (
        pdf_path.stat().st_size > 100_000
    ), "The executive PDF must have valid content (size > 100 KB)"


def test_executive_html_source_content():
    html_path = Path("relatorio_executivo_vertice.html")
    assert html_path.exists(), "The HTML source must exist"
    content = html_path.read_text(encoding="utf-8")
    assert "Vértice Retail" in content
    assert "DRE Gerencial" in content
    assert "348,7M" in content
    assert "Roadmap Executivo" in content
