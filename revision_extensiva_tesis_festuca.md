# Revisión extensiva y *red team* de la tesis sobre fertilización nitrogenada en festuca alta

## Dictamen ejecutivo

**Dictamen: revisión mayor antes de la entrega.** El experimento no es inválido ni la tesis está mal encaminada. Al contrario, tiene una base experimental defendible para estudiar **diferencias entre calendarios de fertilización dentro de cada sector**, y el texto ya reconoce con una honestidad poco habitual dos límites importantes: M0 no es un control sin nitrógeno total, y los sectores de secano y riego no son réplicas independientes del régimen hídrico. Esas dos decisiones evitan errores graves.

Lo que impide considerar la versión actual lista no es una falla única, sino una desalineación entre:

1. la pregunta central, que es explícitamente temporal;
2. el análisis principal, que fragmenta el tiempo en ANOVA independientes;
3. varias afirmaciones de “trayectorias”, “convergencia” y “compensación” que exceden lo identificado por esos análisis o por las variables medidas.

Hay además tres asuntos concretos que deberían resolverse antes de la entrega:

- **La fórmula de imputación de la celda faltante permanece mal escrita y mal aplicada en la tesis.** Con la notación usada en `tesis.md`, se intercambiaron los coeficientes de los totales de bloque y tratamiento. La imputación correcta para el diseño completo es 2,86885 % N, no 2,48579 % N. El código longitudinal actual ya usa la fórmula y el valor correctos; falta trasladar esa corrección al texto de la tesis.
- **Hay que verificar la cronología ejecutada y el manejo del pastoreo.** M1 y M2 recibieron su primera aplicación antes del cierre del 1.º de julio. Si los animales siguieron accediendo a las parcelas, el tratamiento temprano quedó combinado con defoliación, posible redistribución de N y una exposición diferencial. Además, el libro contiene fechas preliminares/conflictivas y años 2026 para un ensayo realizado en 2025.
- **La supuesta compensación entre panojas y semillas estimadas por panoja no está demostrada.** El número de semillas por panoja fue reconstruido usando el rendimiento y el número de panojas; una relación inversa con panojas aparece mecánicamente por la fórmula. El análisis nulo agregado por Agustín muestra que la correlación observada queda aproximadamente en el percentil 49 de la distribución inducida por esa reconstrucción. Por tanto, no aporta evidencia independiente de compensación biológica.

Mi recomendación central coincide en buena medida con la intuición de Agustín, pero la haría un poco más fuerte: **el análisis longitudinal debería integrar el cuerpo principal, no quedar como una curiosidad complementaria**. Los ANOVA por fecha pueden conservarse como análisis de seguimiento y para mostrar medias puntuales, pero una tesis cuyo objetivo es “caracterizar la respuesta temporal” necesita probar directamente tratamiento × fecha. El anexo probabilístico sí puede quedar en un anexo, reducido a los módulos que agregan una pregunta científica nueva y con el alcance de reproducción descrito explícitamente.

---

## 1. Alcance de esta revisión y atribución del material

Para evitar mezclar responsabilidades:

- **Tesis de Emanuel Choca y Serrana Montero:** el contenido de `sources/` y su transcripción exacta en `tesis.md`.
- **Material analítico agregado por Agustín:** `festuca_estudio_longitudinal.ipynb`, `festuca_anexo_probabilistico.ipynb`, el paquete `src/festuca_analysis/`, las pruebas de `tests/`, las figuras y los archivos derivados fuera de `sources/`.

Las objeciones a la formulación científica, documentación de campo, métodos originales, resultados y redacción se refieren a la tesis. Las observaciones sobre reproducibilidad, modelos mixtos, modelos probabilísticos y figuras específicas se refieren al material agregado. La fórmula incorrecta de imputación aparece todavía en `tesis.md`, pero fue corregida en el cuaderno y en el paquete de análisis.

### 1.1 Estado del código al cerrar esta revisión

El código auditado tiene actualmente la siguiente estructura y alcance:

- la lógica estadística vive en el paquete `src/festuca_analysis/`; los notebooks contienen llamadas de alto nivel y texto narrativo;
- `uv run --frozen festuca-longitudinal` y `uv run --frozen festuca-annex` regeneran las tablas y figuras correspondientes;
- la imputación usa la fórmula correcta y permanece solo como sensibilidad;
- los modelos mixtos prueban los optimizadores configurados y seleccionan el ajuste convergido con mayor log-verosimilitud;
- las interacciones de las variables primitivas usan *bootstrap* paramétrico reproducible y ajuste FDR de Benjamini–Hochberg;
- EAN y productividad aparente del agua se resumen descriptivamente, sin repetir pruebas inferenciales sobre transformaciones deterministas del rendimiento;
- el anexo incluye priors numéricos, chequeos predictivos previos y una validación independiente del muestreador contra PyMC y mediante simulación-recuperación;
- los dos notebooks fueron ejecutados completamente y no contienen salidas de error.

Persisten dos límites que el código no puede resolver por sí solo: verificar documentalmente los registros 150/152 y volver a muestrear tres componentes probabilísticos históricos para los que se conservaron resúmenes aceptados, pero no las cadenas completas.

No hice una verificación bibliográfica externa de cada afirmación agronómica ni de cada referencia. La revisión se concentra en la coherencia interna entre diseño, datos, análisis e inferencias.

---

## 2. Qué está bien y conviene preservar

La tesis posee varias decisiones conceptuales sólidas que no deberían perderse durante la revisión.

### 2.1 Se distingue correctamente la pregunta de dosis adicional de la pregunta de calendario

La comparación principal M1–M5 mantiene constante la dosis experimental total; la comparación M0–M5 responde otra pregunta: la respuesta a recibir 200 kg N ha⁻¹ experimentales adicionales sobre un manejo común. Esta separación está bien expresada en `tesis.md:L50`, `L217` y en los métodos. Evita atribuir al “momento” la enorme separación entre M0 y los tratamientos fertilizados.

La tesis también advierte que M0 no es ausencia total de N. Eso es esencial y debe mantenerse, aunque conviene cuantificarlo mejor: todos los tratamientos recibieron aproximadamente 164 kg N ha⁻¹ de fertilización general durante 2025; M1–M5 recibieron, por tanto, alrededor de 364 kg N ha⁻¹ de fertilizante en total, mientras M0 recibió alrededor de 164 kg N ha⁻¹.

### 2.2 Se reconoce la pseudorreplicación del régimen hídrico

`tesis.md:L265-L271` deja claro que hay un único sector físico por condición hídrica y que no se puede atribuir causalmente al riego cualquier diferencia media entre sectores. Esta es la interpretación correcta. El análisis conjunto puede describir si el patrón relativo de M1–M5 difiere entre **estos dos sectores**, pero no estimar una interacción generalizable nitrógeno × riego.

La limitación no obliga a eliminar el sector regado ni el análisis conjunto. Sí obliga a cuidar título, hipótesis, resumen y conclusiones para no sugerir un experimento factorial de riego.

### 2.3 El análisis de bloques dentro de cada sector respeta la unidad experimental

Dentro de cada sector hay un DBCA con cuatro bloques y seis tratamientos, y la parcela es correctamente tratada como unidad experimental. La comparación de calendarios dentro de sector es, por tanto, válida bajo los supuestos habituales del diseño.

### 2.4 El texto ya contiene varias cautelas estadísticas correctas

La tesis señala que `p > 0,05` no demuestra igualdad exacta (`tesis.md:L1251`) y reconoce dependencias matemáticas en varias correlaciones (`L1227-L1233`). También mantiene la observación faltante como ausente en el análisis principal y relega la imputación a una sensibilidad. Son buenas prácticas.

El problema no es que estas cautelas no existan, sino que algunas conclusiones posteriores vuelven a excederlas.

### 2.5 La pregunta agronómica es relevante y los datos muestran un patrón interesante

El resultado central es informativo aunque no identifique un ganador:

- hay una respuesta grande y consistente al N experimental adicional;
- los calendarios alteran claramente el estado del cultivo durante el ciclo;
- la incertidumbre disponible no permite elegir de forma robusta una fecha ni demostrar equivalencia práctica entre M1–M5.

Esa combinación es una conclusión científicamente útil. No hace falta fabricar una historia de compensación ni una recomendación productiva más fuerte para que la tesis tenga valor.

---

## 3. Matriz de problemas por prioridad

