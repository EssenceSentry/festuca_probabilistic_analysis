# Análisis de festuca

Este repositorio contiene dos notebooks ejecutables y un paquete Python común:

- `festuca_estudio_longitudinal.ipynb`: análisis descriptivo, DBCA por fecha,
  diagnósticos, sensibilidades y modelos longitudinales clásicos;
- `festuca_anexo_probabilistico.ipynb`: modelos probabilísticos de rendimiento y
  de trayectorias longitudinales;
- `src/festuca_analysis/`: carga, reconstrucción, auditoría, inferencia y
  exportación compartidas por ambos notebooks.

Los notebooks se entregan **sin ejecutar**. Sus celdas Markdown contienen solo
matemática, supuestos y lógica analítica. Las observaciones, auditorías,
resultados y diagnósticos se presentan como `DataFrame`, figuras o artefactos
regenerados durante la ejecución.

## Fuente de verdad

La única fuente editable y analítica es el conjunto normalizado:

```text
data/
```

`manifest.json` declara esquemas, claves, unidades y rótulos descriptivos en
español. `formulas.json` conserva únicamente las reglas correspondientes a
columnas calculadas. Al cargar los datos se valida todo el conjunto, se calcula
un SHA-256 determinista y se construyen DataFrames separados para:

- mediciones registradas;
- materializaciones calculadas;
- valores estimados explícitamente identificados;
- valores derivados nuevamente por el análisis;
- metadatos de diseño y manejo.

Las magnitudes derivables se reconstruyen desde mediciones primitivas y se
comparan con los CSV `*_calculated.csv`. Esas materializaciones sirven para
conciliación, no como autoridad silenciosa. La estimación identificada en
calidad se mantiene separada y se excluye del análisis primario de N.

El libro `sources/Datos_Ema_Serrana_INN.xlsx` se conserva sin modificaciones
como evidencia histórica de la migración. No es una fuente aceptada por el
cargador analítico. Para validar los datos canónicos:

```bash
uv run festuca-validate-data
```

Para generar una representación tabular coherente en Excel desde esas fuentes:

```bash
uv run festuca-rebuild-workbook
```

El comando crea `dist/datos_festuca_canonicos.xlsx`. El libro contiene una
tabla de Excel por hoja, encabezados descriptivos en español y fórmulas vivas
para las variables calculadas declaradas en `formulas.json`. Es un artefacto
derivado y reemplazable: **no debe editarse como fuente de datos**. La autoridad
exclusiva sigue siendo `data/`. Para comprobar que un libro existente coincide
semánticamente con las fuentes o para reemplazarlo de forma explícita:

```bash
uv run festuca-rebuild-workbook --check
uv run festuca-rebuild-workbook --force
```

También se pueden indicar rutas alternativas mediante `--data-dir` y
`--output`. El reconstructor valida todo el conjunto antes de escribir, rechaza
el archivo de bloqueo de Excel y reemplaza la salida de forma atómica.

La migración desde el libro es deliberadamente protegida y no debe ejecutarse
sobre CSV revisados manualmente. Requiere que Excel esté cerrado y se niega a
sobrescribir `data/` salvo que se indique explícitamente `--force`:

```bash
uv run festuca-export-workbook
```

## Instalación y ejecución

El proyecto requiere Python 3.12. Desde la raíz del repositorio:

```bash
uv sync
uv run jupyter lab
```

Luego abra y ejecute, en orden, uno de los notebooks. El anexo probabilístico es
computacionalmente más costoso porque vuelve a muestrear todos los modelos desde
los datos canónicos actuales.

También existen entradas de terminal:

```bash
uv run festuca-longitudinal
uv run festuca-annex
```

`uv.lock` fija el entorno resuelto del proyecto; use `uv sync --frozen` para
reproducirlo sin modificar dependencias.

## Pruebas sin ejecutar los análisis

```bash
uv run python -m unittest discover -s tests -v
```

Las pruebas verifican, entre otras cosas:

- procedencia y hash del conjunto canónico;
- lectura del calendario desde la cronología atómica;
- identidades de reconstrucción;
- separación de mediciones y estimaciones;
- regla dinámica de auditoría de materia seca;
- selección de ajustes MixedLM convergidos;
- valor p correcto para asociaciones ajustadas;
- notebooks sin salidas y sin lecturas directas que evadan el cargador común.

## Jerarquía inferencial

- **Primaria:** rendimiento limpio entre M1–M5 dentro de cada sector.
- **Contraste adicional:** promedio M1–M5 frente a M0, interpretado como efecto
  de N experimental adicional, no como comparación con ausencia total de N.
- **Secundaria:** trayectorias de biomasa y concentración de N.
- **Apoyo:** N acumulado, INN y componentes derivados.
- **Exploratoria o sensibilidad:** correlaciones, políticas de materia seca,
  EAN, productividad aparente del agua y comparación descriptiva entre los dos
  sectores físicos.

No se estima un efecto causal del riego porque la condición hídrica no está
replicada mediante múltiples unidades físicas independientes. Tampoco se trata
el INN como una medición latente independiente: se conserva como transformación
de biomasa, concentración de N y la curva crítica elegida.

## Salidas

Las salidas se regeneran en carpetas ignoradas por Git:

- `festuca_thesis_analysis_outputs/` y `festuca_thesis_figures/`;
- `results/` para el anexo probabilístico.

Las figuras usan una fuente instalada por Matplotlib; el repositorio no incluye
archivos de fuentes.
