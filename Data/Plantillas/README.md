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

O descomprime `MATCAD_juego_minimal.zip`, reemplaza `Preguntas.csv` y ejecuta `Jugar.bat`.

Modos disponibles: libre simplificado, historia (repaso / simulacro / examen fijo) y resistencia con eventos.

> Más adelante se añadirán aquí otras plantillas (paquete intermedio, metadatos, etc.). El juego completo MATCAD del autor viene en `MATCAD_juego_portable.zip`.
