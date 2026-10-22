# Registro de Decisiones Técnicas — detalle completo

**Este es el archivo de detalle.** `decisions.md` contiene el índice y los resúmenes cortos.

---

## DEC-001: Integración de fuentes

**Área:** importacion | **Fase:** integración | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Mantener `Leads.csv` como la única tabla analítica y asignar `df = leads.copy()`; no ejecutar merges ni concatenaciones.

**Alternativa descartada:** Integrar mediante merge o concat con otras fuentes.

**Por qué la descartamos:** No existen otras fuentes en `02_datos/01_Originales/`; por lo tanto no hay relaciones, match %, cardinalidades ni pérdida de filas que calcular.

**Conclusión:** Analizar siempre el grano y la clave de cada fuente antes de integrarla; no concatenar ni cruzar fuentes sin evidencia de compatibilidad estructural.

---

## DEC-002: Política de faltantes y categorías

**Área:** calidad-datos | **Fase:** limpieza | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Preservar los faltantes estructurales de `score_actividad` y `score_perfil`; imputar categorías faltantes con `Desconocido`; imputar `visitas_total` y `paginas_vistas_visita` con la mediana y conservar indicadores de missingness; unificar `google` con `Google`.

**Alternativa descartada:** Eliminar todos los registros con faltantes, imputar los scores o reemplazar faltantes numéricos por cero.

**Por qué la descartamos:** Los scores tienen 45,99% de faltantes esperables en usuarios nuevos. Los faltantes de visitas/páginas aparecen en 92 filas y 63 de ellas tienen `compra=1`; eliminarlas o reemplazarlas por cero introduciría sesgo.

**Conclusión:** Preservar los faltantes con significado de negocio e imputar con parámetros ajustados en train, incluyendo indicadores cuando la ausencia pueda ser informativa.

---

## DEC-003: Criterios de tipeo y lectura exploratoria

**Área:** eda | **Fase:** análisis exploratorio | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Analizar el tablón limpio de 6.360 filas y 23 columnas por lotes, usando los umbrales estándar de EDA; recategorizar `fuente` conservando `Google`, `Direct Traffic`, `Chat` y `Organic Search`, y agrupar el resto como `Otros`; unificar en `ult_actividad` todas las categorías con frecuencia individual menor al 2% bajo `Otros`; conservar `id` para trazabilidad, pero excluirlo de la interpretación analítica y predictiva.

**Alternativa descartada:** Eliminar automáticamente variables constantes o casi constantes, forzar todas las variables binarias a numéricas, o tratar `id` como predictor continuo.

**Por qué la descartamos:** Las columnas `conociste_revista`, `conociste_periodico` y `conociste_youtube` son constantes, pero eliminarlas durante EDA mezclaría exploración con selección. En `fuente`, conservar todas las categorías dispersas dificultaba la lectura; las cuatro categorías principales concentran la mayor parte de los registros y el resto se agrupó en `Otros`. En `ult_actividad`, las categorías bajo 2% se agruparon para evitar una lectura fragmentada sin afectar las categorías principales. `id` tiene cardinalidad única y no representa comportamiento de leads.

**Conclusión:** Separar siempre tipeo, exploración y selección de variables; no eliminar columnas durante EDA sin una decisión explícita posterior.

---

## DEC-004: División entrenamiento-validación

**Área:** importacion | **Fase:** split | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Dividir el tablón integrado en 70% entrenamiento y 30% validación mediante `train_test_split(random_state=42)`, usando `id` única como clave de control y sin estratificación en esta fase.

**Alternativa descartada:** Usar un split agrupado o eliminar la validación independiente.

**Por qué la descartamos:** `id` es única, no hay grupos repetidos y el split directo produjo 6.365 filas de train, 2.728 de validación y 0 IDs compartidos.

**Conclusión:** Mantener una validación independiente y reproducible; cambiar a split agrupado solo si futuras fuentes introducen múltiples filas por entidad.

---

## DEC-005: Recorte de extremos de comportamiento

**Área:** calidad-datos | **Fase:** limpieza | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Eliminar registros con `visitas_total > 30` o `paginas_vistas_visita > 20`; se eliminaron 5 filas y el tablón limpio quedó en 6.360 filas.

**Alternativa descartada:** No recortar, hacer clipping de valores o eliminar todos los outliers estadísticos detectados por IQR.

