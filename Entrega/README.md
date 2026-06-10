# Entrega — memoria TFG (PDF y LaTeX)

Ficheros de la memoria académica listos para entregar o imprimir. El borrador de trabajo en Markdown permanece en la raíz: [`../Memoria_TFG.md`](../Memoria_TFG.md).

| Fichero | Descripción |
|---------|-------------|
| `Memoria_TFG.tex` | Fuente LaTeX maquetada (versión de entrega) |
| `Memoria_TFG_latex.pdf` | PDF generado desde LaTeX |
| `Memoria_TFG_markdown.pdf` | PDF generado desde `Memoria_TFG.md` |
| `exportar_informe_pdf.py` | Regenera ambos PDF |

`Memoria_TFG.md` y `Memoria_TFG.tex` se mantienen **a mano**; no hay conversión automática entre ellos.

## Regenerar los PDF

Desde la raíz del proyecto:

```bash
python Entrega/exportar_informe_pdf.py
```

Opciones:

| Opción | Efecto |
|--------|--------|
| `--solo-latex` | Solo `Memoria_TFG_latex.pdf` |
| `--solo-markdown` | Solo `Memoria_TFG_markdown.pdf` |
| `--motor xelatex` | Motor LaTeX (por defecto: el primero disponible entre xelatex, pdflatex, lualatex) |
| `--solo-limpiar` | Borra auxiliares LaTeX (`.aux`, `.log`, …) sin compilar |

## Requisitos

- **LaTeX:** MiKTeX o TeX Live con `xelatex` en el PATH (`winget install MiKTeX.MiKTeX`).
- **Markdown → PDF:** `pip install markdown xhtml2pdf`.

En Windows, cierra el PDF en el visor antes de recompilar si el fichero está abierto (bloqueo de escritura).

Los auxiliares de compilación se ignoran en git (ver `.gitignore`).
