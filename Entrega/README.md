# Entrega — memoria TFG

Estructura:

| Carpeta / fichero | Contenido |
|-------------------|-----------|
| [`Memoria/`](Memoria/README.md) | LaTeX, Word (×2) |
| [`Figuras/`](Figuras/README.md) | Imágenes insertadas en la memoria |
| `exportar_memoria.py` | Regenera los dos `.docx` en `Memoria/` |
| `generar_figuras_memoria.py` | Regenera las figuras en `Figuras/` |

El borrador Markdown está en la raíz: [`../Memoria_TFG.md`](../Memoria_TFG.md).

`Memoria_TFG.md` y `Memoria/Memoria_TFG.tex` se mantienen **a mano**; no hay conversión automática entre ellos.

## Regenerar figuras

```bash
python Entrega/generar_figuras_memoria.py
```

Requisito: `matplotlib` (`pip install matplotlib`).

## Regenerar Word

Desde la raíz del proyecto:

```bash
python Entrega/exportar_memoria.py
```

| Opción | Efecto |
|--------|--------|
| *(sin opciones)* | Ambos `.docx` en `Memoria/` |
| `--solo-markdown` | Solo `Memoria_TFG_markdown.docx` |
| `--solo-latex` | Solo `Memoria_TFG_latex.docx` |

## Requisitos

- [Pandoc](https://pandoc.org/) en el PATH (`winget install JohnMacFarlane.Pandoc`).

Cierra Word antes de regenerar si el `.docx` está abierto.

Los PDF de **entrega** los generas tú desde Word tras editar la maquetación.

Los PDF con **comentarios del tutor** no van aquí: [`../Revision/`](../Revision/ESTADO.md).