**Por qué la descartamos:** El análisis descendente mostró una cola extremadamente aislada: cuatro filas superaban 30 visitas y una superaba 20 páginas por visita. Se eligieron umbrales explícitos y aprobados, evitando recortar automáticamente valores estadísticos pero plausibles.

**Conclusión:** Aplicar recortes de filas solo con umbrales de negocio explícitos, documentados y aprobados; no confundir outlier estadístico con error.

---

## DEC-006: Estrategia consolidada de feature engineering

**Área:** feature-engineering | **Fase:** transformación | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Congelar una matriz para clasificación binaria con regresión logística: aplicar `OneHotEncoder(drop="first")` a las variables categóricas y binarias de origen objeto; excluir `id` y las tres columnas constantes; aplicar Yeo-Johnson seguido de MinMaxScaler a `visitas_total`, `tiempo_en_site_total` y `paginas_vistas_visita`; y para los scores, imputar por mediana, conservar solo `score_actividad_missing` como indicador estructural (es idéntico a `score_perfil_missing`) y escalar los valores imputados con MinMaxScaler. Mantener `compra` sin transformación, no escalar dummies ni indicadores binarios y excluir `paginas_vistas_visita_missing` por ser idéntico a `visitas_total_missing`.

**Alternativa descartada:** StandardScaler, conservar numéricas sin transformación, codificación ordinal para nominales, incluir `id` o mantener columnas constantes.

**Por qué la descartamos:** MinMaxScaler deja las numéricas en rango 0–1, coherente con las dummies y adecuado para la regresión logística priorizada. La codificación ordinal inventaría un orden; One-Hot sin `drop="first"` introduciría multicolinealidad perfecta. Los NaN de scores son estructurales, de modo que imputarlos sin indicador perdería señal de negocio.

**Conclusión:** Para tablones futuros con este esquema, ajustar los transformadores solo en train, conservar únicamente las representaciones finales y validar filas, target, NaN, columnas intermedias, unicidad de nombres y multicolinealidad binaria.

---

## DEC-007: Preselección supervisada de variables

**Área:** seleccion-variables | **Fase:** preselección | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Aplicar el modo estándar de `ds-07-seleccionar-variables`: `RFECV` con `LogisticRegression` penalizada L1 (`solver="saga"`, `max_iter=5000`), validación `StratifiedKFold` de 5 folds y scoring `roc_auc`. RFECV seleccionó 43 de 52 predictoras. En la revisión de correlación se usó `|Pearson| > 0,70`; se eliminaron por menor importancia supervisada `visitas_total_yj_mm`, `origen_Lead Add Form` y `ocupacion_Unemployed`, quedando 40 variables finales.

**Alternativa descartada:** Omitir preselección, usar el modo comparativo MI + RFECV + permutation importance, mantener el umbral 0,90 o eliminar pares manualmente sin criterio supervisado.

**Por qué la descartamos:** La regresión logística es sensible a variables irrelevantes y correlacionadas; el usuario pidió un conjunto más compacto. El umbral 0,70 detectó tres pares relevantes y la importancia L1 aportó una regla reproducible para elegir cuál conservar, sin eliminar grupos One-Hot completos durante la deduplicación.

**Conclusión:** Para futuros tablones destinados a modelos lineales, ejecutar RFECV supervisado, agrupar derivados por madre, revisar correlación absoluta y documentar cada eliminación antes de persistir el dataset reducido.

---

---

## DEC-008: No aplicar balanceo y fijar entrada de modelización

**Área:** modelado | **Fase:** balanceo/modelización | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** No aplicar técnicas de balanceo de clases porque la clase positiva `compra` representa aproximadamente el 37% del tablón, una proporción suficiente para iniciar la modelización sin sobremuestreo ni submuestreo. El agente de modelización utilizará `02_datos/03_Entrenamiento/05_train_tablon_preseleccion.pkl` como dataframe de entrenamiento.

**Alternativa descartada:** Aplicar SMOTE, sobremuestreo aleatorio, submuestreo o ponderación de clases antes de evaluar los modelos.

**Por qué la descartamos:** Con una prevalencia cercana al 37%, el problema no presenta un desbalance extremo. Se prioriza medir el comportamiento real de la clase positiva y evitar introducir observaciones sintéticas antes de comparar modelos. La decisión podrá revisarse si las métricas de recall, precisión o la matriz de confusión muestran una limitación relevante.

