# Corrida probabilística de referencia

Estos seis CSV son el mínimo necesario para reconstruir el anexo final sin
versionar aproximadamente 49 MB de cadenas NetCDF. Provienen de la corrida
probabilística aceptada que acompañaba al bundle
`festuca_anexo_probabilistico_tesis_v2`.

El comando `uv run festuca-annex` recalcula el modelo A corregido de rendimiento
y usa estos resúmenes congelados únicamente para el modelo A longitudinal, el
modelo B y el nulo de reconstrucción. Por lo tanto, permiten reproducir todas las
tablas y figuras del anexo, pero no volver a muestrear esos tres componentes
históricos.

| Archivo | SHA-256 |
|---|---|
| `model_a_longitudinal_contrasts.csv` | `8f716a1d2861ae099b93e034e5f91ab85c98339d944edb6df8a932e84c891ed7` |
| `model_a_longitudinal_trajectories.csv` | `53cf762737c244fec52c708e2d07919c23c90e1de488b3dedd6cc4098e6559b2` |
| `model_b_final_nni_probabilities.csv` | `818341b7098095227336c2277021918fed283f36a0a8e96627bbad55540c6b34` |
| `model_b_state_trajectories.csv` | `bfa6568b43d0d3a93c73368e488ea69882ad0bb76dd1d8ae588be78aa150ab04` |
| `original_run_diagnostics.csv` | `b1d9bdca139be3fc528a9df58f0a787540aacb2bd9937214dcbb94b01e42f0e7` |
| `reconstruction_null_percentiles.csv` | `d125851cb2bfe697fb1e8158af59face67942c70a115560d715ccdc9b6772830` |