| Prioridad | Problema | Riesgo si no se corrige | Acción mínima |
|---|---|---|---|
| **P0** | Fórmula de imputación incorrecta en la tesis | Error matemático verificable en Métodos y sensibilidad | Corregir fórmula y valor en `tesis.md`; el código y las sensibilidades actuales ya están corregidos |
| **P0** | Cronología ejecutada y posible pastoreo después de M1/M2 | Posible confusión diferencial del tratamiento temprano | Revisar bitácora; documentar exclusión real de animales, fechas ejecutadas y orden muestreo/aplicación |
| **P0** | Inferencia de compensación desde una variable reconstruida | Conclusión biológica apoyada en acoplamiento algebraico | Retirar del resumen y conclusiones; reformular como descomposición no independiente o hipótesis no probada |
| **P0/P1** | Pregunta longitudinal analizada principalmente con ANOVA separados | No se prueba formalmente el cambio de trayectorias ni la “convergencia” | Incorporar modelo repetido/mixto tratamiento × fecha en Métodos y Resultados principales |
| **P1** | Dos valores de %MS final inconsistentes con pesos crudos | Pueden alterar biomasa, N presente en biomasa e INN finales | Verificar registros 150 y 152; reportar sensibilidad si no se resuelve |
| **P1** | Tratamiento denominado “momento” aunque son paquetes de dos fechas, con intervalos distintos | Se atribuyen efectos a una variable que no fue aislada | Usar “calendario” o “distribución temporal”; evitar inferir efecto de primera/segunda fecha por separado |
| **P1** | No significancia tratada parcialmente como convergencia/equivalencia | Sobreinterpretación del ensayo con n = 4 | Estimar interacciones, efectos e intervalos; declarar que no hubo ganador y tampoco se demostró equivalencia |
| **P1** | Multiplicidad y jerarquía de resultados poco explícitas en la tesis | Hallazgos marginales pueden parecer confirmatorios | Incorporar en la tesis la jerarquía y el control FDR ya implementados en el análisis |
| **P1** | Correlaciones M0–M5 dominadas por la separación de dosis y variables acopladas | Relaciones presentadas como mecanismo sin evidencia independiente | Restringir a M1–M5, ajustar tratamiento/bloque y reducir correlaciones del cuerpo principal |
| **P1** | Tres módulos probabilísticos históricos no se vuelven a muestrear desde el Excel | Los artefactos finales se regeneran, pero esos módulos dependen de resúmenes congelados | Conservar la limitación explícita; si se exige reproducción de cadenas, recuperar o reimplementar esos generadores |
| **P2** | Exceso de tablas y ausencia de figuras en la tesis | La tesis es difícil de leer y oculta magnitud/incertidumbre | Insertar 3–4 de las figuras ya generadas por el análisis y trasladar tablas detalladas al anexo |
| **P2** | Métricas redundantes derivadas de rendimiento | Duplica inferencia sin información nueva | Reducir EAN y productividad aparente del agua a descripción o anexo |
| **P2** | Detalles metodológicos insuficientes | Reproducibilidad agronómica incompleta | Añadir suelo, laboratorio, muestreo, riego, madurez y manejo de franjas destructivas |

---

## 4. Revisión científica del diseño y del constructo experimental

### 4.1 El factor experimental no es simplemente “momento de aplicación”

M1–M5 son **calendarios completos de dos aplicaciones**, no niveles de una única variable temporal. Cambian simultáneamente:

- la fecha de la primera aplicación;
- la fecha de la segunda;
- el intervalo entre aplicaciones;
- la cantidad acumulada disponible en cada fecha de muestreo;
- la proximidad de cada aplicación a lluvias, riego, pastoreo y estados fenológicos.

Los intervalos entre las dos aplicaciones tampoco son constantes. En números aproximados son 49, 35, 42, 35 y 30 días para M1–M5. Por ello, el experimento identifica el efecto de **cinco paquetes de manejo**, no el efecto continuo de “retrasar N” ni el efecto aislado de la primera o segunda aplicación.

El título, objetivos y discusión deberían sustituir sistemáticamente “momento” por **“calendario de aplicación”** o **“distribución temporal de la aplicación”**. Una opción de título más exacta sería:

> **Efecto de cinco calendarios de aplicación de nitrógeno sobre la dinámica de biomasa, el estado nitrogenado y el rendimiento de semilla de festuca alta cv. Rizar en dos sectores contrastantes de un semillero.**

Esto también evita que “en sectores de secano y riego suplementario” suene a factor hídrico replicado.

### 4.2 El contraste es incremental sobre una fertilización general elevada

La tesis describe las aplicaciones comunes, pero no hace suficientemente visible su magnitud. Según los datos consignados:

- abril: 150 kg ha⁻¹ de urea azufrada al 40 % N ≈ 60 kg N ha⁻¹;
- 1.º de julio: 130 kg ha⁻¹ ≈ 52 kg N ha⁻¹;
- agosto: 130 kg ha⁻¹ ≈ 52 kg N ha⁻¹.

El fondo común suma aproximadamente 164 kg N ha⁻¹. Por tanto:

- M0 ≈ 164 kg N ha⁻¹ totales de fertilizante;
- M1–M5 ≈ 364 kg N ha⁻¹ totales.

Esto cambia la interpretación agronómica. La tesis no prueba “200 kg N frente a cero” ni compara calendarios de toda la fertilización; compara **cinco calendarios de 200 kg N adicionales sobre una base común de aproximadamente 164 kg N ha⁻¹**. Conviene decirlo en el resumen, Tabla 1, discusión y conclusiones.

La aplicación general de julio cae dentro del intervalo experimental y la de agosto no tiene fecha exacta. Esa segunda aplicación común puede estar temporalmente muy próxima a M3–M5. Sin su fecha exacta, parte del mecanismo temporal queda indeterminado. Como mínimo debe presentarse en una figura de calendario y discutirse como limitación.

### 4.3 En septiembre M5 no tenía la misma dosis acumulada

El 16 de septiembre, M1–M4 ya habían recibido 200 kg N ha⁻¹ experimentales, mientras M5 solo había recibido 100 kg N ha⁻¹. La tesis lo reconoce en la discusión (`tesis.md:L1159`), lo cual está bien, pero la consecuencia debería ser más explícita:

- la comparación M1–M5 en septiembre **no aísla calendario con dosis acumulada igual**;
- el menor estado de M5 puede ser efecto del retraso, de tener la mitad de dosis aplicada o de ambos;
- una sensibilidad M1–M4 es apropiada.

El cuaderno longitudinal ya calcula esa sensibilidad. En septiembre, restringiendo a M1–M4, se mantienen diferencias de biomasa en secano y riego, y de N presente en biomasa/INN principalmente en riego. Esto fortalece parte de la narrativa temprana sin atribuir a calendario lo que es dosis transitoria.

### 4.4 Falta anclar los calendarios a fenología observada

La discusión interpreta los tratamientos mediante diferenciación reproductiva, elongación, supervivencia de macollos, floración y llenado. Sin embargo, no se registraron estados fenológicos por parcela ni se documentó con precisión en qué fase estaba el cultivo en cada aplicación.

Esto no impide discutir mecanismos plausibles, pero obliga a usar un lenguaje condicional:

- “es compatible con”;
- “podría corresponder a”;
- “no fue posible verificar porque no se midió fenología”.

La hipótesis de “mayor sincronización entre oferta y demanda” (`tesis.md:L247`) no está operacionalizada: no se define qué es sincronización, qué calendario debería maximizarla ni cómo se mediría. Tal como está, solo puede evaluarse retrospectivamente y corre riesgo de circularidad. Debería eliminarse o reformularse como una hipótesis con estados fenológicos y una predicción a priori concreta.

### 4.5 El posible pastoreo durante las primeras aplicaciones es un asunto crítico

La tesis indica antecedentes de pastoreo y señala cierre el 1.º de julio, pero M1 se aplicó el 12 de junio y M2 el 26 de junio. El archivo de manejo agregado también indica pastoreo “hasta cierre”. Debe reconstruirse exactamente qué ocurrió:

- ¿las parcelas experimentales estaban cercadas y excluidas del pastoreo desde antes del 12 de junio?
- ¿el cierre del 1.º de julio se refiere al resto del semillero, pero no a los ensayos?
- ¿hubo animales dentro de M1/M2 después de aplicar urea?
- ¿la medición basal del 12 de junio se tomó antes o después de aplicar M1?

Si las parcelas fueron pastoreadas, el efecto temprano queda combinado con defoliación diferencial, remoción de tejido, devolución localizada de excretas y posible pérdida/distribución de fertilizante. No sería necesariamente fatal, pero debería formar parte de la definición del tratamiento y limitar la interpretación.

Este punto no se resuelve estadísticamente. Requiere la bitácora de campo y memoria de quienes ejecutaron el ensayo.

### 4.6 Fechas conflictivas y procedencia de datos

