# Informe de preselección de variables — Lead Scoring

## Resumen

- Input: `C:\Users\Dell\Agus\Master Agentic DS\Lead_Scoring\02_datos\03_Entrenamiento\04_train_tablon_transformado.pkl`
- Dataset inicial: 6360 filas × 52 predictoras.
- Método: RFECV estándar con regresión logística L1.
- Selección supervisada: 43 de 52 predictoras.
- Deduplicación por variable madre: 43 predictoras, sin bajas adicionales.
- Correlación: umbral `|Pearson| > 0.70`.
- Eliminadas por menor importancia supervisada: visitas_total_yj_mm, origen_Lead Add Form, ocupacion_Unemployed.
- Dataset final: 6360 filas × 41 columnas, incluyendo `compra`.

## Método supervisado

Se usó `LogisticRegression(penalty="l1", solver="saga", max_iter=5000)` con `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` y scoring `roc_auc`. El mejor ROC AUC medio de RFECV fue 0,8976 y el óptimo inicial fue 43 variables.

## Decisiones de desduplicación automática

                madre       tipo_grupo                                                                                                                                                                                                                                                                                                                                                                                                             conservadas                                                                                                 fuera_por_RFECV        acción_deduplicación
        visitas_total numérica + flags                                                                                                                                                                                                                                                                                                                                                                              visitas_total_yj_mm, visitas_total_missing                                                                                                         ninguna mantener grupo seleccionado
 tiempo_en_site_total numérica + flags                                                                                                                                                                                                                                                                                                                                                                                              tiempo_en_site_total_yj_mm                                                                                                         ninguna mantener grupo seleccionado
paginas_vistas_visita numérica + flags                                                                                                                                                                                                                                                                                                                                                                                             paginas_vistas_visita_yj_mm                                                                                                         ninguna mantener grupo seleccionado
      score_actividad numérica + flags                                                                                                                                                                                                                                                                                                                                                                             score_actividad_mm, score_actividad_missing                                                                                                         ninguna mantener grupo seleccionado
         score_perfil numérica + flags                                                                                                                                                                                                                                                                                                                                                                                                         score_perfil_mm                                                                                                         ninguna mantener grupo seleccionado
               origen        OHE/flags                                                                                                                                                                                                                                                                                                                                                origen_Landing Page Submission, origen_Lead Add Form, origen_Lead Import                                                                                                         ninguna mantener grupo seleccionado
               fuente        OHE/flags                                                                                                                                                                                                                                                                                                                                               fuente_Direct Traffic, fuente_Google, fuente_Organic Search, fuente_Otros                                                                                                         ninguna mantener grupo seleccionado
      no_enviar_email        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                     no_enviar_email_Yes                                                                                                         ninguna mantener grupo seleccionado
            no_llamar        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                                 ninguna                                                                                                   no_llamar_Yes mantener grupo seleccionado
        ult_actividad        OHE/flags                                                                                                                                                                                                          ult_actividad_Converted to Lead, ult_actividad_Email Bounced, ult_actividad_Email Link Clicked, ult_actividad_Email Opened, ult_actividad_Otros, ult_actividad_Page Visited on Website, ult_actividad_SMS Sent                                                                                                         ninguna mantener grupo seleccionado
               ambito        OHE/flags ambito_Business Administration, ambito_Desconocido, ambito_E-Business, ambito_E-COMMERCE, ambito_Healthcare Management, ambito_Hospitality Management, ambito_Human Resource Management, ambito_IT Projects Management, ambito_International Business, ambito_Operations Management, ambito_Retail Management, ambito_Rural and Agribusiness, ambito_Select, ambito_Services Excellence, ambito_Supply Chain Management ambito_Finance Management, ambito_Marketing Management, ambito_Media and Advertising, ambito_Travel and Tourism mantener grupo seleccionado
            ocupacion        OHE/flags                                                                                                                                                                                                                                                                                                     ocupacion_Desconocido, ocupacion_Housewife, ocupacion_Student, ocupacion_Unemployed, ocupacion_Working Professional                                                                                                 ocupacion_Other mantener grupo seleccionado
     conociste_google        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                                 ninguna                                                                                            conociste_google_Yes mantener grupo seleccionado
   conociste_facebook        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                                 ninguna                                                                                          conociste_facebook_Yes mantener grupo seleccionado
conociste_referencias        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                                 ninguna                                                                                       conociste_referencias_Yes mantener grupo seleccionado
          descarga_lm        OHE/flags                                                                                                                                                                                                                                                                                                                                                                                                         descarga_lm_Yes                                                                                                         ninguna mantener grupo seleccionado

No se eliminaron derivadas adicionales: los grupos One-Hot y flags se conservaron dentro del conjunto seleccionado; no había ramas numéricas alternativas.

## Correlación

Pares detectados con el umbral 0,70:

           variable_1                  variable_2  corr_abs
  visitas_total_yj_mm paginas_vistas_visita_yj_mm  0.865801
 origen_Lead Add Form                fuente_Otros  0.851071
ocupacion_Desconocido        ocupacion_Unemployed  0.789920

Se eliminó la variable con menor importancia L1 en cada par:
- `visitas_total_yj_mm` frente a `paginas_vistas_visita_yj_mm`.
- `origen_Lead Add Form` frente a `fuente_Otros`.
- `ocupacion_Unemployed` frente a `ocupacion_Desconocido`.

## Recomendaciones

El conjunto final es adecuado como punto de partida para una regresión logística interpretable. Las variables excluidas no deben reincorporarse sin comparar ROC AUC, recall y precisión en una validación independiente. La familia de árboles sigue pendiente y podría justificar una selección distinta.

## Parámetros utilizados

- Modo: estándar.
- RFECV: paso 1, mínimo 1 variable, 5 folds estratificados.
- Scoring: ROC AUC.
- Correlación: Pearson absoluto, umbral 0,70.

## Artefactos

- Dataset: `02_datos/03_Entrenamiento/05_train_tablon_preseleccion.pkl`
- Variables: `01_Documentos/Variables_preseleccionadas.txt`
