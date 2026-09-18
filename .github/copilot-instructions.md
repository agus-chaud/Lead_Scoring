## ESTADO ACTUAL DEL PROYECTO

**Fase completada**: A_09_Pipelines

**Scripts de producción**: `07_despliegue/01_reentrenamiento.py`, `07_despliegue/02_produccion_scoring.py`

**Artefacto**: `07_despliegue/artefacto_pipeline.pkl` (se genera al ejecutar 01)

**Siguiente paso**: el usuario ejecuta `01_reentrenamiento.py`, luego `02_produccion_scoring.py`. Para servirlo: `/ds-12-desplegar-batch` (A_10, ejecución programada) o `/ds-13-desplegar-api` (A_11, API FastAPI)