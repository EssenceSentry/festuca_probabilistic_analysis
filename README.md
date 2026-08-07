# Análisis de festuca

Este repositorio contiene dos informes ejecutables. El código estadístico vive
en el paquete `src/festuca_analysis`; los notebooks solo organizan el informe y
llaman funciones de ese paquete.

## Uso recomendado

1. En una terminal, dentro de esta carpeta, ejecutar:

   ```bash
   uv sync --frozen
   uv run --frozen jupyter lab
   ```

2. Abrir uno de estos notebooks:

   - `festuca_estudio_longitudinal.ipynb`
   - `festuca_anexo_probabilistico.ipynb`

3. Elegir **Run All**. No es necesario modificar el código del notebook.

Las tablas y figuras se regeneran en carpetas ignoradas por Git:

- `festuca_thesis_analysis_outputs/` y `festuca_thesis_figures/` para el estudio
  longitudinal;
- `results/` para el anexo probabilístico.

## Ejecución sin Jupyter

Los mismos análisis pueden ejecutarse desde una terminal:

```bash
uv run --frozen festuca-longitudinal
uv run --frozen festuca-annex
```

La primera ejecución longitudinal incluye un bootstrap paramétrico reproducible
de 199 réplicas para las interacciones de biomasa y concentración de N. Para
validar por separado el muestreador probabilístico personalizado contra PyMC y
con datos simulados:

```bash
uv run --frozen festuca-validate-sampler
```

La auditoría se escribe en `results/validation/`.

Para comprobar que los CSV versionados siguen correspondiendo al Excel fuente:

```bash
uv run --frozen festuca-export-workbook --check
```

## Alcance de la reproducción probabilística

El modelo A corregido de rendimiento se vuelve a calcular. El modelo A
longitudinal, el modelo B y el nulo de reconstrucción utilizan los seis resúmenes
aceptados de la corrida histórica conservados en
`reference_outputs/legacy_probabilistic_run/`. Esto permite regenerar todas las
tablas y figuras del anexo sin versionar 49 MB de cadenas, pero no vuelve a
muestrear esos tres componentes históricos.

## Jerarquía inferencial

- **Primaria:** rendimiento limpio entre M1–M5.
- **Secundaria:** trayectorias de biomasa aérea y concentración de N, con
  bootstrap paramétrico y control FDR por familia.
- **Apoyo:** N presente en biomasa, INN y componentes derivados.
- **Exploratoria/sensibilidad:** correlaciones, políticas de materia seca, EAN y
  productividad aparente del agua. Las dos últimas se resumen sin volver a
  probar transformaciones deterministas del rendimiento.
