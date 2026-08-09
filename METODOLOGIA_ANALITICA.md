# Metodología analítica de los notebooks de festuca

## 1. Propósito y alcance

Este documento describe los cálculos, modelos, diagnósticos y reglas de
interpretación implementados por:

- `festuca_estudio_longitudinal.ipynb`, que contiene la reconstrucción de
  variables, el análisis clásico por fecha, los modelos longitudinales mixtos y
  los análisis de sensibilidad;
- `festuca_anexo_probabilistico.ipynb`, que contiene los modelos bayesianos
  robustos de rendimiento y de trayectorias longitudinales.

Los notebooks son controladores breves. La implementación se encuentra en
`src/festuca_analysis/source_data.py`, `statistics.py`, `longitudinal.py` y
`annex.py`. Por tanto, esta metodología documenta el código que realmente se
ejecuta y no resultados copiados de una corrida anterior.

La estrategia general es:

1. leer las mediciones primitivas y el diseño desde el libro XLSX;
2. reconstruir de forma determinista las magnitudes derivadas;
3. auditar discrepancias y valores estimados sin ocultarlos;
4. responder por separado las preguntas sobre N experimental adicional y sobre
   calendario de aplicación;
5. usar modelos longitudinales para preguntas que involucran cambios entre
   fechas;
6. complementar la inferencia clásica con modelos probabilísticos robustos;
7. verificar supuestos, convergencia, sensibilidad y acoplamiento matemático;
8. exportar tablas, figuras y posteriores como artefactos regenerables.

## 2. Preguntas analíticas y jerarquía inferencial

El análisis evita tratar todas las variables como respuestas independientes de
igual importancia.

| Nivel | Pregunta | Población o contraste | Método principal |
|---|---|---|---|
| Primario | ¿El calendario de aplicación modifica el rendimiento limpio? | M1–M5, dentro de cada sector | DBCA por sector y modelo bayesiano robusto |
| Complementario | ¿Cuál es la respuesta promedio asociada con el N experimental adicional? | Promedio M1–M5 menos M0 | Contraste planificado y posterior |
| Secundario | ¿Difieren las trayectorias de biomasa y concentración de N? | M1–M5 a través de las fechas | Modelos longitudinales con interacción tratamiento por fecha |
| De apoyo | ¿Cómo cambian N acumulado, INN y componentes del rendimiento? | M0–M5 y M1–M5 | DBCA por fecha, resúmenes y contrastes |
| Exploratorio | ¿Qué asociaciones quedan luego de ajustar por tratamiento y bloque? | Pares de variables por sector | Correlaciones de Pearson y regresiones ajustadas |
| Sensibilidad | ¿Cambian las conclusiones bajo otras decisiones razonables? | Política de materia seca, escala, prior y dato de N faltante | Reanálisis completos o parciales |

Se mantienen dos preguntas diferentes:

- **M1–M5:** compara calendarios que recibieron la misma dosis experimental
  total. Es la pregunta principal sobre momento de aplicación.
- **M0–M5:** incorpora el tratamiento de referencia y permite estudiar la
  respuesta al N experimental adicional. M0 no significa necesariamente
  ausencia total de N, porque el manejo común y el aporte del suelo no se
  eliminan.

La falta de significancia no se interpreta como equivalencia. Para afirmar
equivalencia práctica se necesita un margen sustantivo definido y una
probabilidad o prueba diseñada para ese margen.

## 3. Fuente de datos, diseño y trazabilidad

### 3.1 Fuente de verdad

La única fuente de observaciones es
`sources/Datos_Ema_Serrana_INN.xlsx`. La carga:

- calcula el hash SHA-256 del archivo;
- lee las fórmulas con `data_only=False` para registrar qué celdas son
  calculadas;
- lee los valores con `data_only=True` para construir las tablas analíticas;
- no usa CSV exportados, tablas de la tesis ni posteriores históricos como
  entradas;
- clasifica cada variable como registrada, calculada en el libro, estimada en
  el libro, derivada por el análisis o metadato.

Cuando una identidad está completamente determinada por mediciones primitivas,
la magnitud se vuelve a calcular. La columna derivada del XLSX se conserva solo
para conciliación.

### 3.2 Diseño experimental reconstruido

El libro actual describe:

- dos sectores físicos: Secano y Riego;
- seis tratamientos: M0–M5;
- cuatro bloques completos por sector: R1–R4;
- 48 parcelas para la evaluación final;
- tres fechas experimentales para las mediciones longitudinales;
- 144 filas parcela-fecha antes de considerar faltantes de una variable
  particular;
- parcelas de $24\ \mathrm{m^2}$;
- separación entre hileras de $0{,}38\ \mathrm{m}$;
- área de muestreo de biomasa de $0{,}38\ \mathrm{m^2}$;
- área de cosecha de $0{,}76\ \mathrm{m^2}$.

El área de cosecha se deriva de la descripción del libro: un metro en dos
hileras, multiplicado por la separación entre hileras. Esto evita contar dos
veces la longitud cuando el texto informa simultáneamente metros totales y
número de surcos.

### 3.3 Calendario experimental

M0 permanece en $0\ \mathrm{kg\ N\ ha^{-1}}$ de N experimental. M1–M5 reciben
dos aplicaciones de $100\ \mathrm{kg\ N\ ha^{-1}}$, para un total de
$200\ \mathrm{kg\ N\ ha^{-1}}$. Las fechas no están codificadas en el
notebook: se leen de `Ensayo!F:H`.

Para una fecha $t$, el N experimental acumulado del tratamiento $i$ es

$$
N_i(t) =
d\,\mathbf{1}(t \ge a_{i1}) +
d\,\mathbf{1}(t \ge a_{i2}),
$$

donde:

- $d=100\ \mathrm{kg\ N\ ha^{-1}}$ es la dosis por aplicación;
- $a_{i1}$ y $a_{i2}$ son las fechas de primera y segunda aplicación;
- $\mathbf{1}(\cdot)$ vale 1 si la condición se cumple y 0 en caso contrario.

La curva escalonada del notebook representa, por tanto, $0$, $100$ y
$200\ \mathrm{kg\ N\ ha^{-1}}$. No incorpora una dosis común cuya fracción
activa de N no está codificada en el XLSX.

En la versión actual de la fuente, el calendario leído es:

| Tratamiento | Primera aplicación | Segunda aplicación | N experimental total |
|---|---|---|---|
| M0 | Sin aplicación | Sin aplicación | $0\ \mathrm{kg\ N\ ha^{-1}}$ |
| M1 | 12 de junio de 2025 | 31 de julio de 2025 | $200\ \mathrm{kg\ N\ ha^{-1}}$ |
| M2 | 27 de junio de 2025 | 31 de julio de 2025 | $200\ \mathrm{kg\ N\ ha^{-1}}$ |
| M3 | 9 de julio de 2025 | 21 de agosto de 2025 | $200\ \mathrm{kg\ N\ ha^{-1}}$ |
| M4 | 4 de agosto de 2025 | 16 de septiembre de 2025 | $200\ \mathrm{kg\ N\ ha^{-1}}$ |
| M5 | 25 de agosto de 2025 | 16 de septiembre de 2025 | $200\ \mathrm{kg\ N\ ha^{-1}}$ |

Las fechas longitudinales son 16 de septiembre, 20 de octubre y 12 de noviembre
de 2025. Por ello, la segunda aplicación de M4 y M5 comparte fecha calendario
con el primer muestreo.

Si una aplicación y un muestreo comparten fecha, el orden dentro del día es
desconocido. En ese caso, el muestreo no se atribuye a una respuesta posterior
a la aplicación sin una bitácora de campo adicional.

### 3.4 Entradas de agua

Para los meses calendario que intersectan el período experimental se calculan

$$
G_{\mathrm{secano}}=\sum_m R_m,
$$

$$
G_{\mathrm{riego}}=\sum_m (R_m+I_m),
$$

donde $R_m$ es la precipitación mensual e $I_m$ el riego suplementario. Estas
cantidades son entradas brutas registradas. No constituyen balance hídrico,
evapotranspiración ni agua efectivamente consumida por el cultivo.

En la fuente actual, el período agrega $510\ \mathrm{mm}$ de precipitación en
ambos sectores y $165\ \mathrm{mm}$ de riego suplementario, de modo que las
entradas brutas son $510\ \mathrm{mm}$ para Secano y $675\ \mathrm{mm}$ para
Riego.

### 3.5 Controles automáticos de integridad

Antes de modelar se comprueba:

- presencia exacta de M0–M5 en el calendario;
- número esperado de parcelas y filas longitudinales;
- unicidad de parcela y de combinación parcela-fecha;
- número de fechas por parcela;
- coincidencia del peso de mil semillas reconstruido con el libro;
- identificación de valores de calidad estimados;
- conciliación de N acumulado e INN con las columnas del libro;
- observaciones de materia seca que activan la regla dinámica de auditoría.

Un control estructural marcado como error detiene la carga; los controles de
conciliación se muestran para revisión.

La caracterización inicial resume, por sector, conteo, media, desvío estándar,
mínimo y máximo de biomasa y densidad de macollos. Es descriptiva y no se usa
como una prueba adicional de tratamiento.

## 4. Reconstrucción determinista de variables

### 4.1 Símbolos principales

| Símbolo | Definición | Unidad |
|---|---|---|
| $m_f$ | Masa fresca de la submuestra para materia seca | g |
| $m_d$ | Masa seca de la submuestra | g |
| $M_f$ | Masa fresca cosechada en un metro de hilera | g |
| $DM$ | Porcentaje de materia seca usado | % |
| $A_b$ | Área de muestreo de biomasa | $\mathrm{m^2}$ |
| $m_c$ | Masa de semilla limpia | g |
| $m_s$ | Masa de semilla antes de limpiar | g |
| $A_h$ | Área cosechada para rendimiento | $\mathrm{m^2}$ |
| $n_p$ | Número de panojas cosechadas | conteo |
| $w_r$ | Masa de 100 semillas en la réplica técnica $r$ | g |
| $B$ | Biomasa aérea | $\mathrm{kg\ MS\ ha^{-1}}$ |
| $Y$ | Rendimiento de semilla limpia | $\mathrm{kg\ ha^{-1}}$ |
| $P$ | Densidad de panojas | $\mathrm{panojas\ m^{-2}}$ |
| $W_{1000}$ | Peso de mil semillas | g |
| $N$ | Concentración de N en materia seca | % |
| $Q_N$ | N acumulado en la biomasa | $\mathrm{kg\ N\ ha^{-1}}$ |

### 4.2 Materia seca y biomasa

El porcentaje calculable desde la submuestra es

$$
DM_{\mathrm{razón}}=100\frac{m_d}{m_f}.
$$

El análisis primario usa el porcentaje registrado en el libro porque el
procedimiento exacto que originó esa columna no está codificado. La razón
$m_d/m_f$ se usa para auditoría y sensibilidad.

Una fila se marca para verificación cuando se cumplen simultáneamente

$$
\left|DM_{\mathrm{registrado}}-DM_{\mathrm{razón}}\right|
\ge 5\ \text{puntos porcentuales}
$$

y

$$
\frac{
\left|DM_{\mathrm{registrado}}-DM_{\mathrm{razón}}\right|
}{
\left|DM_{\mathrm{registrado}}\right|
}
\ge 0{,}20.
$$

La biomasa se reconstruye como