El libro de Excel contiene tablas preliminares con fechas distintas y, en algunos lugares, año 2026 pese a que el ensayo fue en 2025. También aparecen fechas planificadas de muestreo diferentes de las ejecutadas. La tesis usa una cronología coherente, pero debe dejar explícito cuál es la fuente autoritativa:

> “Las fechas presentadas corresponden a las aplicaciones y muestreos efectivamente ejecutados según la bitácora de campo; las planillas preliminares de planificación no se utilizaron para definir los tratamientos.”

Luego debe corregirse o archivarse la planilla conflictiva. En una defensa, una discrepancia de fechas es exactamente el tipo de detalle que un tribunal puede usar para cuestionar toda la trazabilidad.

### 4.7 “Biomasa producida” y “N acumulado” no son procesos acumulativos observados

Cada fecha usa un corte destructivo diferente dentro de la parcela. La variable mide **biomasa aérea en pie en esa fecha**, no producción acumulada de biomasa. Entre fechas pudo haber senescencia, caída, consumo, respiración, redistribución y material no recuperado. De modo análogo, biomasa × concentración mide **stock de N en la biomasa aérea muestreada**, no absorción total acumulada de N por el cultivo.

Conviene reemplazar:

- “producción de biomasa” por “biomasa aérea presente” o “biomasa aérea en pie”;
- “captura/acumulación de N” por “N presente en la biomasa aérea” o “stock aéreo de N”.

Puede conservarse “acumulación” si se define explícitamente como stock instantáneo, pero “absorción” o “captura” sería demasiado fuerte.

### 4.8 Muestreo destructivo y representatividad dentro de parcela

La parcela mide 24 m², mientras los muestreos usan áreas mucho menores. La tesis debería documentar:

- tamaño y ubicación exacta de cada franja;
- separación entre franjas de septiembre, octubre y noviembre;
- distancia a bordes y calles;
- si la cosecha final evitó áreas previamente cortadas;
- cómo se seleccionó la ubicación dentro de parcela;
- si hubo corrección por espacios faltantes o heterogeneidad visible.

El diseño experimental controla variación entre parcelas mediante bloques, pero no elimina error de submuestreo dentro de parcelas. Esta fuente de variabilidad es relevante con n = 4.

### 4.9 Madurez fisiológica y fecha común de cosecha

La cosecha final se realizó el mismo día. Si los calendarios alteraron fenología o madurez, una fecha común puede favorecer tratamientos que coincidieron mejor con ese momento. Debe indicarse cómo se determinó “madurez fisiológica”, si se midió humedad de semilla, desgrane previo, coloración o algún criterio reproductivo objetivo.

Sin eso, no puede descartarse que parte de las diferencias de componentes o pérdidas refleje distinto grado de madurez al cosechar.

### 4.10 Documentación del suelo, laboratorio y riego

La caracterización edáfica es útil, pero le faltan detalles reproducibles: fecha, profundidad, número de submuestras, si se hizo una muestra compuesta por sector o una sola para todo el sitio, laboratorio y métodos analíticos.

Para las mediciones de N también deben indicarse método de laboratorio, preparación/molienda, precisión y control de calidad. Para riego, conviene informar fechas exactas, láminas por evento, método de medición y cualquier dato de uniformidad o deriva hacia el sector de secano. La suma estacional de 165 mm es insuficiente para interpretar disponibilidad posterior a cada aplicación.

---

## 5. Revisión estadística

### 5.1 Las preguntas deberían formularse como estimandos distintos

La tesis gana mucha claridad si organiza todo el análisis alrededor de cuatro preguntas:

1. **Calendario entre fertilizados:** ¿cómo difieren M1–M5 dentro de cada sector?
2. **Respuesta al N adicional:** ¿cuánto difiere el promedio de M1–M5 respecto de M0 sobre el manejo común?
3. **Trayectoria temporal:** ¿cambia el patrón M1–M5 entre septiembre, octubre y noviembre?
4. **Consistencia entre sectores:** ¿el patrón relativo observado difiere entre estos dos sectores físicos?

Estas preguntas no deberían mezclarse en un único omnibus M0–M5 ni interpretarse con la misma jerarquía.

### 5.2 El análisis longitudinal debería ser principal para las variables repetidas

La tesis analiza biomasa, concentración de N, N presente en biomasa e INN mediante ANOVA separados por fecha. Esos ANOVA responden correctamente a “¿había diferencias en esta fecha?”, pero no a:

- “¿las trayectorias difirieron?”;
- “¿la ventaja temprana se redujo?”;
- “¿el orden de tratamientos cambió?”;
- “¿hubo convergencia?”.

Inferir convergencia porque un p es significativo en septiembre y no lo es en noviembre es un caso clásico de **diferencia de significancia ≠ diferencia significativa**. La afirmación de `tesis.md:L1161` requiere un contraste tratamiento × fecha o contrastes explícitos del cambio.

Por sector, una formulación razonable es:

$$
Y_{ijk}=\mu+B_j+T_i+F_k+(T\times F)_{ik}+u_{ij}+\varepsilon_{ijk},
$$

donde `fecha` se trata como factor categórico, `bloque` como efecto fijo, y `u_{ij}` es un intercepto aleatorio de parcela. El modelo debe ajustarse primero a M1–M5; M0–M5 queda como análisis complementario.

Los resultados actuales del cuaderno son los siguientes. Para biomasa y concentración de N, la inferencia de la interacción usa *bootstrap* paramétrico; N presente en biomasa e INN son variables derivadas de apoyo y conservan el LRT asintótico. El valor `q` es el ajuste de Benjamini–Hochberg dentro de la familia correspondiente.

| Variable | Sector | p calendario promedio | p interacción usada | q BH | Lectura principal |
|---|---:|---:|---:|---:|---|
| Biomasa aérea | Secano | < 0,0001 | 0,225 | 0,300 | Diferencias medias claras, sin evidencia robusta de distinta forma temporal en la escala original |
| Biomasa aérea | Riego | < 0,0001 | 0,900 | 0,900 | Diferencias medias, sin evidencia de distinta forma temporal |
| N en biomasa (%) | Secano | 0,3780 | 0,050 | 0,100 | Señal limítrofe de interacción que no persiste al controlar FDR |
| N en biomasa (%) | Riego | 0,0069 | 0,005 | 0,020 | Diferencias y cambio temporal claros |
| N presente en biomasa | Secano | 0,0015 | 0,0004 | 0,0004 | Interacción clara, como evidencia derivada de apoyo |
| N presente en biomasa | Riego | 0,0008 | 0,0004 | 0,0004 | Interacción clara, como evidencia derivada de apoyo |
| INN | Secano | 0,0508 | < 0,0001 | < 0,0001 | Cambio temporal claro en una variable derivada |
| INN | Riego | 0,0028 | < 0,0001 | < 0,0001 | Diferencias y cambio temporal claros en una variable derivada |

Esto obliga a una lectura más sobria que la basada en los LRT originales. La evidencia primitiva más clara de trayectorias diferentes está en la concentración de N de riego. La interacción de biomasa no está respaldada en la escala original y, en secano, es sensible a la transformación: el *bootstrap* da p = 0,225 en escala original y p = 0,010 en escala logarítmica. Por tanto, no debe presentarse como una conclusión robusta a la especificación.

#### Estado y límites del modelo actual

El código actual prueba cinco optimizadores, conserva el ajuste convergido con mayor log-verosimilitud, registra los casos de varianza del intercepto aleatorio en el límite y usa 199 réplicas de *bootstrap* paramétrico para las interacciones primitivas M1–M5. También informa la relación entre la mayor y la menor desviación residual por fecha y repite biomasa en escala logarítmica.

Quedan límites que deben acompañar la interpretación:

- el modelo principal todavía supone una única varianza residual, aunque los diagnósticos muestran heterogeneidad por fecha, especialmente para concentración de N;
- la varianza del intercepto aleatorio queda en el límite en varios ajustes, señal de poca evidencia de correlación persistente una vez incluidos fecha, bloque y tratamiento;
- 199 réplicas proporcionan una resolución Monte Carlo de 0,005, suficiente para la auditoría actual pero modesta para fijar p-valores muy próximos a un umbral; una versión final podría usar al menos 999;
- la discrepancia entre escalas de biomasa en secano debe presentarse como sensibilidad, no resolverse eligiendo retrospectivamente la escala más favorable.

El objetivo no es construir un modelo sofisticado por deporte. Es probar directamente la afirmación temporal, presentar estimaciones con intervalos y mostrar cuándo la conclusión depende de la especificación.

### 5.3 La fórmula de la celda faltante es incorrecta

En `tesis.md:L584-L590` se presenta:

$$
\hat{x}=\frac{rB+tT-G}{(r-1)(t-1)},
$$

con `r` = número de bloques, `t` = número de tratamientos, `B` = total del bloque que contiene el faltante y `T` = total del tratamiento que contiene el faltante.

Con esas definiciones, la fórmula estándar para una celda faltante en un DBCA es:

$$
\hat{x}=\frac{tB+rT-G}{(t-1)(r-1)}.
$$

Los coeficientes de `B` y `T` están intercambiados en la tesis. El código actual en `src/festuca_analysis/longitudinal.py` y la salida ejecutada de `festuca_estudio_longitudinal.ipynb` ya contienen la expresión correcta.

Para M1–R4–secano–16/09:

- total del bloque sin la celda: $B=9,8771379$;
- total del tratamiento sin la celda: $T=7,0041859$;
- total general sin la celda: $G=44,2468436$;
- $r=4$, $t=6$.

La imputación correcta en el diseño completo es:

$$
\hat{x}=2,8688485\%N.
$$

El valor de 2,4857882 que permanece en `tesis.md` proviene exactamente de la fórmula invertida. En la comparación M1–M5 de concentración de N en septiembre, el p cambia aproximadamente así:

| Tratamiento del faltante | p global M1–M5 |
|---|---:|
| Mantenerlo faltante, análisis principal | 0,2518 |
| Imputación incorrecta publicada | 0,1534 |
| Imputación correcta usando diseño M0–M5 | 0,0829 |
| Imputación correcta calculada solo en M1–M5 | 0,1130 |

No cruza 0,05, pero se acerca bastante más. La tesis debe corregirse porque es un error verificable y porque afecta también N presente en biomasa e INN de la sensibilidad. El análisis actual mantiene correctamente la observación como faltante en el análisis principal; el modelo de máxima verosimilitud usa las demás observaciones bajo una hipótesis MAR sin rellenar el dato.

### 5.4 No significancia no demuestra equivalencia práctica

Con cuatro parcelas por calendario, la prueba omnibus tiene precisión limitada. En rendimiento M1–M5:

- secano: p = 0,4287;
- riego: p = 0,1759.

La conclusión defendible es:

> “No se identificó un calendario superior con la precisión disponible.”

No es defendible:

> “Los calendarios fueron equivalentes” o “el momento no tuvo efecto agronómicamente relevante”.

Las medias abarcan aproximadamente 197 kg ha⁻¹ en secano y 300 kg ha⁻¹ en riego entre el mayor y el menor calendario. Esas diferencias pueden ser agronómicamente relevantes aunque la evidencia sea insuficiente para atribuirlas con seguridad.

El anexo probabilístico lo expresa bien: no hay un ganador claro, pero la probabilidad de que el rango supere un margen provisional de 100 kg ha⁻¹ no es pequeña, especialmente en riego, y depende de la regularización. La tesis debería definir —idealmente con base económica— una diferencia mínima relevante y presentar intervalos de diferencias. Si no puede hacerse antes de la entrega, al menos debe declarar que la equivalencia no fue evaluada.

### 5.5 Multiplicidad y jerarquía de evidencia

Aproximadamente se realizan:

- 4 variables longitudinales × 3 fechas × 2 sectores × 2 conjuntos de tratamientos = 48 ANOVA globales;
- múltiples componentes finales;
- análisis conjuntos;
- Tukey por varios resultados;
- numerosas correlaciones.

Con este volumen, algunos p cercanos a 0,05 son esperables aun sin señales reales. Tukey controla el error dentro de cada familia de comparaciones, no a través de todas las variables, fechas y sectores.

La solución no tiene que ser una corrección Bonferroni indiscriminada. El código actual ya declara la siguiente jerarquía, que debe trasladarse a Métodos, Resultados y Discusión de la tesis:

- **Resultado primario:** rendimiento de semilla limpia, comparación M1–M5 por sector.
- **Contraste complementario predefinido:** promedio M1–M5 frente a M0.
- **Resultados secundarios clave:** biomasa aérea y concentración de N longitudinales, con interacción tratamiento × fecha.
- **Variables derivadas/apoyo:** N presente en biomasa, INN, componentes finales.
- **Exploratorio:** correlaciones, EAN, productividad aparente del agua y sensibilidades.

El análisis actual aplica FDR de Benjamini–Hochberg dentro de las familias definidas y etiqueta el nivel inferencial de cada salida. Las tablas exploratorias deben mantener lenguaje no confirmatorio y enfatizar magnitudes e intervalos aun cuando un `q` sea pequeño.

### 5.6 Las correlaciones M0–M5 mezclan preguntas y están parcialmente inducidas

Las correlaciones con las 24 parcelas de cada sector están dominadas en varios casos por la separación entre M0 y los fertilizados. El análisis actual las etiqueta como exploratorias, marca las variables matemáticamente acopladas, presenta M1–M5 y residuales ajustados, y calcula FDR. Como evidencia del problema que debe corregirse en la tesis, muestra:

| Variable final vs rendimiento | Sector | r M0–M5 | r M1–M5 | r residual ajustando tratamiento y bloque |
|---|---|---:|---:|---:|
| Biomasa | Secano | 0,626 | 0,376 | 0,293 |
| Biomasa | Riego | 0,286 | 0,183 | −0,107 |
| N (%) | Secano | 0,565 | 0,079 | −0,403 |
| N (%) | Riego | 0,531 | 0,069 | 0,016 |
| N presente en biomasa | Secano | 0,791 | 0,448 | 0,006 |
| N presente en biomasa | Riego | 0,583 | 0,211 | −0,094 |

La asociación bruta responde en gran medida a “las parcelas con N adicional rindieron más”, no a una relación parcela-a-parcela independiente dentro de calendarios comparables. `tesis.md:L1231` debería moderarse de forma importante.

A esto se suma el acoplamiento matemático:

- semillas estimadas por panoja contiene rendimiento y panojas;
- índice de cosecha contiene rendimiento;
- merma contiene masa limpia;
- N presente en biomasa contiene biomasa y N%;
- INN es función de biomasa y N%;
- EAN es una transformación del rendimiento contra M0;
- productividad aparente del agua es rendimiento dividido por una constante sectorial.

Analizar estas variables como columnas distintas no genera evidencia independiente. El cuaderno ya las relega a auditoría exploratoria; la tesis debería hacer lo mismo o reducirlas a pocas relaciones no tautológicas.

### 5.7 La “compensación” entre componentes no está identificada

La fórmula usada es:

$$
\widehat{S}=\frac{1000M_{\text{limpia}}}{W_{1000}P},
$$

donde $P$ es densidad de panojas. Incluso si masa limpia, PMS y panojas fueran generados sin ningún mecanismo de compensación, dividir por $P$ induce una asociación inversa entre $P$ y $\widehat{S}$.

El nulo de reconstrucción de Agustín encuentra:

- parcelas M1–M5, ambos sectores: r observado ≈ −0,669; percentil nulo ≈ 49,7;
- medias de tratamientos en secano: r observado ≈ −0,815; percentil ≈ 48,9;
- medias de tratamientos en riego: r observado ≈ −0,818; percentil ≈ 48,5.

El patrón observado es literalmente central bajo la reconstrucción. Por tanto, frases como “la relación inversa pudo atenuar las diferencias” no deben aparecer como resultado en el resumen (`tesis.md:L24`) ni como conclusión (`L1277`). Puede decirse:

> “Los calendarios produjeron descomposiciones contrastantes del rendimiento en densidad de panojas y número reconstruido de semillas por panoja. Como este último se calculó a partir del rendimiento y de la densidad de panojas, el patrón no permite inferir compensación biológica.”

Para demostrar compensación se necesitarían mediciones independientes de flores, semillas potenciales, fertilidad, cuajado, aborto y supervivencia, o al menos conteo directo de semillas por panoja en una muestra independiente.

### 5.8 Métricas redundantes: EAN y productividad aparente del agua

Dentro de cada sector, todos los tratamientos M1–M5 tienen el mismo incremento de 200 kg N ha⁻¹. La EAN es, por tanto, una reexpresión lineal de la diferencia de rendimiento frente a M0; no aporta un test distinto.

La productividad aparente del agua divide rendimiento por 510 mm en secano o 675 mm en riego. Dentro de cada sector, conserva exactamente el orden, p y estructura de incertidumbre del rendimiento. Entre sectores, el denominador es mayor por definición en riego y no representa agua consumida. Es una métrica descriptiva débil y potencialmente confusa.

El código actual implementa la política adecuada:

- resume EAN descriptivamente, sin una sección inferencial propia;
- resume productividad aparente del agua como transformación descriptiva del rendimiento;
- no usa ninguna de las dos como evidencia independiente de la hipótesis de sincronización.

