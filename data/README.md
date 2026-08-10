# Datos canónicos del ensayo

Los CSV de este directorio son la única fuente editable y analítica. Los archivos `*_recorded.csv` contienen mediciones o metadatos; los archivos `*_calculated.csv` son materializaciones comprobables de las reglas declaradas en `formulas.json`.

`manifest.json` define tipos, unidades, claves, relaciones y rótulos descriptivos en español para una futura reconstrucción del libro. El XLSX histórico se conserva únicamente como evidencia de la migración.

Para validar el conjunto sin ejecutar los análisis completos:

```bash
uv run festuca-validate-data
```

No vuelva a ejecutar la migración sobre datos revisados manualmente salvo que realmente quiera reemplazarlos y use `--force`.