$$
B=M_f\frac{DM}{100}\frac{10}{A_b}.
$$

El factor 10 convierte $\mathrm{g\ m^{-2}}$ en
$\mathrm{kg\ ha^{-1}}$. La pregunta respondida es: ¿cuánta materia seca
había por unidad de superficie, usando una identidad uniforme para todas las
filas?

Se evalúan tres políticas:

1. `recorded`: usa el $DM$ registrado, política primaria;
2. `ratio`: sustituye solo las filas marcadas por $DM_{\mathrm{razón}}$;
3. `exclude`: excluye de los cálculos las filas marcadas.

Para comparar las políticas se vuelve a cargar y reconstruir toda la fuente. En
la fecha final se repite el DBCA M1–M5 de biomasa y el DBCA de índice de cosecha,
y se registran sus pruebas globales y el rango descriptivo de medias de biomasa.

### 4.3 N acumulado e Índice de Nutrición Nitrogenada

El N acumulado se calcula mediante

$$
Q_N=B\frac{N}{100}.
$$

Para el INN, primero se expresa la biomasa en toneladas:

$$
W=\frac{B}{1000},
\qquad W\;\text{en}\;\mathrm{t\ MS\ ha^{-1}}.
$$

La curva crítica general es

$$
N_c(W)=aW^b,
$$

y el índice es

$$
INN=\frac{N}{N_c(W)}.
$$

La curva primaria usa $a=3{,}93$ y $b=-0{,}42$. La sensibilidad usa
$a=4{,}8$ y $b=-0{,}32$. El INN es una transformación determinista de $B$,
$N$ y la curva seleccionada; no se trata como una medición independiente ni
como una segunda respuesta latente en el anexo probabilístico.

Las filas que el libro marca como estimadas se conservan en columnas de
auditoría, pero su $N$ se sustituye por ausente en el análisis primario.

### 4.4 Rendimiento y componentes

La densidad de panojas es

$$
P=\frac{n_p}{A_h}.
$$

Los rendimientos antes y después de la limpieza son

$$
Y_{\mathrm{sucio}}=m_s\frac{10}{A_h},
\qquad
Y=m_c\frac{10}{A_h}.
$$

El peso de mil semillas se reconstruye desde tres réplicas técnicas de 100
semillas:

$$
W_{1000}=10\left(\frac{w_1+w_2+w_3}{3}\right).
$$

El número estimado total de semillas y las semillas estimadas por panoja son

$$
\widehat S=\frac{1000m_c}{W_{1000}},
$$

$$
\widehat{S/P}=\frac{\widehat S}{n_p} =
\frac{1000m_c}{W_{1000}n_p}.
$$

Esta última variable no es un conteo independiente: contiene la masa limpia y
el número de panojas. Por ello, su asociación con rendimiento o densidad puede
ser parcialmente algebraica.

La recuperación y la merma de limpieza son

$$
R_c=\frac{m_c}{m_s},
\qquad
L_c=100(1-R_c).
$$

El índice de cosecha se calcula con la biomasa de la fecha final:

$$
IC=100\frac{Y}{B_{\mathrm{final}}}.
$$

Como $Y$ aparece en el numerador, $IC$ no aporta una respuesta independiente
del rendimiento.

### 4.5 Eficiencia agronómica y productividad aparente del agua

Para una parcela del tratamiento fertilizado $i$ y bloque $j$:

$$
EAN_{ij} =
\frac{Y_{ij}-Y_{M0,j}}{D_N},
$$

donde $Y_{M0,j}$ es el rendimiento de M0 en el mismo sector y bloque, y
$D_N=200\ \mathrm{kg\ N\ ha^{-1}}$ es la dosis experimental. La comparación
dentro de bloque conserva el emparejamiento del DBCA. EAN es una transformación
lineal del rendimiento y se usa descriptivamente.

La productividad aparente del agua es

$$
PAA_{ij}=\frac{Y_{ij}}{G_s},
$$

donde $G_s$ es la entrada bruta de agua del sector $s$. No es una eficiencia de
uso fisiológica porque el denominador no es agua consumida.

### 4.6 Precisión de las réplicas técnicas

Para los tres pesos de 100 semillas se calcula

$$
CV_{\mathrm{técnico}}=100\frac{s_w}{\bar w},
$$

donde $\bar w$ y $s_w$ son la media y el desvío estándar muestral de las tres
réplicas. Se informan la mediana, el percentil 95 y el máximo de esos CV, además
de la diferencia entre $W_{1000}$ reconstruido y el valor del libro. Esto
responde si la medición técnica del peso de semilla es internamente precisa.

## 5. Análisis clásico por fecha y sector

### 5.1 Por qué se usa un DBCA

Los tratamientos fueron distribuidos en bloques completos dentro de cada
sector. El modelo ajusta diferencias sistemáticas entre bloques y compara
tratamientos dentro del sector:

$$
Y_{ij}=\mu+\tau_i+\beta_j+\varepsilon_{ij},
$$

donde:

- $Y_{ij}$ es la respuesta del tratamiento $i$ en el bloque $j$;
- $\mu$ es la media general;
- $\tau_i$ es el efecto fijo del tratamiento;
- $\beta_j$ es el efecto fijo del bloque;
- $\varepsilon_{ij}$ es el error residual.

El modelo se ajusta por mínimos cuadrados ordinarios y la prueba global de
tratamiento se obtiene mediante ANOVA de tipo II. Cada sector se analiza por
separado porque existe un solo sector físico por condición hídrica.

### 5.2 Algoritmo por fecha

Para biomasa, concentración de N, N acumulado e INN:

1. seleccionar una fecha y un sector;
2. seleccionar M1–M5 o M0–M5 según la pregunta;
3. eliminar solo las filas sin la respuesta analizada;
4. ajustar el DBCA con tratamiento y bloque fijos;
5. calcular la prueba global de tratamiento;
6. estimar medias marginales promediando el vector de diseño sobre los bloques;
7. calcular intervalos puntuales del 95 %;
8. calcular comparaciones de Tukey, pero marcarlas como confirmatorias solo si
   la prueba global correspondiente detecta tratamiento;
9. ajustar por multiplicidad las pruebas globales de cada familia.

Una prueba por fecha responde: ¿había diferencias entre tratamientos en esta
fecha? No responde si la diferencia cambió, apareció o desapareció a través del
tiempo.

### 5.3 Medias marginales y contrastes

Para el tratamiento $i$, la media ajustada por bloque es

$$
\widehat\mu_i =
\frac{1}{r}\sum_{j=1}^{r}x_{ij}^{\top}\widehat\theta,
$$

donde $x_{ij}$ es el vector de diseño del tratamiento $i$ en el bloque $j$,
$\widehat\theta$ es el vector de coeficientes y $r$ es el número de bloques.

Un contraste se escribe

$$
L=c^{\top}\widehat\theta,
$$

con error estándar

$$
SE(L)=\sqrt{c^{\top}\widehat Vc},
$$

donde $\widehat V$ es la matriz de covarianza estimada. El intervalo puntual es

$$
L\pm t_{0{,}975;\,\nu}SE(L),
$$

y el valor $p$ bilateral se calcula con $\nu$ grados de libertad residuales.

Los contrastes planificados de rendimiento son:

$$
L_N=\frac{1}{5}\sum_{i=1}^{5}\mu_{M_i}-\mu_{M0},
$$

que estima la respuesta promedio al N experimental adicional, y

$$
L_{\mathrm{temprano-tardío}} =
\frac{\mu_{M1}+\mu_{M2}}{2} -
\frac{\mu_{M4}+\mu_{M5}}{2},
$$

que es un contraste secundario entre calendarios.

### 5.4 Comparaciones de Tukey

Para una diferencia $d=\widehat\mu_i-\widehat\mu_{i'}$, el estadístico usado es

$$
q=\frac{|d|\sqrt{2}}{SE(d)}.
$$

El intervalo simultáneo es

$$
d\pm q_{1-\alpha;\,k,\nu}\frac{SE(d)}{\sqrt 2},
$$

donde $k$ es el número de tratamientos de la pregunta y $\nu$ los grados de
libertad residuales. Las comparaciones se calculan para auditoría completa, pero
no se presentan como hallazgos confirmatorios si la prueba global no detecta un
efecto de tratamiento.

### 5.5 Ajuste de Benjamini–Hochberg

Las pruebas repetidas se agrupan por jerarquía de respuesta y por pregunta
M1–M5 o M0–M5. Si $p_{(1)}\le\cdots\le p_{(m)}$ son los valores ordenados, el
ajuste es

$$
\widetilde p_{(k)} =
\min_{j\ge k}\left\{1,\frac{m}{j}p_{(j)}\right\}.
$$

Luego se devuelve cada valor ajustado a su posición original. Este procedimiento
controla la tasa esperada de falsos descubrimientos dentro de la familia
declarada.

### 5.6 Trayectorias observadas

Las figuras descriptivas muestran la media cruda por tratamiento, fecha y
sector, con intervalo t de Student:

$$
\bar Y\pm t_{0{,}975;\,n-1}\frac{s}{\sqrt n}.
$$

Estos intervalos describen la dispersión observada entre bloques. No son
intervalos del modelo mixto y no incorporan una estructura longitudinal. Las
fechas se muestran como categorías equidistantes y los puntos no se conectan,
para no sugerir interpolación continua entre tres momentos discretos.

## 6. Respuestas finales y diagnósticos clásicos

### 6.1 Jerarquía de respuestas finales

El mismo DBCA se aplica por sector a:

- rendimiento limpio, respuesta primaria;
- rendimiento sin limpiar, densidad de panojas y peso de mil semillas,
  respuestas de apoyo;
- semillas estimadas por panoja, merma e índice de cosecha, respuestas
  derivadas de apoyo.

EAN y productividad aparente del agua se resumen como transformaciones
descriptivas, no como respuestas independientes.

### 6.2 Diagnósticos de residuos

Para cada DBCA se calculan:

- prueba de Shapiro–Wilk sobre residuos, como indicador de desviaciones fuertes
  de normalidad;
- prueba de Levene centrada en la mediana entre tratamientos, como indicador de
  heterogeneidad de varianzas;
- distancia de Cook de cada observación;
- número de observaciones con $D_i>4/n$.

Para el rendimiento primario M1–M5 se generan además residuos frente a valores
ajustados y un gráfico Q–Q. Estos diagnósticos identifican incompatibilidades o
influencia; no constituyen pruebas automáticas de validez del modelo.

### 6.3 Sensibilidad para un valor de N no medido

La política primaria usa casos completos y excluye la fila que el XLSX marca
como estimada. Como sensibilidad, una única celda faltante del DBCA se estima
mediante

$$
\widehat Y_{ij} =
\frac{rB_j+tT_i-G}{(r-1)(t-1)},
$$

donde:

- $B_j$ es el total observado del bloque que contiene la celda faltante;
- $T_i$ es el total observado del tratamiento correspondiente;
- $G$ es el total general observado;
- $r$ es el número de bloques;
- $t$ es el número de tratamientos.

El DBCA se vuelve a ajustar y se compara su prueba global con el análisis de
casos completos. Esta imputación no sustituye la política primaria.

### 6.4 Comparación descriptiva entre sectores

Para M1–M5 se comparan dos modelos:

$$
Y=\text{sector}+\text{bloque dentro de sector}+\text{tratamiento}+\varepsilon,
$$

$$
Y=\text{sector}+\text{bloque dentro de sector}+\text{tratamiento}
+\text{sector}\times\text{tratamiento}+\varepsilon.
$$

La comparación describe si el patrón relativo de tratamientos parece distinto
entre los dos sectores observados. No identifica un efecto causal del riego,
porque cada condición hídrica está representada por un solo sector físico.

## 7. Asociaciones exploratorias y acoplamiento matemático

### 7.1 Correlaciones crudas y ajustadas

Las correlaciones de Pearson se calculan por sector para M0–M5 y M1–M5. Para
ajustar por diseño se estima

$$
Y=\alpha+\lambda X+\text{tratamiento}+\text{bloque}+\varepsilon.
$$

Si $t_X$ es el estadístico t del coeficiente $\lambda$ y $\nu$ sus grados de
libertad residuales, la correlación parcial equivalente es

$$
r_{\mathrm{parcial}} =
\operatorname{sign}(t_X)
\sqrt{\frac{t_X^2}{t_X^2+\nu}}.
$$

El valor $p$ se toma del coeficiente $X$ en la regresión completa, por lo que
refleja los grados de libertad consumidos por tratamiento y bloque. Estas
asociaciones son exploratorias y cada fila informa si existe acoplamiento
matemático conocido.

### 7.2 Nulo de reconstrucción

La pregunta es: ¿la correlación entre densidad de panojas y semillas estimadas
por panoja contiene información adicional a compartir $n_p$ en la identidad?

Dentro de cada sector y para cada población analítica:

1. calcular la correlación observada entre $P$ y $\widehat{S/P}$;
2. permutar $\widehat S$ entre parcelas;
3. conservar el $n_p$ de la parcela receptora;
4. reconstruir

$$
\widehat{S/P}^{\,*}=\frac{\pi(\widehat S)}{n_p};
$$

5. recalcular la correlación;
6. repetir 10 000 veces.

Se informan mediana, cuantiles 2,5 % y 97,5 %, percentil de la correlación
observada y una cola bilateral centrada en la mediana nula:

$$
p_{\mathrm{cola}} =
\frac{
1+\#\left\{
|r^*-\widetilde r^*|
\ge
|r_{\mathrm{obs}}-\widetilde r^*|
\right\}
}{B+1}.
$$

