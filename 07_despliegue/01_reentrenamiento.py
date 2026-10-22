"""Retrain the production pipeline following the contract in 00_manifiesto_preproduccion.json.

Inference path (what the notebooks decided, notebook 08):
    quality + category rules -> frozen preprocessor -> 40 finalist columns -> LogisticRegression

Only the logistic regression is fitted here, on the 70% training split (random_state=42).
The 30% validation split (02_datos/02_Validacion/validation.pkl) is never used for fitting.
Run it from anywhere:  python 07_despliegue/01_reentrenamiento.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cloudpickle
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "02_datos" / "01_Originales" / "Leads.csv"
PREPROCESADOR_PATH = ROOT / "05_modelos" / "preprocesador.joblib"
FINALISTAS_PATH = ROOT / "01_Documentos" / "Variables_preseleccionadas.txt"
CONFIG_PATH = ROOT / "06_resultados" / "Modelizacion" / "config_mejor_modelo.json"
CALIDAD_PATH = ROOT / "06_resultados" / "Calidad_Datos" / "transformaciones.json"
REGLAS_PATH = ROOT / "07_despliegue" / "pre-produccion" / "01_reglas_categorias.json"
ARTEFACTO_PATH = ROOT / "07_despliegue" / "artefacto_pipeline.pkl"
TARGET = "compra"
ID_COLUMN = "id"
SEP = ";"
TEST_SIZE = 0.30
RANDOM_STATE = 42

# Names the frozen preprocessor gives its outputs -> canonical names used by the finalists list.
NOMBRES_CANONICOS = {
    "behavior__visitas_total": "visitas_total_yj_mm",
    "behavior__tiempo_en_site_total": "tiempo_en_site_total_yj_mm",
    "behavior__paginas_vistas_visita": "paginas_vistas_visita_yj_mm",
    "score_values__score_actividad": "score_actividad_mm",
    "score_values__score_perfil": "score_perfil_mm",
    "score_missing__missingindicator_score_actividad": "score_actividad_missing",
}
# The 12 inputs of the scoring API: when absent from a frame they are treated as missing.
CAMPOS_API = [
    "origen", "fuente", "no_enviar_email", "visitas_total", "tiempo_en_site_total",
    "paginas_vistas_visita", "ult_actividad", "ambito", "ocupacion",
    "score_actividad", "score_perfil", "descarga_lm",
]
# Never missing in the training data, so the frozen encoder has no category for NaN. An unseen
# value ("Desconocido") is encoded as all zeros, the same as the dropped reference level.
CATEGORICAS_SIN_FALTANTES_EN_ENTRENAMIENTO = ["origen", "no_enviar_email", "descarga_lm"]
# Columns the frozen preprocessor requires but the API does not receive; near-constant ("No").
COLUMNAS_SIN_API = {
    "no_llamar", "conociste_google", "conociste_facebook", "conociste_referencias",
    "conociste_revista", "conociste_periodico", "conociste_youtube",
}


def prepara_datos(df):
    mask_extremos = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    aceptados = df.loc[~mask_extremos].copy()
    rechazados = df.loc[mask_extremos].copy()
    rechazados["motivo_rechazo"] = "extremo_aprobado"
    return aceptados, rechazados


def preparar_leads(df, pasos, reglas, columnas_requeridas, imputaciones_extra):
    """Quality steps (transformaciones.json) and category rules (01_reglas_categorias.json)."""
    X = df.drop(columns=[TARGET, ID_COLUMN], errors="ignore").copy()
    for campo in CAMPOS_API:
        if campo not in X.columns:
            X[campo] = np.nan
    for paso in pasos:  # flags first: they must see the original missing values
        if paso["op"] == "missing_indicator":
            X[paso["column"]] = X[paso["source_column"]].isna().astype("int8")
    for paso in pasos:
        if paso["op"] == "impute":
            X[paso["column"]] = X[paso["column"]].fillna(paso["value"])
        elif paso["op"] == "unify_categories":
            X[paso["column"]] = X[paso["column"]].replace(paso["mapping"])
    for columna, valor in imputaciones_extra.items():  # numeric inputs never missing in training
        X[columna] = X[columna].fillna(valor)
    for columna in CATEGORICAS_SIN_FALTANTES_EN_ENTRENAMIENTO:
        X[columna] = X[columna].fillna("Desconocido")
    X["fuente"] = X["fuente"].where(X["fuente"].isin(reglas["fuente"]["keep"]), reglas["fuente"]["fallback"])
    raras = reglas["ult_actividad"]["rare_categories"]
    X["ult_actividad"] = X["ult_actividad"].where(
        ~X["ult_actividad"].isin(raras), reglas["ult_actividad"]["fallback"]
    )
    ausentes = set(columnas_requeridas) - set(X.columns)
    desconocidas = ausentes - COLUMNAS_SIN_API
    if desconocidas:
        raise ValueError(f"Faltan columnas que el preprocesador exige: {sorted(desconocidas)}")
    for columna in ausentes:
        X[columna] = "No"
    return X


def seleccionar_columnas(X, indices, nombres):
    """Keep the finalist columns of the preprocessor output (`nombres` documents them)."""
    return X[:, indices]


def cargar_contrato(root=ROOT):
    root = Path(root)
    preprocesador = joblib.load(root / PREPROCESADOR_PATH.relative_to(ROOT))
    nombres = [
        NOMBRES_CANONICOS.get(n, n.replace("categorical__", "").replace("binary__", ""))
        for n in preprocesador.get_feature_names_out()
    ]
    finalistas_path = root / FINALISTAS_PATH.relative_to(ROOT)
    finalistas = [l.strip() for l in finalistas_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    faltantes = sorted(set(finalistas) - set(nombres))
    if faltantes:
        raise ValueError(f"Variables finalistas que el preprocesador no produce: {faltantes}")
    return {
        "preprocesador": preprocesador,
        "nombres": nombres,
        "finalistas": finalistas,
        "indices": [nombres.index(f) for f in finalistas],
        "parametros": json.loads((root / CONFIG_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))["parametros"],
        "pasos": json.loads((root / CALIDAD_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))["steps"],
        "reglas": json.loads((root / REGLAS_PATH.relative_to(ROOT)).read_text(encoding="utf-8")),
    }


def entrenar(root=ROOT):
    """Fit the logistic regression on the training split and return (pipeline, metadata)."""
    root = Path(root)
    contrato = cargar_contrato(root)
    leads = pd.read_csv(root / CSV_PATH.relative_to(ROOT), sep=SEP, encoding="utf-8")
    df_train, df_validation = train_test_split(leads, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    entrenamiento, _ = prepara_datos(df_train)

    preprocesador = contrato["preprocesador"]
    limpieza = FunctionTransformer(
        preparar_leads,
        kw_args={
            "pasos": contrato["pasos"],
            "reglas": contrato["reglas"],
            "columnas_requeridas": list(preprocesador.feature_names_in_),
            "imputaciones_extra": {
                "tiempo_en_site_total": float(df_train["tiempo_en_site_total"].median())
            },
        },
        validate=False,
    )
    seleccion = FunctionTransformer(
        seleccionar_columnas,
        kw_args={"indices": contrato["indices"], "nombres": contrato["finalistas"]},
        validate=False,
    )
    X_final = seleccion.transform(preprocesador.transform(limpieza.transform(entrenamiento)))

    p = contrato["parametros"]
    modelo = LogisticRegression(
        C=float(p["C"]), penalty=p["penalty"], solver=p["solver"],
        max_iter=int(p["max_iter"]), random_state=int(p["random_state"]),
    ).fit(X_final, entrenamiento[TARGET])

    # Assembled from fitted parts: Pipeline.fit would refit the frozen preprocessor.
    pipeline = Pipeline(
        [("limpieza", limpieza), ("preprocesador", preprocesador),
         ("finalistas", seleccion), ("logisticregression", modelo)]
    )
    meta = {
        "variables": contrato["finalistas"],
        "n_entrenamiento": int(len(entrenamiento)),
        "ids_entrenamiento": entrenamiento[ID_COLUMN].tolist(),
        "n_validacion_reservada": int(len(df_validation)),
        "parametros": p,
    }
    return pipeline, meta


def guardar(pipeline, ruta=ARTEFACTO_PATH):
    # Functions defined in this script must travel inside the pickle: the API and the batch
    # script load it without importing this file.
    cloudpickle.register_pickle_by_value(sys.modules[__name__])
    try:
        with Path(ruta).open("wb") as archivo:
            cloudpickle.dump(pipeline, archivo)
    finally:
        cloudpickle.unregister_pickle_by_value(sys.modules[__name__])


if __name__ == "__main__":
    pipeline, meta = entrenar()
    guardar(pipeline)
    print(f"Variables finalistas: {len(meta['variables'])}")
    print(f"Filas de entrenamiento: {meta['n_entrenamiento']} (validación reservada: {meta['n_validacion_reservada']})")
    print(f"Parámetros: {meta['parametros']}")
    print(f"Artefacto: {ARTEFACTO_PATH}")
