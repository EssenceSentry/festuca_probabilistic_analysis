# Dictamen ejecutivo

El resultado central está bien:

* M1–M5 es la comparación principal entre calendarios con la misma dosis experimental.
* M0–M5 se usa complementariamente para mostrar la respuesta al N adicional.
* No se identificó un calendario superior para rendimiento.
* Los sectores se analizan principalmente por separado y no se atribuye causalmente al riego su diferencia media.
* El dato faltante de N se mantiene ausente en el análisis principal.
* La productividad aparente del agua y la eficiencia agronómica se reconocen como transformaciones del rendimiento.
* La tesis ya advierte que ausencia de significación no equivale a igualdad exacta.  

Eso constituye una base perfectamente defendible para una versión sencilla.

Los cambios que siguen son **correcciones**, no propuestas de expansión.

---

# P0 — Cambios imprescindibles

## 1. M0 todavía está mal definido en varias partes y falta gran parte de la fertilización común

El resumen ya dice correctamente:

> M0 se incluyó como testigo sin nitrógeno experimental adicional.

Pero la introducción volvió a decir:

> M0 como testigo sin nitrógeno aplicado.

Y Métodos dice:

> M0 correspondió al testigo sin nitrógeno.

Eso contradice tanto al resumen como a las propias limitaciones y conclusiones de la tesis.

Además, el manejo general solo documenta en la tesis la aplicación de abril. En la hoja `Manejo` del libro incluido en el ZIP también figuran:

* abril: 150 kg ha⁻¹ de urea azufrada;
* 1.º de julio: 130 kg ha⁻¹ de urea azufrada;
* agosto: 130 kg ha⁻¹ de urea azufrada, sin fecha exacta consignada.

Con 40 % de N, representan aproximadamente:

$$
60+52+52=164\ \mathrm{kg\ N\ ha^{-1}}
$$

comunes a todo el semillero. Por tanto:

$$
M0 \approx 164\ \mathrm{kg\ N\ ha^{-1}}
$$

y

$$
M1\text{–}M5 \approx 164+200=364\ \mathrm{kg\ N\ ha^{-1}}.
$$

La tesis actual menciona la fertilización de abril y el cierre del 1.º de julio, pero omite las fertilizaciones generales de julio y agosto.

### Corrección exacta para 4.4

> Se evaluaron seis tratamientos definidos por el calendario de las aplicaciones experimentales de nitrógeno. M0 no recibió nitrógeno experimental adicional, mientras que M1–M5 recibieron 200 kg N ha⁻¹ experimentales, fraccionados en dos aplicaciones de 100 kg N ha⁻¹.

### Párrafo que debe agregarse o restaurarse en 4.5

> Además de las aplicaciones experimentales, todo el semillero recibió fertilizaciones generales: 150 kg ha⁻¹ de urea azufrada en abril, 130 kg ha⁻¹ el 1.º de julio y 130 kg ha⁻¹ durante agosto, en fecha exacta no consignada. Estos aportes representaron aproximadamente 164 kg N ha⁻¹ comunes a todos los tratamientos. En consecuencia, M0 debe interpretarse como un testigo sin N experimental adicional y no como un tratamiento sin fertilización nitrogenada.

También cambiaría globalmente:

* “tratamientos fertilizados” → **“M1–M5”** o **“tratamientos con N experimental adicional”**;
* “testigo sin nitrógeno” → **“testigo sin N experimental adicional”**;
* “dosis total de 200 kg N ha⁻¹” → **“dosis experimental adicional de 200 kg N ha⁻¹”**.

Esto también afecta la definición de eficiencia agronómica. La sección actual llama a M0 “testigo sin nitrógeno” y a los 200 kg “dosis total”, cuando son la dosis experimental adicional.

En la Tabla 1, dejaría:

* M0: “Sin aplicación experimental”;
* columna: “N experimental adicional total”.

## 2. Hay que aclarar la cronología entre pastoreo, muestreo y primeras aplicaciones