La tesis debe adoptar la misma jerarquía y moverlas al anexo o reducirlas a un párrafo descriptivo.

### 5.9 Inconsistencia en el uso de Tukey

Métodos declara que Tukey se aplica cuando el ANOVA global es significativo. Sin embargo, varias tablas con omnibus no significativo muestran todas las medias con letra “a”, por ejemplo PMS, índice de cosecha y merma. Esas letras no aportan información y contradicen la regla declarada.

Debe elegirse una convención consistente:

- mostrar grupos de Tukey solo cuando el omnibus predefinido es significativo; o
- declarar que las comparaciones se muestran siempre, pero entonces interpretar con extremo cuidado.

La primera opción es más limpia. También conviene reportar F, grados de libertad, p y una medida de efecto o intervalos, no únicamente p.

### 5.10 Supuestos, valores atípicos y dos registros de materia seca

Los registros finales 150 y 152 presentan discrepancias fuertes entre `%MS` ingresado y el cociente de peso seco/peso verde:

- registro 150, riego M4 R4: 118/420 = 28,10 %, pero se registró 18,2 %;
- registro 152, riego M2 R4: 101/667 = 15,14 %, pero se registró 25,0 %.

La tesis afirma que no hay evidencia de error de medición/registro. Esa frase es demasiado fuerte hasta revisar formularios originales, hojas de laboratorio o unidades. El análisis actual formaliza las tres políticas —registrado, cociente y exclusión— para biomasa, N presente en biomasa e INN, en M1–M5 y M0–M5. En riego M1–M5, por ejemplo, el p de biomasa cambia de 0,0686 a 0,2423 o 0,0735; el de N presente en biomasa, de 0,1037 a 0,1666 o 0,0777; y el de INN, de 0,0512 a 0,0823 o 0,0666. Esto muestra sensibilidad cerca del umbral y refuerza, no reemplaza, la necesidad de verificar la fuente primaria.

La política correcta es:

1. verificar los registros primarios;
2. corregir solo si existe evidencia documental;
3. si no puede resolverse, conservar el dato original como principal y mostrar sensibilidades “registrado / cociente / excluido”.

---

## 6. Revisión por sección de la tesis

### 6.1 Título y resumen

El título actual sobrepromete dos cosas: un factor escalar “momento” y una comparación secano-riego que puede leerse causalmente. Recomiendo la alternativa propuesta antes o una variante que incluya “calendarios” y “dos sectores”.

El resumen actual (`tesis.md:L24`) contiene casi todos los resultados, pero debe cambiar en cinco aspectos:

1. decir “200 kg N ha⁻¹ **adicionales al manejo nitrogenado común**”;
2. usar “calendarios”;
3. presentar el resultado longitudinal con la interacción, no solo ANOVA por fecha;
4. eliminar la relación inversa como explicación de compensación;
5. reemplazar “no permitió identificar” por una formulación que también reconozca la incertidumbre sobre equivalencia.

Una versión conceptualmente más segura del núcleo sería:

> Entre M1–M5 no se identificó un calendario superior para el rendimiento de semilla en ninguno de los sectores, aunque la precisión disponible no permitió demostrar equivalencia agronómica entre ellos. El análisis longitudinal mostró que los calendarios modificaron principalmente la trayectoria de la concentración y del estado nitrogenado; la evidencia de diferencias en la forma temporal de la biomasa fue más débil. Todos los tratamientos con 200 kg N ha⁻¹ experimentales adicionales superaron ampliamente a M0, que recibió el manejo nitrogenado general del semillero. Las diferencias entre sectores se interpretaron únicamente para los dos contextos observados.

### 6.2 Introducción y revisión bibliográfica

La introducción está bien orientada, pero el documento completo dedica bastante espacio a mecanismos que luego no se miden. Conviene acortar la revisión y estructurarla alrededor de las decisiones que el experimento sí puede informar:

- calendario de N y componentes tempranos/tardíos;
- diferencia entre respuesta a dosis y respuesta al fraccionamiento;
- necesidad de análisis temporal;
- limitaciones de inferir procesos reproductivos desde variables reconstruidas;
- papel contextual del agua sin un diseño factorial replicado.

Hay una dependencia fuerte de unas pocas referencias, en particular Formoso. Para una tesis de casi 20.000 palabras, la base bibliográfica parece delgada. Sería conveniente sumar literatura primaria sobre producción de semilla de gramíneas, cronología de N, macollos reproductivos y validez/calibración del INN en etapas reproductivas. Esto requiere una revisión bibliográfica específica, separada de esta auditoría interna.

`tesis.md:L215` ya anticipa la idea de que trayectorias pueden “converger mediante relaciones inversas”. Esa frase predispone toda la tesis hacia una explicación que los datos no identifican. Debe reemplazarse por algo neutral:

> “La ausencia de diferencias finales puede coexistir con trayectorias temporales diferentes; determinar si ello responde a compensación biológica requiere mediciones independientes de los componentes y procesos involucrados.”

### 6.3 Objetivos e hipótesis

El objetivo específico de caracterizar la respuesta temporal (`tesis.md:L231`) exige un modelo longitudinal. Es la principal razón por la que ese análisis debe ir en el cuerpo.

Las hipótesis necesitan revisión:

- **H1** es demasiado específica y casi coincide con la historia observada. Si fue realmente preespecificada, debería documentarse. Si no, conviene dividirla en predicciones más generales y evitar apariencia de *HARKing*.
- **H2** formula ausencia de diferencias finales, pero NHST convencional no puede confirmar equivalencia. Debe incluir un margen o reformularse como expectativa, no hipótesis demostrable por p > 0,05.
- **H3** puede mantenerse solo como patrón entre los dos sectores observados, sin lenguaje de interacción causal con riego.
- **H4** usa “sincronización” sin una métrica observable y luego deriva EAN/PAA del rendimiento; es casi tautológica. Recomiendo eliminarla o definir antes qué calendario se considera sincronizado, con qué estado fenológico y qué contraste lo prueba.

Una versión más defendible sería:

> H1. Los calendarios de aplicación generan trayectorias diferentes de biomasa aérea y estado nitrogenado durante septiembre-noviembre.
>
> H2. Las diferencias entre calendarios en el rendimiento final son menores que [margen agronómico definido], aunque el diseño puede tener precisión limitada para demostrarlo.
>
> H3. El patrón relativo de los calendarios puede diferir entre los dos sectores observados; esta comparación no se interpreta como una interacción causal generalizable con el riego.

Si no puede definirse un margen, H2 debería convertirse en pregunta, no en hipótesis confirmatoria.

### 6.4 Materiales y métodos

La sección es detallada, pero debe incorporar o corregir:

- título del factor como calendario;
- N común y N total de cada grupo;
- cronología autoritativa y fechas de riego;
- acceso de animales y orden de operaciones del 12 de junio;
- fenología observada o ausencia de ella;
- ubicación de franjas destructivas y cosecha;
- método de laboratorio de N;
- muestreo y análisis de suelo;
- criterio de madurez;
- especificación exacta del software, versión y tipo de suma de cuadrados;
- modelo longitudinal y estimandos;
- jerarquía de resultados y política de multiplicidad;
- fórmula corregida de imputación;
- política para los registros 150/152.

Un detalle de presentación: `tesis.md:L281` dice “el Tabla 1”; debe ser “la Tabla 1”. Hay ocurrencias similares posteriores.

### 6.5 Resultados

La sección de resultados es muy extensa, con 19 tablas y prácticamente ninguna visualización. Varias páginas repiten el patrón “la Tabla X muestra… p = …”. Esto reduce legibilidad y hace difícil apreciar efectos e incertidumbre.

La reorganizaría así:

1. **Contexto y cronograma:** una figura de calendario y una tabla mínima de agua/manejo.
2. **Resultado primario:** una figura de rendimiento con las dos escalas M0–M5 y M1–M5.
3. **Trayectorias temporales:** figuras de biomasa y N%, con resultados de interacción.
4. **Componentes finales:** una figura o tabla compacta de panojas y PMS; semillas estimadas explícitamente marcada como reconstruida.
5. **Resultados suplementarios:** N presente en biomasa, INN, análisis por fecha, EAN, PAA, correlaciones y diagnósticos al anexo.

Las frases interpretativas como “consistente con la proximidad de la aplicación” deberían trasladarse a Discusión. En Resultados conviene describir estimaciones, intervalos y contrastes.

Evitar:

- “las diferencias desaparecieron” solo porque p pasó de <0,05 a >0,05;
- “favoreció” cuando solo hay una media numéricamente mayor no significativa;
- “convergió” sin interacción/contraste del cambio;
- repetir todas las letras de Tukey en prosa.

