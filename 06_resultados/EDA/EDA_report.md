# Informe EDA — Lead Scoring

## Portada

- Dataframe: `df`
- Dimensiones: 6360 filas × 23 columnas
- Fecha: 2026-10-20
- Variables numéricas discretas: 5
- Variables numéricas continuas: 4
- Variables categóricas/booleanas: 14
- Variables de alta cardinalidad: 0
- Variables de texto: 0
- Variables fecha: 0

## Numéricas

- `compra` presenta una proporción positiva de 37,5%, con desbalance moderado.
- `visitas_total`, `paginas_vistas_visita` y `tiempo_en_site_total` tienen asimetría positiva.
- `score_actividad` y `score_perfil` son variables acotadas con 45,96% de faltantes estructurales.
- `id` es un identificador y no debe utilizarse como predictor.

## Categóricas y booleanas

- `fuente` quedó consolidada en `Google`, `Direct Traffic`, `Chat`, `Organic Search` y `Otros`.
- `ult_actividad` conserva las categorías principales y agrupa las categorías con frecuencia individual menor al 2% como `Otros`.
- `ambito` y `ocupacion` mantienen categorías `Desconocido` como información explícita de ausencia.
- `conociste_revista`, `conociste_periodico` y `conociste_youtube` son constantes; no se eliminaron durante el EDA.
- Algunas variables binarias son casi constantes y deberán evaluarse durante selección de variables.

## Alta cardinalidad

No se detectaron variables categóricas con más de 50 valores únicos. La máxima cardinalidad categórica fue `ambito`, con 20 categorías.

## Texto

No existen columnas de texto libre.

## Fechas

No existen columnas de fecha.

## Bivariante contra `compra`

- Asociación con `compra` (V de Cramér / IV): `ocupacion` (0,42 / 0,94), `ult_actividad` (0,39 / 0,78), `origen` (0,29 / 0,44), `ambito` (0,26 / 0,38), `fuente` (0,25 / 0,28). `descarga_lm` casi no aporta (IV 0,003).
- Numéricas (AUC univariado): `tiempo_en_site_total` 0,68, `score_perfil` 0,63, `score_actividad` 0,61, `visitas_total` 0,55 y `paginas_vistas_visita` 0,52.
- `Desconocido` en `ocupacion` (14%) y `ambito` (10%) compra mucho menos que la tasa global (37,5%): la ausencia de perfil es una señal.
- La ausencia de scores no es una señal (37,4% con dato, 37,6% sin dato); las 92 filas con `visitas_total` imputado compran 69%.
- Redundancia: `visitas_total` con `paginas_vistas_visita` (Spearman 0,84); `fuente` con `origen` (V 0,65) y con `descarga_lm` (0,67); `no_enviar_email` con `ult_actividad` (0,65).
- Posible leakage en `ult_actividad` (IV > 0,5) y `ocupacion`: quitarlas baja el ROC AUC de CV de 0,8947 a 0,8581 y 0,8799 (0,8376 sin ambas). Se mantienen bajo el supuesto de scoring durante el seguimiento (DEC-014).

## Transformaciones aplicadas

1. En `fuente`, se conservaron las cuatro categorías principales y el resto se agrupó como `Otros`.
2. En `ult_actividad`, las categorías con frecuencia individual menor al 2% se agruparon como `Otros`.
3. No se eliminaron variables constantes ni se modificó `id`; la selección de variables queda para una fase posterior.

## Resumen global y alertas

- El dataset está concentrado en pocos canales de adquisición y acciones de actividad.
- Las variables de comportamiento presentan colas derechas.
- La ausencia de scores tiene significado de negocio y no debe interpretarse automáticamente como error.
- Las variables constantes y casi constantes pueden reducirse en la fase de selección de variables.
- El análisis bivariante contra `compra` y la auditoría de leakage (`06_Auditoria_Leakage.ipynb`) están resumidos en la sección anterior y documentados en DEC-014.

## Estructura final

```
<class 'pandas.DataFrame'>
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
memory usage: 1.3+ MB
```
