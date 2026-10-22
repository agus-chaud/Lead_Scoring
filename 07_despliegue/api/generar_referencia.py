"""Regenerate referencia_explicacion.json (the "average lead" used by /explain).

Run it from 07_despliegue/ after every retraining:  python -m api.generar_referencia
It scores the leads the production model is fitted on: the training split of the contract in
pre-produccion/00_manifiesto_preproduccion.json (see 01_reentrenamiento.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from api.scoring import REFERENCIA_PATH, calcular_referencia

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "02_datos" / "01_Originales" / "Leads.csv"
MANIFIESTO_PATH = ROOT / "07_despliegue" / "pre-produccion" / "00_manifiesto_preproduccion.json"


def main() -> None:
    split = json.loads(MANIFIESTO_PATH.read_text(encoding="utf-8"))["split"]
    leads = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    df_train, _ = train_test_split(leads, test_size=split["ratio_validation"], random_state=split["seed"])
    referencia = calcular_referencia(df_train)
    REFERENCIA_PATH.write_text(
        json.dumps(referencia, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"{REFERENCIA_PATH.name}: {referencia['n_filas']} leads, score medio {referencia['score_medio']:.3f}")


if __name__ == "__main__":
    main()
