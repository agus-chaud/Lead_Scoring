"""The production pipeline must follow the contract of 00_manifiesto_preproduccion.json.

The oracle below replays notebook 08 step by step; production has to match it.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import cloudpickle
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "07_despliegue" / "01_reentrenamiento.py"
LEADS = ROOT / "02_datos" / "01_Originales" / "Leads.csv"
PREPROCESADOR = ROOT / "05_modelos" / "preprocesador.joblib"
FINALISTAS = ROOT / "01_Documentos" / "Variables_preseleccionadas.txt"
CONFIG = ROOT / "06_resultados" / "Modelizacion" / "config_mejor_modelo.json"

NAME_MAP = {
    "behavior__visitas_total": "visitas_total_yj_mm",
    "behavior__tiempo_en_site_total": "tiempo_en_site_total_yj_mm",
    "behavior__paginas_vistas_visita": "paginas_vistas_visita_yj_mm",
    "score_values__score_actividad": "score_actividad_mm",
    "score_values__score_perfil": "score_perfil_mm",
    "score_missing__missingindicator_score_actividad": "score_actividad_missing",
}
API_FIELDS = [
    "origen", "fuente", "no_enviar_email", "visitas_total", "tiempo_en_site_total",
    "paginas_vistas_visita", "ult_actividad", "ambito", "ocupacion",
    "score_actividad", "score_perfil", "descarga_lm",
]


def _cargar_script():
    spec = importlib.util.spec_from_file_location("reentrenamiento", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["reentrenamiento"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _oraculo_notebook08():
    """Notebook 08, cells 4-9, verbatim."""
    leads = pd.read_csv(LEADS, sep=";", encoding="utf-8")
    df_train, df_validation = train_test_split(leads, test_size=0.30, random_state=42)
    df = df_train.copy()
    for column in ["ocupacion", "ambito", "ult_actividad", "fuente"]:
        df[column] = df[column].fillna("Desconocido")
    df["visitas_total_missing"] = df["visitas_total"].isna().astype("int8")
    df["visitas_total"] = df["visitas_total"].fillna(3.0)
    df["paginas_vistas_visita_missing"] = df["paginas_vistas_visita"].isna().astype("int8")
    df["paginas_vistas_visita"] = df["paginas_vistas_visita"].fillna(2.0)
    df["fuente"] = df["fuente"].replace({"google": "Google"})
    mask = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    df = df.loc[~mask].copy()
    df["fuente"] = df["fuente"].where(
        df["fuente"].isin(["Google", "Direct Traffic", "Chat", "Organic Search"]), "Otros"
    )
    freq = df["ult_actividad"].value_counts(normalize=True, dropna=False)
    raras = freq[freq < 0.02].index.tolist()
    df["ult_actividad"] = df["ult_actividad"].where(~df["ult_actividad"].isin(raras), "Otros")

    X_raw = df.drop(columns=["compra", "id"])
    preprocesador = joblib.load(PREPROCESADOR)
    transformada = preprocesador.transform(X_raw)
    nombres = [
        NAME_MAP.get(n, n.replace("categorical__", "").replace("binary__", ""))
        for n in preprocesador.get_feature_names_out()
    ]
    features = pd.DataFrame(transformada, index=df.index, columns=nombres)
    finalistas = [l.strip() for l in FINALISTAS.read_text(encoding="utf-8").splitlines() if l.strip()]
    X_final = features.loc[:, finalistas]
    params = json.loads(CONFIG.read_text(encoding="utf-8"))["parametros"]
    modelo = LogisticRegression(
        C=float(params["C"]), penalty=params["penalty"], solver=params["solver"],
        max_iter=int(params["max_iter"]), random_state=int(params["random_state"]),
    ).fit(X_final, df["compra"])
    return modelo, X_final, df, df_train, df_validation, finalistas


@pytest.fixture(scope="module")
def oraculo():
    return _oraculo_notebook08()


@pytest.fixture(scope="module")
def produccion():
    modulo = _cargar_script()
    pipeline, meta = modulo.entrenar(ROOT)
    return modulo, pipeline, meta


def test_usa_las_40_finalistas_y_la_configuracion_congelada(produccion, oraculo):
    _, pipeline, meta = produccion
    *_, finalistas = oraculo
    modelo = pipeline[-1]

    assert meta["variables"] == finalistas and len(finalistas) == 40
    assert modelo.coef_.shape == (1, 40)
    assert modelo.get_params()["penalty"] == "l2"
    assert modelo.get_params()["C"] == pytest.approx(14.528246637516036)
    assert modelo.get_params()["solver"] == "saga"


def test_entrena_solo_con_el_70_y_nunca_con_validation(produccion, oraculo):
    _, _, meta = produccion
    _, _, df, df_train, df_validation, _ = oraculo

    assert meta["n_entrenamiento"] == len(df)
    assert set(meta["ids_entrenamiento"]) == set(df["id"])
    assert not set(meta["ids_entrenamiento"]) & set(df_validation["id"])
    assert set(df_validation["id"]) == set(pd.read_pickle(ROOT / "02_datos/02_Validacion/validation.pkl")["id"])


def test_las_probabilidades_coinciden_con_el_notebook_08(produccion, oraculo):
    _, pipeline, _ = produccion
    modelo, X_final, df, df_train, *_ = oraculo

    crudo = df_train.loc[df.index].drop(columns=["compra", "id"])  # raw rows, as the API sends them
    esperado = modelo.predict_proba(X_final)[:, 1]
    obtenido = pipeline.predict_proba(crudo)[:, 1]
    assert np.allclose(obtenido, esperado, atol=1e-8)


def test_acepta_solo_los_12_campos_de_la_api(produccion):
    _, pipeline, _ = produccion
    lead = pd.DataFrame([{"origen": "API", "fuente": "Chat", "ocupacion": "Student"}], columns=API_FIELDS)

    score = pipeline.predict_proba(lead)[0, 1]
    assert 0.0 < score < 1.0


def test_el_artefacto_se_carga_sin_importar_el_script(produccion, tmp_path):
    modulo, pipeline, _ = produccion
    ruta = tmp_path / "artefacto.pkl"
    modulo.guardar(pipeline, ruta)

    codigo = (
        "import sys, cloudpickle, pandas as pd;"
        "assert 'reentrenamiento' not in sys.modules;"
        f"p = cloudpickle.load(open({str(ruta)!r}, 'rb'));"
        "x = pd.DataFrame([{'origen': 'API', 'fuente': 'Chat'}]);"
        "print(p.predict_proba(x)[0, 1])"
    )
    salida = subprocess.run([sys.executable, "-W", "ignore", "-c", codigo], capture_output=True, text=True)
    assert salida.returncode == 0, salida.stderr[-600:]
    assert 0.0 < float(salida.stdout.strip().splitlines()[-1]) < 1.0


def test_campos_vacios_no_rompen_y_equivalen_a_la_categoria_de_referencia(produccion):
    _, pipeline, _ = produccion
    base = {c: None for c in API_FIELDS}
    vacio = pd.DataFrame([{**base, "fuente": "Chat"}], columns=API_FIELDS)
    referencia = pd.DataFrame(
        [{**base, "fuente": "Chat", "origen": "API", "no_enviar_email": "No", "descarga_lm": "No"}],
        columns=API_FIELDS,
    )

    assert pipeline.predict_proba(vacio)[0, 1] == pytest.approx(pipeline.predict_proba(referencia)[0, 1])
