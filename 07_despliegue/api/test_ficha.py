"""Guards the plain-language model card against drifting from the deployed model."""
from __future__ import annotations

from pathlib import Path

from api import scoring

FICHA = Path(__file__).resolve().parents[1] / "mcp_server" / "ficha_modelo.md"


def test_la_ficha_describe_el_modelo_desplegado():
    texto = FICHA.read_text(encoding="utf-8")
    modelo = scoring._modelo
    c = f"{modelo.get_params()['C']:.2f}".replace(".", ",")
    penalizacion = modelo.get_params()["penalty"].upper()

    assert f"C = {c}" in texto, "la ficha no refleja el C del modelo desplegado"
    assert f"penalización {penalizacion}" in texto
    assert f"{modelo.coef_.shape[1]} columnas" in texto
    assert "splines" in texto, "la ficha no explica que el modelo usa splines"
    assert f"{len(scoring.VARIABLES)} datos" in texto