La tesis dice simultáneamente:

* M1: primera aplicación el 12 de junio;
* M2: primera aplicación el 26 de junio;
* suspensión del pastoreo: 1.º de julio;
* evaluación inicial: 12 de junio.

Tal como está escrito, el lector concluye que:

1. M1 y M2 recibieron N mientras el semillero aún estaba bajo pastoreo;
2. la evaluación inicial de M1 pudo ocurrir antes o después de su primera aplicación.

No hay que agregar análisis. Solo hay que averiguar cuál de estas historias es verdadera y escribirla.

### Si las parcelas experimentales ya estaban excluidas

> Aunque el cierre general del semillero ocurrió el 1.º de julio, las parcelas experimentales habían sido excluidas del pastoreo desde [fecha], antes de iniciar las aplicaciones de M1 y M2.

### Si efectivamente hubo pastoreo posterior a las aplicaciones

Debe decirse explícitamente:

> Las primeras aplicaciones de M1 y M2 se realizaron antes del cierre del pastoreo. Por tanto, estos calendarios también difirieron de los restantes en su exposición al manejo de defoliación posterior a la aplicación.

Eso no invalida el ensayo, pero impide interpretar la diferencia como una manipulación pura de fecha independiente del pastoreo.

También agregaría una sola precisión:

> La evaluación inicial del 12 de junio se realizó antes de la primera aplicación de M1.

Solo si efectivamente ocurrió así.

## 3. Hay una oración incompleta y una numeración rota en Métodos

La sección 4.8.2 termina literalmente en:

> Debido a que las curvas no fueron desarrolladas específicamente para el cultivar

y salta directamente a 4.8.3. Es un error visible y bastante feo en una entrega formal.

La versión completa ya estaba en el documento anterior del ZIP. Restauraría:

> Los valores del Índice de Nutrición Nitrogenada se interpretaron principalmente de manera comparativa entre tratamientos y fechas de muestreo. Debido a que las curvas no fueron desarrolladas específicamente para el cultivar Rizar destinado a producción de semilla durante etapas reproductivas avanzadas, sus valores no se consideraron umbrales absolutos de suficiencia o deficiencia nitrogenada.

La numeración también pasa de:

* 4.9.2
* a 4.9.4
* 4.9.5
* 4.9.6

porque se eliminó la antigua sección 4.9.3, pero no se renumeró lo siguiente.

Debe quedar:

* 4.9.3 Observación faltante
* 4.9.4 Análisis de correlación
* 4.9.5 Análisis complementario conjunto

Además, en el DOCX:

* `4.6 Manejo hídrico` tiene estilo de encabezado de tercer nivel, aunque es una sección 4.x;
* `4.8.3` y `4.8.4` están formateadas como párrafos normales en negrita, no como encabezados.

No altera los resultados, pero sí la jerarquía del documento y cualquier futura tabla de contenidos.

## 4. Los ANOVA por fecha no permiten afirmar “trayectorias”, “convergencia” o que las diferencias “desaparecieron”

Este sigue siendo el problema estadístico principal de la narrativa actual.

Métodos dice explícitamente que septiembre, octubre y noviembre se analizaron de manera independiente.

Eso permite responder:

* si había diferencias el 16 de septiembre;
* si había diferencias el 20 de octubre;
* si había diferencias el 12 de noviembre.

No permite probar directamente:

* que una diferencia disminuyó;
* que desapareció;
* que dos tratamientos convergieron;
* que el calendario modificó la trayectoria;
* que el efecto cambió entre fechas.

El motivo es sencillo: comparar un resultado significativo en septiembre con uno no significativo en octubre **no es una prueba de que ambos efectos sean diferentes**.

Por ejemplo:

$$
p_{\mathrm{sep}}<0{,}05
\quad\text{y}\quad
p_{\mathrm{oct}}>0{,}05
$$

no implica:

$$
\Delta_{\mathrm{sep}}\neq\Delta_{\mathrm{oct}}.
$$