### 6.6 Discusión

La discusión tiene una estructura razonable, pero su mecanismo central es más fuerte que la evidencia.

#### Rendimiento

`tesis.md:L1139-L1151` es básicamente correcto. Debe añadirse que no se demostró equivalencia práctica y que la diferencia de dosis total respecto de M0 ocurre sobre un fondo común de 164 kg N ha⁻¹.

#### Trayectoria temporal

`tesis.md:L1155-L1167` debe reescribirse usando el modelo longitudinal actual. La concentración de N muestra una interacción clara en riego; en secano queda en p = 0,050 por *bootstrap* y q = 0,100. N presente en biomasa e INN muestran interacciones como evidencia derivada de apoyo. Biomasa no muestra interacción en la escala original de ninguno de los sectores, y el resultado de secano cambia en escala logarítmica. No conviene afirmar una convergencia general ni seleccionar una escala retrospectivamente.

También debe sustituirse “producción” por “biomasa presente” y reconocer que M5 tenía media dosis acumulada en septiembre.

#### Componentes y compensación

`tesis.md:L1171-L1185` es la sección más vulnerable. La interpretación biológica de la relación panojas–semillas estimadas debe retirarse o quedar explícitamente como hipótesis no probada. El texto ya admite la dependencia matemática en `L1183`, pero la usa igualmente para sostener que pudo reducir diferencias. Esa concesión no salva la inferencia.

Además, “M5 no permitió recuperar estructuras reproductivas definidas previamente” (`L1175`) requiere fenología y mediciones directas de macollos reproductivos. Debería ser “es compatible con una menor densidad final, pero no permite determinar cuándo ni por qué se perdió esa estructura”.

#### Agua

La sección reconoce bien la limitación del sector único. Puede acortarse. La productividad aparente del agua no debería ocupar un papel central porque es rendimiento reescalado por entradas brutas y no agua usada.

#### Correlaciones

Debe reducirse drásticamente. Las correlaciones brutas M0–M5 no deberían usarse para fortalecer mecanismos. Podrían presentarse como auditoría exploratoria en anexo, con M1–M5 y residuales.

### 6.7 Conclusiones

Las conclusiones actuales mezclan hallazgos robustos, tendencias débiles y una explicación no identificada. Recomiendo una jerarquía más austera:

1. los 200 kg N ha⁻¹ experimentales adicionales produjeron una respuesta grande frente a M0 sobre el manejo común;
2. no se identificó un calendario M1–M5 superior, pero tampoco se demostró equivalencia agronómica;
3. los calendarios modificaron la trayectoria del estado nitrogenado; la evidencia sobre la forma temporal de la biomasa fue más dependiente del sector;
4. los componentes reconstruidos no permiten demostrar compensación biológica;
5. las diferencias entre sectores no estiman un efecto causal del riego;
6. la generalización requiere ciclos, dosis, fenología y unidades hídricas independientes.

Una redacción propuesta:

> Bajo las condiciones del ciclo 2025, los tratamientos que recibieron 200 kg N ha⁻¹ experimentales adicionales sobre la fertilización general del semillero produjeron cerca del doble de semilla limpia que M0. Entre los cinco calendarios con igual dosis experimental no se identificó uno consistentemente superior. Con cuatro bloques por tratamiento, el estudio tampoco demostró que sus diferencias fueran agronómicamente equivalentes.
>
> Los calendarios modificaron principalmente la trayectoria de la concentración y del estado nitrogenado. Las aplicaciones tempranas se asociaron con mayor biomasa aérea al primer muestreo, aunque la evidencia de diferencias en la forma longitudinal de la biomasa fue más débil que para las variables nitrogenadas. En septiembre, la comparación que incluyó M5 también reflejó que este tratamiento aún había recibido solo la mitad de la dosis experimental.
>
> La densidad de panojas y el número reconstruido de semillas por panoja mostraron patrones contrastantes, pero este último fue calculado usando rendimiento y densidad de panojas. En consecuencia, esos datos no permiten demostrar compensación biológica entre componentes.
>
> Las comparaciones entre secano y riego describen únicamente los dos sectores observados. Para formular recomendaciones generales se requieren varios ciclos y sitios, dosis adicionales, aplicaciones vinculadas a fenología medida y replicación independiente de la condición hídrica.

---

## 7. Revisión del análisis longitudinal agregado por Agustín

### 7.1 Valor científico

Es la adición más importante. Responde directamente al objetivo temporal, usa la parcela como unidad repetida, separa M1–M5 de M0–M5 y hace visible la diferencia transitoria de dosis de M5. También incluye observaciones individuales, medias marginales e incertidumbre, en lugar de depender solo de p-valores.

El encuadre actual ya ubica el modelo longitudinal como análisis inferencial principal para las variables repetidas y deja los ANOVA por fecha como descomposición y control de reproducibilidad. Esa jerarquía es la apropiada y debe trasladarse a la tesis.

### 7.2 Qué resultados deberían pasar al cuerpo

Pasar al cuerpo:

- interacción calendario × fecha para biomasa y concentración de N;
- medias marginales y datos observados;
- sensibilidad M1–M4 en septiembre;
- una frase breve sobre N presente en biomasa/INN, con gráficos detallados en anexo.

No hace falta llevar cada LRT, cada variable derivada y cada diagnóstico al cuerpo. La tesis puede concentrarse en las variables primitivas y usar las derivadas como apoyo.

### 7.3 Implementación actual y límites

La implementación actual incluye:

1. La fórmula y la aserción de imputación esperan 2,868848 % N; el faltante no se rellena en el análisis principal.
2. Los comandos y el `README.md` usan los nombres reales de los notebooks y también ofrecen puntos de entrada de terminal.
3. El ajuste mixto prueba todos los optimizadores configurados y selecciona el mejor convergido por log-verosimilitud.
4. Biomasa se evalúa en escala original y logarítmica, y se informa la heterogeneidad residual por fecha.
5. Las interacciones primitivas M1–M5 usan *bootstrap* paramétrico y FDR; los LRT asintóticos de variables derivadas se rotulan como apoyo.
6. Las salidas usan “biomasa aérea” y “N presente en biomasa”, evitando presentar stocks instantáneos como captura acumulada.
7. Las figuras principales de biomasa y concentración de N tienen dos paneles cada una; N presente en biomasa e INN quedaron en una figura de anexo.
8. La sensibilidad de los registros 150/152, la jerarquía inferencial y el carácter descriptivo de EAN/PAA se exportan a CSV.

No debe confundirse “código corregido” con “incertidumbre metodológica eliminada”. Siguen siendo pertinentes la sensibilidad de escala de biomasa, la varianza aleatoria en el límite, el número modesto de réplicas de *bootstrap* y la verificación documental de los registros 150/152.

### 7.4 Contrastes dirigidos

Los contrastes bayesianos agregados son útiles como síntesis:

- septiembre, biomasa M1–M2 frente a M3–M4: evidencia fuerte en secano y moderada en riego;
- octubre, N% M4–M5 frente a M1–M2: evidencia muy fuerte en riego y sugerente en secano.

El cuaderno actual los llama “contrastes dirigidos por hipótesis”. Debe mantenerse esa denominación salvo que exista documentación de que fueron definidos antes de ver los datos; “preespecificados” sería demasiado fuerte si nacieron durante el reanálisis.

---

## 8. Revisión del anexo probabilístico agregado por Agustín

### 8.1 Qué aporta de verdad

El anexo probabilístico agrega tres ideas valiosas que el análisis clásico no expresa bien:

1. cuantifica la magnitud y certeza de la respuesta M1–M5 frente a M0;
2. distingue “no hay ganador identificado” de “los calendarios son equivalentes”;
3. demuestra que la correlación de componentes no excede lo esperado por reconstrucción matemática.

Esas tres contribuciones justifican un anexo. El modelo longitudinal probabilístico es útil, pero parcialmente redundante si el modelo mixto clásico ya entra al cuerpo. El modelo B de estados latentes es mucho más dependiente de supuestos y no es necesario para sostener la tesis.

### 8.2 Qué conservaría

En un anexo compacto conservaría:

- Modelo A de rendimiento en escala original;
- sensibilidad a la regularización y márgenes prácticos;
- probabilidad de cada calendario de ser mejor, presentada solo como incertidumbre de ranking;
- análisis dejando un bloque afuera;
- nulo de reconstrucción de semillas por panoja;
- opcionalmente, los contrastes longitudinales dirigidos.

### 8.3 Qué reduciría o excluiría

