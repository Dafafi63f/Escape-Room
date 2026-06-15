# Feedback — avisos del jugador al creador

Copias locales de los mensajes enviados desde el **modo feedback** (menú principal, opción 3) o con la tecla **F** durante el juego.

- Generados por [`Consola/envio_feedback.py`](../Consola/envio_feedback.py).
- Nombre: `feedback_<categoria>_<jugador>_<fecha>_<id>.txt`.
- Si hay SMTP en `Data/creador_privado.json` (`feedback_smtp`), también se envía correo al creador.

**No se versionan** en git (`Juego/Feedback/*` en `.gitignore`; solo `.gitkeep` queda en el repositorio).

Para borrar estas copias y otros `.txt` temporales del juego (solo esta carpeta y `Juego/Informes/`):

```bash
python borrar_temporales.py --solo-txt
```
