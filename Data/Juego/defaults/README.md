# Esquemas base de `Data/Juego/`

Plantillas vacías de los JSON que el juego **crea al arrancar** en la carpeta padre (`Data/Juego/`).
Esos ficheros de runtime no se versionan (datos locales del jugador).

| Plantilla (aquí) | Runtime (generado al jugar) | Uso |
|------------------|----------------------------|-----|
| `preferencias_grafico.json` | `../preferencias_grafico.json` | Nombre, tooltips, emojis, informes `.txt` |
| `estadisticas_jugador.json` | `../estadisticas_jugador.json` | Récords y estadísticas agregadas |

**Contenido del juego** (sí versionado, en `Data/Juego/`):

- `presets.json` — catálogo de modos
- `preguntas_resistencia.json` — banco extra del modo resistencia

Al modificar el esquema, actualiza el código en `Juego/Comun/` y estas plantillas.
