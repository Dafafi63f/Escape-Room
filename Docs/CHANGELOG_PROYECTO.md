# Changelog del proyecto — TFG MATCAD

Registro **vivo** del proyecto: snapshot de estado, feedback del tutor y changelog por sesiones. Las tareas abiertas están en [`CHECKLIST.md`](CHECKLIST.md).

**Última actualización:** 2026-06-28
**Alumno:** Daniel Fageda Figueredo · **Tutor:** Víctor Navas Portella

En [`Docs/`](README.md): changelogs, checklist y memoria borrador. El repositorio no versiona PDFs.

| Enlace | Uso |
|--------|-----|
| [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md) | Novedades visibles para el jugador |
| [`CHECKLIST.md`](CHECKLIST.md) | Checklist de pendientes e ideas futuras |
| [`persistencia.py`](../Juego/Comun/persistencia.py) | Esquemas JSON en `Data/Juego/` (`--esquemas-juego`) |
| [`Memoria_TFG.md`](Entrega/Memoria_TFG.md) | Borrador Markdown (`Docs/Entrega/`) |
| [`Entrega/`](Entrega/) | LaTeX y Word de la memoria (`Docs/Entrega/`) |
| [`Figuras/`](Figuras/) | Imágenes de la memoria |
| [`Data/README.md`](Data/README.md) | Banco 480 ítems, plantillas beta, esquema curricular |

Regenerar figuras: `python Docs/generar_figuras_memoria.py` · Word: `python Docs/utilidades_tfg.py --solo-memoria`

---

## 1. Resumen ejecutivo

| Área | Estado | Notas |
|------|--------|-------|
| **Memoria** | En revisión con tutor | Estructura académica; Word desde MD/LaTeX; PDF de entrega manual |
| **Banco de preguntas** | Cerrado | 480/480 revisadas; `Preguntas.csv` protegido (`TFG_PERMITIR_CSV=1` para escribir) |
| **Juego (pygame)** | Operativo | 5 modos: libre, historia, resistencia, escape room, feedback |
| **Scripts mantenimiento** | Operativo | `Files/mantenimiento.py` (scripts en `Files/`) |
| **CI / pruebas** | Operativo | GitHub Actions; **468** tests en `Tests/` |
| **Interfaz gráfica / narrativa** | Parcial | Escape room jugable (mecánicas); narrativa gráfica completa pendiente |
| **Piloto con usuarios** | No realizado | Ver [`CHECKLIST.md`](CHECKLIST.md) |

**Entregable actual:** juego pygame + banco 480 preguntas + herramientas de validación.

---

## 2. Progreso por componente

### 2.1 Documentación

| Elemento | Estado | Ubicación |
|----------|--------|-----------|
| Memoria Markdown | Actualizada | `Docs/Entrega/Memoria_TFG.md` |
| Memoria LaTeX / Word | Regenerables | `Docs/Entrega/` |
| Figuras memoria | Regenerables | `Docs/Figuras/` |
| Este changelog | **Mantener al día** | `Docs/CHANGELOG_PROYECTO.md` |

### 2.2 Código — juego

| Elemento | Estado | Notas |
|----------|--------|-------|
| Lanzador gráfico | OK | `Juego/juego_grafico.py` + `Juego/Grafico/` |
| Paquete `Comun/` | OK | Dominio: reglas, datos, informes, feedback, historia, resistencia, escape |
| Paquete `Grafico/` | OK | UI pygame, cinco modos de juego |
| Ejecutable Windows | Retirado | Arranque con Python + `Jugar.bat` |
| Tests + CI | OK | `python -m unittest discover -s Tests -q` |

### 2.3 Datos y mantenimiento

| Elemento | Estado | Notas |
|----------|--------|-------|
| `Data/Banco/` | Cerrado 480 ítems | CSV + JSON de banco y catálogos (`Preguntas.csv`, plantillas, presets…) |
| `Data/Juego/` | OK | Estado local: preferencias, estadísticas, informes `.txt`; esquemas en `persistencia.py` |
| `duplicados.py revisar` | OK | 0 pares similares (2026-06-15) |
| `simulacion_evaluacion_azar.py` | OK | Validación motor ante respuestas al azar |

---

## 3. Feedback del tutor

Registro consolidado de comentarios del tutor (incorporados en la memoria).

