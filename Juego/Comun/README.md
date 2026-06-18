# Comun — lógica compartida del juego

Paquete **`Comun`** (`Juego/Comun/`). Contiene todo lo que funciona **igual** en consola y gráfico: modelos, datos, reglas, motor de partida (sin E/S), pool del modo libre, historia, resistencia y rutas a `Data/`.

Se importa con `Juego/` en el `sys.path` (véase [`juego_consola.py`](../juego_consola.py) o [`juego_grafico.py`](../juego_grafico.py)).

## Módulos — núcleo

| Módulo | Responsabilidad |
|--------|-----------------|
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `rutas.py` | Rutas a `Data/CSV/`, `Data/JSON/`, informes, feedback, PyInstaller |
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
| `textos_ui.py` | Etiquetas, emojis y textos compartidos consola/gráfico |
| `cierre_informe.py` | Metadatos al cerrar partida con informe |
| `stdio_utf8.py` | Consola UTF-8 en Windows |

## Módulos — modo historia y resistencia

| Módulo | Responsabilidad |
|--------|-----------------|
| `config_historia.py` | Constantes y perfiles de historia |
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
| `modos_diarios.py` | Identificación y orden de presets con semilla diaria |
| `examen_dia_historia.py` | Semilla del examen del día (historia) |
| `ranking_resistencia.py` | Rankings locales (`ranking_resistencia_infinita.json`, `ranking_reto_dia.json`) |
| `preferencias_grafico.py` | Opciones globales gráficas (nombre, feedback, tooltips) |
| `preferencias_ranking.py` | Conservación del ranking (sesión, días, permanente) |
| `limpieza_local.py` | Borrado de `.txt` (informes/feedback) y rankings locales |
| `iconos_resistencia.py` | Emojis y descripciones de eventos/objetos |
| `linea_estado_ui.py` | Segmentos de barra de estado (chips emoji; consola y gráfico) |

## Qué no está aquí

| Ubicación | Contenido específico de UI |
|-----------|--------------------------|
| [`Consola/`](../Consola/README.md) | Menús por teclado, E/S terminal, orquestación consola |
| [`Grafico/`](../Grafico/README.md) | Pantallas pygame, widgets, tema, tooltips |

`Consola/datos.py` solo añade `elegir_banco_preguntas` (menú terminal). El gráfico elige banco en [`Grafico/pantallas_libre.py`](../Grafico/pantallas_libre.py).

## Pruebas de paridad

Los tests en [`Tests/Juego/test_consola_paridad.py`](../../Tests/Juego/test_consola_paridad.py) comprueban que consola y gráfico producen el mismo resultado de dominio para las mismas operaciones.
