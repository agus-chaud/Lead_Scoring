from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
LEADS = ROOT / "02_datos" / "01_Originales" / "Leads.csv"
BATCH = ROOT / "07_despliegue" / "02_produccion_scoring.py"
EVALUACION = ROOT / "07_despliegue" / "03_evaluar_validacion.py"
ARTEFACTO = ROOT / "07_despliegue" / "artefacto_pipeline.pkl"


def _cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def test_las_metricas_se_calculan_con_el_corte_de_0_5():
    evaluacion = _cargar(EVALUACION, "evaluacion")
    y = np.array([1, 1, 0, 0, 1, 0, 0, 0, 1, 0])
    score = np.array([0.9, 0.8, 0.7, 0.2, 0.4, 0.1, 0.3, 0.2, 0.6, 0.5])

    m = evaluacion.calcular_metricas(y, score)

    assert m["roc_auc"] == pytest.approx(21 / 24)  # 21 of 24 buyer/non-buyer pairs ordered correctly
    assert m["accuracy"] == pytest.approx(0.7)
    assert m["precision"] == pytest.approx(0.6)  # predicted 1: .9 .8 .7 .6 .5 -> 3 buyers of 5
    assert m["recall"] == pytest.approx(0.75)  # 3 of 4 buyers found
    assert m["tasa_base"] == pytest.approx(0.4)


def test_la_evaluacion_se_niega_si_validation_se_mezcla_con_entrenamiento():
    evaluacion = _cargar(EVALUACION, "evaluacion")

    evaluacion.verificar_sin_solapamiento([1, 2, 3], [4, 5])
    with pytest.raises(ValueError, match="solap"):
        evaluacion.verificar_sin_solapamiento([1, 2, 3], [3, 4])


def test_el_batch_genera_scores_y_rechaza_extremos(tmp_path):
    leads = pd.read_csv(LEADS, sep=";", encoding="utf-8").head(40)
    extremo = leads.iloc[[0]].copy()
    extremo["id"] = 999999999
    extremo["visitas_total"] = 99
    entrada = tmp_path / "entrada.csv"
    pd.concat([leads, extremo]).to_csv(entrada, sep=";", index=False)
    salida = tmp_path / "scores.csv"

    r = subprocess.run(
        [sys.executable, "-W", "ignore", str(BATCH), "--input", str(entrada), "--output", str(salida)],
        capture_output=True, text=True, cwd=ROOT,
    )

    assert r.returncode == 0, r.stderr[-800:]
    resultado = pd.read_csv(salida)
    assert list(resultado.columns) == ["id", "score", "prediccion"]
    assert len(resultado) == 40 and 999999999 not in set(resultado["id"])
    assert len(pd.read_csv(tmp_path / "scores_rechazados.csv")) == 1

    with ARTEFACTO.open("rb") as f:
        pipeline = cloudpickle.load(f)
    esperado = pipeline.predict_proba(leads.drop(columns=["id"]))[:, 1]
    assert np.allclose(resultado["score"].to_numpy(), esperado)


def test_la_evaluacion_registrada_corresponde_al_artefacto_y_la_ficha_la_refleja():
    """Fails after a retrain until 03_evaluar_validacion.py is rerun and the model card updated."""
    import hashlib
    import json

    evaluacion = json.loads(
        (ROOT / "06_resultados" / "Modelizacion" / "evaluacion_validacion.json").read_text(encoding="utf-8")
    )
    sha = hashlib.sha256(ARTEFACTO.read_bytes()).hexdigest()
    assert evaluacion["artefacto_sha256"] == sha, (
        "evaluacion_validacion.json es de otro artefacto: ejecutá 03_evaluar_validacion.py"
    )

    ficha = (ROOT / "07_despliegue" / "mcp_server" / "ficha_modelo.md").read_text(encoding="utf-8")
    m = evaluacion["metricas"]
    auc = f"{m['roc_auc']:.3f}".replace(".", ",")
    assert f"AUC): {auc}" in ficha, f"la ficha no muestra el AUC {auc} de evaluacion_validacion.json"
    assert f"{round(m['precision'] * 100)} compran" in ficha
    assert f"detecta {round(m['recall'] * 100)}" in ficha
