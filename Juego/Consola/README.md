# Consola — paquete del juego

Implementación del cuestionario en terminal. Nombre del paquete: **`Consola`** (carpeta `Juego/Consola/`). Se importa con `Juego/` en el `sys.path` (véase [`juego_cuestionario.py`](../juego_cuestionario.py)).

Antes del refactor vivía como módulos sueltos o paquetes `matcad` / `Motor` / `Engine`; el código activo es solo este directorio.

## Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| `rutas.py` | Rutas a `Data/`, plantillas e informes (script, cwd, `.exe`) |
| `datos.py` | Carga CSV/JSON, elección de banco |
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `consola.py` | Menús, enteros, opciones A–D |
| `entrada_menu.py` | Teclas (Enter, Supr, dígitos, Ctrl+C) |
| `navegacion.py` | Contexto de pantalla, atrás, pausa, EOF |
| `reglas_partida.py` | Presets de reglas (vidas, tiempo, puntuación) |
| `politica_reglas.py` | Política por modo (libre / historia) |
| `configuracion_reglas_libre.py` | Reglas personalizadas en modo libre |
| `motor_partida.py` | Bucle de preguntas y estado de partida |
| `modo_libre.py` | Modo libre (filtros, informes) |
| `modo_historia.py` | Modo historia (examen balanceado) |
| `modo_feedback.py` | Modo feedback (en desarrollo) |
| `generador_examen_historia.py` | Generación de exámenes según histórico |
| `informe_examen.py` | Informes `.txt` al cerrar partida |

## Dependencias entre capas

```
juego_cuestionario.py
    → modos (libre / historia / feedback)
        → motor_partida, politica_reglas, datos
            → consola, entrada_menu, navegacion, modelos, rutas
```

No hace falta ejecutar nada dentro de esta carpeta; el punto de entrada es `../juego_cuestionario.py`.
