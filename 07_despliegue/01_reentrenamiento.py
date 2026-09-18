from pathlib import Path

import cloudpickle
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import FeatureUnion, make_pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, OneHotEncoder, PowerTransformer

CSV_PATH = Path("02_datos/01_Originales/Leads.csv")
ARTEFACTO_PATH = Path("07_despliegue/artefacto_pipeline.pkl")
TARGET = "compra"
ID_COLUMN = "id"
SEP = ";"


def prepara_datos(df):
    mask_extremos = (df["visitas_total"] > 30) | (df["paginas_vistas_visita"] > 20)
    aceptados = df.loc[~mask_extremos].copy()
    rechazados = df.loc[mask_extremos].copy()
    rechazados["motivo_rechazo"] = "extremo_aprobado"
    return aceptados, rechazados


def normaliza_fuente(df):
    resultado = df.copy()
    resultado["fuente"] = resultado["fuente"].replace({"google": "Google"})
    return resultado


categoricas_generales = make_pipeline(SimpleImputer(strategy="constant", fill_value="Desconocido"), OneHotEncoder(drop="first", handle_unknown="ignore"))
ult_actividad_transformer = make_pipeline(SimpleImputer(strategy="constant", fill_value="Desconocido"), OneHotEncoder(drop="first", handle_unknown="ignore", min_frequency=0.02))
binarias = make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(drop="first", handle_unknown="ignore"))
comportamiento = make_pipeline(SimpleImputer(strategy="median"), PowerTransformer(method="yeo-johnson"), MinMaxScaler())
visitas_total_transformer = FeatureUnion([("valor", comportamiento), ("faltante", MissingIndicator(features="missing-only"))])
score_actividad_transformer = FeatureUnion([("valor", make_pipeline(SimpleImputer(strategy="median"), MinMaxScaler())), ("faltante", MissingIndicator(features="missing-only"))])
score_perfil_transformer = make_pipeline(SimpleImputer(strategy="median"), MinMaxScaler())

preprocesador = make_column_transformer(
    (categoricas_generales, ["origen", "fuente", "ambito", "ocupacion"]),
    (ult_actividad_transformer, ["ult_actividad"]),
    (binarias, ["no_enviar_email", "descarga_lm"]),
    (visitas_total_transformer, ["visitas_total"]),
    (comportamiento, ["tiempo_en_site_total", "paginas_vistas_visita"]),
    (score_actividad_transformer, ["score_actividad"]),
    (score_perfil_transformer, ["score_perfil"]),
    remainder="drop",
)
modelo_base = LogisticRegression(solver="saga", max_iter=5000, random_state=42)
pipeline = make_pipeline(FunctionTransformer(normaliza_fuente, validate=False), preprocesador, modelo_base)
param_distributions = {"logisticregression__C": np.logspace(-3, 2, 100), "logisticregression__penalty": ["l1", "l2"]}
search = RandomizedSearchCV(estimator=pipeline, param_distributions=param_distributions, n_iter=25, scoring="roc_auc", cv=3, random_state=42, refit=True, n_jobs=1)

df = pd.read_csv(CSV_PATH, sep=SEP, encoding="utf-8")
df_entrenamiento, df_rechazados = prepara_datos(df)
X = df_entrenamiento.drop(columns=[TARGET, ID_COLUMN])
y = df_entrenamiento[TARGET]
search.fit(X, y)
mejor_pipeline = search.best_estimator_
ARTEFACTO_PATH.parent.mkdir(parents=True, exist_ok=True)
with ARTEFACTO_PATH.open("wb") as archivo:
    cloudpickle.dump(mejor_pipeline, archivo)

print(search.best_params_)
print(search.best_score_)
print(f"Filas excluidas por extremos: {len(df_rechazados)}")
