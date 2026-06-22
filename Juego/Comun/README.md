# Comun — lógica compartida del juego

Paquete **`Comun`** (`Juego/Comun/`). Dominio del juego: modelos, datos, reglas, motor de partida (sin E/S), pool del modo libre, historia, resistencia, informes, feedback y rutas a `Data/`.

Se importa con `Juego/` en el `sys.path` (véase [`juego_grafico.py`](../juego_grafico.py)).

## Módulos — núcleo

| Módulo | Responsabilidad |
|--------|-----------------|
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `rutas.py` | Rutas a `Data/Banco/`, `Data/Juego/`, PyInstaller |
| `datos.py` | Carga CSV/JSON, conteo de bancos |
| `reglas_partida.py` | Presets, puntuación arcade/nota/porcentaje |
| `compatibilidad_reglas_libre.py` | Bloqueos de combinaciones incoherentes |
| `configuracion_reglas_libre.py` | Construcción de reglas personalizadas |
| `politica_reglas.py` | Validación y clasificación por contexto |
| `reglas_libre.py` | API unificada para el wizard gráfico |
| `dificultad.py` | Complejidad y dificultad progresiva |
| `pool_libre.py` | Pool, filtros, elección de siguiente pregunta |
| `motor_nucleo.py` | `EstadoPartida`, evaluación de respuestas (sin E/S) |
| `jugador.py` | Nombre efectivo y anonimato |
| `textos_ui.py` | Etiquetas, emojis y textos compartidos (UI gráfica) |
| `cierre_informe.py` | Metadatos al cerrar partida con informe |
| `stdio_utf8.py` | UTF-8 en stdout/stderr (Windows) |

## Módulos — modo historia y resistencia

| Módulo | Responsabilidad |
|--------|-----------------|
| `limites_partida.py` | Mínimos globales (p. ej. 5 preguntas por partida) |
| `config_historia.py` | Opciones y validación de presets historia (v27) |
| `presets_historia.py` | Carga de `presets_historia.json` |
| `perfiles_historia.py` | Perfiles de examen (refuerzo, simulacro, etc.) |
| `resistencia_historia.py` | Eventos aleatorios y escalada de dificultad |
| `estado_resistencia.py` | Estado extendido de partida resistencia |
| `mecanicas_resistencia.py` | Apuestas, maldiciones, bloques, progreso, reto del día |
| `probabilidad_resistencia.py` | Probabilidades de eventos y recompensas |
| `reto_dia_resistencia.py` | Identificador y semilla del reto diario |
| `motor_resistencia_comun.py` | Turnos, racha, multiplicadores, objetos |
| `powerups_resistencia.py` | Comodines (50/50, bomba, escudo, skip, tiempo extra) |
| `preguntas_resistencia.py` | Pool exclusivo de preguntas resistencia |
| `modos_diarios.py` | Semilla diaria compartida (`DDMMYYYY`) y orden de presets diarios |
| `examen_dia_historia.py` | Alias de semilla diaria para el examen balanceado |
| `examen_fijo_historia.py` | Preset `examen_fijo` (diario / aleatorio / semilla) |
| `ranking_resistencia.py` | Rankings locales (`ranking_resistencia_infinita.json`, `ranking_reto_dia.json`) |
| `preferencias_grafico.py` | Opciones globales gráficas (nombre, feedback, tooltips) |
| `preferencias_ranking.py` | Retención interna del ranking (sin fichero ni UI) |
| `datos_locales_juego.py` | Creación al inicio y limpieza desde el juego (`Data/Juego/`) |
| `borrar_temporales.py` | Lógica de limpieza de temporales (CLI: [`utilidades_tfg.py`](../../utilidades_tfg.py) en la raíz) |
| `changelog_juego.py` | Lectura de `Docs/CHANGELOG_JUEGO.md` para la UI |
| `contacto_creador.py` | Canales de contacto públicos (sin credenciales SMTP) |
| `feedback_opciones.py` | Categorías y zonas del formulario de feedback |
| `iconos_resistencia.py` | Emojis y descripciones de eventos/objetos |
| `generador_examen_historia.py` | Plan de examen balanceado (modo historia) |
| `informe_examen.py` | Informes `.txt` al cerrar partida |
| `envio_feedback.py` | Guardado local y envío SMTP del feedback |
| `config_creador.py` | Plantilla `creador_privado.json` |

## Qué no está aquí

| Ubicación | Contenido específico de UI |
|-----------|--------------------------|
| [`Grafico/`](../Grafico/README.md) | Pantallas pygame, widgets, tema, tooltips |

El gráfico elige banco en [`Grafico/pantallas_libre.py`](../Grafico/pantallas_libre.py).

## Pruebas de dominio

Los tests en [`Tests/test_dominio_juego.py`](../../Tests/test_dominio_juego.py) comprueban datos, reglas y evaluación vía el adaptador en [`Tests/adaptador_juego.py`](../../Tests/adaptador_juego.py).
