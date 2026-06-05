# Consola — paquete del juego

Implementación del cuestionario en terminal. Nombre del paquete: **`Consola`** (carpeta `Juego/Consola/`). Se importa con `Juego/` en el `sys.path` (véase [`juego_cuestionario.py`](../juego_cuestionario.py)).

Antes del refactor vivía como módulos sueltos o paquetes `matcad` / `Motor` / `Engine`; el código activo es solo este directorio.

## Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| `rutas.py` | Rutas a `Data/`, plantillas, informes y feedback (script, cwd, `.exe`) |
| `datos.py` | Carga CSV/JSON, elección de banco |
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `consola.py` | Menús, texto, opciones A–D |
| `entrada_menu.py` | Teclas: Enter, H, F, Supr, Esc, dígitos, A–D |
| `navegacion.py` | Contexto de pantalla, atrás, pausa, feedback rápido (F) |
| `reglas_partida.py` | Presets de reglas (vidas, tiempo, puntuación) |
| `politica_reglas.py` | Política por modo (libre / historia) |
| `configuracion_reglas_libre.py` | Reglas personalizadas en modo libre |
| `motor_partida.py` | Bucle de preguntas y estado de partida |
| `modo_libre.py` | Modo libre (filtros, informes) |
| `modo_historia.py` | Modo historia (examen balanceado) |
| `modo_feedback.py` | Modo feedback y asistente de avisos al creador |
| `envio_feedback.py` | Guardado local `.txt` y envío SMTP |
| `config_creador.py` | Plantilla de `Data/creador_privado.json` |
| `generador_examen_historia.py` | Generación de exámenes según histórico |
| `informe_examen.py` | Informes `.txt` al cerrar partida |

## Controles de teclado

Resumen de [`entrada_menu.py`](entrada_menu.py):

| Tecla | Uso general |
|-------|-------------|
| **Enter** | Confirmar (opción 1 en menús; A en pregunta si aplica) |
| **1–9** | Opción de menú |
| **A–D** | Respuesta en partida |
| **H** | Ayuda contextual |
| **F** | Feedback al creador sin limpiar la terminal |
| **Esc** | Pausa; en texto con «atrás», volver |
| **Supr** | Atrás en menús; en campos de texto, borrar caracteres |
| **Ctrl+C** | Interrupción de terminal (cierra el programa) |

La tecla **F** queda desactivada durante el propio asistente de feedback y en el menú de pausa.

## Modo feedback

Dos accesos:

1. **Menú principal → opción 3** — limpia la pantalla y abre el asistente.
2. **Tecla F** en cualquier momento — el historial de la pantalla se mantiene visible para redactar el aviso con contexto.

Flujo: categoría → área → mensaje (multilínea) → nombre → contacto. Siempre se guarda copia en `Juego/Feedback/`. Con `feedback_smtp` en `Data/creador_privado.json`, se intenta envío por correo.

## Dependencias entre capas

```
juego_cuestionario.py
    → modos (libre / historia / feedback)
        → motor_partida, politica_reglas, datos
            → consola, entrada_menu, navegacion, modelos, rutas
    → envio_feedback, config_creador (feedback)
```

No hace falta ejecutar nada dentro de esta carpeta; el punto de entrada es `../juego_cuestionario.py`.