Este es un nulo de reconstrucción, no un modelo completo de la biología
reproductiva. Si el valor observado es compatible con el nulo, la correlación
no constituye evidencia independiente de compensación.

## 8. Modelo longitudinal clásico

### 8.1 Pregunta y población

El modelo longitudinal responde si el patrón entre M1–M5 cambia entre fechas.
M0 se excluye porque la pregunta es el calendario a dosis experimental total
común. Se ajustan por separado:

- biomasa en escala original;
- biomasa en escala logarítmica;
- concentración de N en escala original.

La escala original estudia diferencias absolutas. La escala logarítmica estudia
diferencias proporcionales y funciona como sensibilidad de forma y varianza.

### 8.2 Transformación numérica

Sea $g(Y)=Y$ para escala original y $g(Y)=\log Y$ para escala logarítmica. En
cada sector y respuesta:

$$
Z=\frac{g(Y)-c}{s},
$$

donde $c$ y $s$ son la media y el desvío estándar muestral de $g(Y)$. Esta
estandarización mejora la optimización; no cambia la pregunta estadística.

### 8.3 Modelos anidados

Para parcela $k$, tratamiento $i$, bloque $j$ y fecha $t$, el modelo reducido es

$$
Z_{ijkt} =
\mu+\beta_j+\tau_i+\delta_t+u_k+\varepsilon_{ijkt},
$$

y el modelo completo es

$$
Z_{ijkt} =
\mu+\beta_j+\tau_i+\delta_t+(\tau\delta)_{it}
+u_k+\varepsilon_{ijkt},
$$

con

$$
u_k\sim\mathcal N(0,\sigma_u^2),
\qquad
\varepsilon_{ijkt}\sim\mathcal N(0,\sigma^2).
$$

El intercepto aleatorio $u_k$ representa la dependencia de mediciones repetidas
de la misma parcela. Bloque, tratamiento y fecha son efectos fijos.

### 8.4 Ajuste y selección del optimizador

Los modelos se ajustan por máxima verosimilitud, no REML, porque se comparan
efectos fijos anidados. Se prueban `lbfgs`, `bfgs`, `powell`, `nm` y `cg`. Se
conserva el ajuste convergido con mayor log-verosimilitud. Un resultado finito
sin convergencia no se acepta silenciosamente.

La razón de verosimilitudes observada es

$$
\Lambda =
\max\left\{0,\;2(\ell_{\mathrm{completo}}-\ell_{\mathrm{reducido}})\right\}.
$$

El valor asintótico usa una distribución $\chi^2$ con grados de libertad iguales
a la diferencia de parámetros. La decisión principal se calibra además por
bootstrap paramétrico.

### 8.5 Bootstrap paramétrico de la interacción

El algoritmo es:

1. ajustar los modelos reducido y completo;
2. simular interceptos de parcela y residuos bajo el modelo reducido;
3. construir una respuesta simulada;
4. volver a ajustar ambos modelos;
5. calcular $\Lambda^*$;
6. repetir el número solicitado de veces, 199 en el notebook;
7. exigir al menos $\max(20,\lceil0{,}8B\rceil)$ ajustes dobles exitosos;
8. calcular

