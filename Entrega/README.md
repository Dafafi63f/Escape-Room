# Entrega — memoria TFG (Word y LaTeX)

Ficheros de la memoria académica. El borrador Markdown está en la raíz: [`../Memoria_TFG.md`](../Memoria_TFG.md).

| Fichero | Descripción |
|---------|-------------|
| `Memoria_TFG_markdown.docx` | Word desde `Memoria_TFG.md` (editar y exportar PDF manualmente) |
| `Memoria_TFG_latex.docx` | Word desde `Memoria_TFG.tex` (editar y exportar PDF manualmente) |
| `Memoria_TFG.tex` | Fuente LaTeX maquetada |
| `exportar_memoria.py` | Regenera los dos `.docx` |

`Memoria_TFG.md` y `Memoria_TFG.tex` se mantienen **a mano**; no hay conversión automática entre ellos.

## Regenerar Word

Desde la raíz del proyecto:

```bash
python Entrega/exportar_memoria.py
```

| Opción | Efecto |
|--------|--------|
| *(sin opciones)* | Ambos `.docx` |
| `--solo-markdown` | Solo `Memoria_TFG_markdown.docx` |
| `--solo-latex` | Solo `Memoria_TFG_latex.docx` |

## Requisitos

- [Pandoc](https://pandoc.org/) en el PATH (`winget install JohnMacFarlane.Pandoc`).

Cierra Word antes de regenerar si el `.docx` está abierto.

Los PDF de **entrega** los generas tú desde Word tras editar la maquetación.

Los PDF con **comentarios del tutor** no van aquí: [`../Revision/`](../Revision/ESTADO.md).
