# Revisión extensiva y *red team* de la tesis sobre fertilización nitrogenada en festuca alta

## Dictamen ejecutivo

**Dictamen: revisión mayor antes de la entrega.** El experimento no es inválido ni la tesis está mal encaminada. Al contrario, tiene una base experimental defendible para estudiar **diferencias entre calendarios de fertilización dentro de cada sector**, y el texto ya reconoce con una honestidad poco habitual dos límites importantes: M0 no es un control sin nitrógeno total, y los sectores de secano y riego no son réplicas independientes del régimen hídrico. Esas dos decisiones evitan errores graves.

Lo que impide considerar la versión actual lista no es una falla única, sino una desalineación entre:

1. la pregunta central, que es explícitamente temporal;
2. el análisis principal, que fragmenta el tiempo en ANOVA independientes;
3. varias afirmaciones de “trayectorias”, “convergencia” y “compensación” que exceden lo identificado por esos análisis o por las variables medidas.

Hay además tres asuntos concretos que deberían resolverse antes de la entrega:

- **La fórmula de imputación de la celda faltante está mal escrita y mal aplicada.** Con la notación usada en la tesis, se intercambiaron los coeficientes de los totales de bloque y tratamiento. La imputación correcta para el diseño completo es 2,86885 % N, no 2,48579 % N. El resultado principal no cambia al 5 %, pero la sensibilidad sí cambia de forma material.
- **Hay que verificar la cronología ejecutada y el manejo del pastoreo.** M1 y M2 recibieron su primera aplicación antes del cierre del 1.º de julio. Si los animales siguieron accediendo a las parcelas, el tratamiento temprano quedó combinado con defoliación, posible redistribución de N y una exposición diferencial. Además, el libro contiene fechas preliminares/conflictivas y años 2026 para un ensayo realizado en 2025.
- **La supuesta compensación entre panojas y semillas estimadas por panoja no está demostrada.** El número de semillas por panoja fue reconstruido usando el rendimiento y el número de panojas; una relación inversa con panojas aparece mecánicamente por la fórmula. El análisis nulo agregado por Agustín muestra que la correlación observada queda aproximadamente en el percentil 49 de la distribución inducida por esa reconstrucción. Por tanto, no aporta evidencia independiente de compensación biológica.

Mi recomendación central coincide en buena medida con la intuición de Agustín, pero la haría un poco más fuerte: **el análisis longitudinal debería integrar el cuerpo principal, no quedar como una curiosidad complementaria**. Los ANOVA por fecha pueden conservarse como análisis de seguimiento y para mostrar medias puntuales, pero una tesis cuyo objetivo es “caracterizar la respuesta temporal” necesita probar directamente tratamiento × fecha. El anexo probabilístico sí puede quedar en un anexo, reducido a los módulos que agregan una pregunta científica nueva y cuya reproducibilidad quede cerrada.

---

## 1. Alcance de esta revisión y atribución del material

Para evitar mezclar responsabilidades:

- **Tesis de Emanuel Choca y Serrana Montero:** el contenido de `sources/` y su transcripción exacta en `tesis.md`.
- **Material analítico agregado por Agustín:** `festuca_estudio_longitudinal.ipynb`, `festuca_anexo_probabilistico.ipynb`, sus versiones Markdown, el código, figuras, diagramas y archivos derivados fuera de `sources/`.

