# Informe de calidad de datos

## Resumen

- Filas iniciales del train: 6365
- Filas finales: 6360
- Columnas finales: 23
- Fecha: 2026-09-16

## Problemas detectados y decisiones

- Los nombres de columnas ya estaban normalizados: 0 cambios y 0 colisiones.
- No se aplicó deduplicación: el análisis previo encontró 0 filas duplicadas e `id` único.
- `score_actividad` y `score_perfil` conservan sus faltantes estructurales para usuarios nuevos.
- Faltantes categóricos en `ocupacion`, `ambito`, `ult_actividad` y `fuente` se imputaron como `Desconocido`.
- Faltantes numéricos en `visitas_total` y `paginas_vistas_visita` se imputaron con la mediana del train y se agregaron indicadores de missingness.
- `fuente` se normalizó unificando `google` con `Google`.
- Se eliminaron registros con `visitas_total > 30` o `paginas_vistas_visita > 20`: 5 filas.
- `id` se conserva para trazabilidad, pero se excluye como predictor.

## Transformaciones por variable

| Variable | Transformaciones aplicadas |
|---|---|
| `ocupacion` | Imputación constante `Desconocido` |
| `ambito` | Imputación constante `Desconocido` |
| `ult_actividad` | Imputación constante `Desconocido` |
| `fuente` | Imputación constante `Desconocido`; `google` → `Google` |
| `visitas_total` | Imputación con mediana; eliminación de filas > 30; indicador `visitas_total_missing` |
| `paginas_vistas_visita` | Imputación con mediana; eliminación de filas > 20; indicador `paginas_vistas_visita_missing` |
| `score_actividad` | Sin transformación; se preservan NaN estructurales |
| `score_perfil` | Sin transformación; se preservan NaN estructurales |
| `id` | Sin transformación; excluir durante modelado |

## Estructura final

```
<class 'pandas.core.frame.DataFrame'>
Index: 6360 entries, 2954 to 7270
Data columns (total 23 columns):
 #   Column                         Non-Null Count  Dtype  
---  ------                         --------------  -----  
 0   id                             6360 non-null   int64  
 1   origen                         6360 non-null   object 
 2   fuente                         6360 non-null   object 
 3   no_enviar_email                6360 non-null   object 
 4   no_llamar                      6360 non-null   object 
 5   compra                         6360 non-null   int64  
 6   visitas_total                  6360 non-null   float64
 7   tiempo_en_site_total           6360 non-null   int64  
 8   paginas_vistas_visita          6360 non-null   float64
 9   ult_actividad                  6360 non-null   object 
 10  ambito                         6360 non-null   object 
 11  ocupacion                      6360 non-null   object 
 12  conociste_google               6360 non-null   object 
 13  conociste_revista              6360 non-null   object 
 14  conociste_periodico            6360 non-null   object 
 15  conociste_youtube              6360 non-null   object 
 16  conociste_facebook             6360 non-null   object 
 17  conociste_referencias          6360 non-null   object 
 18  score_actividad                3437 non-null   float64
 19  score_perfil                   3437 non-null   float64
 20  descarga_lm                    6360 non-null   object 
 21  visitas_total_missing          6360 non-null   int8   
 22  paginas_vistas_visita_missing  6360 non-null   int8   
dtypes: float64(4), int64(3), int8(2), object(14)
memory usage: 1.1+ MB
```

## Artefactos

- Dataframe limpio: `02_datos/03_Entrenamiento/02_train_tablon_calidad.pkl`
- Especificación: `06_resultados/Calidad_Datos/transformaciones.json`