**Conclusión:** Saltar la fase `ds-08-balancear-clases` y continuar con `ds-09-modelizar` usando el tablón preseleccionado, sin modificar el dataset de entrada.


---

## DEC-009: Configuración candidata de modelización

**Área:** modelado | **Fase:** modelización | **Fecha:** 2026-09-16 | **Estado:** Vigente

**Decisión:** Congelar `LogisticRegression` con `C=14.528246637516036`, `penalty="l2"`, `solver="saga"` y `max_iter=5000`. La selección se realizó por ROC AUC medio (0,8919) con `StratifiedKFold` de 5 folds sobre una muestra estratificada del 80% (5.088 filas). Recall, precisión, F1 y accuracy se conservaron como métricas complementarias.

**Alternativa descartada:** Las restantes configuraciones de `C` y penalización del ranking, y la evaluación inmediata sobre `validation.pkl`.

**Por qué la descartamos:** La configuración congelada obtuvo el mejor ROC AUC medio, con desviación estándar 0,0136. La validación externa debe permanecer intacta para medir generalización en una fase posterior.

**Conclusión:** El agente posterior de entrenamiento de producción usará `06_resultados/Modelizacion/config_mejor_modelo.json` y evaluará el modelo final sobre `02_datos/02_Validacion/validation.pkl`.

---

## DEC-010: Consolidación de preproducción con artefactos congelados

**Área:** despliegue | **Fase:** preproducción | **Fecha:** 2026-09-16 | **Estado:** Vigente (aclarada por DEC-016: ese contrato es el que ejecuta producción)

**Decisión:** Consolidar `03_notebooks/08_Preproduccion.ipynb` de forma estática a partir de `Leads.csv`, el preprocesador ajustado, la lista de 40 variables finalistas y `config_mejor_modelo.json`. El notebook carga el preprocesador existente, no reconstruye `Pipeline` ni `ColumnTransformer`, y prepara la `LogisticRegression` con `C=14.528246637516036`, `penalty="l2"`, `solver="saga"` y `max_iter=5000`. No utiliza `validation.pkl`.

**Alternativa descartada:** Reconstruir los transformadores desde el notebook de transformación, volver a ajustar artefactos o utilizar la validación externa durante la consolidación.

**Por qué la descartamos:** `05_modelos/preprocesador.joblib`, `01_Documentos/Variables_preseleccionadas.txt` y `06_resultados/Modelizacion/config_mejor_modelo.json` son los contratos persistidos de las fases ya aprobadas. `01_Importacion_Datos.ipynb` confirma la lectura de `Leads.csv` con separador `;` y codificación UTF-8, pero no contiene el split; DEC-004 documenta el split 70/30 con `random_state=42`, que se reproduce y se deja señalado como riesgo residual.

**Conclusión:** En consolidaciones estáticas, reutilizar artefactos congelados como fuente de verdad y documentar explícitamente cualquier paso cuya implementación no esté presente en el notebook fuente.

**Código afectado:** `03_notebooks/08_Preproduccion.ipynb`, `07_despliegue/pre-produccion/00_resumen_limpieza.md`.

---

## DEC-011: Fijar entorno y persistir reglas categóricas de inferencia

**Área:** despliegue | **Fase:** preproducción | **Fecha:** 2026-09-18 | **Estado:** Vigente

**Decisión:** Incorporar `requirements.txt` con `scikit-learn==1.9.1`, `numpy==2.5.3`, `scipy==1.18.1`, `pandas==3.0.5` y `joblib==1.6.0`; persistir la consolidación categórica en `07_despliegue/pre-produccion/01_reglas_categorias.json`; y cargar esas reglas en `08_Preproduccion.ipynb` antes de usar el preprocesador.

**Alternativa descartada:** Ignorar la advertencia de versiones y recalcular las categorías raras de `ult_actividad` en cada corrida o registro de inferencia.

**Por qué la descartamos:** Cargar artefactos serializados en una versión distinta de scikit-learn no está soportado y puede alterar o interrumpir el scoring. Además, una categoría es rara respecto de la distribución de entrenamiento, no respecto de un lead individual; recalcularla en inferencia cambiaría el contrato de features.