Las objeciones a la formulación científica, documentación de campo, métodos originales, resultados y redacción se refieren a la tesis. Las observaciones sobre reproducibilidad, modelos mixtos, modelos probabilísticos y figuras específicas se refieren al material agregado. Hay un error compartido: la fórmula incorrecta de imputación aparece tanto en la tesis como en el cuaderno longitudinal.

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
| **P0** | Fórmula de imputación incorrecta | Error matemático verificable en Métodos y sensibilidad | Corregir fórmula, valor y todos los resultados derivados; corregir también el cuaderno longitudinal |
| **P0** | Cronología ejecutada y posible pastoreo después de M1/M2 | Posible confusión diferencial del tratamiento temprano | Revisar bitácora; documentar exclusión real de animales, fechas ejecutadas y orden muestreo/aplicación |
| **P0** | Inferencia de compensación desde una variable reconstruida | Conclusión biológica apoyada en acoplamiento algebraico | Retirar del resumen y conclusiones; reformular como descomposición no independiente o hipótesis no probada |
| **P0/P1** | Pregunta longitudinal analizada principalmente con ANOVA separados | No se prueba formalmente el cambio de trayectorias ni la “convergencia” | Incorporar modelo repetido/mixto tratamiento × fecha en Métodos y Resultados principales |
| **P1** | Dos valores de %MS final inconsistentes con pesos crudos | Pueden alterar biomasa, N acumulado e INN finales | Verificar registros 150 y 152; reportar sensibilidad si no se resuelve |
| **P1** | Tratamiento denominado “momento” aunque son paquetes de dos fechas, con intervalos distintos | Se atribuyen efectos a una variable que no fue aislada | Usar “calendario” o “distribución temporal”; evitar inferir efecto de primera/segunda fecha por separado |
| **P1** | No significancia tratada parcialmente como convergencia/equivalencia | Sobreinterpretación del ensayo con n = 4 | Estimar interacciones, efectos e intervalos; declarar que no hubo ganador y tampoco se demostró equivalencia |
| **P1** | Multiplicidad y jerarquía de resultados poco explícitas | Hallazgos marginales pueden parecer confirmatorios | Definir resultado primario, secundarios y exploratorios; controlar FDR o interpretar exploratoriamente |
| **P1** | Correlaciones M0–M5 dominadas por la separación de dosis y variables acopladas | Relaciones presentadas como mecanismo sin evidencia independiente | Restringir a M1–M5, ajustar tratamiento/bloque y reducir correlaciones del cuerpo principal |
| **P1** | Anexo probabilístico no reproducible de extremo a extremo en el ZIP | Resultados importados sin artefactos ni generador disponible | Incluir pipeline completo o artefactos versionados con checksum; validar el muestreador personalizado |
| **P2** | Exceso de tablas y ausencia total de figuras | La tesis es difícil de leer y oculta magnitud/incertidumbre | Incorporar 3–4 figuras centrales y trasladar tablas detalladas al anexo |
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

El cuaderno longitudinal ya calcula esa sensibilidad. En septiembre, restringiendo a M1–M4, se mantienen diferencias de biomasa en secano y riego, y de N acumulado/INN principalmente en riego. Esto fortalece parte de la narrativa temprana sin atribuir a calendario lo que es dosis transitoria.

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

La tesis analiza biomasa, concentración de N, N aéreo e INN mediante ANOVA separados por fecha. Esos ANOVA responden correctamente a “¿había diferencias en esta fecha?”, pero no a:

- “¿las trayectorias difirieron?”;
- “¿la ventaja temprana se redujo?”;
- “¿el orden de tratamientos cambió?”;
- “¿hubo convergencia?”.

Inferir convergencia porque un p es significativo en septiembre y no lo es en noviembre es un caso clásico de **diferencia de significancia ≠ diferencia significativa**. La afirmación de `tesis.md:L1161` requiere un contraste tratamiento × fecha o contrastes explícitos del cambio.

Por sector, una formulación razonable es:

\[
Y_{ijk}=\mu+B_j+T_i+F_k+(T\times F)_{ik}+u_{ij}+\varepsilon_{ijk},
\]

donde `fecha` se trata como factor categórico, `bloque` como efecto fijo, y `u_{ij}` es un intercepto aleatorio de parcela. El modelo debe ajustarse primero a M1–M5; M0–M5 queda como análisis complementario.

Los resultados del cuaderno agregado son informativos:

| Variable | Sector | p calendario promedio | p calendario × fecha | Lectura principal |
|---|---:|---:|---:|---|
| Biomasa aérea | Secano | < 0,0001 | 0,0746 | Diferencias medias claras; evidencia solo sugestiva de trayectorias no paralelas |
| Biomasa aérea | Riego | < 0,0001 | 0,7863 | Diferencias medias, pero sin evidencia de distinta forma temporal |
| N en biomasa (%) | Secano | 0,3780 | 0,0088 | El orden cambia entre fechas |
| N en biomasa (%) | Riego | 0,0069 | < 0,0001 | Diferencias y cambio temporal claros |
| N aéreo | Secano | 0,0015 | 0,0004 | Trayectorias claramente diferentes |
| N aéreo | Riego | 0,0008 | 0,0004 | Trayectorias claramente diferentes |
| INN | Secano | 0,0508 | < 0,0001 | Cambio temporal claro; promedio fronterizo |
| INN | Riego | 0,0028 | < 0,0001 | Diferencias y cambio temporal claros |

