from pathlib import Path
from build_presentation_deliverable import generate_deliverable_html


def test_generate_deliverable_html():
    html = generate_deliverable_html()
    assert "<!DOCTYPE html>" in html
    assert "Vértice Retail" in html
    assert "DRE Gerencial Conciliada" in html
    assert "Matriz de Validação Empírica da Árvore" in html
    assert "Score ICE" in html
    assert "R$ 9,52M" in html
    assert "120,05M" in html
