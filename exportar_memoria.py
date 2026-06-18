#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las dos memorias en Word desde Markdown y LaTeX.

Salida en ``Entrega/Memoria/``; fuentes:

  - ``Memoria_TFG_markdown.docx`` ← ``Memoria_TFG.md``
  - ``Memoria_TFG_latex.docx``    ← ``Entrega/Memoria/Memoria_TFG.tex``

Requisitos: Pandoc (``winget install JohnMacFarlane.Pandoc``). Figuras en
``Entrega/Figuras/`` (regenerar antes si faltan:
``python Entrega/generar_figuras_memoria.py``).

El PDF de entrega lo exportas tú desde Word tras editar.

Uso (desde la raíz del TFG):

  python Entrega/generar_figuras_memoria.py   # opcional, si cambiaron datos o gráficos
  python exportar_memoria.py
  python exportar_memoria.py --solo-markdown
  python exportar_memoria.py --solo-latex
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
ENTREGA = ROOT / "Entrega"
MEMORIA = ENTREGA / "Memoria"
FIGURAS = ENTREGA / "Figuras"
MD = ROOT / "Memoria_TFG.md"
TEX = MEMORIA / "Memoria_TFG.tex"
DOCX_MD = MEMORIA / "Memoria_TFG_markdown.docx"
DOCX_LATEX = MEMORIA / "Memoria_TFG_latex.docx"


def _rel(p: Path) -> Path | str:
    try:
        return p.relative_to(ROOT)
    except ValueError:
        return p


def _rel_entrega(p: Path) -> Path | str:
    try:
        return p.relative_to(ENTREGA)
    except ValueError:
        return _rel(p)


def _pandoc(entrada: Path, salida: Path, *, formato_entrada: str) -> None:
    if not entrada.is_file():
        raise FileNotFoundError(f"No existe {entrada}")
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError(
            "No se encontró pandoc en el PATH.\n"
            "Instálalo: winget install JohnMacFarlane.Pandoc"
        )
    salida.unlink(missing_ok=True)
    cmd = [
        pandoc,
        str(entrada),
        "-o",
        str(salida),
        f"--from={formato_entrada}",
        "--to=docx",
    ]
    resultado = subprocess.run(
        cmd,
        cwd=entrada.parent if entrada.parent != ENTREGA else ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falló pandoc ({entrada.name} → {salida.name}).\n"
            f"{(resultado.stderr or '') + (resultado.stdout or '')}"
        )
    if not salida.is_file():
        raise RuntimeError(f"No se generó el DOCX esperado: {salida}")


def exportar_docx_markdown(destino: Path = DOCX_MD) -> None:
    _pandoc(MD, destino, formato_entrada="markdown")


def exportar_docx_latex(destino: Path = DOCX_LATEX) -> None:
    _pandoc(TEX, destino, formato_entrada="latex")


def _avisar_si_faltan_figuras() -> None:
    esperadas = (
        "arquitectura_sistema.png",
        "flujo_modo_historia.png",
        "monte_carlo_histograma_notas.png",
        "monte_carlo_convergencia.png",
    )
    faltan = [n for n in esperadas if not (FIGURAS / n).is_file()]
    if faltan:
        print(
            "  Aviso: faltan figuras en Entrega/Figuras/: "
            + ", ".join(faltan)
            + "\n  Ejecuta: python Entrega/generar_figuras_memoria.py",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera Memoria_TFG_markdown.docx y Memoria_TFG_latex.docx."
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--solo-markdown", action="store_true", help="Solo Word desde Markdown")
    grupo.add_argument("--solo-latex", action="store_true", help="Solo Word desde LaTeX")
    args = parser.parse_args(argv)

    hacer_md = not args.solo_latex
    hacer_tex = not args.solo_markdown
    errores = 0

    _avisar_si_faltan_figuras()

    if hacer_md:
        print("Markdown → Word")
        print(f"  Origen: {_rel(MD)}")
        try:
            exportar_docx_markdown()
            print(f"  DOCX:   Entrega/{_rel_entrega(DOCX_MD)}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1
        print()

    if hacer_tex:
        print("LaTeX → Word")
        print(f"  Origen: {_rel(TEX)}")
        try:
            exportar_docx_latex()
            print(f"  DOCX:   Entrega/{_rel_entrega(DOCX_LATEX)}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1

    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