Esto obliga a matizar una parte de la historia actual: el desplazamiento temporal de concentración de N y estado nitrogenado está bien respaldado; la idea de “convergencia de biomasa” es mucho menos clara, especialmente en riego.

#### Refinamientos recomendables del modelo

El cuaderno usa un intercepto aleatorio de parcela y error residual homogéneo. Es una mejora sustantiva sobre ANOVA separados, pero no debería considerarse la única especificación posible:

- los residuos de biomasa probablemente aumentan de escala entre septiembre y noviembre;
- una transformación logarítmica o un modelo con varianza residual por fecha puede ser más realista;
- con solo 20 parcelas en M1–M5 por sector, los LRT asintóticos pueden ser optimistas;
- sería ideal usar grados de libertad de Satterthwaite/Kenward–Roger o *parametric bootstrap* para interacciones importantes;
- la varianza del intercepto aleatorio queda en cero en varios ajustes, lo que indica poca evidencia de correlación residual persistente después de fecha, bloque y tratamiento. No invalida el modelo, pero sugiere que un GLS con estructura de varianza/correlación simple podría ser igual o más estable.

El objetivo no es construir un modelo sofisticado por deporte. Es probar directamente la afirmación temporal y presentar estimaciones con intervalos.

### 5.3 La fórmula de la celda faltante es incorrecta

En `tesis.md:L584-L590` se presenta:

\[
\hat{x}=\frac{rB+tT-G}{(r-1)(t-1)},
\]

con `r` = número de bloques, `t` = número de tratamientos, `B` = total del bloque que contiene el faltante y `T` = total del tratamiento que contiene el faltante.

Con esas definiciones, la fórmula estándar para una celda faltante en un DBCA es:

\[
\hat{x}=\frac{tB+rT-G}{(t-1)(r-1)}.
\]

Los coeficientes de `B` y `T` están intercambiados en la tesis y en `festuca_estudio_longitudinal_markdown.md:L151-L159`.

Para M1–R4–secano–16/09:

- total del bloque sin la celda: \(B=9,8771379\);
- total del tratamiento sin la celda: \(T=7,0041859\);
- total general sin la celda: \(G=44,2468436\);
- \(r=4\), \(t=6\).

La imputación correcta en el diseño completo es:

\[
\hat{x}=2,8688485\%N.
\]

El valor publicado, 2,4857882, proviene exactamente de la fórmula invertida. En la comparación M1–M5 de concentración de N en septiembre, el p cambia aproximadamente así:

| Tratamiento del faltante | p global M1–M5 |
|---|---:|
| Mantenerlo faltante, análisis principal | 0,2518 |
| Imputación incorrecta publicada | 0,1534 |
| Imputación correcta usando diseño M0–M5 | 0,0829 |
| Imputación correcta calculada solo en M1–M5 | 0,1130 |

No cruza 0,05, pero se acerca bastante más. Debe corregirse porque es un error verificable y porque afecta también N aéreo e INN de la sensibilidad. La recomendación sigue siendo no imputar en el análisis principal; un modelo de máxima verosimilitud puede usar las demás observaciones bajo una hipótesis MAR sin rellenar el dato.

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

La solución no tiene que ser una corrección Bonferroni indiscriminada. Conviene declarar una jerarquía:

- **Resultado primario:** rendimiento de semilla limpia, comparación M1–M5 por sector.
- **Contraste complementario predefinido:** promedio M1–M5 frente a M0.
- **Resultados secundarios clave:** biomasa aérea y concentración de N longitudinales, con interacción tratamiento × fecha.
- **Variables derivadas/apoyo:** N aéreo, INN, componentes finales.
- **Exploratorio:** correlaciones, EAN, productividad aparente del agua y sensibilidades.

Para las tablas exploratorias se puede usar FDR o, como mínimo, evitar lenguaje confirmatorio y enfatizar magnitudes e intervalos.

