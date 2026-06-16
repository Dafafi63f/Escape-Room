# Estado del proyecto — TFG MATCAD

Documento **vivo**: resume progreso, feedback del tutor y pendientes. Actualízalo al cerrar cada bloque de trabajo (memoria, código, datos, scripts).

**Última actualización:** 2026-06-15
**Alumno:** Daniel Fageda Figueredo · **Tutor:** Víctor Navas Portella

| Enlace | Uso |
|--------|-----|
| [`Memoria_TFG.md`](../Memoria_TFG.md) | Borrador académico (editar aquí primero) |
| [`Entrega/`](../Entrega/README.md) | `Memoria/` (LaTeX + Word ×2), `Figuras/`; PDF manual desde Word |
| [`revision_manual_banco.md`](revision_manual_banco.md) | Detalle tramo a tramo del banco 480 ítems |
| PDF anotado del tutor | `Revision/Memoria_TFG_latex_Comentarios_VNP.pdf` (local, gitignored) |

Regenerar figuras: `python Entrega/generar_figuras_memoria.py` · Word: `python Entrega/exportar_memoria.py`

---

## 1. Resumen ejecutivo

| Área | Estado | Notas |
|------|--------|-------|
| **Memoria** | En revisión con tutor | Estructura académica (intro + hipótesis contrastables + resultados); Word desde MD/LaTeX regenerables; PDF de entrega manual |
| **Banco de preguntas** | Cerrado | 480/480 revisadas; `Preguntas.csv` protegido (`TFG_PERMITIR_CSV=1` para escribir) |
| **Juego (consola)** | Operativo | 3 modos: libre, historia, feedback; referencia funcional completa |
| **Juego (gráfico)** | En desarrollo | Rama `feature/juego-grafico-pygame`; modo libre v1; coexistencia con terminal |
| **Scripts mantenimiento** | Operativo | `Files/Scripts/mantenimiento.py`; `utils_plantillas_core.py` compartido con el juego |
| **CI / pruebas** | Operativo | GitHub Actions; suite `Tests/` (74 tests) |
| **Interfaz gráfica / narrativa** | En desarrollo | Pygame v1; migración futura: solo gráfico, borrar UI terminal |
| **Piloto con usuarios** | No realizado | Trabajo futuro (motivación / SUS) |

**Entregable actual:** juego en consola (completo) + versión gráfica en desarrollo + banco 480 preguntas + herramientas de validación. Objetivo: paridad gráfica → retirar terminal.

---

## 2. Progreso por componente

### 2.1 Documentación

| Elemento | Estado | Ubicación |
|----------|--------|-----------|
| Memoria Markdown | Actualizada | `Memoria_TFG.md` |
| Memoria LaTeX | Sincronizada con MD (manual) | `Entrega/Memoria/Memoria_TFG.tex` |
| Word desde Markdown | Regenerable | `Entrega/Memoria/Memoria_TFG_markdown.docx` |
| Word desde LaTeX | Regenerable | `Entrega/Memoria/Memoria_TFG_latex.docx` |
| Figuras memoria | Regenerables | `Entrega/Figuras/` |
| README raíz / carpetas | OK | `README.md`, `Juego/`, `Data/`, `Files/`, `Tests/`, `Entrega/` |
| Este estado | **Mantener al día** | `Revision/ESTADO.md` |

### 2.2 Código — juego

| Elemento | Estado | Notas |
|----------|--------|-------|
| Lanzador consola | OK | `Juego/juego_consola.py` |
| Paquete `Comun/` | OK | Dominio compartido (modelos, datos, reglas, motor, pool) |
| Paquete `Consola/` | OK | UI terminal, modos, informes, feedback |
| Tests unitarios | OK | `python -m unittest discover -s Tests -v` → 57 tests (`Tests/Juego/` + `Tests/Scripts/`) |
| CI | OK | `.github/workflows/tests.yml` — Python 3.14 |
| Build `.exe` | Opcional | `Juego/build_exe_onefile.ps1` |

