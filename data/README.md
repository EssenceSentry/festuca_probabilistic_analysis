# Datos en CSV

Este directorio contiene una representación textual del libro
`sources/Datos_Ema_Serrana_INN.xlsx`, pensada para revisión y comparación en
Git.

- Cada pestaña del libro se exporta completa a un archivo CSV UTF-8 con finales
  de línea LF.
- Las fechas se representan en formato ISO 8601.
- Los CSV de las pestañas contienen los valores guardados en el libro.
- `formulas.csv` conserva por separado la celda, la fórmula original y el valor
  guardado de todas las fórmulas.
- `manifest.csv` registra dimensiones, conteos de fórmulas y el SHA-256 del
  libro utilizado para generar la exportación.

El libro XLSX continúa siendo la fuente utilizada por los notebooks. Estos CSV
no modifican ni recalculan el libro.

Para regenerar los archivos:

```bash
uv run python code/export_workbook_csv.py
```

Para comprobar que los CSV existentes coinciden con el libro:

```bash
uv run python code/export_workbook_csv.py --check
```
