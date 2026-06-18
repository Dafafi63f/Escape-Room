# Consola — motor del juego y UI terminal

Paquete **`Consola`** (`Juego/Consola/`). Interfaz **terminal** y orquestación de modos en consola.

La lógica compartida con el gráfico está en [`Comun/`](../Comun/README.md). Este paquete conserva menús por teclado, navegación, informes, historia y feedback.

Se importa con `Juego/` en el `sys.path` (véase [`juego_consola.py`](../juego_consola.py) o [`juego_grafico.py`](../juego_grafico.py)).

## Modos de juego

| Modo | Estado | Módulo principal |
|------|--------|------------------|
| **Libre** | Implementado | `modo_libre.py` — banco dataset o plantillas (beta), filtros, informes |
| **Historia** | Implementado (v1) | `modo_historia.py` + `generador_examen_historia.py` — examen balanceado |
| **Resistencia** | Implementado (v1) | `motor_resistencia.py` + `modo_historia.py` — partida infinita y ranking |
| **Feedback** | Implementado (v1) | `modo_feedback.py` + `envio_feedback.py` — avisos al creador (menú o tecla **F**) |

Los modos comparten la capa de datos (`Data/CSV/Preguntas.csv`, `Data/CSV/listado_materias.csv`, `Data/JSON/plantillas.json`, histórico CSV y JSON de historia/resistencia).

## Módulos

| Módulo | Responsabilidad | ¿Sobrevive a migración gráfica? |
|--------|-----------------|--------------------------------|
| [`Comun/rutas.py`](../Comun/rutas.py) | Rutas a `Data/`, plantillas, informes, feedback y `Files/Scripts` en `sys.path` | Sí |
| `datos.py` | Carga CSV/JSON (consola) y elección de banco en terminal | Parcial* |
| [`Comun/modelos.py`](../Comun/modelos.py) | `Pregunta`, `BancoPreguntas`, etiquetas | Sí |
| `consola.py` | Menús, texto, opciones A–D | No (solo terminal) |
| `entrada_teclas.py` | Lectura tecla a tecla (`msvcrt` en Windows; fallback en otros SO) | No |
| `entrada_menu.py` | Menús, contexto de ayuda, bucles de entrada | No |
| `navegacion.py` | Contexto de pantalla, atrás, pausa, feedback rápido (F) | No |
| [`Comun/reglas_partida.py`](../Comun/reglas_partida.py) | Presets de reglas (vidas, tiempo, puntuación) | Sí |
| `politica_reglas.py` | Política por modo (libre / historia) | Sí |
| `configuracion_reglas_libre.py` | Reglas personalizadas en modo libre | Sí |
| `motor_partida.py` | Bucle de preguntas y estado de partida | Sí |
| `modo_libre.py` | Orquestación modo libre (terminal hoy; lógica reutilizable) | Parcial* |
| `modo_historia.py` | Modo historia (examen balanceado) y entrada a resistencia | Parcial* |
| `motor_resistencia.py` | Bucle de partida infinita, eventos y ranking | Parcial* |
| `modo_feedback.py` | Modo feedback y asistente de avisos al creador | Parcial* |
| `envio_feedback.py` | Guardado local `.txt` y envío SMTP | Sí |
| `config_creador.py` | Plantilla de `Data/JSON/creador_privado.json` | Sí |
| `generador_examen_historia.py` | Generación de exámenes según histórico | Sí |
| `informe_examen.py` | Informes `.txt` al cerrar partida | Sí |

\* Los `modo_*.py` mezclan flujo de UI terminal con lógica de partida; en la migración la UI pasará a `Grafico/` y el motor quedará en el paquete de dominio.

## Entrada de datos y rutas

El lanzador detecta la ruta base del proyecto para funcionar en ejecución normal o empaquetado con PyInstaller. A partir de esa base localiza (vía [`Comun/rutas.py`](../Comun/rutas.py)):

- `Data/CSV/Preguntas.csv` — dataset principal.
- `Data/CSV/listado_materias.csv` — metadatos académicos por materia.
- `Data/JSON/plantillas.json`, `Data/CSV/Historic_qualificacions_MatCAD_completo.csv` — según modo.
- `Data/JSON/presets_historia.json` — catálogo modo historia.
- `Data/JSON/preguntas_resistencia.json`, `ranking_resistencia_infinita.json`, `ranking_reto_dia.json` — modo resistencia.
- `Juego/Informes/` — informes de examen cerrado (`.txt`, gitignored salvo `.gitkeep`).
- `Juego/Feedback/` — copias locales del modo feedback (gitignored salvo `.gitkeep`).
- `Data/JSON/creador_privado.json` — datos personales y SMTP (plantilla en `config_creador.py`).

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
| 1 — Dataset | **MODO SEGURO** (por defecto) | `Data/CSV/Preguntas.csv` — **480** preguntas revisadas |
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

En partidas con corrección al final, `informe_examen.py` escribe un `.txt` en `Juego/Informes/` (o `Informes/` junto al `.exe`), con ID de sesión y detalle de respuestas. El modo resistencia registra el ranking en `Data/JSON/ranking_resistencia_infinita.json` o `ranking_reto_dia.json` (este último se reinicia cada día).

## Controles de teclado

Resumen de [`entrada_teclas.py`](entrada_teclas.py) (Windows) y [`entrada_menu.py`](entrada_menu.py):

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

Flujo: categoría → área → mensaje (multilínea) → nombre → contacto. Siempre se guarda copia en `Juego/Feedback/`. Con `feedback_smtp` en `Data/JSON/creador_privado.json`, se intenta envío por correo.

## Calidad del banco (2026-06-15)

`python Files/Scripts/duplicados.py revisar` → **0 pares similares** en CSV y plantillas intra-materia. `mantenimiento.py validar` → OK.

Mejoras futuras opcionales: ampliar catálogo de plantillas, repuestos LSTM/Sharpe, dedup al cargar banco beta. Ver [`CHECKLIST.md`](../../CHECKLIST.md).

## Dependencias entre capas

```
juego_consola.py / juego_grafico.py
    → Consola/ (modos terminal) o Grafico/ (UI pygame)
        → Comun/ (motor_nucleo, reglas, datos, pool)
            → consola, entrada_teclas, entrada_menu, navegacion (solo terminal)
    → envio_feedback, config_creador (feedback)
```

No hace falta ejecutar nada dentro de esta carpeta; el punto de entrada es `../juego_consola.py`. Al arrancar, el lanzador muestra un tutorial breve de foco de teclado (línea `>>`); ver `entrada_teclas.py` y `entrada_menu.py`.