La diferencia puede haber disminuido, pero también puede haberse mantenido con mayor variabilidad o menor precisión.

La tesis todavía contiene las siguientes inferencias no justificadas:

* “las acumulaciones tendieron a converger”;
* “las diferencias […] habían desaparecido hacia octubre”;
* “el efecto […] fue evidente en septiembre, pero no se mantuvo”;
* “el momento modificó principalmente la trayectoria temporal”;
* “lo que indica una convergencia”;
* “las aplicaciones tempranas adelantaron…”;
* “las intermedias y tardías prolongaron…”.

Y reaparece en evaluación de hipótesis y conclusiones.  

### Sustituciones seguras

| Evitar                                                  | Usar                                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------------------- |
| “las diferencias desaparecieron”                        | “no se detectaron diferencias en octubre”                                       |
| “las acumulaciones convergieron”                        | “la separación numérica fue menor y el ANOVA de octubre no detectó diferencias” |
| “el efecto no se mantuvo”                               | “no se detectaron diferencias en las evaluaciones posteriores”                  |
| “modificó la trayectoria”                               | “produjo diferencias entre calendarios en fechas específicas”                   |
| “las aplicaciones tempranas adelantaron la acumulación” | “M1 y M2 presentaron mayores valores en la evaluación de septiembre”            |
| “las aplicaciones tardías mantuvieron…”                 | “M4 y M5 presentaron mayores medias en algunas evaluaciones posteriores”        |

### Párrafo correctivo para la discusión

> Los análisis realizados por fecha mostraron diferencias entre calendarios en evaluaciones específicas. En septiembre, M1 y M2 presentaron mayores valores de biomasa y contenido de N, mientras que en algunas evaluaciones posteriores M4 y M5 presentaron mayores concentraciones de N, especialmente en el sector regado. Dado que las fechas se analizaron de manera independiente, estos resultados describen cambios en el orden numérico de los tratamientos, pero no constituyen una prueba directa de una interacción calendario × fecha ni de convergencia entre tratamientos.

Eso conserva casi toda la historia agronómica sin afirmar algo que el análisis no probó.

## 5. Hay que retirar por completo la afirmación de que la relación panojas–semillas “atenuó” el rendimiento

La tesis ya reconoce correctamente que semillas por panoja se calculó como:

$$
\widehat S
==========

\frac{1000,Y}
{W_{1000}P},
$$

donde:

* (Y) es rendimiento limpio;
* (W_{1000}) es peso de mil semillas;
* (P) es número de panojas.

También reconoce que esta variable comparte matemáticamente el rendimiento y no constituye una medición independiente.  

Sin embargo, el resumen todavía afirma:

> Se observó una relación inversa […] que pudo atenuar las diferencias de rendimiento.

La discusión dice:

> esta relación pudo reducir las diferencias de rendimiento final;

y propone menor competencia y disponibilidad tardía de N como explicación.

La conclusión repite:

> pudo atenuar las diferencias de rendimiento.

Eso no queda salvado por agregar después “no demuestra compensación completa”. El problema es anterior: **ni siquiera hay evidencia independiente de compensación parcial**.

Como (P) está en el denominador, una relación inversa entre panojas y semillas estimadas por panoja aparece mecánicamente. El nulo de reconstrucción incluido en los cálculos del ZIP muestra que la correlación observada cae aproximadamente en el percentil 49 de lo esperable por la propia fórmula. Es decir, no es inusual en absoluto bajo una reconstrucción sin mecanismo biológico de compensación.

### Reemplazo exacto

> Los calendarios mostraron patrones contrastantes en la densidad de panojas y en el número estimado de semillas por panoja. Sin embargo, como esta última variable se reconstruyó algebraicamente a partir del rendimiento limpio, el peso de mil semillas y el número de panojas, la relación inversa observada no constituye evidencia independiente de compensación ni permite afirmar que atenuó las diferencias de rendimiento.

Eliminaría también:

> Una menor competencia entre inflorescencias y la disponibilidad más tardía de nitrógeno constituyen explicaciones agronómicamente plausibles.

Puede conservarse como hipótesis para estudios futuros, pero no como interpretación sostenida por estos datos.

## 6. Las letras de Tukey contradicen el método declarado

Métodos establece que Tukey se aplica únicamente cuando el ANOVA global es significativo.

Sin embargo:

* Tabla 12, Secano M1–M5: (p=0{,}0945), pero todos tienen “a”;
* Tabla 13, Secano M1–M5: (p=0{,}1496), pero todos tienen “a”;
* Tabla 14, peso de mil semillas: ANOVA no significativo en ambos sectores, pero todos tienen “a”;
* Tabla 16, índice de cosecha: ANOVA no significativo, pero todos tienen “a”;
* Tabla 17, merma: ANOVA no significativo, pero todos tienen “a”.  

Aunque “todos a” comunica que no se encontraron pares diferentes, **no es el procedimiento que dice haber utilizado la tesis**.

Corrección mínima:

* reemplazar esas letras por `—`;
* añadir al pie:

> El guion indica que no se realizaron comparaciones de Tukey debido a que el ANOVA global no fue significativo.

Deben conservarse las letras donde el omnibus sí fue significativo, por ejemplo:

* panojas bajo riego M1–M5;
* semillas estimadas bajo riego M1–M5;
* comparaciones M0–M5 que sí resultaron significativas.

## 7. En peso de mil semillas, índice de cosecha y merma se reportan los p-valores de M0–M5 como si fueran la comparación principal

Métodos declara que M1–M5 es el análisis principal y M0–M5 el complementario.

Pero las secciones 5.5.3, 5.7 y 5.8 presentan únicamente los valores de M0–M5 sin identificarlo claramente.  

Al reproducir los ANOVA del ZIP:

| Variable             | Sector | p mostrado actualmente | Corresponde a | p principal M1–M5 |
| -------------------- | ------ | ---------------------: | ------------- | ----------------: |
| Peso de mil semillas | Secano |                 0,5728 | M0–M5         |            0,5159 |
| Peso de mil semillas | Riego  |                 0,8385 | M0–M5         |            0,8238 |
| Índice de cosecha    | Secano |                 0,0654 | M0–M5         |            0,1585 |
| Índice de cosecha    | Riego  |                 0,0599 | M0–M5         |            0,4248 |
| Merma                | Secano |                 0,3085 | M0–M5         |            0,2823 |
| Merma                | Riego  |                 0,0748 | M0–M5         |            0,1014 |

No cambia ninguna conclusión: todos continúan siendo no significativos. Pero el lector debe saber qué pregunta responde cada número.

### Corrección mínima

Por ejemplo, para índice de cosecha:

> Entre M1–M5 no se detectaron diferencias significativas en secano ((p=0{,}1585)) ni en el sector regado ((p=0{,}4248)). En el análisis complementario M0–M5, los valores fueron (p=0{,}0654) y (p=0{,}0599), respectivamente.

En las tablas, cambiar:

> Valor de p del tratamiento

por:

> Valor de p, M0–M5

Esto también debería hacerse en las tablas de rendimiento y productividad del agua, donde los p-valores mostrados corresponden a M0–M5, aunque el texto sí informa correctamente el análisis M1–M5.

## 8. Quedó una referencia a análisis de sensibilidad que ya no existe en Métodos

En biomasa se afirma:

> Los análisis de sensibilidad con las observaciones señaladas por el rango intercuartílico no modificaron esta conclusión general.

Pero la sección que definía:

* el criterio del rango intercuartílico;
* la inspección de residuos;
* las sensibilidades con y sin observaciones;

fue eliminada en esta versión. De ahí también proviene el salto de 4.9.2 a 4.9.4.

Si no van a restaurar la metodología y detallar qué observaciones se evaluaron, **hay que eliminar esa oración**.

Además, en el libro existen dos registros finales de materia seca que deben verificarse contra la fuente original:

| Muestra | Sector/bloque/tratamiento | %MS registrado | %MS según peso seco / peso fresco |
| ------: | ------------------------- | -------------: | --------------------------------: |
|     150 | Riego–R4–M4               |         18,2 % |                           28,10 % |
|     152 | Riego–R4–M2               |         25,0 % |                           15,14 % |

No puedo determinar cuál columna es correcta sin la hoja primaria o el cuaderno de laboratorio. No deben “corregirse” automáticamente mediante el cociente, pero sí verificarse.

Esto no afecta el rendimiento limpio, pero sí puede modificar:

* biomasa final;
* contenido de N;
* INN;
* índice de cosecha.

De hecho, algunas pruebas secundarias cercanas a 0,05 cambian de lado dependiendo de cuál valor se use. Por eso, no conviene dejar una afirmación vaga de robustez sin documentar qué se hizo.

En cambio, la decisión actual para la concentración de N faltante está bien: se utilizan las observaciones efectivamente medidas y no se imputa en el análisis principal.  No reintroduciría el antiguo valor imputado del documento previo.

## 9. El texto sobre la dosis al 16 de septiembre es incompleto

En la sección de INN se dice:

> M1 y M2 ya habían recibido las dos aplicaciones previstas, mientras que M5 todavía no había recibido la segunda.

Según la propia Tabla 1:

* M1 completó el 31 de julio;
* M2 completó el 31 de julio;
* M3 completó el 21 de agosto;
* M4 completó el 4 de septiembre;
* M5 completó el 20 de septiembre.

Por tanto, el 16 de septiembre:

* **M1–M4 habían recibido 200 kg N ha⁻¹ experimentales**;
* **M5 había recibido 100 kg N ha⁻¹ experimentales**.

Corrección:

> En esta fecha, M1–M4 ya habían completado las dos aplicaciones experimentales, mientras que M5 había recibido únicamente la primera. Por tanto, la comparación de M5 con los restantes calendarios reflejó también una diferencia transitoria en la dosis acumulada hasta el muestreo.

---

# P1 — Correcciones importantes de interpretación

## 10. Las correlaciones crudas están fuertemente dominadas por M0

La tesis presenta correlaciones con las 24 parcelas de cada sector, es decir, incluyendo M0, y luego las discute como relaciones entre rendimiento y características productivas o nutricionales.

Al recalcular las mismas correlaciones solo entre M1–M5:

| Variable                      | Secano, M0–M5 | Secano, M1–M5 | Riego, M0–M5 | Riego, M1–M5 |
| ----------------------------- | ------------: | ------------: | -----------: | -----------: |
| Concentración de N            |         0,565 |         0,079 |        0,531 |        0,069 |
| Contenido de N en biomasa     |         0,791 |         0,448 |        0,583 |        0,211 |
| Semillas estimadas por panoja |         0,758 |         0,196 |        0,760 |        0,390 |
| Densidad de panojas           |         0,606 |         0,457 |        0,440 |        0,418 |

La asociación entre concentración de N y rendimiento prácticamente desaparece dentro de los calendarios con igual dosis. En gran medida, la correlación original captura la separación entre:

* M0, con menor N experimental y menor rendimiento;
* M1–M5, con mayor N experimental y mayor rendimiento.

El método ya las denomina exploratorias y reconoce varias dependencias matemáticas. Eso está bien.  Pero la discusión todavía dice:

> Esto confirma su importancia como componente.

y presenta las correlaciones nutricionales como si aportaran evidencia adicional.

### Reemplazo sugerido

> Las correlaciones se calcularon incluyendo M0 y reflejaron en parte la separación general entre el testigo y los tratamientos con N experimental adicional. Por ello, no permiten identificar qué variables explicaron las diferencias de rendimiento entre M1–M5 ni establecer relaciones causales independientes.

Cambiaría:

> Esto confirma su importancia como componente

por:

> Esta asociación es consistente con su condición de componente del rendimiento, pero no aísla un efecto causal ni independiente del tratamiento nitrogenado.

