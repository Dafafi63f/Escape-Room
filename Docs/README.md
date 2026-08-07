# Documentación y entrega del TFG

Todo lo relacionado con la memoria, el seguimiento del proyecto y los artefactos de entrega.

## En la raíz de `Docs/`

| Fichero | Contenido |
|---------|-----------|
| [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) | Estado del TFG, feedback del tutor, historial técnico |
| [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md) | Novedades visibles para quien juega (hub Info del juego gráfico) |
| [`CHECKLIST.md`](CHECKLIST.md) | Pendientes e ideas futuras |
| [`RELEASE_1.0.md`](RELEASE_1.0.md) | Alcance de la entrega TFG (v1.0.0); continuación personal en v1.1.0+ |
| [`../Juego/COMO_JUGAR.md`](../Juego/COMO_JUGAR.md) | Requisitos para jugar (Python, zips, `Jugar.bat`) — ver también [`Juego/`](../Juego/README.md) |
| [`utilidades_tfg.py`](utilidades_tfg.py) | Memoria Word, limpieza y zips de distribución (incremental: reutiliza si no hay cambios) |
| [`generar_figuras_memoria.py`](generar_figuras_memoria.py) | Regenera PNG de datos (Monte Carlo, pity, catálogo Inka) |

## Subcarpetas (solo estas dos)

| Carpeta | Contenido |
|---------|-----------|
| [`Entrega/`](Entrega/) | Borrador Markdown, LaTeX y Word (`Memoria_TFG.*`) |
| [`Figuras/`](Figuras/) | Imágenes insertadas en la memoria |

## Comandos (desde la raíz del repo)

```bash
python Docs/utilidades_tfg.py                 # figuras + Word → limpieza → zip (incremental)
python Docs/utilidades_tfg.py --solo-memoria  # figuras + Word si hace falta
python Docs/utilidades_tfg.py --solo-figuras  # solo PNG
python Docs/utilidades_tfg.py --sin-figuras    # reutilizar PNG existentes
python Docs/utilidades_tfg.py --solo-zip       # zips portable + mínimo
```

**Incremental:** figuras (solo gráficos con datos), Word y zip se omiten si sus entradas no cambiaron.
Arquitectura, pipeline historia y comparación Inka ↔ TFG son **tablas** en la memoria, no PNG.
Forzar: `--forzar-figuras`, `--forzar-memoria`, `--forzar-zip`.
También: `python Docs/generar_figuras_memoria.py` (equivalente a `--solo-figuras`).

Salida Word: `Docs/Entrega/Memoria_TFG_markdown.docx` y `Memoria_TFG_latex.docx` (secciones numeradas, pie de página). Estructura de páginas:

1. **Página 1 — portada:** título, alumno/tutor, resumen y notas administrativas (fuera del índice).
2. **Página 2 — índice** (solo tabla de contenidos).
3. **Página 3 en adelante — memoria:** introducción y resto del trabajo.

Todo el borrador Markdown está en `Entrega/Memoria_TFG.md` (portada al inicio, antes de la introducción). Pandoc genera el índice y un script (`ajustar_word_memoria.py`) reordena portada → índice → cuerpo. Tras exportar, la limpieza final borra plantilla Pandoc, `__pycache__`, runtime del juego y restos de build en `Juego/`.

**Convención de tablas en la memoria:** las tablas numeradas (1–9) llevan pie en cursiva *debajo* (`*Tabla N. …*`, igual que las figuras). Las tablas auxiliares sin número (objetivos, reparto del banco, mecanismos del motor, etc.) usan solo un encabezado en negrita *antes* del grid, sin pie duplicado.

Al abrir el Word, Word debería pedir actualizar los campos; si no, pulsa **F9** (o clic derecho en el índice → *Actualizar campos*). El índice es un campo con enlaces a cada sección (no texto fijo).

El PDF de entrega lo exportas desde Word tras editar (fuera del repositorio).
