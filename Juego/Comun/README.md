# Comun — lógica compartida del juego

Paquete **`Comun`** (`Juego/Comun/`). Dominio del juego: modelos, datos, reglas, motor de partida (sin E/S), pool del modo libre, historia, resistencia, escape room, informes, feedback y rutas a `Data/`.

Se importa con `Juego/` en el `sys.path` (véase [`juego_grafico.py`](../juego_grafico.py)).

## Juego completo vs mínimo

Al arrancar, [`contenido.py`](contenido.py) construye un [`PerfilContenido`](perfil_contenido.py) según los datos disponibles. La UI y el motor consultan **propiedades del perfil** (`modo_minimo`, `banco_beta_disponible` — banco ampliado 960 —, `filtros_libre_disponibles`, `modo_disponible()`, etc.) en lugar de ramificar por rutas globales.

| Módulo | Responsabilidad |
|--------|-----------------|
| `contenido.py` | Marcadores de paquete, validación CSV, bootstrap y degradación automática |
| `perfil_contenido.py` | Capacidades activas según datos y modo |

Rutas resueltas en carga (`path_listado_materias`, `path_plantillas_json`) viajan en `DatosJuego`; no usar `PATH_MATERIAS` ni `resolver_plantillas()` en pantallas si hay datos cargados.

El repositorio de desarrollo se comporta como paquete completo si `Data/` cumple requisitos; con solo un CSV mínimo (`--csv` o layout plano) el perfil degrada a modo mínimo.

## Módulos — núcleo

| Módulo | Responsabilidad |
|--------|-----------------|
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `rutas.py` | Rutas a `Data/Banco/`, `Data/Juego/` |
| `datos.py` | Carga CSV/JSON, conteo de bancos |
| `reglas.py` | Presets, puntuación, modo libre, validación por contexto y complejidad |
| `pool_libre.py` | Pool, filtros, elección de siguiente pregunta |
| `motor_nucleo.py` | `EstadoPartida`, evaluación de respuestas, `NavegacionFinPartida` (sin E/S) |
| `semillas.py` | Semilla diaria (examen del día), semilla de partida, `RngPartida` y `resolver_semillas_partida()` |
| `preferencias_grafico.py` | Preferencias globales gráficas y nombre de jugador |
| `textos_ui.py` | Etiquetas, emojis y textos compartidos (UI gráfica) |
| `informe_examen.py` | Informes `.txt` y metadatos al cerrar partida |
| `utils_plantillas_core.py` | Claves de contenido y expansión de plantillas (reexportado desde `Files/`) |

## Módulos — modo historia, resistencia y especiales

| Módulo | Responsabilidad |
|--------|-----------------|
| `config_historia.py` | Opciones y validación de presets historia |
| `presets_historia.py` | Carga de `Juego/presets.json` (catálogo unificado) |
| `generador_examen_historia.py` | Plan de examen balanceado y perfiles pedagógicos (modo historia) |
| `resistencia_partida.py` | Pool, escalada y selección de preguntas del modo resistencia |
| `resistencia_motor.py` | Probabilidades, estado, powerups, iconos, mecánicas y turnos del modo resistencia |
| `preguntas_resistencia.py` | Pool exclusivo de preguntas resistencia |
| `preguntas_resistencia_exclusivas_datos.py` | 40 preguntas exclusivas (datos embebidos) |
| `modos_diarios.py` | Examen del día y examen fijo (`semilla_diaria` vía `semillas.py`) |
| `estadisticas_jugador.py` | Estadísticas locales agregadas (`estadisticas_jugador.json`) |
| `persistencia.py` | Esquemas JSON, valores por defecto e inicialización/limpieza de `Data/Juego/` |
| `feedback.py` | Formulario, envío SMTP, contacto público y plantilla `creador_privado.json` |
| `eventos_partida.py` | Catálogo común; `rol_escape` puerta vs contenido; botín y pity escape; eventos sí/no resistencia |
| `escape_room.py` | Salas, generación de puertas, pity y semilla aleatoria por partida |
| `escape_partida.py` | Pool progresivo, selección de desafíos y bonificación al completar |
| `objetos_partida.py` | Catálogo unificado de powerups, bonificaciones e inventario |
| `economia_partida.py` | Precios, tienda escape, ofertas sí/no resistencia y selección de artículos |
| `tienda_escape.py` | Fachada escape sobre `objetos_partida` + `economia_partida` |
| `emojis_escape.py` | Emojis y capas de iconos en cartas de puerta escape |
| `emojis_partida.py` | Emojis de objetos, ofertas resistencia y recompensas |
| `linea_estado_ui.py` | Fragmentos de barra de estado (vidas, progreso sala/puerta) |

## Semillas de partida

| Modo | Semilla de arranque |
|------|---------------------|
| **Examen del día** | Contenido fijado por `semilla_diaria()` (fecha UTC); semilla de partida nueva al jugar (baraja el orden si aplica) |
| **Resto de modos** | `semilla_partida_aleatoria()` al iniciar; un `RngPartida` avanza todo el azar de la sesión |

La **semilla** identifica la partida; el **azar** sale de un único `RngPartida` creado al arrancar. Cada `.random()`, `.shuffle()`, `.choice()`, etc. consume el generador y devuelve un valor distinto aunque la semilla no cambie. Recrear `Random(semilla)` a mitad de partida reiniciaría la secuencia.

La resolución central está en ``resolver_semillas_partida()`` ([`semillas.py`](semillas.py)). El examen fijo con semilla numérica manual también usa una sola semilla de partida. En el examen del día, `semilla_diaria()` fija el contenido y la semilla de partida baraja el orden cuando aplica.

No está previsto reto diario con semilla fija para escape room ni resistencia (solo el Examen del día).

Detalle en [`semillas.py`](semillas.py) y [`modos_diarios.py`](modos_diarios.py).

## Qué no está aquí

| Ubicación | Contenido |
|-----------|-----------|
| [`Grafico/`](../Grafico/README.md) | Pantallas pygame, widgets, tema, tooltips, [`arranque_partida.py`](../Grafico/arranque_partida.py) (`construir_navegacion_fin_partida`), [`changelog_juego.py`](../Grafico/changelog_juego.py) |
| [`Docs/utilidades.py`](../../Docs/utilidades.py) | Limpieza externa del repo y `MATCAD_juego_portable.zip` en la raíz |

El gráfico elige banco en [`Grafico/pantallas_libre.py`](../Grafico/pantallas_libre.py).

## Pruebas de dominio

Los tests en [`Tests/test_dominio_juego.py`](../../Tests/test_dominio_juego.py), [`Tests/test_escape_room.py`](../../Tests/test_escape_room.py), [`Tests/test_eventos_partida.py`](../../Tests/test_eventos_partida.py), [`Tests/test_carga_contenido.py`](../../Tests/test_carga_contenido.py) y [`Tests/test_semillas.py`](../../Tests/test_semillas.py) cubren dominio, escape, eventos, contenido y semillas. Soporte en [`Tests/Fixtures/`](../../Tests/README.md#fixtures-soporte-no-tests).
