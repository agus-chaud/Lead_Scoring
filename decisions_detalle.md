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
