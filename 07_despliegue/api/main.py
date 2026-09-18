from __future__ import annotations

import json
import platform
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

from api.schemas import RegistroEntrada, ScoringSalida
from api.scoring import scoring_df

BASE_DIR = Path(__file__).resolve().parent
PAYLOAD_PATH = BASE_DIR / "test_payload.json"

app = FastAPI(title="Lead Scoring API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug")
def debug() -> dict[str, object]:
    try:
        payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8-sig"))
        df = pd.DataFrame(payload)
        resultado = scoring_df(df)
        return {
            "python_version": platform.python_version(),
            "status": "OK",
            "input_columns": df.columns.tolist(),
            "output_columns": resultado.columns.tolist(),
            "sample_output": resultado.iloc[0].to_dict() if not resultado.empty else None,
            "engine_error": None,
        }
    except Exception as exc:
        return {
            "python_version": platform.python_version(),
            "status": "ERROR",
            "input_columns": [],
            "output_columns": [],
            "sample_output": None,
            "engine_error": str(exc),
        }


@app.post("/predict", response_model=list[ScoringSalida])
def predict(registros: list[RegistroEntrada]) -> list[ScoringSalida]:
    df = pd.DataFrame([registro.model_dump(by_alias=True) for registro in registros])
    resultado = scoring_df(df)
    return [ScoringSalida(**fila) for fila in resultado.to_dict(orient="records")]
