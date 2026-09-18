import argparse
from pathlib import Path

import cloudpickle
import pandas as pd

ARTEFACTO_PATH = Path("07_despliegue/artefacto_pipeline.pkl")
ID_COLUMN = "id"
SEP = ";"
UMBRAL = 0.5  # Default business threshold; review with Commercial before deployment.


def prepara_datos(df):
    mask_extremos = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    aceptados = df.loc[~mask_extremos].copy()
    rechazados = df.loc[mask_extremos].copy()
    rechazados["motivo_rechazo"] = "extremo_aprobado"
    return aceptados, rechazados


parser = argparse.ArgumentParser(description="Genera scores para leads nuevos.")
parser.add_argument("--input", required=True, help="CSV de leads crudos.")
parser.add_argument("--output", required=True, help="CSV de scores generado.")
args = parser.parse_args()

df_entrada = pd.read_csv(args.input, sep=SEP, encoding="utf-8")
df_aceptados, df_rechazados = prepara_datos(df_entrada)
with ARTEFACTO_PATH.open("rb") as archivo:
    pipeline = cloudpickle.load(archivo)

X = df_aceptados.drop(columns=[ID_COLUMN], errors="ignore")
scores = pipeline.predict_proba(X)[:, 1]
resultado = pd.DataFrame({ID_COLUMN: df_aceptados[ID_COLUMN].to_numpy(), "score": scores, "prediccion": (scores >= UMBRAL).astype(int)})
resultado.to_csv(args.output, index=False)

ruta_salida = Path(args.output)
ruta_rechazados = ruta_salida.with_name(f"{ruta_salida.stem}_rechazados.csv")
df_rechazados.to_csv(ruta_rechazados, index=False)
print(f"Scores generados: {len(resultado)}")
print(f"Leads rechazados por extremos: {len(df_rechazados)}")