- Modelo B: dejar como análisis exploratorio técnico o eliminar de la tesis, salvo que se verifiquen los datos de materia seca y se justifiquen errores de medición y curva crítica.
- Modelos C y D: correcto excluirlos; no hace falta narrar mucho su historia en una tesis agronómica.
- Detalles de implementación del muestreador: están correctamente relegados al repositorio; la tesis o el anexo deben conservar la especificación matemática y la tabla numérica de priors que ahora exporta el código.
- Figuras probabilísticas redundantes: elegir pocas y orientadas a una decisión.

### 8.4 Alcance actual de la reproducibilidad

El repositorio contiene `reference_outputs/legacy_probabilistic_run/` con los seis resúmenes mínimos de la corrida histórica, sus SHA-256 y una explicación de procedencia. `uv run --frozen festuca-annex` recalcula el modelo A corregido de rendimiento y regenera todas las tablas y figuras del anexo; los resultados se escriben en `results/`.

La reproducibilidad tiene, sin embargo, dos niveles distintos:

- **Reproducción de los artefactos finales:** está cerrada. El comando único reconstruye tablas y figuras usando el Excel, el código actual y los resúmenes congelados versionados.
- **Remuestreo completo desde datos primitivos:** está cerrado para el modelo A corregido de rendimiento, pero no para el modelo A longitudinal, el modelo B y el nulo de reconstrucción. Esos tres componentes consumen resúmenes aceptados de la corrida histórica porque no se conservaron sus cadenas completas.

Esta solución es auditable, pero no debe describirse como remuestreo integral. Si el tribunal o el repositorio institucional exigen regenerar cada cadena desde el Excel, habrá que recuperar las cadenas/generadores originales o reimplementar esos tres componentes y documentar el cambio de versión inferencial.

### 8.5 Priors y validación del muestreador

El anexo actual exporta una tabla completa de priors y un chequeo predictivo previo con 20 000 simulaciones por sector y escala de regularización. La especificación usa verosimilitud Student-t con 5 grados de libertad, priors explícitos para intercepto, N adicional, bloque, escala de los contrastes temporales y varianza residual, todo documentado en la escala estandarizada y en kg ha⁻¹ tras desestandarizar.

El muestreador personalizado fue contrastado con una implementación independiente en PyMC:

- diferencia máxima entre medias posteriores de tratamiento: 4,31 kg ha⁻¹;
- cero divergencias en las corridas de referencia;
- R-hat máximo: 1,006;
- ESS *bulk* mínimo: 1416;
- cobertura de los intervalos del 95 % en simulación-recuperación: 6 de 6 medias verdaderas.

Además, las pruebas unitarias cubren la parametrización del diseño, la densidad de la escala jerárquica, la selección de optimizador, el LRT y el ajuste de multiplicidad. R-hat y ESS quedan así complementados por validación contra una referencia independiente y por recuperación sobre datos simulados. Una calibración basada en muchas simulaciones (*simulation-based calibration*) seguiría siendo una mejora posible, no un requisito pendiente para sostener los resultados actuales.

En el texto en español conviene escribir ESS como “1416” o “1 416”; “1.416” puede leerse como uno coma cuatrocientos dieciséis.

### 8.6 Interpretación del rango posterior

El rango máximo–mínimo entre cinco medias es sensible a incertidumbre, regularización y selección de extremos. El propio anexo lo reconoce. No debería transformarse en una probabilidad de “efecto real” sin matiz.

Los contrastes agronómicos planificados y las probabilidades de estar dentro de una región de equivalencia definida son más interpretables. El margen de 100 kg ha⁻¹ debe justificarse económicamente o presentarse explícitamente como ilustrativo.

---

## 9. Plan de figuras para la tesis

La ausencia actual de figuras es una debilidad importante. No hace falta convertir la tesis en un atlas; cuatro figuras bien elegidas serían suficientes para cambiar radicalmente su legibilidad.

### Figura 1. Cronograma experimental y N acumulado

El análisis genera `figura_01_cronograma_y_n_acumulado` en PNG y PDF. Presenta M0–M5, aplicaciones experimentales y comunes, muestreos y N acumulado, y resalta que M5 tenía 100 kg N ha⁻¹ experimentales el 16 de septiembre. Es científicamente esencial porque revela de inmediato qué significa cada “calendario”. Antes de insertarla en la tesis solo debe verificarse que todas las fechas coincidan con la bitácora autoritativa.

### Figura 2. Rendimiento: dos preguntas y dos escalas

`figura_03_rendimiento_dos_preguntas` está lista en PNG y PDF y separa visualmente:

- la gran respuesta M0 vs fertilizados;
- la incertidumbre y solapamiento entre M1–M5.

La figura muestra puntos individuales y medias ajustadas con IC. El pie de la tesis debe aclarar que los IC son puntuales y que n = 4 por tratamiento.

### Figuras 3 y 4. Trayectorias primitivas

El análisis ya genera las dos figuras destinadas al cuerpo:

- **Figura 3:** biomasa aérea en pie por fecha, sector y calendario;
- **Figura 4:** concentración de N en biomasa por fecha, sector y calendario.

Estas dos variables son más primitivas e interpretables que N presente en biomasa e INN. `figura_04_trayectorias_biomasa_aerea` y `figura_05_trayectorias_concentracion_n` usan dos paneles, uno por sector, con:

- puntos de parcela discretos;
- líneas de medias marginales;
- IC del 95 %;
- p de interacción en el pie, no dentro de cada panel;
- nota sobre M5 en septiembre.

N presente en biomasa e INN están juntos en `anexo_trayectorias_n_biomasa_e_inn`, fuera de las figuras principales.

### Figura opcional 5. Componentes finales

Mostrar densidad de panojas y PMS. Si se incluye semillas por panoja, rotularla como **“número reconstruido de semillas por panoja”** y añadir en el pie la fórmula. No usar una línea de correlación como evidencia de compensación.

### Figuras para anexos

- contrastes simultáneos de rendimiento;
- sensibilidad del faltante;
- sensibilidad de registros 150/152;
- diagnósticos residuales;
- prior-sensitivity y margen práctico;
- distribución nula de la correlación reconstruida.

### Principios gráficos

- evitar gráficos de barras sin datos;
- mostrar observaciones individuales;
- mantener el mismo color/marcador por M1–M5 en toda la tesis;
- no depender solo del color;
- exportar PDF/SVG vectorial;
- indicar n y datos faltantes;
- usar escalas coherentes entre sectores cuando la comparación visual lo requiera;
- reservar letras de Tukey para una tabla o pie, no saturar la figura.

---

## 10. Reestructuración propuesta

### 4. Materiales y métodos

**4.1 Sitio y semillero**  
**4.2 Diseño, unidad experimental y alcance de la comparación hídrica**  
**4.3 Calendarios, fertilización común y cronograma ejecutado**  
**4.4 Muestreo, laboratorio y variables primitivas/derivadas**  
**4.5 Control y auditoría de datos**  
**4.6 Estrategia estadística**

- 4.6.1 Resultado primario: rendimiento M1–M5
- 4.6.2 Contraste complementario: promedio M1–M5 vs M0
- 4.6.3 Modelos longitudinales
- 4.6.4 Componentes finales
- 4.6.5 Comparación descriptiva entre sectores
- 4.6.6 Sensibilidades y análisis exploratorios

### 5. Resultados

**5.1 Cronograma y contexto ambiental**  
**5.2 Rendimiento de semilla: respuesta al N y comparación de calendarios**  
**5.3 Trayectorias de biomasa y estado nitrogenado**  
**5.4 Componentes finales**  
**5.5 Sensibilidades y robustez**

### 6. Discusión

**6.1 Respuesta al N adicional y precisión entre calendarios**  
**6.2 Efectos temporales sobre biomasa y N**  
**6.3 Componentes: qué se observó y qué no puede inferirse**  
**6.4 Alcance de la comparación entre sectores**  
**6.5 Implicancias, límites y diseño de futuros ensayos**

### Anexos

- **Anexo A:** ANOVA por fecha, Tukey, diagnósticos y tablas completas.
- **Anexo B:** análisis probabilístico reducido y reproducible.
- **Anexo C:** auditoría de datos, imputación y sensibilidades.

---

## 11. *Red team*: preguntas que podría hacer un tribunal exigente

### 11.1 Sobre el diseño

**“¿Por qué el riego aparece en el título y en las hipótesis si hay una sola unidad por régimen?”**  
Respuesta defendible: no se estima el efecto causal del riego; los sectores se presentan como contextos observados y el análisis de interacción solo describe diferencias de patrón entre ellos. Acción: ajustar título e hipótesis para que eso sea inequívoco.