Leyenda: ✅ aplicado · 🔄 parcial · ⏳ pendiente

### 3.1 Estructura y redacción de la memoria

| Comentario | Estado | Dónde se reflejó |
|------------|--------|------------------|
| Marco teórico en **Introducción** | ✅ | `Docs/Entrega/Memoria_TFG.md` §1.5 |
| Resumen / abstract | ✅ | Inicio memoria + LaTeX |
| Objetivos: cumplimiento en **Discusión** | ✅ | §6.1 |
| Título **juego interactivo** | ✅ | Portada MD/LaTeX |
| Evaluación del jugador en memoria | ✅ | §4.3 |
| Hipótesis contrastables | ✅ | H1–H3; §6.6 |
| Bibliografía actualizada | ✅ | §8 |

### 3.2 Contenido técnico

| Comentario | Estado | Dónde se reflejó |
|------------|--------|------------------|
| Histórico calificaciones (H3) | ✅ | §5.6; modo historia |
| Simulación respuestas al azar | ✅ | §5.7 |
| Más contenido estadístico | 🔄 | Piloto usuarios ⏳ |
| Pygame en desarrollo | ✅ | §5.2 |

### 3.3 Pendiente de tutor / entrega

| Tema | Prioridad | Notas |
|------|-----------|-------|
| Piloto con estudiantes | Media | En [`CHECKLIST.md`](CHECKLIST.md) |
| Escape room narrativo | Baja | Mecánicas en juego; guion visual completo en [`CHECKLIST.md`](CHECKLIST.md) |
| Revisión final Word → PDF | Alta | En [`CHECKLIST.md`](CHECKLIST.md) |
| Pares similares CSV/plantillas | ✅ | 2026-06-15 |

---

## 4. Changelog (historial)

Síntesis de **41 commits** en git (mayo–junio 2026) más el trabajo reciente en la rama gráfica. Las filas antiguas de la tabla resumen siguen abajo; el detalle por periodo es el referencia principal.

### 2026-06-28 — Estadísticas locales, fusión de `Comun/` y limpieza de ranking

| Ámbito | Cambio |
|--------|--------|
| Juego | `estadisticas_jugador.py`: panel «Mis estadísticas», registro al cerrar partida, récords agregados |
| Juego | Eliminados `ranking_resistencia.py`, `preferencias_ranking.py` y `ranking_resistencia.json` |
| Juego | Opciones: «Restablecer estadísticas»; init crea JSON de stats al arrancar (`juego_grafico.py`) |
| Juego | Valores vacíos de datos locales en `persistencia.py` (fusiona `esquemas_datos_juego` + `datos_locales_juego`) |
| Juego | Fusión de módulos en `Comun/`: `contenido.py`, `reglas.py`, `persistencia.py`, `util.py`; modos especiales en `presets_historia.py` |
| Docs | `Juego/Comun/persistencia.py`; `utilidades_tfg.py --esquemas-juego` |
| Tests | `Tests/test_estadisticas_jugador.py`; soporte en `Tests/Fixtures/`; sync esquemas en `test_grafico_ui` |
| Repo | Eliminados `Files/test_*.py` (mantenimiento); validación del banco solo vía `mantenimiento.py validar` |

### 2026-06-27 — Plantillas, portable y documentación

| Ámbito | Cambio |
|--------|--------|
| Datos | Inyección de **12** filas del CSV ausentes en `plantillas.json` → cobertura **480/480** (`mantenimiento.py plantillas inyectar`) |
| Juego | `utils_plantillas_core.py` canónico en `Juego/Comun/`; zip portable sin carpeta `Files/` |
| Docs | Memoria y README unificados a **5 modos**; conteo tests **395**; pool plantillas **1411** |

### 2026-06-26 — Escape room (mecánicas)

| Ámbito | Cambio |
|--------|--------|
| Escape | Salas, puertas, escalada, cronómetros, niebla, puertas jefe; catálogo unificado en `eventos_partida.py` |
| Escape | Tienda (`tienda_escape.py`): economía en puntos, inventario, 3 artículos/visita, compra múltiple (1 u. c/u) |
| Escape | Botín: vidas, corazón máximo y objetos (bomba, 50/50, …); pity cada 3 salas; hard pity descanso/tienda |
| Escape | Pity dual descanso/tienda; persistencia entre salas; UI cartas puerta + inventario inferior |
| Gráfico | `PartidaEscapeRoom` en `pantallas_modos.py`; emojis escape (`emojis_escape.py`) |
| Tests | `test_escape_room.py` ampliado; suite **387** tests en `Tests/` |

