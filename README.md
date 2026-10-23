# Lead Scoring

Lead Scoring es un sistema para **ordenar leads comerciales según su probabilidad de compra**. Ayuda al equipo comercial a decidir a quién contactar primero.

> Las decisiones técnicas están documentadas en [`decisions.md`](decisions.md) y [`decisions_detalle.md`](decisions_detalle.md).

## ¿Qué problema resuelve?

Sin un criterio objetivo, todos los leads parecen igual de importantes. Eso hace que el equipo comercial invierta tiempo en contactos con baja probabilidad de compra mientras oportunidades valiosas pueden quedar sin seguimiento.

## ¿Cómo funciona?

1. **Captación y perfil:** incorpora canal de adquisición, ocupación, ámbito de interés y señales de perfil.
2. **Comportamiento:** considera visitas, páginas vistas, tiempo en el sitio y última actividad.
3. **Preparación:** trata faltantes, normaliza categorías, controla extremos y transforma las variables.
4. **Scoring:** el pipeline estima la probabilidad de compra y produce una predicción operativa.
5. **Acción comercial:** ventas prioriza la cartera según el score; el modelo apoya la decisión, no reemplaza el criterio comercial.

## Impacto de negocio

- **Mejor asignación del esfuerzo comercial:** permite priorizar los leads con mayor potencial y medir si mejora el contacto efectivo y la conversión.
- **Priorización consistente:** reduce la dependencia de la intuición individual para ordenar la cartera.
- **Explicabilidad:** la regresión logística con splines sigue siendo aditiva, lo que permite descomponer cada score en el aporte exacto de cada variable frente a un lead promedio (`POST /explain`, DEC-017).
- **Trazabilidad:** los leads con valores extremos quedan identificados con su motivo de rechazo, sin desaparecer silenciosamente del proceso.

## Modelo y evaluación

- Target: `compra`, clasificación binaria.
- Positivos: **37,48 %**; no se aplica balanceo porque la proporción no es extrema.
- Predictoras finales: **40**, seleccionadas con RFECV y análisis de correlación.
- Familia evaluada: **Logistic Regression**, priorizada por su explicabilidad para el equipo comercial. El modelo desplegado agrega **splines** cúbicos (6 nodos) a las 4 variables continuas para capturar efectos no lineales (DEC-019).
- Configuración: `C=1.2229`, `penalty="l2"`, `solver="saga"`, `max_iter=5000`, entrenada con el 70 % de los leads.
- ROC AUC medio en validación cruzada (desarrollo): **0,9106** (la logística lineal daba 0,8919).
- Validación externa (`02_datos/02_Validacion/validation.pkl`, 2.722 leads no vistos): ROC AUC **0,910**, precisión 0,806 y recall 0,764 con el corte 0,5, frente a 0,887, 0,776 y 0,714 de la logística lineal. Detalle en `06_resultados/Modelizacion/evaluacion_validacion.json`.

## Cómo interpretar el resultado

- `score`: probabilidad estimada de compra para un lead. Es una señal continua para ordenar prioridades, no una garantía de conversión.
- `prediccion`: resultado técnico de aplicar el umbral actual de `0,5` al score.

## Pipeline productivo

El flujo de producción es:

```text
CSV crudo → control de extremos → calidad y reglas de categorías → preprocesador congelado → 40 variables finalistas → splines en las 4 continuas → Logistic Regression → score y predicción
```

- `07_despliegue/01_reentrenamiento.py` sigue el contrato de `07_despliegue/pre-produccion/00_manifiesto_preproduccion.json` (DEC-016) y la configuración de `06_resultados/Modelizacion/config_mejor_modelo.json` (DEC-019): reutiliza el preprocesador congelado y las 40 variables finalistas, reentrena solo los splines y la regresión logística con el 70 % de los leads y serializa el artefacto.
- `07_despliegue/03_evaluar_validacion.py` evalúa el artefacto sobre `validation.pkl`. Ejecutalo una sola vez después de reentrenar y no ajustes el modelo a partir del resultado.
- `07_despliegue/02_produccion_scoring.py` carga el artefacto y genera un CSV con `id`, `score` y `prediccion`.
- `07_despliegue/api/` expone el mismo motor mediante FastAPI con `POST /predict`, `POST /explain`, `GET /health` y `GET /debug`.
- Los leads excluidos por extremos se escriben en un CSV separado en batch; la API los rechaza con HTTP 422.

## Cómo ejecutar batch

1. Instalá las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Reentrená y generá el artefacto del pipeline. La API lee su propia copia y su referencia de explicaciones, así que hay que actualizarlas:

   ```bash
   python 07_despliegue/01_reentrenamiento.py
   cp 07_despliegue/artefacto_pipeline.pkl 07_despliegue/api/artefacto_pipeline.pkl
   cd 07_despliegue && python -m api.generar_referencia
   python 03_evaluar_validacion.py
   ```

   **Después de cada reentrenamiento actualizá a mano las cifras de rendimiento de `07_despliegue/mcp_server/ficha_modelo.md`** (AUC, precisión, recall y top-k) con lo que escribe `06_resultados/Modelizacion/evaluacion_validacion.json`. Esos números no se actualizan solos. El test `07_despliegue/tests/test_evaluacion_y_batch.py` falla si el JSON es de otro artefacto o si la ficha muestra un AUC, una precisión o un recall distintos a los del JSON; si falla tras reentrenar, es el recordatorio de este paso.