**Conclusión:** El entorno debe instalar las versiones fijadas y las reglas categóricas ajustadas sobre train deben viajar como artefacto versionado junto al preprocesador y el modelo.

**Código afectado:** `requirements.txt`, `07_despliegue/pre-produccion/01_reglas_categorias.json`, `03_notebooks/08_Preproduccion.ipynb`, `07_despliegue/pre-produccion/00_resumen_limpieza.md`.

---
## DEC-012: Búsqueda de reentrenamiento basada en evidencia disponible

**Área:** despliegue | **Fase:** pipelines | **Fecha:** 2026-09-18 | **Estado:** Reemplazada por DEC-016

**Decisión:** El script de reentrenamiento busca hiperparámetros de `LogisticRegression` con penalizaciones L1/L2 y valores de `C` que cubren el rango observado, usando `RandomizedSearchCV` con ROC AUC.

**Alternativa descartada:** Agregar familias de árboles o boosting sin ranking previo.

**Por qué la descartamos:** El ranking persistido solo contiene configuraciones de regresión logística. Inventar familias cambiaría el alcance experimental sin evidencia comparable.

**Conclusión:** El reentrenamiento explora el candidato validado; una comparación de nuevas familias requiere una fase explícita de modelización.

---

## DEC-013: Exponer scoring mediante API REST

**Área:** despliegue | **Fase:** API | **Fecha:** 2026-09-18 | **Estado:** Vigente

**Decisión:** Exponer el motor de inferencia con FastAPI mediante `POST /predict`. El endpoint recibe siempre una lista JSON de registros crudos y devuelve una lista con `id`, `score` y `prediccion`. No se agrega una regla HOT/WARM/COLD.

**Alternativa descartada:** Definir segmentación comercial fija sobre el score o devolver solo una etiqueta sin probabilidad.

**Por qué la descartamos:** No hay umbrales comerciales aprobados ni evidencia de capacidad operativa que justifique HOT/WARM/COLD. Mantener el score entrega la señal continua para que Comercial defina su priorización, mientras que `prediccion` conserva el resultado del umbral técnico de 0,5.

**Conclusión:** El contrato público es simple y trazable. Los registros con `visitas_total > 30` o `paginas_vistas_visita > 20` devuelven HTTP 422, en vez de ser filtrados silenciosamente por el motor. Cualquier regla comercial futura debe documentar sus umbrales, dueño y evidencia.

**Código afectado:** `07_despliegue/api/main.py`, `07_despliegue/api/schemas.py`, `07_despliegue/api/scoring.py`, `07_despliegue/api/test_payload.json`.

---

## DEC-014: Lectura bivariante y auditoría de leakage

**Área:** seleccion-variables | **Fase:** EDA bivariante | **Fecha:** 2026-10-20 | **Estado:** Vigente

**Decisión:** Incorporar al EDA el análisis bivariante contra `compra` (tasa y lift con IC de Wilson, V de Cramér, IV/WoE, Mann-Whitney/AUC univariado y redundancia por Spearman y V de Cramér) como evidencia de apoyo a la preselección, sin eliminar variables solo por un resultado univariante. Auditar `ult_actividad` (IV 0,78) y `ocupacion` (IV 0,94), que superan el IV de 0,5 usado como alerta, mediante ablación en train (CV de 5 folds × 3 repeticiones, configuración de DEC-009, sin usar `validation.pkl`) y controles por engagement y origen. Fijar el supuesto de diseño: el lead se puntúa durante el seguimiento, con la información acumulada hasta ese momento. Con ese supuesto se mantienen ambas variables y el pipeline de DEC-006 a DEC-013 no cambia; el riesgo se documenta y se reportan dos referencias de rendimiento: ROC AUC de 0,8947 con las 40 variables y 0,8376 sin ambas como cota conservadora.

**Alternativa descartada:** Excluir `ult_actividad` o `ocupacion` por precaución, o puntuar en la captura del lead.

