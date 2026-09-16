# Lead Scoring

Lead Scoring es un sistema para **ordenar leads comerciales según su probabilidad de compra**. Ayuda al equipo comercial a decidir a quién contactar primero.

> Las decisiones técnicas están documentadas en [`decisions.md`](decisions.md) y [`decisions_detalle.md`](decisions_detalle.md).

## ¿Qué problema resuelve?

Sin un criterio objetivo, todos los leads se tratan igual. Eso hace que el equipo comercial gaste tiempo en contactos con baja probabilidad mientras puede capaz se le escapan oportunidades valiosas.

## ¿Cómo funciona el proceso de Lead Scoring?

1. **Captación:** una persona llega desde un canal como Google, Direct Traffic, Chat u Organic Search.
2. **Comportamiento:** se observan sus visitas, páginas vistas, tiempo en el sitio y  ¿ltima actividad.
3. **Perfil:** se incorporan datos como ocupación,  ámbito de interés y scores de actividad/perfil cuando están disponibles.
4. **Conversión histórica:** cada registro indica si terminó en `compra`. Esa variable es el objetivo que el modelo aprende a predecir.
5. **Priorización:** el modelo combina las señales y estima una probabilidad de compra. El equipo puede ordenar la cartera de leads de mayor a menor prioridad.
6. **Acción comercial:** ventas decide el contacto y la estrategia. El score es una ayuda para asignar recursos, no una decisión automática sobre el cliente.

## ¿Cómo impacta en el negocio?

- **Mejor uso del tiempo comercial:** se contactan primero los leads con mayor potencial.
- **Más oportunidades capturadas:** se reduce el riesgo de que un lead valioso quede sin seguimiento.
- **Criterio consistente:** las prioridades se basan en datos y no solo en intuición individual.
- **Explicabilidad:** la regresión logística permite explicar qué señales empujan la probabilidad hacia arriba o hacia abajo.
- **Medición:** el desempeño puede monitorearse con ROC AUC, recall, precisión y otras métricas antes de llevar el modelo a producción.

## Estado actual del proyecto

El flujo completó importación, calidad de datos, EDA, transformación, preselección de variables y la primera modelización.

- Target: `compra`, clasificación binaria.
- Positivos: **37,48 %**.
- Balanceo: **no se aplica** porque la proporción no es extrema.
- Predictoras finales: **40**.
- Modelo candidato: regresión logística interpretable.
- Configuración: `C=14.5282`, `penalty="l2"`, `solver="saga"`, `max_iter=5000`.
- ROC AUC medio en validación cruzada: **0,8919**.
- Validación externa reservada: `02_datos/02_Validacion/validation.pkl`.

## Decisiones técnicas resumidas

1. `Leads.csv` se mantuvo como fuente  única.
2. Se separaron entrenamiento y validación con `random_state=42`.
3. Se preservaron faltantes estructurales y se imputaron variables según la matriz aprobada.
4. Se aplicaron One-Hot Encoding, Yeo-Johnson y MinMaxScaler para preparar la regresión logística.
5. RFECV redujo 52 predictoras a 43; la revisión de correlación con umbral 0,70 dejó 40.
6. Se omitió el balanceo de clases y se reservó `validation.pkl` para la evaluación externa.
7. Se congeló la configuración logística por su mejor ROC AUC y su interpretabilidad comercial.

## Organización del proyecto

- `01_Documentos/`: diseños y listas de variables aprobadas.
- `02_datos/`: datos originales, entrenamiento, validación y tablones intermedios.
- `03_notebooks/`: notebooks de importación, calidad, EDA, transformación, preselección y modelización.
- `05_modelos/`: espacio para modelos y preprocesadores de producción.
- `06_resultados/`: informes, rankings, configuraciones y gráficos.
- `07_despliegue/`: espacio reservado para batch, API o aplicación.
- `decisions.md` y `decisions_detalle.md`: registro de decisiones técnicas.

## Próximos pasos

1. Entrenar el modelo de producción con la configuración congelada.
2. Evaluarlo sobre `validation.pkl`, sin usar ese conjunto durante la selección.
3. Comparar la familia de  árboles como alternativa de rendimiento.
4. Preparar los pipelines y el despliegue del scoring.