En la Tabla 20 también cambiaría:

> Semillas por panoja

por:

> Semillas estimadas por panoja.

## 11. “Nitrógeno acumulado” está definido como un stock instantáneo, no como absorción acumulativa durante el ciclo

La fórmula utilizada es:

$$
Q_t
===

\text{biomasa aérea}_t
\times
\text{concentración de N}_t.
$$

La propia tesis define el resultado como “cantidad de nitrógeno presente en la biomasa aérea”.

Eso es un **contenido de N en biomasa aérea en la fecha de muestreo**. No mide necesariamente todo el N absorbido desde el comienzo del ciclo, porque entre fechas puede haber:

* senescencia;
* pérdida de tejido;
* retranslocación;
* traslado hacia órganos no incluidos.

No considero obligatorio cambiar las veinte apariciones si “N acumulado” es el término agronómico que exige el director. Pero sí evitaría verbos y explicaciones que lo traten como absorción acumulativa irrevocable.

La solución más limpia sería sustituir:

> nitrógeno acumulado en la biomasa aérea

por:

> contenido de N en la biomasa aérea.

Eso también hace más comprensible que el valor pueda disminuir entre octubre y noviembre.

## 12. Los resultados secundarios tienen un problema de multiplicidad que exige lenguaje moderado

Se realizan muchos ANOVA:

* cuatro variables temporales;
* tres fechas;
* dos sectores;
* dos conjuntos de tratamientos;
* varias variables finales;
* numerosas correlaciones.

Tukey controla las comparaciones por pares dentro de un ANOVA, pero no controla el conjunto de pruebas entre variables y fechas.

No es necesario agregar una corrección FDR a estas alturas. La corrección textual mínima es no tratar valores aislados como (p=0{,}0291), (p=0{,}0281) o resultados próximos a 0,05 como pruebas contundentes de mecanismos.

Usaría:

* “se detectó evidencia en esa evaluación”;
* “resultado secundario”;
* “patrón compatible con…”;

y evitaría:

* “confirmó”;
* “demostró”;
* “el momento modificó…” como conclusión global basada en varias pruebas separadas.

## 13. El análisis conjunto está descrito de manera más general de lo que aparece en Resultados

Métodos describe un análisis conjunto de M1–M5 para examinar el patrón entre sectores en términos generales.

Sin embargo, la única tabla explícita del modelo conjunto es la del INN.

Hay dos correcciones posibles, sin agregar resultados:

1. restringir 4.9.5 a:

   > Para el INN se ajustó complementariamente…

2. conservar la descripción general, pero no afirmar después que “no hubo una interacción consistente” para todas las variables si esos resultados no se muestran.

Los cálculos del ZIP efectivamente indican que las interacciones calendario × sector no fueron claramente significativas para las variables centrales, por lo que la conclusión no parece numéricamente falsa. El problema es de trazabilidad entre Métodos, Resultados y Discusión.

## 14. Algunas explicaciones mecanísticas deben quedar como hipótesis, no como resultados

Por ejemplo:

> La menor densidad de M5 […] sugiere que una aplicación tardía no permitió recuperar estructuras reproductivas definidas en etapas anteriores.

No se midieron:

* iniciación reproductiva;
* supervivencia de macollos reproductivos;
* aborto de estructuras;
* recuperación de estructuras.

Una forma segura sería:

> La menor densidad de panojas observada en M5 es compatible con la hipótesis de que parte de las estructuras reproductivas se definió antes de sus aplicaciones; sin embargo, estos procesos no fueron medidos directamente.

---

# P2 — Errores editoriales y de consistencia

Estos no cambian las conclusiones, pero son correcciones fáciles.

## Texto y tablas