### 5.6 Las correlaciones M0–M5 mezclan preguntas y están parcialmente inducidas

Las correlaciones con las 24 parcelas de cada sector están dominadas en varios casos por la separación entre M0 y los fertilizados. Por ejemplo, el cuaderno de auditoría muestra:

| Variable final vs rendimiento | Sector | r M0–M5 | r M1–M5 | r residual ajustando tratamiento y bloque |
|---|---|---:|---:|---:|
| Biomasa | Secano | 0,626 | 0,376 | 0,293 |
| Biomasa | Riego | 0,286 | 0,183 | −0,107 |
| N (%) | Secano | 0,565 | 0,079 | −0,403 |
| N (%) | Riego | 0,531 | 0,069 | 0,016 |
| N aéreo | Secano | 0,791 | 0,448 | 0,006 |
| N aéreo | Riego | 0,583 | 0,211 | −0,094 |

La asociación bruta responde en gran medida a “las parcelas con N adicional rindieron más”, no a una relación parcela-a-parcela independiente dentro de calendarios comparables. `tesis.md:L1231` debería moderarse de forma importante.

A esto se suma el acoplamiento matemático:

- semillas estimadas por panoja contiene rendimiento y panojas;
- índice de cosecha contiene rendimiento;
- merma contiene masa limpia;
- N aéreo contiene biomasa y N%;
- INN es función de biomasa y N%;
- EAN es una transformación del rendimiento contra M0;
- productividad aparente del agua es rendimiento dividido por una constante sectorial.

Analizar estas variables como columnas distintas no genera evidencia independiente. Las correlaciones deberían ir al anexo o reducirse a pocas relaciones no tautológicas, mostrando M1–M5 y ajuste por tratamiento/bloque.

### 5.7 La “compensación” entre componentes no está identificada

La fórmula usada es:

\[
\widehat{S}=\frac{1000M_{\text{limpia}}}{W_{1000}P},
\]

donde \(P\) es densidad de panojas. Incluso si masa limpia, PMS y panojas fueran generados sin ningún mecanismo de compensación, dividir por \(P\) induce una asociación inversa entre \(P\) y \(\widehat{S}\).

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

Recomendación:

- mantener EAN en un párrafo o tabla suplementaria, sin una sección inferencial propia;
- mover productividad aparente del agua al anexo o eliminarla del núcleo argumental;
- no usar ninguna de las dos como evidencia adicional de la hipótesis de sincronización.

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

La tesis afirma que no hay evidencia de error de medición/registro. Esa frase es demasiado fuerte hasta revisar formularios originales, hojas de laboratorio o unidades. El análisis de sensibilidad agregado muestra que las conclusiones globales son razonablemente robustas, pero algunos p finales cambian. Eso es tranquilizador, no una razón para omitir la verificación.

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
5. **Resultados suplementarios:** N aéreo, INN, análisis por fecha, EAN, PAA, correlaciones y diagnósticos al anexo.

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

`tesis.md:L1155-L1167` debe reescribirse usando el modelo longitudinal. La concentración de N, N aéreo e INN muestran evidencia clara de interacción; biomasa no muestra una interacción clara en riego y solo sugestiva en secano. No conviene afirmar una convergencia general de biomasa o N aéreo únicamente desde ANOVA puntuales.

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

Mi única discrepancia con el encuadre del cuaderno es la frase “complementa; no sustituye”. Para la tesis revisada, el modelo longitudinal debería **sustituir como análisis inferencial principal** a la colección de ANOVA independientes para biomasa/N, aunque estos últimos sigan como descomposición por fecha y control de reproducibilidad.

### 7.2 Qué resultados deberían pasar al cuerpo

Pasar al cuerpo:

- interacción calendario × fecha para biomasa y concentración de N;
- medias marginales y datos observados;
- sensibilidad M1–M4 en septiembre;
- una frase breve sobre N aéreo/INN, con gráficos detallados en anexo.

No hace falta llevar cada LRT, cada variable derivada y cada diagnóstico al cuerpo. La tesis puede concentrarse en las variables primitivas y usar las derivadas como apoyo.

### 7.3 Correcciones necesarias