### 2026-06-19 — Rama gráfica (local / pendiente de commit)

| Ámbito | Cambio |
|--------|--------|
| Gráfico | **Modo feedback** pygame: formulario (tipo, zona, mensaje, contacto); envío SMTP; pantalla de resultado |
| Gráfico | **Info del juego** (ℹ️): estadísticas, contacto visible en panel, novedades del juego *(ranking retirado en 2026-06-28)* |
| Gráfico | Barra fija: pausa · diarios · info · feedback · opciones; emoji ℹ️ en lugar de 🏆 para info |
| Gráfico | Popup apuesta: botones ✅/❌; power-up Saltar 🦘; ajustes UI feedback e info |
| Juego | `feedback.py`, `Grafico/changelog_juego.py`, `persistencia.py` *(antes: contacto_creador, feedback_opciones, datos_locales_juego)* |
| Docs | Todo en `Docs/`: memoria, changelogs, `Entrega/` y `Figuras/` |
| Datos | Reorganización `Data/Banco/` + `Data/Juego/`; informes y feedback fuera de `Juego/Informes` |
| Repo | `Docs/utilidades_tfg.py` (limpieza + Word); eliminados `borrar_temporales.py` y `exportar_memoria.py` de la raíz |
| Tests | Suite unificada en `Tests/` (raíz); tests changelog, feedback, menús gráficos |

### 2026-06-19 — Git

| Commit | Cambio |
|--------|--------|
| `637f4a6` | Merge `main` en rama gráfica: dominio `Comun/` + capa `Grafico/` |

### 2026-06-18 — Git

| Commit | Cambio |
|--------|--------|
| `fbef854` | Resistencia ampliada (reto día, apuestas, maldiciones, bloques); tests reorganizados; docs |
| `cc048f2` | Merge dominio compartido sin duplicar trabajo gráfico |
| `8153cd0` | Resistencia e historia en dominio; reorganización `Data/` (sin capa gráfica en main) |
| `9c02d53` | WIP: resistencia consola, pygame, tests (split pendiente) |

### 2026-06-17 — Git

| Commit | Cambio |
|--------|--------|
| `059fa0f` | Primera interfaz **pygame** y tests paridad consola/gráfico |
| `a78fc3c` | Paquete **`Comun/`**; lanzador renombrado a `juego_consola.py` |

### 2026-06-15 — Git

| Commit | Cambio |
|--------|--------|
| `d8f6f27` | Calidad banco, refactor juego, tests unificados, CI |
| `36ff556` | CI: Tests, PR-Agent, SonarCloud, pre-commit |
| `9a3f278` | Python **3.14** en CI y desarrollo |
| `26d7701` | Tests entrada en Linux (msvcrt / MyPy) |
| Varios | Limpieza cachés, SonarCloud sin token, checks CI sin duplicar push/PR |

### 2026-06-09 — 2026-06-11 — Git

| Commit | Cambio |
|--------|--------|
| `cf567bb` | Memoria: figuras, Monte Carlo §5.7, `Entrega/` reorganizada |
| `f339da0` | Feedback tutor; entrega memoria en **Word** |
| `64ab9fd` | Carpeta `Entrega/` y exportación PDF memoria |
| `0bc63c9` | Reestructuración memoria TFG y documentación repo |

### 2026-06-03 — 2026-06-05 — Git

| Commit | Cambio |
|--------|--------|
| `2cfbc77` | **Modo feedback** consola, controles teclado, limpieza unificada |
| `c0018b2` | Paquete **`Consola/`**, `Files/Scripts/`, documentación |
| `0fa9e03` | **Banco cerrado** 480 ítems; plantillas beta; juego con 3 capas de banco |

### 2026-06-01 — 2026-06-02 — Git

| Commit | Cambio |
|--------|--------|
| `9278a84` | Banco ampliado a **480** preguntas; revisión manual 1–240 |
| `fb372e7` | Revisión manual banco ids 1–130; scripts mantenimiento |

