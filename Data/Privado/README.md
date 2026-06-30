# Data/Privado — local del autor

Carpeta **única** para ficheros privados, fuentes de mantenimiento y datos locales del autor que **no** van en el zip portable (salvo excepciones versionadas; ver `.gitignore`).

| Fichero | Para qué |
|---------|----------|
| `creador_privado.json` | SMTP del feedback, datos personales, secretos GitHub |
| `Preguntas_minimal.csv` | Exportación mínima del banco (480 preguntas; tests y `MATCAD_juego_minimal.zip`) |
| `Historic_qualificacions_MatCAD.xlsx` | Fuente del histórico (el CSV exportado está en `Data/Banco/`) |
| Otros `.xlsx` / notas | Fuentes de mantenimiento del banco |

## Regenerar `Preguntas_minimal.csv`

```bash
python Tests/Fixtures/generar_preguntas_minimal.py
```

Lee `Data/Banco/Preguntas.csv` y escribe solo columnas mínimas (`Id`, `Pregunta`, `A`–`D`, `Correcta`).

## Plantilla para usuarios (3 preguntas de ejemplo)

[`Data/Plantillas/Preguntas.csv`](../Plantillas/Preguntas.csv) — punto de partida si montas tu propio banco mínimo.

## Configuración del creador

```bash
cd Juego
python -m Comun.feedback
```

Los datos del **jugador** (preferencias, estadísticas, informes `.txt`) van en `Data/Juego/`, no aquí.
