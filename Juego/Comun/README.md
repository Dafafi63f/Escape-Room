# Comun — lógica compartida del juego

Paquete **`Comun`** (`Juego/Comun/`). Contiene todo lo que funciona **igual** en consola y gráfico: modelos, datos, reglas, motor de partida (sin E/S), pool del modo libre y rutas a `Data/`.

Se importa con `Juego/` en el `sys.path` (véase [`juego_consola.py`](../juego_consola.py) o [`juego_grafico.py`](../juego_grafico.py)).

## Módulos

| Módulo | Responsabilidad |
|--------|-----------------|
| `modelos.py` | `Pregunta`, `BancoPreguntas`, etiquetas |
| `rutas.py` | Rutas a `Data/`, informes, feedback, PyInstaller |
| `datos.py` | Carga CSV/JSON, conteo de bancos |
| `reglas_partida.py` | Presets, puntuación arcade/nota/porcentaje |
| `compatibilidad_reglas_libre.py` | Bloqueos de combinaciones incoherentes |
| `configuracion_reglas_libre.py` | Construcción de reglas personalizadas |
| `politica_reglas.py` | Validación y clasificación por contexto |
| `reglas_libre.py` | API unificada para el wizard gráfico |
| `dificultad.py` | Complejidad y dificultad progresiva |
| `pool_libre.py` | Pool, filtros, elección de siguiente pregunta |
| `motor_nucleo.py` | `EstadoPartida`, evaluación de respuestas (sin E/S) |

## Qué no está aquí

| Ubicación | Contenido específico de UI |
|-----------|--------------------------|
| [`Consola/`](../Consola/README.md) | Menús por teclado, E/S terminal, informes, historia, feedback |
| [`Grafico/`](../Grafico/README.md) | Pantallas pygame, widgets, tema |

`Consola/datos.py` solo añade `elegir_banco_preguntas` (menú terminal). El gráfico elige banco en `Grafico/pantallas.py`.

## Pruebas de paridad

Los tests en [`Tests/Juego/test_paridad_consola_grafico.py`](../../Tests/Juego/test_paridad_consola_grafico.py) comprueban que `juego_consola.py` y `juego_grafico.py` producen el mismo resultado de dominio para las mismas operaciones.
