# Changelog del proyecto — TFG MATCAD

Registro **vivo** del proyecto: snapshot de estado, feedback del tutor y changelog por sesiones. Las tareas abiertas están en [`CHECKLIST.md`](CHECKLIST.md).

**Última actualización:** 2026-06-18  
**Alumno:** Daniel Fageda Figueredo · **Tutor:** Víctor Navas Portella

En la raíz del repo: este fichero y [`CHECKLIST.md`](CHECKLIST.md). El repositorio no versiona PDFs.

| Enlace | Uso |
|--------|-----|
| [`CHECKLIST.md`](CHECKLIST.md) | Checklist de pendientes e ideas futuras |
| [`Memoria_TFG.md`](Memoria_TFG.md) | Borrador académico |
| [`Entrega/`](Entrega/README.md) | Word, LaTeX, figuras; PDF manual desde Word |
| [`Data/README.md`](Data/README.md) | Banco 480 ítems, plantillas beta, esquema curricular |

Regenerar figuras: `python Entrega/generar_figuras_memoria.py` · Word: `python exportar_memoria.py`

---

## 1. Resumen ejecutivo

| Área | Estado | Notas |
|------|--------|-------|
| **Memoria** | En revisión con tutor | Estructura académica; Word desde MD/LaTeX; PDF de entrega manual |
| **Banco de preguntas** | Cerrado | 480/480 revisadas; `Preguntas.csv` protegido (`TFG_PERMITIR_CSV=1` para escribir) |
| **Juego (consola)** | Operativo | 4 modos: libre, historia, resistencia, feedback |
| **Juego (gráfico)** | En desarrollo avanzado | Libre, historia y resistencia; reto del día, apuestas, maldiciones, bloques temáticos |
| **Scripts mantenimiento** | Operativo | `Files/Scripts/mantenimiento.py` |
| **CI / pruebas** | Operativo | GitHub Actions; **238 tests** |
| **Interfaz gráfica / narrativa** | En desarrollo | Pygame; migración futura: solo gráfico |
| **Piloto con usuarios** | No realizado | Ver [`CHECKLIST.md`](CHECKLIST.md) |

**Entregable actual:** juego consola + gráfico pygame + banco 480 preguntas + herramientas de validación.

---

## 2. Progreso por componente

### 2.1 Documentación

| Elemento | Estado | Ubicación |
|----------|--------|-----------|
| Memoria Markdown | Actualizada | `Memoria_TFG.md` |
| Memoria LaTeX / Word | Regenerables | `Entrega/Memoria/` |
| Figuras memoria | Regenerables | `Entrega/Figuras/` |
| Este changelog | **Mantener al día** | `CHANGELOG.md` |

### 2.2 Código — juego

| Elemento | Estado | Notas |
|----------|--------|-------|
| Lanzador consola | OK | `Juego/juego_consola.py` |
| Lanzador gráfico | Avanzado | `Juego/juego_grafico.py` + `Juego/Grafico/` |
| Paquete `Comun/` | OK | Dominio compartido + historia/resistencia/ranking |
| Paquete `Consola/` | OK | UI terminal, modos, informes, feedback |
| Tests + CI | OK | `python -m unittest discover -s Tests -q` |

### 2.3 Datos y mantenimiento

| Elemento | Estado | Notas |
|----------|--------|-------|
| `Data/CSV/Preguntas.csv` | Cerrado 480 ítems | Revisión manual completada; `mantenimiento.py validar` |
| `JSON/plantillas.json` | OK | Pool beta 1289 entradas |
| `JSON/presets_historia.json` | OK | Catálogo modo historia |
| `JSON/preguntas_resistencia.json` | OK | Exclusivas resistencia |
| `duplicados.py revisar` | OK | 0 pares similares (2026-06-15) |
| `simulacion_evaluacion_azar.py` | OK | Validación motor ante respuestas al azar |

---

## 3. Feedback del tutor

Registro consolidado de comentarios del tutor (incorporados en la memoria).

Leyenda: ✅ aplicado · 🔄 parcial · ⏳ pendiente

### 3.1 Estructura y redacción de la memoria

| Comentario | Estado | Dónde se reflejó |
|------------|--------|------------------|
| Marco teórico en **Introducción** | ✅ | `Memoria_TFG.md` §1.5 |
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
| Escape room narrativo | Baja | En [`CHECKLIST.md`](CHECKLIST.md) |
| Revisión final Word → PDF | Alta | En [`CHECKLIST.md`](CHECKLIST.md) |
| Pares similares CSV/plantillas | ✅ | 2026-06-15 |

---

## 4. Changelog (por sesión)

Añade una fila al cerrar cada bloque de trabajo relevante.

| Fecha | Ámbito | Cambio |
|-------|--------|--------|
| 2026-06-18 | Gráfico | Barra de estado: chips emoji (⏰/⏱️), resistencia con 📝 #N y 🔥 racha; sin récord fantasma |
| 2026-06-18 | Repo | Limpieza: tests fusionados, `Revision/` y `Entrega/exportar_memoria.py` eliminados; JSON runtime en `.gitignore` |
| 2026-06-18 | Juego | Resistencia: reto del día, hitos, apuestas, maldiciones, bloques, Cambio; tests reorganizados (238) |
| 2026-06-18 | Docs | Eliminado PDF anotado del tutor; repo sin PDFs versionados |
| 2026-06-18 | Docs | Renombrados `BITACORA.md` → `CHANGELOG.md` y `TAREAS.md` → `CHECKLIST.md` |
| 2026-06-18 | Docs | Eliminada carpeta `Revision/` y `revision_manual_banco.md`; checklist unificado |
| 2026-06-17 | Gráfico | Historia y resistencia pygame; tooltips; wizard libre |
| 2026-06-17 | Tests | Suite inicial **177** tests (reorganizada junio 2026 → **238**) |
| 2026-06-15 | Banco | 0 pares similares; dedup plantillas (1289) |
| 2026-06-15 | Repo | CI GitHub Actions; tests en `Tests/` |
| 2026-06-11 | Repo | Carpeta `Revision/`; PDF comentarios gitignored |
| 2026-06-11 | Memoria | Exportación Word; figuras; Monte Carlo §5.7 |

---

## 5. Comprobaciones rápidas

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/simulacion_evaluacion_azar.py
python -m unittest discover -s Tests -q
python Entrega/generar_figuras_memoria.py
python exportar_memoria.py
```

---

## 6. Cómo actualizar

1. **Comentarios del tutor** → filas en **§3**; changelog en **§4**.
2. **Código o datos** → **§2** + línea en **§4**; ajustar **§1** si cambia el panorama.
3. **Tarea cerrada o nueva** → [`CHECKLIST.md`](CHECKLIST.md) (borrar o añadir ítems).
4. Cambiar la fecha de **Última actualización** al inicio.
