"""Evaluate the production artifact ONCE on the reserved validation split.

validation.pkl was never used to fit or tune anything. Run this after retraining, record the
result, and do not adjust the model after looking at it (that would turn it into training data).
    python 07_despliegue/03_evaluar_validacion.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
ARTEFACTO_PATH = ROOT / "07_despliegue" / "artefacto_pipeline.pkl"
CSV_PATH = ROOT / "02_datos" / "01_Originales" / "Leads.csv"
VALIDACION_PATH = ROOT / "02_datos" / "02_Validacion" / "validation.pkl"
MANIFIESTO_PATH = ROOT / "07_despliegue" / "pre-produccion" / "00_manifiesto_preproduccion.json"
SALIDA_PATH = ROOT / "06_resultados" / "Modelizacion" / "evaluacion_validacion.json"
TARGET = "compra"
ID_COLUMN = "id"
UMBRAL = 0.5


def calcular_metricas(y, score):
    y = np.asarray(y)
    score = np.asarray(score)
    pred = (score >= UMBRAL).astype(int)
    orden = np.argsort(-score, kind="stable")
    metricas = {
        "roc_auc": float(roc_auc_score(y, score)),
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred)),
        "recall": float(recall_score(y, pred)),
        "tasa_base": float(y.mean()),
        "proporcion_predicha_compra": float(pred.mean()),
    }
    for fraccion in (0.1, 0.2, 0.3):
        top = y[orden][: int(len(y) * fraccion)]
        metricas[f"top_{int(fraccion * 100)}pct"] = {
            "tasa_compra": float(top.mean()),
            "compradores_capturados": float(top.sum() / y.sum()),
        }
    return metricas


def verificar_sin_solapamiento(ids_entrenamiento, ids_validacion):
    comunes = set(ids_entrenamiento) & set(ids_validacion)
    if comunes:
        raise ValueError(f"Hay {len(comunes)} ids que se solapan entre entrenamiento y validación.")


def main():
    split = json.loads(MANIFIESTO_PATH.read_text(encoding="utf-8"))["split"]
    leads = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    df_train, df_validation = train_test_split(
        leads, test_size=split["ratio_validation"], random_state=split["seed"]
    )
    validacion = pd.read_pickle(VALIDACION_PATH)
    verificar_sin_solapamiento(df_train[ID_COLUMN], validacion[ID_COLUMN])
    if set(validacion[ID_COLUMN]) != set(df_validation[ID_COLUMN]):
        raise ValueError("validation.pkl no coincide con el split del contrato.")

    mask_extremos = (validacion["visitas_total"] > 30) | (validacion["paginas_vistas_visita"] > 20)
    aceptados = validacion.loc[~mask_extremos]
    with ARTEFACTO_PATH.open("rb") as archivo:
        pipeline = cloudpickle.load(archivo)
    score = pipeline.predict_proba(aceptados.drop(columns=[TARGET, ID_COLUMN]))[:, 1]

    resultado = {
        "fecha": date.today().isoformat(),
        "artefacto_sha256": hashlib.sha256(ARTEFACTO_PATH.read_bytes()).hexdigest(),
        "filas_validacion": int(len(validacion)),
        "filas_evaluadas": int(len(aceptados)),
        "filas_rechazadas_por_extremos": int(mask_extremos.sum()),
        "umbral": UMBRAL,
        "metricas": calcular_metricas(aceptados[TARGET], score),
    }
    SALIDA_PATH.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