1. **Corregir la fórmula de imputación** y la aserción que espera 2,485788.
2. El comando de reproducción menciona `festuca_thesis_replication_longitudinal.ipynb`, pero el archivo incluido se llama `festuca_estudio_longitudinal.ipynb`.
3. El optimizador debería seleccionar el mejor ajuste convergido, no el primer ajuste finito. En los resultados actuales todos parecen converger, así que no cambia las conclusiones, pero sí la robustez del código.
4. Evaluar log-transformación o varianza por fecha para biomasa.
5. Para inferencia final, preferir *bootstrap* paramétrico o corrección de grados de libertad sobre LRT puramente asintótico.
6. Cambiar el título “crecimiento y captura de N” por “biomasa aérea y N presente en biomasa”.
7. No mostrar cuatro paneles con demasiados p-valores en una sola figura principal. La versión de tesis debería ser más simple.

### 7.4 Contrastes dirigidos

Los contrastes bayesianos agregados son útiles como síntesis:

- septiembre, biomasa M1–M2 frente a M3–M4: evidencia fuerte en secano y moderada en riego;
- octubre, N% M4–M5 frente a M1–M2: evidencia muy fuerte en riego y sugerente en secano.

Deben llamarse “contrastes dirigidos por hipótesis” salvo que exista documentación de que fueron definidos antes de ver los datos. “Preespecificados” sería demasiado fuerte si nacieron durante el reanálisis.

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
- Detalles de implementación del muestreador: pueden ir en repositorio, no en el texto, pero la especificación del modelo y priors sí debe estar completa.
- Figuras probabilísticas redundantes: elegir pocas y orientadas a una decisión.

### 8.4 Problema de reproducibilidad actual

El ZIP no contiene `festuca_probabilistic_outputs/` ni `results/`, pese a que el código y el cuaderno declaran importar cadenas y tablas desde esas rutas. `code/festuca_annex_v2_analysis.py` recalcula el modelo corregido de rendimiento, pero los modelos longitudinales, B y el nulo de reconstrucción dependen de resultados externos no incluidos.

Por tanto, el anexo actual **no es reproducible de extremo a extremo** a partir del paquete entregado. Las salidas embebidas en el notebook prueban que alguna corrida existió, pero no permiten auditar cómo se generaron todos los números.

Hay dos soluciones aceptables:

- incluir todo el generador y un comando único que produzca tablas, figuras y cadenas desde el Excel; o
- incluir artefactos de posterior versionados, con hashes/checksums, metadatos de software/semilla y código exacto que los consumió.

La primera es preferible.

### 8.5 Priors y validación del muestreador

El anexo describe la regularización cualitativamente, pero debería incluir una tabla numérica completa de priors y análisis predictivo previo. En particular, el modelo de rendimiento usa resultados estandarizados y varias escalas de regularización; esa transformación y cada prior deben poder reconstruirse sin leer el código.

Si se mantiene un muestreador Gibbs personalizado, R-hat y ESS solo indican mezcla de las cadenas, no que el algoritmo apunte a la distribución correcta. Debería añadirse al repositorio:

- prueba contra una implementación de referencia en Stan/PyMC/brms en un subconjunto;
- simulación-recuperación de parámetros;
- idealmente *simulation-based calibration*;
- tests unitarios de parametrización y transformación a kg ha⁻¹.

También conviene escribir ESS como “1 704” o “1704”; “1.704” en español puede leerse como uno coma siete.

### 8.6 Interpretación del rango posterior

El rango máximo–mínimo entre cinco medias es sensible a incertidumbre, regularización y selección de extremos. El propio anexo lo reconoce. No debería transformarse en una probabilidad de “efecto real” sin matiz.

Los contrastes agronómicos planificados y las probabilidades de estar dentro de una región de equivalencia definida son más interpretables. El margen de 100 kg ha⁻¹ debe justificarse económicamente o presentarse explícitamente como ilustrativo.

---

## 9. Plan de figuras para la tesis

La ausencia actual de figuras es una debilidad importante. No hace falta convertir la tesis en un atlas; cuatro figuras bien elegidas serían suficientes para cambiar radicalmente su legibilidad.

### Figura 1. Cronograma experimental y N acumulado

La figura existente `cell_011_out_1.png` contiene la información correcta, pero está demasiado cargada para el cuerpo principal. Debería simplificarse:

- mostrar M0–M5 en filas y las dos aplicaciones como puntos/segmentos;
- añadir aplicaciones comunes y muestreos como líneas verticales discretas;
- indicar N total común y total final;
- resaltar que M5 tenía 100 kg N ha⁻¹ experimentales el 16 de septiembre;
- no mezclar demasiados colores, etiquetas y sombras mensuales;
- usar las fechas ejecutadas verificadas.

Esta figura es científicamente esencial porque revela de inmediato qué significa cada “calendario”.

### Figura 2. Rendimiento: dos preguntas y dos escalas

`cell_027_out_0.png` es probablemente la mejor figura lista para el cuerpo. Separa visualmente:

- la gran respuesta M0 vs fertilizados;
- la incertidumbre y solapamiento entre M1–M5.

Mantendría puntos individuales y medias ajustadas con IC. Reduciría texto incrustado, usaría una paleta accesible en escala de grises y aclararía en el pie que los IC son puntuales y n = 4.

### Figuras 3 y 4. Trayectorias primitivas

El cuerpo debería mostrar:

- **Figura 3:** biomasa aérea en pie por fecha, sector y calendario;
- **Figura 4:** concentración de N en biomasa por fecha, sector y calendario.

Estas dos variables son más primitivas e interpretables que N aéreo e INN. Se pueden usar dos paneles por figura, uno por sector, con:

- puntos de parcela discretos;
- líneas de medias marginales;
- IC del 95 %;
- p de interacción en el pie, no dentro de cada panel;
- nota sobre M5 en septiembre.

N aéreo e INN pueden ir juntos en una figura del anexo. La figura actual de cuatro paneles es útil para auditoría, pero demasiado densa para lectura narrativa.

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
La versión actual no presenta una jerarquía suficiente. Acción: primario/secundario/exploratorio y FDR o cautela explícita.

**“¿Por qué p > 0,05 implica que los calendarios son agronómicamente iguales?”**  
No lo implica. Acción: no afirmar igualdad; presentar intervalos/margen.

**“¿Por qué imputaron con esa fórmula?”**  
La fórmula actual es incorrecta. Acción: corregir y mantener el faltante como análisis principal.

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
No con el ZIP actual. Acción: cerrar reproducibilidad.

**“¿Cómo validaron el Gibbs personalizado?”**  
R-hat/ESS no bastan. Acción: comparación con implementación de referencia y simulación-recuperación.

**“¿Por qué 100 kg ha⁻¹ es el margen relevante?”**  
Es provisional. Acción: justificar económicamente o mostrar una curva de márgenes sin privilegiarlo.

---

## 12. Secuencia de revisión recomendada

### Fase 1: resolver hechos y errores

1. Confirmar fechas ejecutadas, pastoreo/exclusión, orden del 12 de junio y fecha general de agosto.
2. Verificar registros de materia seca 150 y 152.
3. Corregir fórmula de imputación y volver a generar todas las sensibilidades.
4. Confirmar dosis/unidades y cuantificar N común/total.
5. Corregir archivos de procedencia y nombres conflictivos.

### Fase 2: rehacer la columna vertebral inferencial

1. Incorporar modelo longitudinal M1–M5 por sector.
2. Definir jerarquía de resultados.
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

1. Cronograma simplificado.
2. Rendimiento en dos escalas.
3. Biomasa longitudinal.
4. Concentración de N longitudinal.
5. Anexo clásico con tablas completas y diagnósticos.
6. Anexo probabilístico compacto y reproducible.

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

El análisis longitudinal de Agustín mejora de manera directa la adecuación entre objetivo y método, y debería incorporarse al núcleo. El anexo probabilístico añade valor si se reduce a preguntas distintas, se corrige su reproducibilidad y se evita que una capa estadística sofisticada oculte limitaciones básicas del diseño.

Con las correcciones P0 y P1, tres o cuatro figuras y una reescritura que distinga resultado, inferencia e hipótesis, la tesis puede quedar no solo defendible, sino bastante más fuerte que la versión típica basada en una secuencia de ANOVA y letras de Tukey. Sin esas correcciones, un tribunal atento puede desmontar la narrativa de convergencia/compensación con dos objeciones algebraicas y una pregunta sobre la cronología de campo.
