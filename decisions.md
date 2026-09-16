# Registro de Decisiones Técnicas

Por qué se tomó cada decisión, el código ya explica qué se hizo.

**El razonamiento completo está en [`decisions_detalle.md`](decisions_detalle.md)** — mismos IDs y mismo orden.

---

## Índice

| ID | Área | Decisión |
|----|------|----------|
| DEC-001 | importacion | Integrar la única fuente sin merge ni concat |
| DEC-002 | calidad-datos | Preservar faltantes informativos e imputar sin borrar evidencia |
| DEC-003 | eda | Explorar por tipo sin eliminar variables automáticamente |
| DEC-004 | importacion | Dividir train/validación 70/30 reproduciblemente |
| DEC-005 | calidad-datos | Recortar extremos con umbrales explícitos aprobados |

---

## Pendientes reales

| Decisión | Área |
|---|---|

---

## Decisiones

**DEC-001 — Integración de fuentes.** Se mantuvo `Leads.csv` como única tabla y se asignó `df = leads.copy()`. **Por qué:** solo existía una fuente importable. **Regla:** analizar siempre grano y clave antes de integrar nuevas fuentes.

**DEC-002 — Política de faltantes y categorías.** Se preservaron scores faltantes, se imputaron faltantes categóricos/numéricos y se normalizó `google` a `Google`. **Por qué:** los faltantes de scores son estructurales y 63 de las 92 filas con faltantes de actividad tenían compra. **Regla:** preservar faltantes con significado e imputar con parámetros de train.

**DEC-003 — Criterios de tipeo y lectura exploratoria.** Se analizó el tablón por tipo y por lotes, agrupando las categorías minoritarias de `fuente` y las categorías de `ult_actividad` bajo 2% como `Otros`, sin tratar `id` como predictor. **Por qué:** esto mejora la lectura sin eliminar evidencia relevante y mantiene separada la exploración de la selección. **Regla:** explorar primero, agrupar categorías solo con un criterio explícito y seleccionar variables mediante una decisión posterior.

**DEC-004 — División entrenamiento-validación.** Se utilizó `train_test_split` 70/30 con `random_state=42`, sin IDs compartidos. **Por qué:** `id` era única y no había grupos repetidos. **Regla:** mantener una validación independiente y reproducible.

**DEC-005 — Recorte de extremos de comportamiento.** Se eliminaron 5 filas con `visitas_total > 30` o `paginas_vistas_visita > 20`. **Por qué:** eran valores extremadamente aislados según el análisis descendente. **Regla:** recortar solo con umbrales explícitos, documentados y aprobados.

---