$$
p_{\mathrm{boot}} =
\frac{1+\#\{\Lambda^*\ge\Lambda_{\mathrm{obs}}\}}
{1+B_{\mathrm{exitosas}}}.
$$

La simulación es preferible como calibración principal porque el tamaño de
muestra es pequeño y la aproximación asintótica de un modelo mixto puede ser
imprecisa. Los valores bootstrap se ajustan por Benjamini–Hochberg dentro de la
familia de escalas de biomasa o de concentración de N.

Como diagnóstico adicional de varianza se calcula, sobre los residuos del modelo
completo, el cociente entre el mayor y el menor desvío estándar residual por
fecha.

### 8.6 Estimaciones e intervalos del modelo mixto

El modelo completo genera medias ajustadas para cada tratamiento y fecha,
promediando el vector de diseño sobre los bloques. Para propagar la incertidumbre
asintótica de los efectos fijos se simulan 20 000 vectores:

$$
\theta^{(b)}\sim
\mathcal N\left(\widehat\theta,\widehat{\operatorname{Var}}(\widehat\theta)\right).
$$

Los efectos aleatorios se fijan en cero, de modo que el estimando representa la
trayectoria típica ajustada, no la predicción de una parcela concreta. En escala
original se informa la media de los sorteos; en escala logarítmica se informa la
mediana retrotransformada, interpretada como valor típico geométrico. Los
cuantiles 2,5 % y 97,5 % forman el intervalo aproximado.

Estos intervalos propagan la covarianza asintótica de los efectos fijos. No son
intervalos de predicción para una nueva parcela y no agregan variación residual.

También se calcula $L_{\mathrm{temprano-tardío}}$ en cada fecha y la fracción
de sorteos en la que el contraste es positivo. Esa fracción es una aproximación
asintótica basada en efectos fijos, no una probabilidad bayesiana posterior.

## 9. Modelo bayesiano robusto de rendimiento

### 9.1 Motivación

El anexo cuantifica directamente incertidumbre, magnitud y probabilidades de
interés práctico. Se usa una verosimilitud t de Student para reducir la
sensibilidad a observaciones extremas y regularización jerárquica porque hay
pocas parcelas por tratamiento.

Se ajusta un modelo independiente por sector. Esto respeta el diseño y evita
interpretar los dos sectores físicos como réplicas aleatorias de condiciones
hídricas.

### 9.2 Estandarización y predictores

Para rendimiento $y_i$:

$$
z_i=\frac{y_i-c_s}{s_s},
$$

donde $c_s$ y $s_s$ son la media y el desvío estándar observados dentro del
sector. El predictor es

$$
\mu_i =
\alpha+\delta E_i+h(T_i)^{\top}\gamma+b(B_i)^{\top}\eta.
$$

Las variables son:

- $E_i=0$ para M0 y $E_i=1$ para M1–M5;
- $h(T_i)$, cuatro contrastes ortonormales de Helmert entre M1–M5, con vector
  cero para M0;
- $b(B_i)$, contrastes ortonormales de Helmert para bloque;
- $\delta$, diferencia promedio estandarizada entre M1–M5 y M0;
- $\gamma$, forma del patrón entre calendarios fertilizados;
- $\eta$, ajustes de bloque.

La codificación centrada separa el promedio del grupo fertilizado de las
diferencias internas de calendario: los coeficientes de forma no modifican el
contraste promedio con M0.

### 9.3 Verosimilitud y priors

El modelo observacional es

$$
z_i\sim t_{\nu}(\mu_i,\sigma),
\qquad \nu=5.
$$

Los priors en escala estandarizada son

$$
\alpha\sim\mathcal N(0,1{,}5^2),
$$

$$
\delta\sim\mathcal N(0,2^2),
$$

$$
\eta_q\sim\mathcal N(0,0{,}75^2),
\qquad
\sigma\sim\operatorname{HalfNormal}(1),
$$

$$
\gamma_k=\tau_\gamma\gamma_k^*,
\qquad
\gamma_k^*\sim\mathcal N(0,1),
\qquad
\tau_\gamma\sim\operatorname{HalfNormal}(s_\gamma).
$$

La especificación primaria usa $s_\gamma=0{,}50$. Las sensibilidades usan
$0{,}25$ y $1{,}00$, que representan regularización más fuerte y más débil.

### 9.4 Auditoría predictiva condicional de los priors

Antes del ajuste se simulan 20 000 realizaciones por sector y prior. Se revisa:

- rango previo de medias M1–M5;
- probabilidad de medias de tratamiento negativas;
- probabilidad de rendimientos replicados negativos;
- probabilidad de rendimientos replicados superiores a
  $3000\ \mathrm{kg\ ha^{-1}}$.

Como $c_s$ y $s_s$ provienen de la respuesta observada, esta es una auditoría
condicional de escala, no una predicción previa a observar datos. La distinción
evita presentar un prior empíricamente escalado como conocimiento externo puro.

### 9.5 Muestreo posterior

Cada modelo se muestrea con NUTS mediante PyMC usando:

- 2 000 iteraciones de ajuste;
- 2 000 sorteos posteriores por cadena;
- cuatro cadenas;
- `target_accept = 0.95`;
- semillas deterministas derivadas del sector y la especificación.

Luego se simula la distribución posterior predictiva de la respuesta. El modelo
de rendimiento se repite para los tres valores de $s_\gamma$ en cada sector.

### 9.6 Estimandos posteriores de rendimiento

Las localizaciones de tratamiento vuelven a la escala original mediante

$$
\mu_{Y,i}=c_s+s_s\mu_i.
$$

Para cada estimando se informan media posterior, mediana e intervalo creíble del
95 %. Los estimandos principales son:

$$
\Delta_N =
\frac{1}{5}\sum_{i=1}^{5}\mu_{M_i}-\mu_{M0},
$$

$$
\Delta_{ET} =
\frac{\mu_{M1}+\mu_{M2}}{2} -
\frac{\mu_{M4}+\mu_{M5}}{2},
$$

$$
\Delta_{M5} =
\mu_{M5}-\frac{1}{4}\sum_{i=1}^{4}\mu_{M_i},
$$

y el rango entre calendarios

$$
R=\max_{i=1,\ldots,5}\mu_{M_i} -
\min_{i=1,\ldots,5}\mu_{M_i}.
$$

Se calculan $P(\Delta>0\mid y)$ y
$P(|\Delta|>100\ \mathrm{kg\ ha^{-1}}\mid y)$. Para cada calendario también
se calculan las probabilidades de ser el mejor, ser el peor y quedar a 50, 100 o
$150\ \mathrm{kg\ ha^{-1}}$ del mejor.

### 9.7 Curva de margen práctico

Para una grilla $\delta=0,5,10,\ldots,300\ \mathrm{kg\ ha^{-1}}$ se calcula

$$
P(R>\delta\mid y)
$$

y su complemento

$$
P(R\le\delta\mid y).
$$

La curva responde cómo cambia la conclusión al cambiar la definición de una
diferencia relevante. No declara equivalencia por sí sola; el margen debe
justificarse agronómicamente y, para una afirmación confirmatoria, fijarse antes
de examinar el resultado.

### 9.8 Chequeo posterior predictivo del ANOVA

Cada respuesta replicada se somete al mismo ANOVA M1–M5 ajustado por bloque. El
modelo completo contiene intercepto, indicadores de tratamiento e indicadores
de bloque; el reducido omite tratamiento. Para cada replicación:

$$
F^* =
\frac{(SSE_R^*-SSE_C^*)/df_1}{SSE_C^*/df_2},
$$

donde $SSE_R^*$ y $SSE_C^*$ son las sumas de cuadrados residuales de los
modelos reducido y completo. El valor $p^*$ se obtiene de la cola superior de
la distribución F.

Se resumen:

- $P(p^*>0{,}05\mid y)$;
- $P(p^*\le p_{\mathrm{obs}}\mid y)$;
- $P(R>100\mid y)$;
- $P(p^*>0{,}05\mid R>100,y)$.

Esto responde qué produciría nuevamente el análisis convencional bajo datos
generados por el modelo. No convierte el valor $p$ observado en probabilidad de
una hipótesis.

## 10. Modelo bayesiano longitudinal

### 10.1 Diseño y pregunta

Se ajustan por sector los mismos tres casos del modelo mixto clásico: biomasa
original, biomasa logarítmica y concentración de N original. Solo se incluyen
M1–M5.

El diseño usa contrastes suma para bloque, tratamiento y fecha. Sea $x_{kt}$ el
vector de intercepto y efectos principales, y $w_{kt}$ el vector de
interacciones tratamiento por fecha:

$$
z_{kt}\sim t_5(\mu_{kt},\sigma),
$$

$$
\mu_{kt} =
x_{kt}^{\top}\beta+w_{kt}^{\top}\gamma+u_k,
$$

$$
u_k\sim\mathcal N(0,\sigma_u^2).
$$

El intercepto aleatorio $u_k$ absorbe la dependencia de medidas repetidas de la
misma parcela. La t de Student limita la influencia de residuos extremos.

### 10.2 Priors

Los coeficientes principales tienen priors normales centrados en cero:

- desvío 1,5 para el intercepto;
- desvío 0,75 para contrastes de bloque;
- desvío 1,0 para los restantes efectos principales.

La interacción usa

$$
\gamma_q=\tau_I\gamma_q^*,
\qquad
\gamma_q^*\sim\mathcal N(0,1),
\qquad
\tau_I\sim\operatorname{HalfNormal}(0{,}5).
$$

El efecto de parcela y la escala residual usan

$$
\sigma_u\sim\operatorname{HalfNormal}(0{,}75),
\qquad
\sigma\sim\operatorname{HalfNormal}(1).
$$

La regularización jerárquica permite que los datos sostengan interacciones
grandes cuando hay evidencia, pero contrae patrones inestables hacia cero.

### 10.3 Predicciones y contrastes

La grilla de predicción contiene cada combinación tratamiento-fecha y promedia
el vector de diseño sobre los cuatro bloques. El efecto aleatorio de parcela se
fija en cero. En escala original se resume la localización aritmética; en escala
logarítmica se calcula

$$
Y_{\mathrm{típico}}=\exp(c+s\mu_z).
$$

Este es un valor típico geométrico. No es la media aritmética marginal, porque
esta última requeriría integrar explícitamente la distribución residual en la
retrotransformación.

En cada fecha se calcula $\Delta_{ET,t}$ y también

$$
\Delta_{\mathrm{cambio}} =
\Delta_{ET,\mathrm{última}} -
\Delta_{ET,\mathrm{primera}}.
$$

Este último estimando responde si el contraste dirigido temprano-tardío cambia
entre la primera y la última fecha. No reemplaza una prueba global de toda la
interacción.

## 11. Diagnósticos bayesianos y reglas de aceptación

Para cada modelo se calcula:

- el máximo $\widehat R$;
- el mínimo tamaño efectivo de muestra central;
- el mínimo tamaño efectivo de muestra de colas;
- el número de divergencias.

Un modelo se marca como aceptado si

$$
\max(\widehat R)\le 1{,}01,
\qquad
\min(ESS_{\mathrm{bulk}})\ge 400,
\qquad
\text{divergencias}=0.
$$

El ESS de colas se informa, aunque la regla implementada de aceptación usa el
ESS central. Los resultados de un modelo no aceptado permanecen visibles, pero
se marcan como no utilizables en la síntesis.

Las comparaciones probabilísticas entre sectores restan sorteos de modelos
sectoriales independientes. Describen diferencias de patrón entre los dos
sectores observados y mantienen explícitamente `causal_interpretation = False`.
El estimando usado es

$$
D_{\mathrm{sector}} =
\Delta_{ET,\mathrm{Riego}}-\Delta_{ET,\mathrm{Secano}},
$$

para el cual se informan el intervalo posterior, $P(D_{\mathrm{sector}}>0)$ y
las probabilidades de que $|D_{\mathrm{sector}}|$ exceda 50 o
$100\ \mathrm{kg\ ha^{-1}}$.

## 12. Métodos de visualización

Las figuras no agregan inferencia diferente a la de sus tablas; hacen visible
la pregunta y la incertidumbre correspondiente.

| Figura o familia | Geometría | Pregunta que hace visible |
|---|---|---|
| Calendario experimental | Curva escalonada 0–100–200 y fechas de muestreo | ¿Cuánto N experimental llevaba acumulado cada tratamiento en cada fecha? |
| Agua | Barras de precipitación y riego suplementario | ¿Qué entradas brutas mensuales registra el XLSX? |
| Trayectorias observadas | Medias e intervalos t, sin líneas | ¿Qué dispersión cruda hay entre bloques en cada celda? |
| Rendimiento 2 por 2 | Parcelas y medias DBCA con IC puntual | ¿Qué cambia al incluir M0 y al ampliar M1–M5? |
| Nulo de reconstrucción | Intervalo nulo y correlación observada | ¿La asociación excede la esperable por la identidad algebraica? |
| Residuos | Residuos-ajustados y Q–Q | ¿Hay patrones fuertes de varianza, forma o influencia? |
| Modelo mixto | Observaciones tenues y medias ajustadas con intervalo | ¿Qué estima el modelo completo por tratamiento y fecha? |
| Rendimiento posterior | Parcelas y media posterior con ICr 95 % | ¿Cuál es la incertidumbre posterior por tratamiento? |
| Curva de margen | $P(R>\delta\mid y)$ contra $\delta$ | ¿Cómo depende la conclusión del margen práctico? |
| Predictiva posterior | Histograma de $p^*$ con guías | ¿Qué valores produciría el ANOVA al repetir el experimento bajo el modelo? |
| Trayectorias posteriores | Medianas e intervalos creíbles categóricos | ¿Qué trayectoria típica estima el modelo para M1–M5? |

Las fechas se tratan como categorías en las figuras de estimaciones y no se
conectan, porque solo existen tres muestreos y el modelo no estima una curva
continua entre ellos.

## 13. Reproducibilidad y algoritmo completo

### 13.1 Semillas deterministas

Las simulaciones derivan una semilla estable de la semilla base y de
identificadores como sector, respuesta, escala y etapa. En forma esquemática:

$$
s_{\mathrm{etapa}} =
s_0+
\left[
\operatorname{CRC32}(\text{identificadores})
\bmod 10^6
\right].
$$

Esto evita depender del hash aleatorio del proceso de Python y permite repetir
cada etapa con la misma configuración.

### 13.2 Flujo del notebook clásico

1. registrar versiones, semilla, nivel $\alpha$, curvas de INN y política de
   materia seca;
2. cargar el XLSX, comprobar hash, estructura, linaje y auditorías;
3. reconstruir biomasa, N acumulado, INN, rendimiento y componentes;
4. resumir estado inicial, calendario y agua;
5. ejecutar DBCA por fecha para las dos preguntas;
6. construir trayectorias descriptivas;
7. ejecutar DBCA y contrastes de las respuestas finales;
8. auditar acoplamiento matemático y correlaciones;
9. ejecutar diagnósticos y sensibilidades;
10. ajustar modelos mixtos, calibrar interacciones por bootstrap y obtener
    estimaciones;
11. generar síntesis, manifiesto de figuras y CSV regenerables.

### 13.3 Flujo del anexo probabilístico

1. cargar el mismo XLSX con la misma política primaria;
2. declarar verosimilitudes, priors y escalado empírico;
3. auditar condicionalmente los priors;
4. ajustar los tres modelos de rendimiento por sector;
5. revisar convergencia y conservar la especificación primaria para la síntesis;
6. calcular medias, contrastes, rangos, posiciones y curvas de margen;
7. ejecutar chequeos posteriores predictivos;
8. ajustar los modelos longitudinales por respuesta, escala y sector;
9. calcular trayectorias y contrastes posteriores;
10. regenerar el nulo de reconstrucción;
11. exportar tablas CSV, figuras, manifiesto JSON y posteriores NetCDF.

## 14. Límites de interpretación

1. **Sectores hídricos:** Secano y Riego no son niveles aleatorizados replicados
   en varios sectores independientes. Toda comparación entre ellos es
   descriptiva, no causal.
2. **M0:** representa ausencia de N experimental adicional, no necesariamente
   ausencia total de N disponible.
3. **Pruebas por fecha:** no demuestran cambio temporal. La interacción
   tratamiento por fecha es la pregunta longitudinal apropiada.
4. **No significancia:** no demuestra igualdad ni equivalencia práctica.
5. **Variables derivadas:** INN, N acumulado, EAN, PAA, índice de cosecha y
   semillas estimadas por panoja comparten componentes con otras respuestas.
6. **Semillas por panoja:** es una reconstrucción algebraica, no un conteo
   independiente.
7. **Escala logarítmica:** la retrotransformación de la localización describe un
   valor típico geométrico, no automáticamente una media aritmética.
8. **Priors escalados con datos:** la auditoría de priors es condicional al
   centro y escala observados.
9. **Diagnósticos:** una prueba diagnóstica aislada no valida ni invalida por sí
   sola todo el análisis.
10. **Artefactos exportados:** son salidas regenerables y nunca vuelven a entrar
    como datos en los notebooks.

Estas restricciones no son notas editoriales: forman parte de la definición de
los estimandos y determinan qué conclusiones pueden sostener los análisis.
