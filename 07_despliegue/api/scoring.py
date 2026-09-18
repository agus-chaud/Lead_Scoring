from __future__ import annotations

from pathlib import Path

import cloudpickle
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
ARTEFACTO_PATH = BASE_DIR / "artefacto_pipeline.pkl"
ID_COLUMN = "id"
UMBRAL = 0.5


def prepara_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask_extremos = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    aceptados = df.loc[~mask_extremos].copy()
    rechazados = df.loc[mask_extremos].copy()
    rechazados["motivo_rechazo"] = "extremo_aprobado"
    return aceptados, rechazados


with ARTEFACTO_PATH.open("rb") as archivo:
    pipeline = cloudpickle.load(archivo)


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