**Por qué la descartamos:** No hay evidencia de que sean una fuga y excluirlas tiene un costo medible: quitar `ult_actividad` baja el AUC de 0,8947 a 0,8581 (-0,037), quitar `ocupacion` a 0,8799 (-0,015) y quitar ambas a 0,8376 (-0,057); en los 15 folds pareados todos los escenarios rinden peor. `Working Professional` conserva entre 76% y 96% de compra en cada cuartil de tiempo en el sitio y entre 89% y 95% en cada origen; `SMS Sent` supera a `Email Opened` en los cuatro cuartiles y en `API` y `Landing Page Submission`, de modo que no se explican por engagement ni por canal. Puntuar en la captura dejaría sin `ult_actividad`, comportamiento ni scores: el modelo bajaría a un AUC de 0,7722 y contradiría el diseño vigente.

**Riesgo residual:** Los controles son iguales para una señal legítima que para una fuga. `SMS Sent` (62% de compra) es compatible con un seguimiento posterior a la calificación o al cierre, y el dataset no tiene fecha ni acceso a negocio para descartarlo. Si se obtiene el orden temporal de los eventos y `SMS Sent` resulta posterior al cierre, excluir `ult_actividad` y repetir la cadena 04 → 05 → 07 → 08 (AUC esperado cercano a 0,858).

**Conclusión:** Ante variables con IV o AUC extremo, medir la dependencia del modelo mediante ablación, documentar el supuesto de momento de scoring y reportar el AUC conservador junto al base. Una validación aleatoria no detecta leakage porque la fuga está en train y en validación.

**Código afectado:** `03_notebooks/03_EDA.ipynb`, `03_notebooks/06_Auditoria_Leakage.ipynb`, `06_resultados/EDA/EDA_report.md`.

---

## DEC-015: Categorías raras en ocupacion y ambito

**Área:** feature-engineering | **Fase:** transformación | **Fecha:** 2026-10-20 | **Estado:** Propuesta

**Decisión:** Agrupar bajo `Otros` las categorías con frecuencia individual menor al 1% en `ocupacion` (`Other`, `Housewife`, `Businessman`) y `ambito` (`Services Excellence`, `E-Business`, `Rural and Agribusiness`), y persistir la regla en `01_reglas_categorias.json`.

**Alternativa descartada:** Mantener las categorías raras como dummies propias.

**Por qué la descartamos:** `Housewife` tiene 7 filas con 100% de compra (WoE 3,2) y entra a las 40 variables finales: la regresión logística le asigna un coeficiente inestable. El criterio de frecuencia mínima ya se aplicó a `fuente` y `ult_actividad` (DEC-003).

**Conclusión:** Aplicar el mismo umbral a todas las nominales. Requiere regenerar `preprocesador.joblib` y repetir la cadena 04 → 05 → 07 → 08, por lo que se ejecuta como un único cambio y queda pendiente hasta entonces.

**Código afectado:** `03_notebooks/04_Transformacion.ipynb`, `07_despliegue/pre-produccion/01_reglas_categorias.json`, `07_despliegue/api/`.

---

## DEC-016: Alinear producción con el contrato de los notebooks

**Área:** despliegue | **Fase:** pipelines | **Fecha:** 2026-10-22 | **Estado:** Vigente

**Decisión:** El reentrenamiento de producción sigue el contrato de `00_manifiesto_preproduccion.json`: reglas de calidad y de categorías, `05_modelos/preprocesador.joblib` congelado, las 40 variables de `01_Documentos/Variables_preseleccionadas.txt` y `LogisticRegression(C=14.528246637516036, penalty="l2", solver="saga", max_iter=5000, random_state=42)` entrenada solo con el 70% del split `train_test_split(test_size=0.30, random_state=42)`. Solo se ajusta la regresión logística; no hay búsqueda de hiperparámetros.

**Alternativa descartada:** Mantener el pipeline autónomo de `01_reentrenamiento.py` (12 datos de entrada, 59 columnas, `RandomizedSearchCV`, entrenado con todos los leads) y corregir la documentación.

**Por qué la descartamos:** Ese camino descartaba la selección de variables (DEC-007) y la auditoría de leakage (DEC-014), que se hicieron sobre el modelo de 40 variables, y dejaba al modelo sin validación externa porque ya había visto `validation.pkl`. El README, DEC-007/009/010 y la auditoría describían un modelo distinto del desplegado.

