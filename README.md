# Lead Scoring

Modelo de priorización de leads comerciales a partir de datos de comportamiento y perfil, para predecir la probabilidad de compra.

> Registro de decisiones técnicas: [`decisions.md`](decisions.md) (índice) y [`decisions_detalle.md`](decisions_detalle.md) (detalle completo).

## Hallazgos clave

- La variable objetivo `compra` tiene **37,5 % de positivos**: nos compra el 37% de los posibles clientes
- `score_actividad` y `score_perfil` faltan en **45,96 % de los leads**: falta el dato porque el 45% son usuarios nuevos (sin actividad previa ni perfil creado)
- La adquisición está concentrada en cuatro canales (`Google`, `Direct Traffic`, `Chat`, `Organic Search`) más `Otros`.


## Problema

Sin un criterio de priorización, el equipo comercial dedicaría el mismo esfuerzo a leads con baja y alta probabilidad de compra, provocando que se pierdan clientes.

## Fases del scoring de leads

1. **Captación**: el lead ingresa por un canal (`fuente`: Google, Direct Traffic, Chat, Organic Search, u otros ).
2. **Comportamiento en el sitio**: se registran `visitas_total`, `paginas_vistas_visita`, `tiempo_en_site_total` y `ult_actividad`.
3. **Scoring de marketing**: una vez que el lead acumula actividad suficiente, se le asignan `score_actividad` y `score_perfil`; los leads nuevos aún no tienen ese puntaje, de ahí el faltante estructural.
4. **Conversión**: el lead termina o no en `compra`, que es la variable a predecir.


## Objetivo

Identificar qué variables de comportamiento y perfil se asocian con la conversión, dejando un tablón limpio y explorado listo para selección de variables y modelado predictivo.

## Enfoque técnico

1. Importar `Leads.csv` como fuente única, sin merges ni concats.
2. Dividir en train/validación 70/30 de forma reproducible (`random_state=42`).
3. Tipar y limpiar el tablón de train: imputar categóricos como `Desconocido`, imputar `visitas_total`/`paginas_vistas_visita` con la mediana más un indicador de missingness, preservar los `NaN` estructurales de los scores, unificar `google` → `Google`, y recortar 5 outliers extremos.
4. Explorar el tablón limpio por tipo de variable (numéricas, categóricas, cardinalidad, texto, fechas), agrupando categorías minoritarias como `Otros`.
5. Documentar hallazgos, decisiones y alertas en informes markdown.
6. Pendiente: selección de variables, análisis bivariante contra `compra` y modelado.

## Resultados principales

| Área analizada | Hallazgo | Interpretación |
|---|---|---|
| Balance de clases | `compra` tiene 37,5 % de positivos | Desbalance moderado; a monitorear en el modelado, sin requerir técnicas extremas |
| Scores de actividad/perfil | 45,96 % de faltantes en `score_actividad` y `score_perfil` | Faltante estructural de usuarios nuevos, no error de captura — no se imputa |
| Faltantes de comportamiento | 92 filas sin `visitas_total`/`paginas_vistas_visita`, 63 con `compra=1` | Eliminarlas o ponerlas en cero sesgaría el modelo hacia leads sin conversión |
| Outliers de comportamiento | 5 filas con `visitas_total > 30` o `paginas_vistas_visita > 20` | Cola aislada y extrema; se recortó con umbral explícito, no por regla estadística automática |
| Canales de adquisición | `fuente` concentrada en Google, Direct Traffic, Chat, Organic Search | El resto se agrupó como `Otros` para no fragmentar la lectura |
| Variables constantes | `conociste_revista`, `conociste_periodico`, `conociste_youtube` son constantes | Se conservan en el EDA; su eliminación queda para la fase de selección de variables |

## Estructura del proyecto

```text
.
├── 01_Documentos/
│   └── PlantillaTransformaciones.xlsx  # plantilla de transformaciones aplicadas
├── 02_datos/
│   ├── 01_Originales/
│   │   └── Leads.csv                   # fuente única, sin procesar
│   ├── 02_Validacion/
│   │   └── validation.pkl              # 30% de validación, separado en la importación
│   ├── 03_Entrenamiento/
│   │   ├── 01_train_tablon_integrado.pkl  # train tras el split 70/30
│   │   ├── 02_train_tablon_calidad.pkl    # train tras limpieza de calidad
│   │   └── 03_train_tablon_eda.pkl        # train tras el EDA
│   └── 04_Caches/                      # cachés intermedias
├── 03_notebooks/
│   ├── 01_Importacion_Datos.ipynb      # importación y split train/validación
│   ├── 02_Calidad_Datos.ipynb          # limpieza y validación de calidad
│   └── 03_EDA.ipynb                    # análisis exploratorio univariante
├── 04_scripts/                         # reservado para scripts reutilizables
├── 05_modelos/                         # reservado para modelos entrenados
├── 06_resultados/
│   ├── Calidad_Datos/
│   │   ├── informe_calidad_datos.md    # informe de calidad de datos
│   │   └── transformaciones.json       # especificación de transformaciones aplicadas
│   └── EDA/
│       └── EDA_report.md               # informe de EDA
├── 07_despliegue/                      # reservado para despliegue del modelo
├── 99_otros/                           # archivos varios
├── decisions.md                        # índice de decisiones técnicas
└── decisions_detalle.md                # detalle completo de decisiones técnicas
```

## Cómo reproducir el proyecto

### Requisitos

- Python 3.13.
- Jupyter Notebook o JupyterLab.
- `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`.

El repositorio no incluye un `requirements.txt`; instalar las librerías directamente como se indica abajo.

### Instalación del entorno

Desde la raíz del proyecto:

```bash
python -m venv .venv
```

Activación en Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Activación en macOS o Linux:

```bash
source .venv/bin/activate
```

Instalación de las librerías:

```bash
python -m pip install pandas numpy matplotlib seaborn scikit-learn jupyter
```

### Ejecución

1. Colocá `Leads.csv` en `02_datos/01_Originales/`.
2. Abrí la carpeta raíz del proyecto en VS Code o iniciá Jupyter desde ahí.
3. Ejecutá los notebooks en este orden, desde el principio y con el kernel del `.venv` activo:
   - `03_notebooks/01_Importacion_Datos.ipynb`
   - `03_notebooks/02_Calidad_Datos.ipynb`
   - `03_notebooks/03_EDA.ipynb`
4. Los tablones intermedios se generan en `02_datos/03_Entrenamiento/` y la validación en `02_datos/02_Validacion/validation.pkl`. Los informes se generan en `06_resultados/Calidad_Datos/` y `06_resultados/EDA/`.

## Limitaciones y próximos pasos

El EDA hecho hasta ahora es univariante; falta el análisis bivariante contra `compra` que el propio informe recomienda como siguiente paso.  Las variables constantes o casi constantes (`conociste_revista`, `conociste_periodico`, `conociste_youtube`) todavía no se descartaron: eso queda para la fase de selección de variables. Tampoco hay diccionario de datos formal ni `requirements.txt` en el repositorio, y el modelo de scoring en sí (carpetas `05_modelos/` y `07_despliegue/`) todavía no se implementó.
