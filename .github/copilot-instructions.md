## ESTADO ACTUAL DEL PROYECTO

**Fase completada**: A_11_API_Deployer

**Modo**: `LOCAL + RENDER_ROOT_READY`

**Motor y API**: `07_despliegue/api/scoring.py` carga `07_despliegue/api/artefacto_pipeline.pkl`; `07_despliegue/api/main.py` expone la API FastAPI.

**Contrato final**: `POST /predict`; entrada canónica: lista JSON `[{...}]`; salida: lista JSON de objetos con `id`, `score` y `prediccion`. Ejemplo: `[{"id": 660737, "score": 0.15312413831374566, "prediccion": 0}]`.

**Validación local**: verificada en `http://127.0.0.1:8001` con `uvicorn api.main:app --host 127.0.0.1 --port 8001 --app-dir ..`; `/health`, `/debug` y `/predict` devolvieron resultados correctos. Registros con `visitas_total > 30` o `paginas_vistas_visita > 20` se rechazan con HTTP 422 para evitar que queden sin respuesta silenciosamente.

**Render**: Root Directory `07_despliegue/api`; Build Command `pip install -r requirements.txt`; Start Command `uvicorn api.main:app --host 0.0.0.0 --port $PORT --app-dir ..`; variable manual `PYTHON_VERSION=3.13.7`.

**Siguiente paso**: `/ds-14-app-streamlit` (A_12) consume este contrato de API.