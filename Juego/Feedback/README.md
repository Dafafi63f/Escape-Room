# Feedback — avisos del jugador al creador

Copias locales de los mensajes enviados al creador del juego.

| Acceso | Dónde |
|--------|-------|
| **Consola** | Menú principal opción 3, o tecla **F** durante el juego |
| **Gráfico** | Icono 📣 en la barra fija (abre pantalla informativa; envío completo sigue en consola por ahora) |

- Generados por [`Consola/envio_feedback.py`](../Consola/envio_feedback.py).
- Nombre: `feedback_<categoria>_<jugador>_<fecha>_<id>.txt`.
- Si hay SMTP en `Data/JSON/creador_privado.json` (`feedback_smtp`), también se envía correo al creador.

**No se versionan** en git (`Juego/Feedback/*` en `.gitignore`; solo `.gitkeep` queda en el repositorio).

Para borrar estas copias y otros `.txt` temporales del juego (solo esta carpeta y `Juego/Informes/`):

```bash
python borrar_temporales.py --solo-txt
```
