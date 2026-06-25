# Comun — lógica compartida del juego

Paquete **`Comun`** (`Juego/Comun/`). Dominio del juego: modelos, datos, reglas, motor de partida (sin E/S), pool del modo libre, historia, resistencia, informes, feedback y rutas a `Data/`.

Se importa con `Juego/` en el `sys.path` (véase [`juego_grafico.py`](../juego_grafico.py)).

## Módulos — núcleo

| Módulo | Responsabilidad |
|--------|-----------------|
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `rutas.py` | Rutas a `Data/Banco/`, `Data/Juego/`, PyInstaller |
| `datos.py` | Carga CSV/JSON, conteo de bancos |
| `reglas_partida.py` | Presets, puntuación arcade/nota/porcentaje y mínimos globales |
| `reglas_libre.py` | Compatibilidad, configuración y API del wizard del modo libre |
| `politica_reglas.py` | Validación y clasificación por contexto |
| `dificultad.py` | Complejidad y dificultad progresiva |
| `pool_libre.py` | Pool, filtros, elección de siguiente pregunta |
| `motor_nucleo.py` | `EstadoPartida`, evaluación de respuestas (sin E/S) |
| `jugador.py` | Nombre efectivo y anonimato |
| `textos_ui.py` | Etiquetas, emojis y textos compartidos (UI gráfica) |
| `informe_examen.py` | Informes `.txt` y metadatos al cerrar partida |
| `stdio_utf8.py` | UTF-8 en stdout/stderr (Windows) |

## Módulos — modo historia, resistencia y especiales

| Módulo | Responsabilidad |
|--------|-----------------|
| `config_historia.py` | Opciones y validación de presets historia (v27) |
| `presets_historia.py` | Carga de `presets.json` (catálogo unificado) |
| `generador_examen_historia.py` | Plan de examen balanceado y perfiles pedagógicos (modo historia) |
| `resistencia_partida.py` | Pool, escalada y selección de preguntas del modo resistencia |
| `resistencia_motor.py` | Probabilidades, estado, powerups, iconos, mecánicas y turnos del modo resistencia |
| `preguntas_resistencia.py` | Pool exclusivo de preguntas resistencia |
| `modos_diarios.py` | Semilla diaria (`DDMMYYYY`), examen del día y examen fijo (diario / aleatorio / semilla) |
| `ranking_resistencia.py` | Ranking local (`ranking_resistencia.json`) |
| `preferencias_grafico.py` | Opciones globales gráficas (nombre, feedback, tooltips) |
| `preferencias_ranking.py` | Retención interna del ranking (sin fichero ni UI) |
| `datos_locales_juego.py` | Creación al inicio y limpieza desde el juego (`Data/Juego/`) |
| `borrar_temporales.py` | Lógica de limpieza de temporales (CLI: [`utilidades_tfg.py`](../../utilidades_tfg.py) en la raíz) |
| `changelog_juego.py` | Lectura de `Docs/CHANGELOG_JUEGO.md` para la UI |
| `contacto_creador.py` | Canales de contacto públicos (sin credenciales SMTP) |
| `feedback_opciones.py` | Categorías y zonas del formulario de feedback |
| `eventos_partida.py` | Catálogo común; ``rol_escape`` puerta vs contenido |
| `escape_room.py` | Salas, generación de puertas y partida |
| `escape_partida.py` | Pool progresivo del dataset revisado y selección de desafíos |
| `envio_feedback.py` | Guardado local y envío SMTP del feedback |
| `config_creador.py` | Plantilla `creador_privado.json` |

## Qué no está aquí

| Ubicación | Contenido específico de UI |
|-----------|--------------------------|
| [`Grafico/`](../Grafico/README.md) | Pantallas pygame, widgets, tema, tooltips |

El gráfico elige banco en [`Grafico/pantallas_libre.py`](../Grafico/pantallas_libre.py).

## Pruebas de dominio

Los tests en [`Tests/test_dominio_juego.py`](../../Tests/test_dominio_juego.py) comprueban datos, reglas y evaluación vía el adaptador en [`Tests/adaptador_juego.py`](../../Tests/adaptador_juego.py).
