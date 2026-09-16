## ESTADO ACTUAL DEL PROYECTO

**Dataframe actual**: `../02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl`

**Estructura del dataframe**:
```
<class 'pandas.DataFrame'>
Index: 6360 entries, 2954 to 7270
Data columns (total 53 columns):
 #   Column                                 Non-Null Count  Dtype  
---  ------                                 --------------  -----  
 0   compra                                 6360 non-null   int64  
 1   visitas_total_yj_mm                    6360 non-null   float64
 2   tiempo_en_site_total_yj_mm             6360 non-null   float64
 3   paginas_vistas_visita_yj_mm            6360 non-null   float64
 4   score_actividad_mm                     6360 non-null   float64
 5   score_perfil_mm                        6360 non-null   float64
 6   score_actividad_missing                6360 non-null   float64
 7   origen_Landing Page Submission         6360 non-null   float64
 8   origen_Lead Add Form                   6360 non-null   float64
 9   origen_Lead Import                     6360 non-null   float64
 10  fuente_Direct Traffic                  6360 non-null   float64
 11  fuente_Google                          6360 non-null   float64
 12  fuente_Organic Search                  6360 non-null   float64
 13  fuente_Otros                           6360 non-null   float64
 14  no_enviar_email_Yes                    6360 non-null   float64
 15  no_llamar_Yes                          6360 non-null   float64
 16  ult_actividad_Converted to Lead        6360 non-null   float64
 17  ult_actividad_Email Bounced            6360 non-null   float64
 18  ult_actividad_Email Link Clicked       6360 non-null   float64
 19  ult_actividad_Email Opened             6360 non-null   float64
 20  ult_actividad_Otros                    6360 non-null   float64
 21  ult_actividad_Page Visited on Website  6360 non-null   float64
 22  ult_actividad_SMS Sent                 6360 non-null   float64
 23  ambito_Business Administration         6360 non-null   float64
 24  ambito_Desconocido                     6360 non-null   float64
 25  ambito_E-Business                      6360 non-null   float64
 26  ambito_E-COMMERCE                      6360 non-null   float64
 27  ambito_Finance Management              6360 non-null   float64
 28  ambito_Healthcare Management           6360 non-null   float64
 29  ambito_Hospitality Management          6360 non-null   float64
 30  ambito_Human Resource Management       6360 non-null   float64
 31  ambito_IT Projects Management          6360 non-null   float64
 32  ambito_International Business          6360 non-null   float64
 33  ambito_Marketing Management            6360 non-null   float64
 34  ambito_Media and Advertising           6360 non-null   float64
 35  ambito_Operations Management           6360 non-null   float64
 36  ambito_Retail Management               6360 non-null   float64
 37  ambito_Rural and Agribusiness          6360 non-null   float64
 38  ambito_Select                          6360 non-null   float64
 39  ambito_Services Excellence             6360 non-null   float64
 40  ambito_Supply Chain Management         6360 non-null   float64
 41  ambito_Travel and Tourism              6360 non-null   float64
 42  ocupacion_Desconocido                  6360 non-null   float64
 43  ocupacion_Housewife                    6360 non-null   float64
 44  ocupacion_Other                        6360 non-null   float64
 45  ocupacion_Student                      6360 non-null   float64
 46  ocupacion_Unemployed                   6360 non-null   float64
 47  ocupacion_Working Professional         6360 non-null   float64
 48  conociste_google_Yes                   6360 non-null   float64
 49  conociste_facebook_Yes                 6360 non-null   float64
 50  conociste_referencias_Yes              6360 non-null   float64
 51  descarga_lm_Yes                        6360 non-null   float64
 52  visitas_total_missing                  6360 non-null   float64
dtypes: float64(52), int64(1)
memory usage: 2.6 MB
```
