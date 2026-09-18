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
- **Explicabilidad:** la regresión logística permite identificar las señales que impulsan o reducen el score.
- **Trazabilidad:** los leads con valores extremos quedan identificados con su motivo de rechazo, sin desaparecer silenciosamente del proceso.

## Modelo y evaluación

- Target: `compra`, clasificación binaria.
- Positivos: **37,48 %**; no se aplica balanceo porque la proporción no es extrema.
- Predictoras finales: **40**, seleccionadas con RFECV y análisis de correlación.
- Única familia evaluada: **Logistic Regression**, priorizada por su explicabilidad para el equipo comercial.
- Configuración candidata: `C=14.5282`, `penalty="l2"`, `solver="saga"`, `max_iter=5000`.
- ROC AUC medio en validación cruzada: **0,8919**.
- Validación externa reservada: `02_datos/02_Validacion/validation.pkl`.

## Cómo interpretar el resultado

- `score`: probabilidad estimada de compra para un lead. Es una señal continua para ordenar prioridades, no una garantía de conversión.
- `prediccion`: resultado técnico de aplicar el umbral actual de `0,5` al score.

## Pipeline productivo

El flujo de producción es:

```text
CSV crudo → control de extremos → transformaciones → Logistic Regression → score y predicción
```

- `07_despliegue/01_reentrenamiento.py` reconstruye el pipeline, busca la mejor configuración logística y serializa el artefacto.
- `07_despliegue/02_produccion_scoring.py` carga el artefacto y genera un CSV con `id`, `score` y `prediccion`.
- `07_despliegue/api/` expone el mismo motor mediante FastAPI con `POST /predict`, `GET /health` y `GET /debug`.
- Los leads excluidos por extremos se escriben en un CSV separado en batch; la API los rechaza con HTTP 422.

## Cómo ejecutar batch

1. Instalá las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Reentrená y generá el artefacto del pipeline:

   ```bash
   python 07_despliegue/01_reentrenamiento.py
   ```

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
    "score": 0.15312413831374566,
    "prediccion": 0
  }
]
```

La documentación interactiva está disponible en `http://127.0.0.1:8000/docs`.

## Qué falta para medir impacto real

- Medir conversión, contacto efectivo y tiempo comercial por segmentos de score después de ponerlo operativo.
- Monitorear drift en variables de entrada, categorías nuevas y distribución de scores.
- Revisar la calibración y el umbral `0,5` con evidencia de negocio antes de definir reglas comerciales de priorización.

## Organización del proyecto

- `01_Documentos/`: diseño de transformaciones y variables aprobadas.
- `02_datos/`: datos originales, entrenamiento, validación y tablones intermedios.
- `03_notebooks/08_Preproduccion.ipynb`: flujo consolidado de preproducción.
- `05_modelos/`: preprocesadores y modelos del proyecto.
- `06_resultados/`: informes, rankings, configuraciones y gráficos.
- `07_despliegue/pre-produccion/00_manifiesto_preproduccion.json`: contrato del pipeline.
- `07_despliegue/01_reentrenamiento.py`: reentrenamiento y serialización del pipeline.
- `07_despliegue/02_produccion_scoring.py`: scoring batch de datos nuevos.
- `07_despliegue/api/`: API FastAPI, contrato, payload de prueba y cliente de ejemplo.
- `requirements.txt`: dependencias fijadas para reproducibilidad.
- `decisions.md` y `decisions_detalle.md`: registro de decisiones técnicas.
