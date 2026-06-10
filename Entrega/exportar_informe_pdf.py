#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera los dos PDF de la memoria: desde Markdown y desde LaTeX.

Fuentes y salida en ``Entrega/``; el Markdown de trabajo queda en la raíz:

  - ``Memoria_TFG_markdown.pdf`` ← ``../Memoria_TFG.md``
  - ``Memoria_TFG_latex.pdf``    ← ``Memoria_TFG.tex``

LaTeX: MiKTeX o TeX Live (``winget install MiKTeX.MiKTeX``).
Markdown: ``pip install markdown xhtml2pdf``.

Uso (desde la raíz del TFG):

  python Entrega/exportar_informe_pdf.py
  python Entrega/exportar_informe_pdf.py --solo-markdown
  python Entrega/exportar_informe_pdf.py --solo-latex
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent

MD = ROOT / "Memoria_TFG.md"
TEX = DIR / "Memoria_TFG.tex"
PDF_MD = DIR / "Memoria_TFG_markdown.pdf"
PDF_LATEX = DIR / "Memoria_TFG_latex.pdf"

AUXILIARES_LATEX = frozenset({".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".synctex.gz"})
MOTORES = ("xelatex", "pdflatex", "lualatex")

CSS_INFORME = """
@page { size: A4; margin: 2.2cm 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.45; }
h1 { font-size: 20pt; }
h2 { font-size: 15pt; }
h3 { font-size: 12.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 10pt; }
th, td { border: 1px solid #888; padding: 5px 8px; }
"""


def _rel(p: Path) -> Path | str:
    try:
        return p.relative_to(ROOT)
    except ValueError:
        return p


def _rel_entrega(p: Path) -> Path | str:
    try:
        return p.relative_to(DIR)
    except ValueError:
        return _rel(p)


def _detectar_motor(preferido: str | None) -> str:
    if preferido:
        if shutil.which(preferido):
            return preferido
        raise RuntimeError(f"No se encontró el motor LaTeX solicitado: {preferido}")
    for motor in MOTORES:
        if shutil.which(motor):
            return motor
    raise RuntimeError(
        "No hay motor LaTeX disponible (xelatex, pdflatex o lualatex).\n"
        "Instala MiKTeX o TeX Live y asegúrate de que el motor esté en el PATH."
    )


def _limpiar_auxiliares(directorio: Path, jobname: str) -> None:
    for sufijo in AUXILIARES_LATEX:
        (directorio / f"{jobname}{sufijo}").unlink(missing_ok=True)


def limpiar_auxiliares_entrega(directorio: Path = DIR) -> int:
    """Borra restos de compilación LaTeX en Entrega/ (.aux, .log, …)."""
    borrados = 0
    for sufijo in AUXILIARES_LATEX:
        for fichero in directorio.glob(f"*{sufijo}"):
            try:
                fichero.unlink()
                borrados += 1
            except OSError:
                pass
    return borrados


def _markdown_a_html(texto_md: str) -> str:
    import markdown

    cuerpo = markdown.markdown(
        texto_md,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        output_format="html5",
    )
    titulo = "Memoria TFG"
    primera = texto_md.strip().splitlines()
    if primera and primera[0].startswith("# "):
        titulo = primera[0].lstrip("# ").strip()
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>{titulo}</title>
<style>{CSS_INFORME}</style></head><body>{cuerpo}</body></html>"""


def exportar_pdf_markdown(destino: Path = PDF_MD) -> None:
    try:
        import markdown  # noqa: F401
        from xhtml2pdf import pisa
    except ImportError as exc:
        raise RuntimeError(
            "Para el PDF desde Markdown: pip install markdown xhtml2pdf"
        ) from exc
    if not MD.is_file():
        raise FileNotFoundError(f"No existe {MD}")
    html = _markdown_a_html(MD.read_text(encoding="utf-8"))
    with destino.open("wb") as f:
        estado = pisa.CreatePDF(html, dest=f, encoding="utf-8")
    if estado.err:
        raise RuntimeError(f"xhtml2pdf devolvió {estado.err} error(es)")


def compilar_latex_a_pdf(
    entrada: Path,
    salida: Path,
    *,
    motor: str,
    pasadas: int = 2,
    limpiar_aux: bool = True,
) -> None:
    if not entrada.is_file():
        raise FileNotFoundError(f"No existe el informe LaTeX: {entrada}")

    directorio = entrada.parent.resolve()
    jobname = salida.stem
    cmd = [
        motor,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-jobname={jobname}",
        entrada.name,
    ]

    ultimo_error = ""
    try:
        for _ in range(max(1, pasadas)):
            resultado = subprocess.run(
                cmd,
                cwd=directorio,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            ultimo_error = (resultado.stderr or "") + (resultado.stdout or "")
            if resultado.returncode != 0:
                log = directorio / f"{jobname}.log"
                pista_log = f"Revisa el .log en {log}\n\n" if log.is_file() else ""
                raise RuntimeError(
                    f"Falló la compilación con {motor}.\n"
                    f"{pista_log}"
                    f"{ultimo_error[-2000:]}"
                )

        pdf_generado = directorio / f"{jobname}.pdf"
        if not pdf_generado.is_file():
            raise RuntimeError(f"No se generó el PDF esperado: {pdf_generado}")

        destino = salida.resolve()
        if pdf_generado != destino:
            destino.unlink(missing_ok=True)
            shutil.move(str(pdf_generado), str(destino))
    finally:
        if limpiar_aux:
            _limpiar_auxiliares(directorio, jobname)


def exportar_pdf_latex(
    destino: Path = PDF_LATEX,
    *,
    motor: str | None = None,
    pasadas: int = 2,
    limpiar_aux: bool = True,
) -> str:
    motor_usado = _detectar_motor(motor)
    compilar_latex_a_pdf(
        TEX,
        destino,
        motor=motor_usado,
        pasadas=pasadas,
        limpiar_aux=limpiar_aux,
    )
    return motor_usado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera Memoria_TFG_markdown.pdf y Memoria_TFG_latex.pdf.")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--solo-markdown", action="store_true", help="Solo PDF desde Markdown")
    grupo.add_argument("--solo-latex", action="store_true", help="Solo PDF desde LaTeX")
    parser.add_argument("--motor", choices=MOTORES, default=None, help="Motor LaTeX")
    parser.add_argument("--pasadas", type=int, default=2, help="Pasadas del motor LaTeX")
    parser.add_argument("--sin-limpiar", action="store_true", help="Conservar .aux, .log, …")
    parser.add_argument(
        "--solo-limpiar",
        action="store_true",
        help="Solo borra auxiliares LaTeX en Entrega/ (sin generar PDF)",
    )
    args = parser.parse_args(argv)

    if args.solo_limpiar:
        n = limpiar_auxiliares_entrega()
        print(f"Auxiliares LaTeX borrados en Entrega/: {n}")
        return 0

    hacer_md = not args.solo_latex
    hacer_tex = not args.solo_markdown
    errores = 0

    if hacer_md:
        print("Markdown → PDF")
        print(f"  Origen: {_rel(MD)}")
        try:
            exportar_pdf_markdown()
            print(f"  PDF:    Entrega/{_rel_entrega(PDF_MD)}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1
        print()

    if hacer_tex:
        print("LaTeX → PDF")
        print(f"  Origen: {_rel(TEX)}")
        try:
            motor = exportar_pdf_latex(
                motor=args.motor,
                pasadas=args.pasadas,
                limpiar_aux=not args.sin_limpiar,
            )
            print(f"  PDF:    Entrega/{_rel_entrega(PDF_LATEX)}")
            print(f"  Motor:  {motor}")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            errores += 1

    if not args.sin_limpiar:
        restantes = limpiar_auxiliares_entrega()
        if restantes:
            print(f"Auxiliares LaTeX eliminados: {restantes}")

    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