3. Generá scores para leads nuevos:

   ```bash
   python 07_despliegue/02_produccion_scoring.py --input ruta/al/archivo.csv --output ruta/al/scoring.csv
   ```

## Camino rápido: usar la API

Desde `07_despliegue/api/`, con el entorno del proyecto activo:

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --app-dir ..
```

Verificá que el servicio esté disponible:

```bash
curl http://127.0.0.1:8000/health
```

Enviá siempre una lista JSON, incluso para un solo lead:

```json
[
  {
    "id": 660737,
    "origen": "API",
    "fuente": "Chat",
    "no_enviar_email": "No",
    "visitas_total": 0.0,
    "tiempo_en_site_total": 0,
    "paginas_vistas_visita": 0.0,
    "ult_actividad": "Page Visited on Website",
    "ambito": "Select",
    "ocupacion": "Unemployed",
    "score_actividad": 15.0,
    "score_perfil": 15.0,
    "descarga_lm": "No"
  }
]
```

La respuesta conserva una fila por lead aceptado:

```json
[
  {
    "id": 660737,
    "score": 0.14467028562707906,
    "prediccion": 0
  }
]
```

La documentación interactiva está disponible en `http://127.0.0.1:8000/docs`.

## Usar el modelo desde Claude (servidor MCP)

`07_despliegue/mcp_server/` expone la API como servidor MCP. Un usuario sin conocimientos técnicos pide el score en lenguaje natural y Claude llama a la API. El servidor no contiene lógica de modelo: cada score sale de la API (DEC-018).

Herramientas: `score_lead` (un lead), `score_leads` (lote), `explain_score` (por qué ese score) y `check_api_health`. El recurso `leadscoring://ficha-modelo` (fuente: `07_despliegue/mcp_server/ficha_modelo.md`) explica en lenguaje simple qué hace el modelo, qué tan bien funciona y sus límites. El recurso `leadscoring://variables` documenta los campos, sus límites y la advertencia de leakage de `ult_actividad` y `ocupacion` (DEC-014).

1. Levantá la API (sección anterior). Usá un entorno con las versiones de `07_despliegue/api/requirements.txt`: con otra versión de scikit-learn `/predict` responde 500.
2. Instalá las dependencias del MCP: `pip install -r 07_despliegue/mcp_server/requirements.txt`.
3. Registralo en el cliente MCP. Ejemplo para Claude Desktop (`claude_desktop_config.json`), con rutas absolutas:

```json
{
  "mcpServers": {
    "lead-scoring": {
      "command": "python",
      "args": ["C:/ruta/al/proyecto/07_despliegue/mcp_server/server.py"],
      "env": { "SCORING_API_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

### Explicar un score

`explain_score` usa el endpoint `POST /explain` de la API (DEC-017). Descompone el score en el aporte de cada variable **frente a un lead promedio** (el promedio de los 6.360 leads de entrenamiento, 29,2% de score). La descomposición es exacta porque el modelo es una regresión logística: con splines, cada variable continua aporta la suma de sus columnas de curva. Un factor `x0,11` significa que esa variable reduce las chances de compra a un 11% de las de un lead típico.

La referencia vive en `07_despliegue/api/referencia_explicacion.json`. Si reentrenás el modelo, regenerala desde `07_despliegue/`; mientras no coincida con el modelo, `/explain` falla con un mensaje que lo indica:

```bash
python -m api.generar_referencia
```

Tests: `cd 07_despliegue/mcp_server && python -m pytest` (MCP) y `cd 07_despliegue/api && python -m pytest` (API, con el entorno de `api/requirements.txt`; la API necesita además `httpx` para los tests).

## Qué falta para medir impacto real

- Medir conversión, contacto efectivo y tiempo comercial por segmentos de score después de ponerlo operativo.
- Monitorear drift en variables de entrada, categorías nuevas y distribución de scores.
- Revisar la calibración y el umbral `0,5` con evidencia de negocio antes de definir reglas comerciales de priorización.
- Resolver los pendientes técnicos listados en `decisions.md` (DEC-015, defectos de `/predict` con lista vacía y valores negativos, migración a `mcp` 2.x).

## Organización del proyecto

- `01_Documentos/`: diseño de transformaciones y variables aprobadas.
- `02_datos/`: datos originales, entrenamiento, validación y tablones intermedios.
- `03_notebooks/08_Preproduccion.ipynb`: flujo consolidado de preproducción.
- `05_modelos/`: preprocesadores y modelos del proyecto.
- `06_resultados/`: informes, rankings, configuraciones y gráficos.
- `07_despliegue/pre-produccion/00_manifiesto_preproduccion.json`: contrato del pipeline.
- `07_despliegue/01_reentrenamiento.py`: reentrenamiento y serialización del pipeline.
- `07_despliegue/02_produccion_scoring.py`: scoring batch de datos nuevos.
- `07_despliegue/api/`: API FastAPI, contrato, payload de prueba, cliente de ejemplo, referencia de explicaciones y sus tests.
- `07_despliegue/tests/`: tests del reentrenamiento, la evaluación y el batch.
- `07_despliegue/03_evaluar_validacion.py`: evaluación única sobre `validation.pkl`.
- `07_despliegue/mcp_server/`: servidor MCP que expone la API a clientes como Claude.
- `requirements.txt`: dependencias fijadas para reproducibilidad.
- `decisions.md` y `decisions_detalle.md`: registro de decisiones técnicas.