### 2026-05-28 — 2026-05-19 — Git

| Commit | Cambio |
|--------|--------|
| `f88b886` | Consolidación scripts redundantes en CLIs unificados |
| `b2ba3bc` | Balance, deduplicación, clasificación por contenido |
| `23b70f5` | Orden canónico banco (ladder TF…TD / CF…CD) |

### 2026-05-12 — Git (inicio del repositorio)

| Commit | Cambio |
|--------|--------|
| `36cadbd` | **Commit inicial**: datos, scripts, juego consola, memoria |
| `970e17f` | Histórico MatCAD a `Data/`; eliminación `Backups/` |
| `8c35875` | Coherencia CSV, balanceo ~400 preguntas, memoria actualizada |
| `0562384` | Dataset CSV mínimo; utilidades y limpieza scripts |
| `25d3d03` | `Memoria_TFG.md` unificado; notas GitHub integradas |

### Tabla resumen (sesiones recientes)

| Fecha | Ámbito | Cambio |
|-------|--------|--------|
| 2026-06-28 | Stats | Estadísticas locales v1; eliminado ranking JSON; esquemas documentados |
| 2026-06-27 | Semillas | `RngPartida`: un generador por sesión que avanza (sin sub-semillas); docs, simulaciones, figuras y Word regenerados |
| 2026-06-27 | Escape | Semilla aleatoria por partida; tienda pospuesta sin saldo; pity tienda; emoji botín en cartas; limpieza alias obsoletos |
| 2026-06-27 | Refactor | `objetos_partida` + `economia_partida`; fachada `tienda_escape`; eliminados `semilla_partida_diaria`, GuionEscapeRoom, wrappers `_tienda` |
| 2026-06-27 | Tests | `Tests/test_semillas.py`; suite **416** tests en `Tests/` |
| 2026-06-26 | Escape | Modo escape room: tienda, botín, inventario, pity |
| 2026-06-19 | Entrega | Prep. informe: figuras y Word regenerados, limpieza, merge en `main` |
| 2026-06-19 | Migración | Solo pygame: eliminado `Juego/Consola/`, módulos a `Comun/`, 258 tests |
| 2026-06-19 | Build | PyInstaller: empaqueta `utils_plantillas_core` (`--paths Files`, hidden-import) *(retirado)* |
| 2026-06-19 | Build | PyInstaller: `build_exe_onefile.ps1` → `juego_grafico.exe` *(retirado; distribución por zips)* |
| 2026-06-19 | Gráfico | Feedback, info, barra superior, contacto solo correo, changelogs separados |
| 2026-06-19 | Docs | Documentación alineada: `Docs/`, `Docs/utilidades_tfg.py`, 258 tests |
| 2026-06-18 | Gráfico | Barra de estado: chips emoji; resistencia con #N y racha |
| 2026-06-18 | Juego | Resistencia: reto del día, apuestas, maldiciones, bloques |
| 2026-06-18 | Repo | Limpieza `Revision/`; `BITACORA`→`CHANGELOG`, `TAREAS`→`CHECKLIST` |
| 2026-06-17 | Gráfico | Historia y resistencia pygame; tooltips; wizard libre |
| 2026-06-17 | Tests | Suite ~177→~260 tests |
| 2026-06-15 | Banco | 0 pares similares; dedup plantillas (1289) |
| 2026-06-15 | Repo | CI GitHub Actions |
| 2026-06-11 | Memoria | Exportación Word; figuras; Monte Carlo |

---

## 5. Comprobaciones rápidas

```bash
python Docs/utilidades_tfg.py
python Docs/utilidades_tfg.py --esquemas-juego
python Docs/generar_figuras_memoria.py
python Files/mantenimiento.py validar
python Files/simulacion_evaluacion_azar.py
python -m unittest discover -s Tests -q
```

---

## 6. Cómo actualizar

1. **Comentarios del tutor** → filas en **§3**; changelog en **§4**.
2. **Código o datos** → **§2** + línea en **§4**; ajustar **§1** si cambia el panorama.
3. **Cambios visibles al jugador** → [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md).
4. **Tarea cerrada o nueva** → [`CHECKLIST.md`](CHECKLIST.md) (borrar o añadir ítems).
5. Cambiar la fecha de **Última actualización** al inicio.
