from __future__ import annotations

from pathlib import Path

import hashlib
import json
import re
from functools import lru_cache

import cloudpickle
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
ARTEFACTO_PATH = BASE_DIR / "artefacto_pipeline.pkl"
ID_COLUMN = "id"
REFERENCIA_PATH = BASE_DIR / "referencia_explicacion.json"
UMBRAL = 0.5


def prepara_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask_extremos = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    aceptados = df.loc[~mask_extremos].copy()
    rechazados = df.loc[mask_extremos].copy()
    rechazados["motivo_rechazo"] = "extremo_aprobado"
    return aceptados, rechazados


with ARTEFACTO_PATH.open("rb") as archivo:
    pipeline = cloudpickle.load(archivo)


VARIABLES = [
    "origen", "fuente", "no_enviar_email", "visitas_total", "tiempo_en_site_total",
    "paginas_vistas_visita", "ult_actividad", "ambito", "ocupacion",
    "score_actividad", "score_perfil", "descarga_lm",
]
# Variables whose leakage could not be ruled out (DEC-014).
VARIABLES_SENSIBLES = ["ult_actividad", "ocupacion"]
_EPS = 1e-6


def _variable_de(nombre_transformado: str) -> str:
    """Map a model column (e.g. 'ocupacion_Student', 'tiempo_en_site_total_yj_mm') to its raw variable."""
    candidatas = [
        v for v in VARIABLES if re.search(rf"(?:^|__|_){re.escape(v)}(?:_|$)", nombre_transformado)
    ]
    if len(candidatas) != 1:
        raise RuntimeError(f"No se pudo asignar '{nombre_transformado}' a una variable: {candidatas}")
    return candidatas[0]


_preprocesador = pipeline[:-1]
_modelo = pipeline[-1]
# The "finalistas" step keeps the 40 columns the model was fitted on, in order.
_VARIABLE_POR_COLUMNA = [_variable_de(n) for n in pipeline.named_steps["finalistas"].kw_args["nombres"]]


def _valor_crudo(valor):
    if pd.isna(valor):
        return None
    return valor.item() if hasattr(valor, "item") else valor


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _aportes_por_variable(X: pd.DataFrame) -> np.ndarray:
    """Per-row contribution to the logit of each raw variable, shape (n_rows, len(VARIABLES))."""
    matriz = _preprocesador.transform(X)
    matriz = matriz.toarray() if hasattr(matriz, "toarray") else np.asarray(matriz)
    por_columna = matriz * _modelo.coef_[0]
    aportes = np.zeros((len(X), len(VARIABLES)))
    for columna, variable in enumerate(_VARIABLE_POR_COLUMNA):
        aportes[:, VARIABLES.index(variable)] += por_columna[:, columna]
    return aportes


def calcular_referencia(df: pd.DataFrame) -> dict:
    """Average contribution of each variable over the leads the model was fitted on."""
    aceptados, _ = prepara_datos(df)
    X = aceptados.drop(columns=[ID_COLUMN, "compra"], errors="ignore")
    aportes = _aportes_por_variable(X)
    logits = _modelo.intercept_[0] + aportes.sum(axis=1)
    return {
        "artefacto_sha256": _sha256(ARTEFACTO_PATH),
        "n_filas": int(len(X)),
        "score_medio": float((1.0 / (1.0 + np.exp(-logits))).mean()),
        "aporte_promedio": dict(zip(VARIABLES, map(float, aportes.mean(axis=0)))),
    }


def cargar_referencia(path: Path = REFERENCIA_PATH) -> dict:
    if not path.exists():
        raise RuntimeError(f"Falta {path.name}. Generala con: python -m api.generar_referencia")
    referencia = json.loads(path.read_text(encoding="utf-8"))
    if referencia.get("artefacto_sha256") != _sha256(ARTEFACTO_PATH):
        raise RuntimeError(
            "La referencia no corresponde al modelo actual. "
            "Regenerala con: python -m api.generar_referencia"
        )
    return referencia


@lru_cache(maxsize=1)
def _referencia() -> tuple[dict[str, float], float]:
    aporte = cargar_referencia()["aporte_promedio"]
    return aporte, float(_modelo.intercept_[0] + sum(aporte.values()))


def explicar_df(df: pd.DataFrame) -> list[dict]:
    """Explain each lead's score against the average lead, as exact logit contributions.

    The model is a logistic regression, so logit = intercept + sum(coef * transformed value).
    Grouping the terms by raw variable and subtracting the average lead's term gives
    logit = logit_referencia + sum(contribucion): "sube"/"baja" mean above/below a typical lead.
    """
    df_aceptados, _ = prepara_datos(df)
    X = df_aceptados.drop(columns=[ID_COLUMN], errors="ignore")
    aporte_referencia, logit_referencia = _referencia()
    aportes = _aportes_por_variable(X)
    logits = float(_modelo.intercept_[0]) + aportes.sum(axis=1)
    scores = 1.0 / (1.0 + np.exp(-logits))

    explicaciones = []
    for i, (_, fila) in enumerate(X.iterrows()):
        valores = {v: _valor_crudo(fila.get(v)) for v in VARIABLES}
        factores = []
        for j, v in enumerate(VARIABLES):
            c = float(aportes[i, j]) - aporte_referencia[v]
            factores.append(
                {
                    "variable": v,
                    "valor": valores[v],
                    "contribucion_logit": c,
                    "efecto": "neutro" if abs(c) < _EPS else ("sube" if c > 0 else "baja"),
                    "multiplicador_odds": float(np.exp(c)),
                }
            )
        factores.sort(key=lambda f: abs(f["contribucion_logit"]), reverse=True)
        explicaciones.append(
            {
                ID_COLUMN: int(df_aceptados[ID_COLUMN].iloc[i]),
                "score": float(scores[i]),
                "prediccion": int(scores[i] >= UMBRAL),
                "logit": float(logits[i]),
                "logit_referencia": logit_referencia,
                "score_referencia": float(1.0 / (1.0 + np.exp(-logit_referencia))),
                "factores": factores,
                "banderas": {
                    "datos_faltantes": [v for v in VARIABLES if valores[v] is None],
                    "variables_sensibles_leakage": [
                        v for v in VARIABLES_SENSIBLES if valores[v] is not None
                    ],
                },
            }
        )
    return explicaciones


def scoring_df(df: pd.DataFrame) -> pd.DataFrame:
    """Score canonical raw leads and return id, score and prediction."""
    df_aceptados, _ = prepara_datos(df)
    X = df_aceptados.drop(columns=[ID_COLUMN], errors="ignore")
    scores = pipeline.predict_proba(X)[:, 1]
    return pd.DataFrame(
        {
            ID_COLUMN: df_aceptados[ID_COLUMN].to_numpy(),
            "score": scores,
            "prediccion": (scores >= UMBRAL).astype(int),
        }
    )