### 2.3 Datos y mantenimiento (`Files/`)

| Elemento | Estado | Notas |
|----------|--------|-------|
| `Data/Preguntas.csv` | Cerrado 480 ítems | Ver [`revision_manual_banco.md`](revision_manual_banco.md) |
| `listado_materias.csv` | OK | 40 materias, metadatos curriculares |
| `plantillas.json` | OK | Pool beta **1289** entradas (modos 2–3 del juego) |
| Histórico calificaciones | OK | Modo historia |
| `mantenimiento.py validar` | OK | Balance estructural |
| `auditar-distractores` | OK | Salida consola |
| `duplicados.py revisar` | OK | **0 pares similares** en CSV y plantillas intra-materia (2026-06-15) |
| `simulacion_evaluacion_azar.py` | **Nuevo** | Validación motor: azar ≈ 25 % aciertos, nota ≈ 2,5/10 |

---

## 3. Feedback del tutor — seguimiento

Fuente principal: `Revision/Memoria_TFG_latex_Comentarios_VNP.pdf` + comentarios generales sobre estructura TFG.

Leyenda: ✅ aplicado en memoria/código · 🔄 parcial · ⏳ pendiente

### 3.1 Estructura y redacción de la memoria

| Comentario | Estado | Dónde se reflejó |
|------------|--------|------------------|
| Marco teórico dentro de la **Introducción** | ✅ | `Memoria_TFG.md` §1.5; `Entrega/Memoria/Memoria_TFG.tex` |
| Añadir **resumen / abstract** | ✅ | Resumen al inicio de memoria + abstract LaTeX |
| Definir gamificación, narrativa, banco auditable, distractores | ✅ | §1.2 + §1.5.6 |
| Objetivos: estado de cumplimiento en **Discusión**, no en §2 | ✅ | Tabla en §6.1 |
| «Estado actual» en **Resultados**, no en intro | ✅ | §5.2 |
| Título: **juego interactivo** (no videojuego) | ✅ | Portada MD/LaTeX con título académico + nota escape room |
| Maquetación tabla arquitectura (LaTeX / Word) | ✅ | `Entrega/Memoria/Memoria_TFG.tex` §4.3: `tabularx`, módulos en líneas separadas |
| Exportación Word (×2) para maquetación manual | ✅ | `exportar_memoria.py` → Markdown + LaTeX; PDF manual desde Word |
| Explicar **evaluación del jugador** en el texto (no solo README) | ✅ | Tabla en §4.3 |
| Hipótesis **contrastables**; motivación sin datos → futuro | ✅ | H1–H3; motivación en §6.6 |
| Tablas/gráficos organización curricular (4×2×5, grupos) | ✅ | §5.3 |
| Bibliografía (ediciones, DOI Gee/Prensky, Biggs 2022) | ✅ | §8 |
| Suavizar frase sobre recursos del grado | ✅ | §1.1 |
| Citar serious games / ansiedad-motivación con fuentes | ✅ | §1.1, §1.5 |

### 3.2 Contenido técnico y validación

| Comentario | Estado | Dónde se reflejó |
|------------|--------|------------------|
| H3/H4: contrastar con histórico de calificaciones | ✅ | §5.6; `generador_examen_historia.py` |
| Simulación automática respuestas al azar | ✅ | §5.7; `simulacion_evaluacion_azar.py` |
| Más contenido matemático / estadístico | 🔄 | Simulación + índice dificultad; piloto usuarios ⏳ |
| Diagramas arquitectura en metodología | ✅ | Tabla capas §4.3 |
| Clarificar si Pygame se usó | ✅ | §5.2: no utilizado |

### 3.3 Pendiente de tutor / entrega

| Tema | Prioridad | Acción sugerida |
|------|-----------|-----------------|
| Piloto con estudiantes (SUS, motivación) | Media | Diseño en §6.6; ejecutar si hay tiempo |
| Capa gráfica / escape room | Baja (futuro) | Fuera del alcance actual |
| Sustituir pares similares en CSV y plantillas | ✅ | Resuelto 2026-06-15 — ver [`revision_manual_banco.md`](revision_manual_banco.md) |
| Revisión final Word → PDF (maquetación) | Alta antes de entregar | Editar `.docx`, exportar PDF y leer completo |