* “**El Tabla 3**” → “**La Tabla 3**”.
* “se presentan **en el Tabla 5**” → “se presentan **en la Tabla 5**”.
* En Tabla 5: `riegado` → `riego` o `sector regado`.
* Homogeneizar “secano”, “riego”, “sector regado” y “riego suplementario”.
* En tablas con p-valores, identificar siempre `M0–M5` o `M1–M5`.
* Usar `p < 0,0001`, nunca `p = 0,0000`.
* Las ecuaciones del INN deberían usar consistentemente:

$$
W^{-0,42}
\qquad\text{y}\qquad
W^{-0,32}
$$

en lugar de mezclar `W^(−0,42)` con superíndices que en alguna tabla aparecen como `W⁻⁰·⁴²`.

## Bibliografía

Hay una cita en el texto a **Lemaire y Gastal (1997)** para la curva histórica, pero esa referencia no aparece en la bibliografía.

Debe incorporarse la referencia exacta de la fuente realmente utilizada.

En sentido contrario, después de la simplificación quedaron referencias bibliográficas aparentemente no citadas:

* FAO, 2021;
* Gibson y Newman, 2001;
* Hurlbert, 1984.

Las opciones correctas son:

* restaurar sus citas donde corresponden; o
* retirarlas de la bibliografía.

Hurlbert encajaría naturalmente en la justificación de por qué los dos sectores no son réplicas independientes del régimen hídrico.

## Software estadístico

La versión anterior indicaba el software utilizado; la actual ya no lo hace. No es un error numérico, pero debería existir una frase que identifique el programa real con el cual se obtuvieron los resultados finales. No pondría InfoStat, Python o cualquier otro por inercia: debe decir el que efectivamente produjo las tablas incluidas.

---

# Redacciones listas para reemplazar

## Resumen: sustituir la parte interpretativa

Desde “Las aplicaciones tempranas…” hasta antes de la comparación con M0, usaría:

> En las evaluaciones realizadas por fecha, M1 y M2 presentaron mayores valores de biomasa y contenido de N en septiembre, mientras que M4 y M5 mostraron mayores concentraciones de N en algunas evaluaciones posteriores, especialmente en el sector regado. Las aplicaciones tempranas e intermedias tendieron a presentar una mayor densidad de panojas. El número estimado de semillas por panoja mostró un patrón contrastante, pero, al haberse reconstruido algebraicamente a partir del rendimiento, el peso de mil semillas y el número de panojas, no se interpretó como evidencia independiente de compensación.

Y la conclusión del resumen:

> Se concluye que los calendarios de aplicación produjeron diferencias en variables intermedias en fechas específicas, pero no permitieron identificar un calendario consistentemente superior para el rendimiento final.

Eso sustituye las dos afirmaciones problemáticas del resumen actual.

## Resultados de N en biomasa

Sustituir:

> las diferencias entre momentos observadas en septiembre habían desaparecido hacia octubre

por:

> Al considerar únicamente M1–M5, no se detectaron diferencias significativas en octubre. Este resultado no constituye por sí mismo una prueba de que las diferencias observadas en septiembre hayan desaparecido, dado que ambas fechas se analizaron por separado.

Y sustituir la síntesis:

> El efecto específico del momento fue evidente en septiembre, pero no se mantuvo…

por:

> Entre M1–M5 se detectaron diferencias en septiembre, pero no en los análisis correspondientes a octubre y noviembre.

## Discusión de componentes

Reemplazar el bloque sobre compensación por:

> Los calendarios mostraron patrones contrastantes en la densidad de panojas y en el número estimado de semillas por panoja. Los tratamientos tempranos tendieron a presentar una mayor densidad de panojas, mientras que algunos calendarios intermedios y tardíos presentaron mayores valores de semillas estimadas por panoja. Sin embargo, esta última variable se reconstruyó algebraicamente a partir del rendimiento limpio, el peso de mil semillas y el número de panojas. Por tanto, la relación inversa observada no constituye evidencia independiente de compensación ni permite afirmar que redujo las diferencias de rendimiento.

## Conclusiones: versión mínima y defendible

