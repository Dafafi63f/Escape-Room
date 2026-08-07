# Plantilla CSV para jugar con tus preguntas

Por ahora, lo único que necesitas para usar **tu banco** es un CSV con columnas mínimas.

## `Preguntas.csv`

| Columna | Obligatoria |
|---------|-------------|
| `Pregunta` | Sí |
| `A`, `B`, `C`, `D` | Sí |
| `Correcta` | Sí (`A`, `B`, `C` o `D`) |
| `Id` | Opcional |

Separador **`;`**. Sin columnas curriculares (`Materia`, `Dificultad`, `Tipo`, …).

Copia [`Preguntas.csv`](Preguntas.csv) como punto de partida (3 preguntas de ejemplo) y sustituye filas por las tuyas.

## Cómo jugar

```bash
python Juego/juego_grafico.py --csv ruta/Preguntas.csv
```

Modos disponibles: libre simplificado, historia (repaso / simulacro / examen fijo) y resistencia con eventos.

> El CSV mínimo completo del autor (480 preguntas desde `Data/Banco/`) está en `Data/Privado/Preguntas_minimal.csv`.