**Conclusión:** Un único camino. El modelo se evaluó una sola vez sobre `validation.pkl` (2.722 leads, 6 rechazados por extremos): ROC AUC 0,887, accuracy 0,813, precisión 0,776, recall 0,714 con corte 0,5; consistente con el AUC de 0,892 de validación cruzada. Supuestos que el contrato no definía: faltantes en `origen`, `no_enviar_email` y `descarga_lm` se codifican como "Desconocido" (ceros, igual que la categoría de referencia); `tiempo_en_site_total` faltante usa la mediana de train; las columnas que la API no recibe (`no_llamar`, `conociste_*`) se completan con "No". Tras cada reentrenamiento hay que regenerar `07_despliegue/api/referencia_explicacion.json`.

**Código afectado:** `07_despliegue/01_reentrenamiento.py`, `07_despliegue/03_evaluar_validacion.py`, `07_despliegue/api/scoring.py`, `07_despliegue/api/generar_referencia.py`, `07_despliegue/tests/`.

---

## DEC-017: Explicabilidad exacta frente a un lead promedio

**Área:** despliegue | **Fase:** API | **Fecha:** 2026-10-22 | **Estado:** Vigente

**Decisión:** Exponer `POST /explain`, que devuelve para cada lead el score, el `logit`, el `logit_referencia` y un factor por variable original con su valor, `contribucion_logit`, efecto (sube, baja o neutro) y `multiplicador_odds`. Las contribuciones se miden frente a un lead promedio calculado con los 6.360 leads de entrenamiento y almacenado en `07_despliegue/api/referencia_explicacion.json` junto con el hash del artefacto. También informa banderas: datos faltantes y variables con posible leakage (`ult_actividad`, `ocupacion`).

**Alternativa descartada:** Usar directamente los términos `coeficiente × valor transformado` del logit, o una aproximación tipo SHAP.

**Por qué la descartamos:** Los términos crudos se miden contra el valor 0 de variables escaladas, no contra un lead típico: el score_actividad de un lead normal salía como +5,84 (×344 las chances) cuando contra el promedio es +0,46 (×1,6), y un lead con datos vacíos parecía tener ventajas enormes. En una regresión logística la descomposición es exacta, así que una aproximación no aporta.

**Conclusión:** La referencia es el promedio de los aportes de cada variable sobre los datos de entrenamiento; el lead promedio puntúa 29,4%. Si el artefacto cambia, la referencia deja de coincidir y `/explain` lo rechaza con un mensaje claro. La explicación describe al modelo, no relaciones causales.

**Código afectado:** `07_despliegue/api/scoring.py`, `07_despliegue/api/schemas.py`, `07_despliegue/api/main.py`, `07_despliegue/api/generar_referencia.py`, `07_despliegue/api/test_explain.py`.

---

## DEC-018: Servidor MCP sin lógica de modelo

**Área:** despliegue | **Fase:** integración | **Fecha:** 2026-10-22 | **Estado:** Vigente

**Decisión:** Publicar `07_despliegue/mcp_server/server.py` (stdio) con las herramientas `score_lead`, `score_leads`, `explain_score` y `check_api_health`, y los recursos `leadscoring://variables` y `leadscoring://ficha-modelo`. El servidor traduce lenguaje natural a llamadas a la API y devuelve resúmenes y avisos en castellano; el score y la explicación siempre salen de la API.

**Alternativa descartada:** Cargar el modelo dentro del servidor MCP, o dejar a un LLM calcular o inferir el score.

**Por qué la descartamos:** Duplicar el modelo crearía una segunda fuente de verdad que se desalinea (como ocurrió entre notebooks y producción, DEC-016). Un LLM que calcule el score no es auditable.

**Conclusión:** La versión de `mcp` queda fijada en 1.30.0 porque la 2.x renombró `FastMCP` a `MCPServer`; el servidor declara `httpx` porque el SDK ya no lo incluye. El umbral 0,5 está duplicado en `server.py` y en `api/scoring.py`. La ficha del modelo se mantiene a mano: las cifras de rendimiento no se actualizan solas. Tras cada reentrenamiento hay que ejecutar `03_evaluar_validacion.py` y copiar AUC, precisión, recall y top-k a la ficha. Dos tests lo vigilan: `test_ficha.py` compara los parámetros con el modelo real, y `test_evaluacion_y_batch.py` falla si `evaluacion_validacion.json` es de otro artefacto o si la ficha muestra un AUC, una precisión o un recall distintos a los del JSON.

**Código afectado:** `07_despliegue/mcp_server/`.
