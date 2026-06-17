# Informes — partidas en disco

Aquí se guardan los informes de partida (ficheros `.txt` con ID de sesión, respuestas y resumen).

- **Consola:** [`Consola/informe_examen.py`](../Consola/informe_examen.py) al terminar una partida con corrección al final.
- **Gráfico:** [`Grafico/informe_partida.py`](../Grafico/informe_partida.py) (botón «Guardar informe» en el resumen).
- Con el script Python: ruta por defecto `Juego/Informes/`.
- Con el **`.exe`**: carpeta `Informes/` en el mismo directorio que `juego_consola.exe` (se crea sola).

**No se versionan** en git (`Juego/Informes/*` en `.gitignore`; solo `.gitkeep` queda en el repositorio).

Para borrar informes y otros `.txt` temporales del juego (solo esta carpeta y `Juego/Feedback/`):

```bash
python borrar_temporales.py --solo-txt
```

Si borras esta carpeta, el juego la vuelve a crear al publicar un informe.