**“¿El tratamiento es momento, primera fecha, segunda fecha o un paquete de dos aplicaciones?”**  
Respuesta: es un calendario categórico completo. Acción: abandonar interpretaciones continuas y usar “calendario”.

**“¿Por qué los intervalos entre aplicaciones no son iguales?”**  
Respuesta: fueron calendarios agronómicos definidos, no un diseño factorial para separar fecha e intervalo. Acción: reconocer que no se identifican sus componentes por separado.

**“¿M1 y M2 fueron pastoreados después de recibir N?”**  
Hoy no hay una respuesta documental suficientemente clara. Acción P0: recuperar la bitácora.

**“¿La muestra del 12 de junio se tomó antes de aplicar M1?”**  
Debe documentarse el orden exacto.

### 11.2 Sobre dosis y manejo

**“¿200 kg N ha⁻¹ significa N elemental o 200 kg de urea?”**  
La tesis dice N elemental y calcula 217,4 kg de urea por aplicación. Conviene mantener esa aclaración visible.

**“¿Cuánto N total recibió realmente cada tratamiento?”**  
M0 aproximadamente 164 kg N ha⁻¹ de manejo común; M1–M5 aproximadamente 364 kg N ha⁻¹. Acción: informarlo de forma central.

**“¿Cuándo ocurrió exactamente la aplicación general de agosto?”**  
No está documentado en la versión disponible. Acción: recuperar fecha o reconocer la incertidumbre.

**“¿Qué lluvia o riego ocurrió después de cada urea superficial?”**  
La tesis solo usa totales mensuales/estacionales. Acción: incorporar series diarias si existen o evitar mecanismos de disponibilidad demasiado precisos.

### 11.3 Sobre datos y trazabilidad

**“¿Por qué el Excel contiene 2026 y fechas distintas a la tesis?”**  
Debe explicarse como planificación preliminar y quedar una fuente autoritativa ejecutada.

**“¿Por qué confían en los registros 150 y 152 si el %MS no coincide con los pesos?”**  
Respuesta actual insuficiente. Acción: verificar primaria y reportar sensibilidad.

**“¿Cómo se colocaron los cortes destructivos y cómo se evitó afectar la cosecha?”**  
Falta detalle metodológico.

**“¿Cómo se determinó madurez fisiológica?”**  
Falta criterio observable.

### 11.4 Sobre inferencia estadística

**“¿Cómo pueden afirmar convergencia si solo deja de ser significativo el ANOVA?”**  
No se puede. Acción: usar tratamiento × fecha y contrastes de cambio.

**“¿Por qué hay letras Tukey cuando el omnibus no es significativo?”**  
Inconsistencia que debe corregirse.

**“¿Cómo controlaron el gran número de pruebas?”**  
El análisis reproducible define resultados primarios, secundarios, de apoyo y exploratorios, y aplica FDR por familias. Acción: incorporar explícitamente esa misma jerarquía en la tesis.

**“¿Por qué p > 0,05 implica que los calendarios son agronómicamente iguales?”**  
No lo implica. Acción: no afirmar igualdad; presentar intervalos/margen.

**“¿Por qué imputaron con esa fórmula?”**  
La fórmula que permanece en `tesis.md` es incorrecta. El código usa la fórmula correcta y mantiene el faltante en el análisis principal. Acción: corregir el texto de la tesis.

### 11.5 Sobre mecanismos

**“¿Cómo saben que hubo compensación si semillas por panoja se calculó dividiendo por panojas?”**  
No se sabe; la relación es algebraicamente inducida. Acción: retirar la inferencia.

**“¿Cómo saben que la aplicación tardía no recuperó macollos reproductivos?”**  
No se midieron macollos reproductivos ni fenología. Solo se observó densidad final de panojas.

**“¿Por qué llaman absorción de N a biomasa × concentración en un corte instantáneo?”**  
Debe llamarse stock aéreo de N.

**“¿Qué evidencia independiente aportan EAN y productividad del agua?”**  
Prácticamente ninguna dentro de sector; son transformaciones del rendimiento.

### 11.6 Sobre el anexo probabilístico

**“¿Puedo regenerar todos los resultados desde el Excel con un comando?”**  
`uv run --frozen festuca-annex` regenera todas las tablas y figuras. El modelo A de rendimiento se remuestrea desde los datos; el modelo A longitudinal, el modelo B y el nulo de reconstrucción se reconstruyen desde seis resúmenes históricos con checksums. La respuesta correcta debe distinguir regeneración de artefactos de remuestreo integral.

**“¿Cómo validaron el Gibbs personalizado?”**  
Se comparó con una implementación independiente en PyMC y con simulación-recuperación: diferencia máxima de 4,31 kg ha⁻¹ en medias de tratamiento, cero divergencias, R-hat máximo 1,006, ESS *bulk* mínimo 1416 y cobertura 6/6. Las pruebas unitarias verifican además parametrización y transformaciones clave.

**“¿Por qué 100 kg ha⁻¹ es el margen relevante?”**  
Es provisional. Acción: justificar económicamente o mostrar una curva de márgenes sin privilegiarlo.

---

## 12. Secuencia de revisión recomendada

### Fase 1: resolver hechos y errores

1. Confirmar fechas ejecutadas, pastoreo/exclusión, orden del 12 de junio y fecha general de agosto.
2. Verificar registros de materia seca 150 y 152.
3. Corregir en `tesis.md` la fórmula y el valor de imputación; las sensibilidades reproducibles ya usan el cálculo correcto.
4. Confirmar dosis/unidades y cuantificar N común/total.
5. Corregir archivos de procedencia y nombres conflictivos.

### Fase 2: rehacer la columna vertebral inferencial

1. Incorporar en la tesis los resultados del modelo longitudinal M1–M5 por sector ya implementado.
2. Adoptar la jerarquía inferencial y el control FDR documentados por el análisis.
3. Presentar rendimiento como dos preguntas: M0 vs fertilizados y M1–M5.
4. Retirar inferencias de compensación y correlaciones mecanísticas acopladas.
5. Reformular no significancia como falta de identificación, no equivalencia.

### Fase 3: reescribir narrativa

1. Título, pregunta, objetivos e hipótesis en términos de calendarios.
2. Resumen y conclusiones según la jerarquía revisada.
3. Discusión de mecanismos en lenguaje condicional y anclada a lo medido.
4. Cambiar “producción/captura” por variables de stock observadas.
5. Reducir redundancias, tablas y resultados derivados.

### Fase 4: figuras y anexos

1. Insertar el cronograma generado y verificar sus fechas contra la bitácora.
2. Insertar la figura generada de rendimiento en dos escalas.
3. Insertar la figura generada de biomasa longitudinal.
4. Insertar la figura generada de concentración de N longitudinal.
5. Seleccionar del análisis reproducible las tablas y diagnósticos que irán al anexo clásico.
6. Mantener compacto el anexo probabilístico y declarar el uso de resúmenes históricos congelados.

### Fase 5: auditoría final

1. Comprobar que cada número del resumen/conclusión provenga de una tabla o figura reproducible.
2. Revisar que ningún resultado exploratorio se presente como confirmatorio.
3. Verificar referencias, unidades, fechas, nombres M0/MO y gramática de tablas.
4. Ejecutar el proyecto desde un entorno limpio.
5. Pedir a una persona no involucrada que intente responder: “¿qué se puede afirmar causalmente?” y “¿qué no se puede afirmar?” solo leyendo resumen y conclusiones.

---

## 13. Veredicto final

La tesis tiene un experimento útil y una historia científica defendible, pero esa historia debe ser más sobria:

- **sí** hubo una respuesta grande al N experimental adicional;
- **sí** los calendarios alteraron el estado del cultivo a lo largo del tiempo;
- **no** se identificó un calendario superior para rendimiento;
- **no** se demostró equivalencia entre calendarios;
- **no** se demostró compensación biológica entre componentes;
- **no** se estimó causalmente el efecto del riego.

El análisis longitudinal de Agustín mejora de manera directa la adecuación entre objetivo y método y debería incorporarse al núcleo. El anexo probabilístico ya puede regenerar sus tablas y figuras, documenta sus priors y valida el muestreador; debe mantenerse centrado en preguntas distintas y declarar que tres componentes históricos se reconstruyen desde resúmenes congelados, no mediante remuestreo integral.

Con las correcciones P0 y P1, tres o cuatro figuras y una reescritura que distinga resultado, inferencia e hipótesis, la tesis puede quedar no solo defendible, sino bastante más fuerte que la versión típica basada en una secuencia de ANOVA y letras de Tukey. Sin esas correcciones, un tribunal atento puede desmontar la narrativa de convergencia/compensación con dos objeciones algebraicas y una pregunta sobre la cronología de campo.
