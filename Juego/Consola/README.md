# Consola — paquete del juego

Implementación del cuestionario en terminal. Nombre del paquete: **`Consola`** (carpeta `Juego/Consola/`). Se importa con `Juego/` en el `sys.path` (véase [`juego_cuestionario.py`](../juego_cuestionario.py)).

Antes del refactor vivía como módulos sueltos o paquetes `matcad` / `Motor` / `Engine`; el código activo es solo este directorio.

## Modos de juego

| Modo | Estado | Módulo principal |
|------|--------|------------------|
| **Libre** | Implementado | `modo_libre.py` — banco dataset o plantillas (beta), filtros, informes |
| **Historia** | Implementado (v1) | `modo_historia.py` + `generador_examen_historia.py` — examen balanceado |
| **Feedback** | Implementado (v1) | `modo_feedback.py` + `envio_feedback.py` — avisos al creador (menú o tecla **F**) |

Los tres modos comparten la capa de datos (`Data/Preguntas.csv`, `listado_materias.csv`, plantillas e histórico CSV).

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

## Entrada de datos y rutas

El lanzador detecta la ruta base del proyecto para funcionar en ejecución normal o empaquetado con PyInstaller. A partir de esa base localiza:

- `Data/Preguntas.csv` — dataset principal.
- `Data/listado_materias.csv` — metadatos académicos por materia.
- `Data/plantillas.json`, `Data/Historic_qualificacions_MatCAD_completo.csv` — según modo.
- `Juego/Informes/` — informes de examen cerrado (`.txt`, gitignored salvo `.gitkeep`).
- `Juego/Feedback/` — copias locales del modo feedback (gitignored salvo `.gitkeep`).
- `Data/creador_privado.json` — datos personales y SMTP (plantilla en `config_creador.py`).

La carga valida que cada pregunta tenga enunciado, cuatro opciones completas y respuesta correcta en `{A, B, C, D}`.

## Modelo interno `Pregunta`

Cada fila del CSV se transforma en una instancia de `Pregunta`:

- **Evaluación:** `texto`, `opciones`, `correcta`
- **Metadatos académicos:** `materia`, `tematica`, `grupo`, `nivel`, `curso`, `semestre`
- **Metadatos didácticos:** `dificultad`, `tipo`

## Modo libre — banco y filtros

Al iniciar cada partida, el jugador elige el **banco**:

| Opción | Calidad | Fuente |
|--------|---------|--------|
| 1 — Dataset | **MODO SEGURO** (por defecto) | `Data/Preguntas.csv` — **480** preguntas revisadas |
| 2 — Todo | **MODO BETA** | **480 + 960 = 1440** (dataset + pool extra de plantillas) |
| 3 — Plantillas extra | **MODO BETA** | **960** instancias (**24** por materia; no revisadas) |

Equilibrio del pool extra: `python Files/Scripts/equilibrar_pool_extra_juego.py --inplace`. Si hay duplicados o variantes sintéticas: `python Files/Scripts/dedup_reemplazar_plantillas.py --inplace` y volver a equilibrar.

La coincidencia con el dataset usa materia + enunciado + opciones + correcta. Las plantillas con placeholders sin sustituir se omiten.

**Recomendación:** modo seguro (banco 1) para evaluación; modos 2–3 son beta.

Tras elegir banco, el jugador indica nombre y número de preguntas. Filtro principal:

- todas las preguntas,
- por temática,
- por semestre (`curso-semestre`),
- o por tipo.

Si el `pool` queda vacío, la partida no comienza.

### Filtros adicionales en partida

Por `curso`, `semestre`, `grupo`, `nivel`, `materia` y `dificultad`. En cada pregunta mostrada se visualizan los metadatos académicos.

## Dificultad global progresiva

La dificultad global numérica combina:

- dificultad declarada (`Facil` / `Media` / `Dificil`),
- y nivel académico de la materia (`nivel`).

La partida empieza en una dificultad inicial configurable (`1..max`) y sube cada tres preguntas respondidas hasta el máximo del `pool`.

## Puntuación y vidas

- **+10 / +20 / +30** puntos por acierto según dificultad (Fácil / Media / Difícil).
- Penalización por error: al menos 5 puntos (o la mitad del valor base).
- **3 vidas** por partida.

La partida termina al agotar vidas o al completar el objetivo de preguntas.

## Informes de partida

En partidas con corrección al final, `informe_examen.py` escribe un `.txt` en `Juego/Informes/` (o `Informes/` junto al `.exe`), con ID de sesión y detalle de respuestas. No hay fichero de ranking global.

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

## Tareas pendientes (calidad / unicidad semántica)

No bloquean el uso actual; revisar con `python Files/Scripts/duplicados.py revisar`.

1. **CSV (modo seguro):** sustituir **3 pares similares** (Ids 14↔21, 298↔322, 69↔72).
2. **Plantillas (misma materia):** reducir **~13 pares similares** intra-materia.
3. **Plantillas (entre materias):** ampliar `catalogo_internet_plantillas.py` por materia.
4. **Limpieza opcional:** alinear entradas `repuesto` que dupliquen enunciado pero no opciones del CSV.
5. **Modo beta:** valorar dedup semántica al cargar el banco extra.

## Dependencias entre capas

```
juego_cuestionario.py
    → modos (libre / historia / feedback)
        → motor_partida, politica_reglas, datos
            → consola, entrada_menu, navegacion, modelos, rutas
    → envio_feedback, config_creador (feedback)
```

No hace falta ejecutar nada dentro de esta carpeta; el punto de entrada es `../juego_cuestionario.py`. Al arrancar, el lanzador muestra un tutorial breve de foco de teclado (línea `>>`); ver `entrada_menu.py`.
