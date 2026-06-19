#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades locales del TFG: limpieza de temporales y exportación de la memoria.

Por defecto ejecuta **ambas** tareas (desde la raíz del proyecto):

  python utilidades_tfg.py

Solo una tarea:

  python utilidades_tfg.py --solo-limpieza
  python utilidades_tfg.py --solo-memoria

Limpieza (ver también ``Juego/Comun/borrar_temporales.py``):

  python utilidades_tfg.py --solo-limpieza --dry-run
  python utilidades_tfg.py --solo-limpieza --solo-pycache

Memoria (requiere Pandoc; figuras en ``Docs/Figuras/``):

  python utilidades_tfg.py --solo-memoria --solo-markdown
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent
if str(_ROOT / "Juego") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Juego"))

from Comun.borrar_temporales import main as main_limpieza  # noqa: E402

DOCS = _ROOT / "Docs"
ENTREGA = DOCS / "Entrega"
FIGURAS = DOCS / "Figuras"
MD = ENTREGA / "Memoria_TFG.md"
TEX = ENTREGA / "Memoria_TFG.tex"
DOCX_MD = ENTREGA / "Memoria_TFG_markdown.docx"
DOCX_LATEX = ENTREGA / "Memoria_TFG_latex.docx"


def _rel(p: Path) -> Path | str:
    try:
        return p.relative_to(_ROOT)
    except ValueError:
        return p


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
        cwd=entrada.parent,
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
            "  Aviso: faltan figuras en Docs/Figuras/: "
            + ", ".join(faltan)
            + "\n  Ejecuta: python Docs/generar_figuras_memoria.py",
            file=sys.stderr,
        )


def ejecutar_exportacion(
    *,
    solo_markdown: bool = False,
    solo_latex: bool = False,
) -> int:
    hacer_md = not solo_latex
    hacer_tex = not solo_markdown
    errores = 0

    _avisar_si_faltan_figuras()

    if hacer_md:
        print("Markdown → Word")
        print(f"  Origen: {_rel(MD)}")
        try:
            exportar_docx_markdown()
            print(f"  DOCX:   {_rel(DOCX_MD)}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1
        print()

    if hacer_tex:
        print("LaTeX → Word")
        print(f"  Origen: {_rel(TEX)}")
        try:
            exportar_docx_latex()
            print(f"  DOCX:   {_rel(DOCX_LATEX)}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1

    return 1 if errores else 0


def _argv_limpieza(args: argparse.Namespace) -> list[str]:
    argv: list[str] = []
    if args.dry_run:
        argv.append("--dry-run")
    if args.solo_pycache:
        argv.append("--solo-pycache")
    elif args.solo_juego:
        argv.append("--solo-juego")
    elif args.solo_txt:
        argv.append("--solo-txt")
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Limpia artefactos temporales y/o exporta la memoria a Word."
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--solo-limpieza",
        action="store_true",
        help="Solo limpieza (__pycache__, datos locales en Data/Juego/)",
    )
    modo.add_argument(
        "--solo-memoria",
        action="store_true",
        help="Solo exportación Word (Markdown y LaTeX → .docx)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Limpieza: listar sin borrar (no afecta a la exportación)",
    )
    grupo_limpieza = parser.add_mutually_exclusive_group()
    grupo_limpieza.add_argument("--solo-pycache", action="store_true", help="Limpieza: solo __pycache__")
    grupo_limpieza.add_argument("--solo-juego", action="store_true", help="Limpieza: solo JSON en Data/Juego/")
    grupo_limpieza.add_argument("--solo-txt", action="store_true", help="Limpieza: solo .txt en Data/Juego/")

    grupo_memoria = parser.add_mutually_exclusive_group()
    grupo_memoria.add_argument("--solo-markdown", action="store_true", help="Memoria: solo Word desde Markdown")
    grupo_memoria.add_argument("--solo-latex", action="store_true", help="Memoria: solo Word desde LaTeX")

    args = parser.parse_args(argv)

    filtros_limpieza = args.solo_pycache or args.solo_juego or args.solo_txt
    filtros_memoria = args.solo_markdown or args.solo_latex
    hacer_limpieza = args.solo_limpieza or filtros_limpieza or not (args.solo_memoria or filtros_memoria)
    hacer_memoria = args.solo_memoria or filtros_memoria or not (args.solo_limpieza or filtros_limpieza)

    if args.solo_limpieza:
        hacer_memoria = False
    if args.solo_memoria:
        hacer_limpieza = False

    codigo = 0

    if hacer_limpieza:
        print("=== Limpieza de temporales ===\n")
        codigo = max(codigo, main_limpieza(_argv_limpieza(args)))
        if hacer_memoria:
            print()

    if hacer_memoria:
        print("=== Exportación de memoria ===\n")
        codigo = max(
            codigo,
            ejecutar_exportacion(
                solo_markdown=args.solo_markdown,
                solo_latex=args.solo_latex,
            ),
        )

    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
