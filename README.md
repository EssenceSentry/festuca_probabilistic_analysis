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

La única fuente de valores observados es:

```text
sources/Datos_Ema_Serrana_INN.xlsx
```

El análisis no usa CSV generados, resultados históricos ni valores copiados de
la tesis como entrada. Al cargar el libro se registra su SHA-256 y se construyen
DataFrames separados para:

- mediciones registradas;
- fórmulas calculadas dentro del XLSX;
- valores estimados explícitamente en el XLSX;
- valores derivados nuevamente por el análisis;
- metadatos de diseño y manejo.

Las magnitudes derivables se reconstruyen desde mediciones primitivas siempre
que el libro contiene la información necesaria. Las columnas derivadas del
XLSX se conservan para conciliación, no como autoridad silenciosa. Las
estimaciones identificadas en la hoja de calidad se mantienen en columnas de
auditoría y se excluyen del análisis primario de N.

## Instalación y ejecución

El proyecto requiere Python 3.12. Desde la raíz del repositorio:

```bash
uv sync
uv run jupyter lab
```

Luego abra y ejecute, en orden, uno de los notebooks. El anexo probabilístico es
computacionalmente más costoso porque vuelve a muestrear todos los modelos desde
el XLSX actual.

También existen entradas de terminal:

```bash
uv run festuca-longitudinal
uv run festuca-annex
```

No se incluye un `uv.lock` preexistente porque el conjunto de dependencias fue
corregido. `uv sync` genera uno consistente con el sistema donde se ejecutará el
análisis.

## Pruebas sin ejecutar los análisis

```bash
uv run python -m unittest discover -s tests -v
```

Las pruebas verifican, entre otras cosas:

- procedencia y hash del XLSX;
- lectura del calendario desde la hoja estructurada;
- identidades de reconstrucción;
- separación de mediciones y estimaciones;
- regla dinámica de auditoría de materia seca;
- selección de ajustes MixedLM convergidos;
- valor p correcto para asociaciones ajustadas;
- notebooks sin salidas ni entradas CSV generadas.

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
