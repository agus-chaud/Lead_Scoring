"""Regenerate referencia_explicacion.json (the "average lead" used by /explain).

Run it from 07_despliegue/ after every retraining:  python -m api.generar_referencia
It scores the same leads the production model is fitted on (see 01_reentrenamiento.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from api.scoring import REFERENCIA_PATH, calcular_referencia

CSV_PATH = Path(__file__).resolve().parents[2] / "02_datos" / "01_Originales" / "Leads.csv"


def main() -> None:
    referencia = calcular_referencia(pd.read_csv(CSV_PATH, sep=";", encoding="utf-8"))
    REFERENCIA_PATH.write_text(
        json.dumps(referencia, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{REFERENCIA_PATH.name}: {referencia['n_filas']} leads, score medio {referencia['score_medio']:.3f}")


if __name__ == "__main__":
    main()