---

## 4. Registro de cambios (bitácora)

Añade una fila al cerrar cada sesión de trabajo relevante.

| Fecha | Ámbito | Cambio |
|-------|--------|--------|
| 2026-06-15 | Banco | 0 pares similares CSV/plantillas; sustituciones Ids 21,25,72,83,125,298,322; dedup plantillas (1289) |
| 2026-06-15 | Código | `utils_plantillas_core.py`; rutas lazy; carga única CSV en `main()`; split `entrada_teclas.py` |
| 2026-06-15 | Repo | Tests en `Tests/` (51); CI GitHub Actions; `borrar_temporales.py` acotado; `requirements-dev.txt` |
| 2026-06-11 | Código | `simulacion_evaluacion_azar.py`; docstring/tutorial en `juego_consola.py` |
| 2026-06-11 | Repo | Carpeta `Revision/`; PDF comentarios gitignored; `ESTADO.md` creado |
| 2026-06-11 | Repo | `revision_manual_banco.md` movido desde `Data/` a `Revision/` |
| 2026-06-11 | Memoria | Título académico en portada MD/LaTeX (ya no «Memoria TFG» genérico) |
| 2026-06-11 | Memoria | Tabla arquitectura §4.3 corregida en LaTeX; apéndice H → `Revision/` |
| 2026-06-11 | Entrega | Flujo Word: `exportar_memoria.py`; eliminados PDF automáticos y `exportar_informe_pdf.py` |
| 2026-06-11 | Docs | README raíz/Entrega/Revision alineados con exportación Word + PDF manual |
| 2026-06-11 | Entrega | `Memoria/` + `Figuras/`; `generar_figuras_memoria.py`; §5.7 matemático y 4 gráficos |
| 2026-06-11 | Memoria | Prosa §1.2/§6; sin `---` en MD; figuras y Monte Carlo formalizado |

---

## 5. Pendientes abiertos (todas las áreas)

### Memoria
- [x] Tabla arquitectura §4.3 sin solapamiento (fuente LaTeX corregida)
- [x] Flujo de entrega: dos Word + PDF manual desde Word
- [ ] Editar maquetación en Word y exportar PDF de entrega
- [ ] Releer el PDF final completo antes de entregar
- [ ] Confirmar con tutor si la estructura actual es aceptable antes de pulir redacción

### Banco / `Files/`
- [x] 3 pares similares en CSV (modo seguro) — sustituidos 2026-06-15 (Ids 21, 72, 298, 322; + mejoras 25, 125, 83)
- [x] Pares intra-materia en plantillas beta — 0 tras dedup 2026-06-15 (pool 1289)
- [ ] Campos `Materias_relacionadas` / `Prerequisitos` (evolución esquema)

### Juego / repo
- [x] Refactor entrada teclado (`entrada_teclas.py`) y módulo compartido de plantillas
- [x] Suite de tests unificada + CI
- [ ] GUI / narrativa (OE1, OE4)
- [ ] Piloto usabilidad con estudiantes del grado

### Comprobaciones rápidas

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/simulacion_evaluacion_azar.py
python -m unittest discover -s Tests -q
python Entrega/generar_figuras_memoria.py
python Entrega/exportar_memoria.py
```

---

## 6. Cómo actualizar este fichero

1. Tras recibir comentarios del tutor: copia el PDF a `Revision/` y añade filas en **§3**.
2. Tras cambios de código o datos: actualiza **§2** y una línea en **§4**.
3. Al cerrar tareas: marca **§5** y ajusta el resumen **§1**.
4. Cambia la fecha de **Última actualización** al inicio.

No dupliques aquí el detalle del banco (Ids 1–480): sigue en [`revision_manual_banco.md`](revision_manual_banco.md).
