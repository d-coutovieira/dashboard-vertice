"""
Tests for build_diagnostic_pdf_report.py.
Verifies HTML content integrity and PDF generation.
"""

from pathlib import Path
import pytest
from build_diagnostic_pdf_report import generate_diagnostic_html, build_pdf


def test_generate_diagnostic_html_contains_core_sections():
    html = generate_diagnostic_html()
    assert "Bloco 1: Matriz de Validação Empírica da Árvore" in html
    assert "Bloco 2: Decomposição da DRE Gerencial Conciliada" in html
    assert "Bloco 3: Definição Algorítmica da Prioridade #1" in html
    assert "Bloco 4: Business Case Detalhado" in html
    assert "R$ 20.526.133,84" in html
    assert "R$ 17.714.096,89" in html
    assert "Score ICE" in html
    assert "R$ 9.521.682,81" in html


def test_build_pdf_creates_valid_file(tmp_path):
    output_html = "test_diagnostico.html"
    output_pdf = "test_diagnostico.pdf"
    
    pdf_path = build_pdf(output_html_name=output_html, output_pdf_name=output_pdf)
    
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 50000  # PDF should be at least ~50KB
    
    # Cleanup test files
    html_path = pdf_path.parent / output_html
    if html_path.exists():
        html_path.unlink()
    if pdf_path.exists():
        pdf_path.unlink()