> Entre M1–M5, que recibieron la misma dosis experimental adicional de 200 kg N ha⁻¹, no se detectaron diferencias significativas en el rendimiento de semilla limpia. Dentro de los calendarios estudiados no fue posible identificar un momento de aplicación consistentemente superior.
>
> En los análisis realizados por fecha, las aplicaciones tempranas presentaron mayores valores de biomasa y contenido de N en septiembre, mientras que algunos calendarios intermedios y tardíos mostraron mayores concentraciones de N en evaluaciones posteriores, especialmente en el sector regado. Dado que las fechas se analizaron por separado, estos resultados se interpretan como diferencias específicas de cada evaluación y no como una prueba formal de trayectorias diferentes.
>
> Las aplicaciones tempranas e intermedias tendieron a presentar una mayor densidad de panojas. El número estimado de semillas por panoja mostró un patrón contrastante, pero su dependencia algebraica del rendimiento impide interpretarlo como evidencia independiente de compensación. El peso de mil semillas no fue afectado significativamente.
>
> De manera complementaria, M1–M5 produjeron aproximadamente el doble de semilla limpia que M0. M0 representó un testigo sin N experimental adicional y no una condición de ausencia total de fertilización nitrogenada.
>
> Las diferencias medias entre los sectores se interpretaron descriptivamente porque cada condición hídrica estuvo representada por un único sector. El experimento permite caracterizar la respuesta de los calendarios dentro de cada sector, pero no estimar aisladamente el efecto causal del riego.
>
> En conjunto, los calendarios produjeron diferencias en variables intermedias en fechas específicas, pero no permitieron recomendar una fecha única de aplicación ni determinar una dosis óptima.

---

# Lo que ya está bien y no conviene volver a tocar

La versión actual hizo varias correcciones importantes:

1. **La limitación del riego está bien formulada.** Se reconoce que solo hubo un sector por condición y que las diferencias medias no son una estimación causal exclusiva del riego.  

2. **La comparación principal M1–M5 está claramente separada de M0–M5.**

3. **El dato faltante se mantiene ausente**, evitando la antigua imputación errónea.

4. **La productividad aparente del agua está correctamente limitada**: no se confunde el agua aportada con la consumida ni se interpreta su menor valor en el sector regado como menor eficiencia fisiológica.

5. **La eficiencia agronómica y la productividad del agua se reconocen como transformaciones del rendimiento**, no como evidencia estadística independiente.  

6. **La limitación del tamaño muestral está bien expresada**: no significación no implica igualdad exacta.

7. **El alcance externo está bien limitado** a un sitio, ciclo, cultivar y dosis.

No insistiría ahora con el modelo probabilístico ni con el longitudinal. Los usaría únicamente como auditoría interna:

* el probabilístico respalda “no se identificó un ganador”, pero también impide decir “los calendarios fueron equivalentes”;
* el nulo de reconstrucción obliga a retirar la afirmación de compensación;
* el longitudinal confirma que la palabra “trayectoria” requeriría otra prueba, por lo que, sin incluir ese modelo, hay que usar redacción específica por fecha.

# Orden mínimo de corrección

Si realmente van a hacer solo una pasada rápida, este sería mi orden:

1. corregir M0 y documentar las fertilizaciones comunes de julio y agosto;
2. aclarar pastoreo, muestreo inicial y aplicaciones de junio;
3. completar la oración cortada y renumerar 4.9;
4. eliminar “convergencia”, “desaparecieron”, “no se mantuvo” y “modificó la trayectoria”;
5. eliminar “pudo atenuar/reducir las diferencias de rendimiento”;
6. retirar Tukey cuando el omnibus no fue significativo;
7. identificar correctamente qué p-valores son M0–M5 y cuáles M1–M5;
8. eliminar la oración del rango intercuartílico;
9. verificar las muestras 150 y 152;
10. hacer la pasada editorial y bibliográfica.

Con esas correcciones, la tesis puede seguir siendo sencilla y convencional, pero deja de contener las afirmaciones que un tribunal atento podría desmontar con una sola pregunta.
