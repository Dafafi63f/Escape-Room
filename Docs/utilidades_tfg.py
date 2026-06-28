#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades locales del TFG: regeneración y limpieza del proyecto.

Flujo por defecto (**regenerar todo → limpiar → zip portable**):

  python Docs/utilidades_tfg.py

1. Regenera figuras PNG en ``Docs/Figuras/``, **solo si cambió** el script, datos o simulaciones.
2. Exporta la memoria a Word (Markdown y LaTeX → .docx), **solo si cambió** el origen.
3. Regenera ``juego_grafico.exe``, **solo si cambió** código/datos del juego.
4. Limpia temporales (__pycache__, runtime del juego, intermedios de Entrega/, PyInstaller).
5. Crea ``MATCAD_juego_portable.zip``, **solo si cambió** el contenido empaquetado.

También puedes ejecutar solo figuras:

  python Docs/generar_figuras_memoria.py
  python Docs/utilidades_tfg.py --solo-figuras

**Regeneración incremental:** cada artefacto compara fechas de modificación con sus entradas.
Si el resultado ya existe y está al día, se reutiliza (segunda ejecución mucho más rápida).
Forzar reconstrucción: ``--forzar-figuras``, ``--forzar-memoria``, ``--forzar-exe``, ``--forzar-zip``.
Omitir figuras en el flujo completo: ``--sin-figuras``.

Los artefactos regenerados (``.exe``, zip portable, ``.docx`` de memoria) se versionan en el repositorio.

Solo una fase:

  python Docs/utilidades_tfg.py --solo-memoria
  python Docs/utilidades_tfg.py --solo-figuras
  python Docs/utilidades_tfg.py --solo-exe
  python Docs/utilidades_tfg.py --solo-limpieza
  python Docs/utilidades_tfg.py --solo-zip

Atajos:

  python Docs/utilidades_tfg.py --sin-exe           # memoria sin .exe (más rápido)
  python Docs/utilidades_tfg.py --sin-figuras       # no regenerar PNG (usa los existentes)
  python Docs/utilidades_tfg.py --sin-zip           # no generar zip portable
  python Docs/utilidades_tfg.py --forzar-figuras    # reconstruir PNG aunque no haya cambios
  python Docs/utilidades_tfg.py --forzar-memoria    # reconstruir .docx aunque no haya cambios
  python Docs/utilidades_tfg.py --forzar-exe        # reconstruir .exe aunque no haya cambios
  python Docs/utilidades_tfg.py --forzar-zip        # reconstruir zip aunque no haya cambios
  python Docs/utilidades_tfg.py --conservar-cache-exe  # no borrar Juego/build/ tras el build
  python Docs/utilidades_tfg.py --solo-memoria --con-exe
  python Docs/utilidades_tfg.py --solo-memoria --solo-markdown

Limpieza (ver también ``Files/borrar_temporales.py``):

  python Docs/utilidades_tfg.py --solo-limpieza --dry-run
  python Docs/utilidades_tfg.py --solo-limpieza --solo-pycache
  python Docs/utilidades_tfg.py --solo-limpieza --solo-entrega
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_DOCS = Path(__file__).resolve().parent
_ROOT = _DOCS.parent
if str(_ROOT / "Juego") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Juego"))
if str(_ROOT / "Files") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Files"))

import borrar_temporales  # noqa: E402

main_limpieza = borrar_temporales.main

DOCS = _DOCS
ENTREGA = DOCS / "Entrega"
FIGURAS = DOCS / "Figuras"
JUEGO = _ROOT / "Juego"
DISTRIBUCION = JUEGO / "Distribucion"
BUILD_PS1 = JUEGO / "Scripts" / "build_exe_onefile.ps1"
EXE_SALIDA = DISTRIBUCION / "juego_grafico.exe"
FILES = _ROOT / "Files"
DATA = _ROOT / "Data"
CHANGELOG_JUEGO = DOCS / "CHANGELOG_JUEGO.md"
GENERAR_FIGURAS = DOCS / "generar_figuras_memoria.py"
REQUIREMENTS_JUEGO = JUEGO / "requirements.txt"
ZIP_PORTABLE = DISTRIBUCION / "MATCAD_juego_portable.zip"
MD = ENTREGA / "Memoria_TFG.md"
TEX = ENTREGA / "Memoria_TFG.tex"
DOCX_MD = ENTREGA / "Memoria_TFG_markdown.docx"
DOCX_LATEX = ENTREGA / "Memoria_TFG_latex.docx"
DOCX_REF = ENTREGA / "pandoc_reference.docx"
DOCX_REF_DEFAULT = ENTREGA / "pandoc_reference_default.docx"

_LATEX_TEMP_ENTREGA = (
    "*.aux",
    "*.log",
    "*.out",
    "*.toc",
    "*.fls",
    "*.fdb_latexmk",
    "*.synctex.gz",
)

_ARTEFACTOS_ENTREGA_INTERMEDIOS_FIJOS = (
    DOCX_REF,
    DOCX_REF_DEFAULT,
    ENTREGA / "pandoc_reference.tmp.docx",
)

_ARTEFACTOS_ENTREGA_SALIDA = (
    DOCX_MD,
    DOCX_LATEX,
)

_ZIP_CARPETAS = (DATA, JUEGO)
_ZIP_EXCLUIR_DIRNAMES = frozenset({"__pycache__", "build", "dist", "Scripts"})
_ZIP_EXCLUIR_FICHEROS = frozenset({
    "juego_grafico.exe",
    "juego_grafico.spec",
    "MATCAD_juego_portable.zip",
})
_ZIP_EXCLUIR_SUFIJOS = (".spec", ".pyc", ".ps1", ".exe")


def _listar_ficheros_existentes(candidatos: list[Path]) -> list[Path]:
    vistos: set[Path] = set()
    existentes: list[Path] = []
    for ruta in candidatos:
        resuelta = ruta.resolve()
        if resuelta in vistos or not ruta.is_file():
            continue
        vistos.add(resuelta)
        existentes.append(ruta)
    return sorted(existentes, key=lambda p: p.name.lower())


def _candidatos_entrega_intermedios() -> list[Path]:
    candidatos = list(_ARTEFACTOS_ENTREGA_INTERMEDIOS_FIJOS)
    for patron in _LATEX_TEMP_ENTREGA:
        candidatos.extend(ENTREGA.glob(patron))
    return candidatos


def _candidatos_entrega_todos_regenerables() -> list[Path]:
    return [
        *_ARTEFACTOS_ENTREGA_SALIDA,
        *_candidatos_entrega_intermedios(),
    ]


def _limpiar_ficheros(
    candidatos: list[Path],
    *,
    dry_run: bool = False,
    vacio: str | None = "  (nada que borrar)",
) -> bool:
    artefactos = _listar_ficheros_existentes(candidatos)
    for ruta in artefactos:
        prefijo = "[dry-run] " if dry_run else ""
        print(f"  {prefijo}{_rel(ruta)}")
        if not dry_run:
            ruta.unlink()
    if not artefactos and vacio is not None:
        print(vacio)
    return bool(artefactos)


def _limpiar_entrega_pycache(*, dry_run: bool = False) -> bool:
    cache = ENTREGA / "__pycache__"
    if not cache.is_dir():
        return False
    prefijo = "[dry-run] " if dry_run else ""
    print(f"  {prefijo}{_rel(cache)}/")
    if not dry_run:
        shutil.rmtree(cache)
    return True


def limpiar_artefactos_entrega_intermedios(*, dry_run: bool = False) -> int:
    """Borra plantilla Pandoc, ``__pycache__`` local y restos LaTeX de ``Docs/Entrega/``."""
    borrado = _limpiar_ficheros(
        _candidatos_entrega_intermedios(),
        dry_run=dry_run,
        vacio=None,
    )
    borrado = _limpiar_entrega_pycache(dry_run=dry_run) or borrado
    if not borrado:
        print("  (nada que borrar)")
    return 0


def limpiar_entrega_generada(*, dry_run: bool = False) -> int:
    """Borra todos los artefactos regenerables de ``Docs/Entrega/`` (incluye los .docx)."""
    borrado = _limpiar_ficheros(
        _candidatos_entrega_todos_regenerables(),
        dry_run=dry_run,
        vacio=None,
    )
    borrado = _limpiar_entrega_pycache(dry_run=dry_run) or borrado
    if not borrado:
        print("  (nada que borrar)")
    return 0


def _borrar_cache_pyinstaller(*, dry_run: bool = False) -> bool:
    """Borra Juego/build/ si existe (caché incremental de PyInstaller)."""
    build_dir = JUEGO / "build"
    if not build_dir.is_dir():
        return False
    prefijo = "[dry-run] " if dry_run else ""
    print(f"  {prefijo}{_rel(build_dir)}/")
    if not dry_run:
        shutil.rmtree(build_dir)
    return True


def _limpiar_artefactos_pyinstaller(
    *,
    dry_run: bool = False,
    conservar_cache: bool = False,
) -> bool:
    borrado = False
    carpetas: list[Path] = [JUEGO / "build", JUEGO / "dist"] if not conservar_cache else [JUEGO / "dist"]
    for carpeta in carpetas:
        if not carpeta.is_dir():
            continue
        prefijo = "[dry-run] " if dry_run else ""
        print(f"  {prefijo}{_rel(carpeta)}/")
        if not dry_run:
            shutil.rmtree(carpeta)
        borrado = True
    for spec in sorted(JUEGO.glob("*.spec")):
        prefijo = "[dry-run] " if dry_run else ""
        print(f"  {prefijo}{_rel(spec)}")
        if not dry_run:
            spec.unlink()
        borrado = True
    if not borrado:
        print("  (nada que borrar)")
    return borrado


def _rel(p: Path) -> Path | str:
    try:
        return p.relative_to(_ROOT)
    except ValueError:
        return p


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _mtime_max(rutas: list[Path]) -> float:
    return max((_mtime(r) for r in rutas), default=0.0)


def _cargar_generador_figuras():
    import importlib.util

    spec = importlib.util.spec_from_file_location("generar_figuras_memoria", GENERAR_FIGURAS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {GENERAR_FIGURAS}")
    mod = importlib.util.module_from_spec(spec)
    prev_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev_bytecode
    return mod


def _entradas_png_memoria() -> list[Path]:
    if not FIGURAS.is_dir():
        return []
    return sorted(p for p in FIGURAS.glob("*.png") if p.is_file())


def _entradas_memoria_markdown() -> list[Path]:
    entradas = [MD, ENTREGA / "preparar_plantilla_pandoc.py", ENTREGA / "ajustar_word_memoria.py"]
    entradas.extend(_entradas_png_memoria())
    return [p for p in entradas if p.is_file()]


def _entradas_memoria_latex() -> list[Path]:
    entradas = [TEX, ENTREGA / "preparar_plantilla_pandoc.py", ENTREGA / "ajustar_word_memoria.py"]
    entradas.extend(_entradas_png_memoria())
    return [p for p in entradas if p.is_file()]


def _docx_necesita_regeneracion(destino: Path, entradas: list[Path]) -> tuple[bool, str]:
    if not destino.is_file():
        return True, f"aún no existe {destino.name}"
    destino_mtime = _mtime(destino)
    for ruta in entradas:
        if _mtime(ruta) > destino_mtime + 1e-6:
            return True, f"cambió {_rel(ruta)}"
    return False, ""


def _zip_necesita_regeneracion(destino: Path) -> tuple[bool, str]:
    if not destino.is_file():
        return True, f"aún no existe {destino.name}"
    destino_mtime = _mtime(destino)
    for ruta, _ in _iterar_ficheros_zip_portable():
        if _mtime(ruta) > destino_mtime + 1e-6:
            return True, f"cambió {_rel(ruta)}"
    return False, ""


def _plantilla_pandoc() -> Path:
    import importlib.util

    ruta = ENTREGA / "preparar_plantilla_pandoc.py"
    spec = importlib.util.spec_from_file_location("preparar_plantilla_pandoc", ruta)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {ruta}")
    mod = importlib.util.module_from_spec(spec)
    prev_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
        mod.crear_plantilla_memoria(destino=DOCX_REF)
    finally:
        sys.dont_write_bytecode = prev_bytecode
    if not DOCX_REF.is_file():
        raise RuntimeError(f"No se generó la plantilla Pandoc: {DOCX_REF}")
    return DOCX_REF


def _cargar_ajustar_word():
    import importlib.util

    ruta = ENTREGA / "ajustar_word_memoria.py"
    spec = importlib.util.spec_from_file_location("ajustar_word_memoria", ruta)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {ruta}")
    mod = importlib.util.module_from_spec(spec)
    prev_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev_bytecode
    return mod


def _pandoc(
    entradas: list[Path],
    salida: Path,
    *,
    formato_entrada: str,
    indice_pandoc: bool = True,
    reordenar_portada: bool = True,
) -> None:
    if not entradas:
        raise ValueError("Se requiere al menos un fichero de entrada para Pandoc.")
    for entrada in entradas:
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
        *[str(p.resolve().as_posix()) for p in entradas],
        "-o",
        str(salida),
        f"--from={formato_entrada}",
        "--to=docx",
        "--number-sections",
        "-M",
        "toc-title=Índice",
        "-M",
        "lang=es",
        f"--reference-doc={_plantilla_pandoc()}",
    ]
    if indice_pandoc:
        idx = cmd.index("--number-sections")
        cmd[idx:idx] = ["--toc", "--toc-depth=2"]
    resultado = subprocess.run(
        cmd,
        cwd=entradas[0].parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falló pandoc ({', '.join(p.name for p in entradas)} → {salida.name}).\n"
            f"{(resultado.stderr or '') + (resultado.stdout or '')}"
        )
    if not salida.is_file():
        raise RuntimeError(f"No se generó el DOCX esperado: {salida}")
    if reordenar_portada and indice_pandoc:
        ajustar = _cargar_ajustar_word()
        if not ajustar.ajustar_portada_indice(salida):
            print(
                f"  Aviso: no se pudo reordenar portada/índice en {salida.name}",
                file=sys.stderr,
            )


def exportar_docx_markdown(destino: Path = DOCX_MD) -> None:
    _pandoc(
        [MD],
        destino,
        formato_entrada="markdown+yaml_metadata_block+tex_math_dollars",
    )


def exportar_docx_latex(destino: Path = DOCX_LATEX) -> None:
    _pandoc(
        [TEX],
        destino,
        formato_entrada="latex",
    )


def _avisar_si_faltan_figuras() -> None:
    try:
        mod = _cargar_generador_figuras()
        esperadas = mod.FIGURAS_SALIDA
    except RuntimeError:
        esperadas = (
            "monte_carlo_histograma_notas.png",
            "monte_carlo_convergencia.png",
            "pity_curva_probabilidad.png",
        )
    faltan = [n for n in esperadas if not (FIGURAS / n).is_file()]
    if faltan:
        print(
            "  Aviso: faltan figuras en Docs/Figuras/: "
            + ", ".join(faltan)
            + "\n  Ejecuta: python Docs/utilidades_tfg.py --solo-figuras",
            file=sys.stderr,
        )


def ejecutar_figuras_memoria(*, force: bool = False) -> int:
    print("=== Figuras de memoria ===\n")
    try:
        mod = _cargar_generador_figuras()
    except RuntimeError as exc:
        print(f"  Error:  {exc}", file=sys.stderr)
        return 1

    motivo = ""
    if not force:
        necesita, motivo = mod.figuras_necesitan_regeneracion()
        if not necesita:
            print(
                f"  Sin cambios relevantes; se reutilizan {len(mod.FIGURAS_SALIDA)} PNG "
                f"en {_rel(FIGURAS)}/"
            )
            print("  (usa --forzar-figuras para reconstruir desde cero)")
            return 0

    codigo, _ = mod.generar_todas_figuras(force=force, imprimir_stats=True)
    return codigo


def ejecutar_exportacion(
    *,
    solo_markdown: bool = False,
    solo_latex: bool = False,
    force: bool = False,
) -> int:
    hacer_md = not solo_latex
    hacer_tex = not solo_markdown
    errores = 0

    _avisar_si_faltan_figuras()

    if hacer_md:
        print("Markdown → Word")
        print(f"  Origen: {_rel(MD)}")
        entradas_md = _entradas_memoria_markdown()
        motivo_md = ""
        if not force:
            necesita, motivo_md = _docx_necesita_regeneracion(DOCX_MD, entradas_md)
            if not necesita:
                print(f"  Sin cambios relevantes; se reutiliza {_rel(DOCX_MD)}")
                print("  (usa --forzar-memoria para reconstruir desde cero)")
        if force or motivo_md or not DOCX_MD.is_file():
            if force:
                print("  Modo: reconstrucción forzada")
            elif motivo_md:
                print(f"  Motivo: {motivo_md}")
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
        entradas_tex = _entradas_memoria_latex()
        motivo_tex = ""
        if not force:
            necesita, motivo_tex = _docx_necesita_regeneracion(DOCX_LATEX, entradas_tex)
            if not necesita:
                print(f"  Sin cambios relevantes; se reutiliza {_rel(DOCX_LATEX)}")
                print("  (usa --forzar-memoria para reconstruir desde cero)")
        if force or motivo_tex or not DOCX_LATEX.is_file():
            if force:
                print("  Modo: reconstrucción forzada")
            elif motivo_tex:
                print(f"  Motivo: {motivo_tex}")
            try:
                exportar_docx_latex()
                print(f"  DOCX:   {_rel(DOCX_LATEX)}")
            except (FileNotFoundError, RuntimeError) as exc:
                print(f"  Error:  {exc}", file=sys.stderr)
                errores += 1

    return 1 if errores else 0


def _iterar_entradas_exe() -> list[Path]:
    """Ficheros que invalidan el .exe si cambian tras la última compilación."""
    entradas: list[Path] = []
    fijos = (
        JUEGO / "juego_grafico.py",
        BUILD_PS1,
        REQUIREMENTS_JUEGO,
        CHANGELOG_JUEGO,
    )
    for ruta in fijos:
        if ruta.is_file():
            entradas.append(ruta)
    for carpeta, sufijo in (
        (JUEGO / "Comun", ".py"),
        (JUEGO / "Grafico", ".py"),
        (FILES, ".py"),
    ):
        if carpeta.is_dir():
            entradas.extend(p for p in carpeta.rglob(f"*{sufijo}") if p.is_file())
    if DATA.is_dir():
        entradas.extend(p for p in DATA.rglob("*") if p.is_file())
    return entradas


def _exe_necesita_regeneracion() -> tuple[bool, str]:
    if not EXE_SALIDA.is_file():
        return True, "aún no existe juego_grafico.exe"
    exe_mtime = EXE_SALIDA.stat().st_mtime
    for ruta in _iterar_entradas_exe():
        try:
            if ruta.stat().st_mtime > exe_mtime + 1e-6:
                return True, f"cambió {_rel(ruta)}"
        except OSError:
            return True, f"cambió {_rel(ruta)}"
    return False, ""


def _powershell_ejecutable() -> Path:
    candidatos = (
        shutil.which("powershell"),
        shutil.which("powershell.exe"),
        shutil.which("pwsh"),
        shutil.which("pwsh.exe"),
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    )
    for candidato in candidatos:
        if not candidato:
            continue
        ruta = Path(candidato)
        if ruta.is_file():
            return ruta
    raise RuntimeError(
        "No se encontró PowerShell en el PATH.\n"
        "Instálalo o ejecuta manualmente: .\\Juego\\Scripts\\build_exe_onefile.ps1"
    )


def regenerar_exe(*, force: bool = False) -> None:
    if sys.platform != "win32":
        raise RuntimeError(
            "La generación del .exe solo está soportada en Windows (PyInstaller)."
        )
    motivo = ""
    if not force:
        necesita, motivo = _exe_necesita_regeneracion()
        if not necesita:
            print("PyInstaller → ejecutable")
            print(f"  Sin cambios relevantes; se reutiliza {_rel(EXE_SALIDA)}")
            print("  (usa --forzar-exe para reconstruir desde cero)")
            if _borrar_cache_pyinstaller():
                print("  Caché PyInstaller (build/) eliminada para ahorrar espacio")
            return
    if not BUILD_PS1.is_file():
        raise FileNotFoundError(f"No existe {BUILD_PS1}")
    ps1 = BUILD_PS1.resolve()
    powershell = _powershell_ejecutable()
    print("PyInstaller → ejecutable")
    if force:
        print("  Modo: reconstrucción forzada")
    elif motivo:
        print(f"  Motivo: {motivo}")
    print(f"  Script: {_rel(ps1)}")
    print(f"  PowerShell: {powershell}")
    cmd = [
        str(powershell),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
    ]
    if force:
        cmd.append("-Force")
    try:
        resultado = subprocess.run(
            cmd,
            cwd=JUEGO,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise RuntimeError(
            f"No se pudo lanzar PowerShell para {ps1.name}: {exc}\n"
            f"Comando: {' '.join(cmd)}"
        ) from exc
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falló {ps1.name} (código {resultado.returncode}).\n"
            "Cierra juego_grafico.exe si está abierto y vuelve a intentarlo, "
            "o ejecuta manualmente:\n"
            f"  .\\Juego\\Scripts\\build_exe_onefile.ps1"
        )
    if not EXE_SALIDA.is_file():
        raise RuntimeError(
            f"No se generó el ejecutable esperado: {EXE_SALIDA}\n"
            f"Revisa la salida de {ps1.name}."
        )
    print(f"  EXE:    {_rel(EXE_SALIDA)}")


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


def _limpieza_tiene_filtro(argv: list[str]) -> bool:
    return any(
        flag in argv
        for flag in ("--solo-pycache", "--solo-juego", "--solo-txt")
    )


def ejecutar_limpieza_final(args: argparse.Namespace) -> int:
    if args.solo_entrega:
        print("=== Limpieza de artefactos regenerables (Docs/Entrega/) ===\n")
        return limpiar_entrega_generada(dry_run=args.dry_run)

    argv = _argv_limpieza(args)
    print("=== Limpieza final ===\n")
    codigo = main_limpieza(argv)
    if _limpieza_tiene_filtro(argv):
        return codigo

    print()
    print("--- Docs/Entrega/ (intermedios) ---\n")
    limpiar_artefactos_entrega_intermedios(dry_run=args.dry_run)
    print()
    print("--- PyInstaller (Juego/) ---\n")
    _limpiar_artefactos_pyinstaller(
        dry_run=args.dry_run,
        conservar_cache=args.conservar_cache_exe,
    )
    return codigo


def _planificar_tareas(
    args: argparse.Namespace,
) -> tuple[bool, bool, bool, bool, bool]:
    """memoria, figuras, exe, limpieza, zip."""
    filtros_limpieza = (
        args.solo_pycache or args.solo_juego or args.solo_txt or args.solo_entrega
    )
    solo_limpieza = args.solo_limpieza or filtros_limpieza

    if args.solo_figuras:
        return False, True, False, False, False
    if args.solo_zip:
        return False, False, False, False, True
    if solo_limpieza:
        return False, False, False, True, not args.sin_zip
    if args.solo_exe:
        return False, False, True, True, not args.sin_zip
    if args.solo_memoria:
        return (
            True,
            not args.sin_figuras,
            bool(args.con_exe),
            True,
            not args.sin_zip,
        )
    incluir_exe = not args.sin_exe
    if args.con_exe:
        incluir_exe = True
    return True, not args.sin_figuras, incluir_exe, True, not args.sin_zip


def _excluir_del_zip_portable(ruta: Path) -> bool:
    if not ruta.is_file():
        return True
    if ruta.name in _ZIP_EXCLUIR_FICHEROS:
        return True
    return ruta.suffix.lower() in _ZIP_EXCLUIR_SUFIJOS


def _iterar_ficheros_zip_portable() -> list[tuple[Path, str]]:
    """Pares (ruta_absoluta, nombre_dentro_del_zip) para Data/ y Juego/."""
    entradas: list[tuple[Path, str]] = []
    for base in _ZIP_CARPETAS:
        if not base.is_dir():
            raise FileNotFoundError(f"No existe la carpeta necesaria: {base}")
        for ruta in sorted(base.rglob("*")):
            if not ruta.is_file():
                continue
            if any(part in _ZIP_EXCLUIR_DIRNAMES for part in ruta.relative_to(base).parts):
                continue
            if _excluir_del_zip_portable(ruta):
                continue
            entradas.append((ruta, f"{base.name}/{ruta.relative_to(base).as_posix()}"))
    return entradas


def crear_zip_juego_portable(destino: Path = ZIP_PORTABLE) -> Path:
    """Empaqueta el juego para Python (sin .exe, .ps1 ni artefactos PyInstaller)."""
    if destino.exists():
        destino.unlink()
    ficheros = _iterar_ficheros_zip_portable()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for ruta, arcname in ficheros:
            zf.write(ruta, arcname)
    return destino


def ejecutar_zip_portable(destino: Path = ZIP_PORTABLE, *, force: bool = False) -> int:
    print("=== Zip portable (Python) ===\n")
    print("  Contenido: Data/, Juego/ (codigo, requirements, LEEME, COMO_JUGAR, Distribucion/), sin Scripts/")
    print("  Excluye: .exe, .ps1, .spec, build/, dist/, __pycache__, zip previo")
    print("  Requisito: Python 3.10+ en el PC destino (ver Juego/LEEME.txt)")
    try:
        motivo = ""
        if not force:
            necesita, motivo = _zip_necesita_regeneracion(destino)
            if not necesita:
                tam_mb = destino.stat().st_size / (1024 * 1024)
                print(f"  Sin cambios relevantes; se reutiliza {_rel(destino)} ({tam_mb:.1f} MiB)")
                print("  (usa --forzar-zip para reconstruir desde cero)")
                return 0
        if force:
            print("  Modo: reconstrucción forzada")
        elif motivo:
            print(f"  Motivo: {motivo}")
        ficheros = _iterar_ficheros_zip_portable()
        salida = crear_zip_juego_portable(destino)
    except FileNotFoundError as exc:
        print(f"  Error:  {exc}", file=sys.stderr)
        return 1
    tam_mb = salida.stat().st_size / (1024 * 1024)
    print(f"  Ficheros: {len(ficheros)}")
    print(f"  ZIP:      {_rel(salida)} ({tam_mb:.1f} MiB)")
    print()
    print("  En el PC destino:")
    print("    1. Descomprimir el zip y leer Juego/LEEME.txt")
    print("    2. pip install -r Juego/requirements.txt")
    print("    3. python Juego/juego_grafico.py   (o Juego/Distribucion/Jugar.bat)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenera artefactos del TFG (memoria, .exe en Windows), "
            "limpia temporales y crea zip portable al final."
        )
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--solo-limpieza",
        action="store_true",
        help="Solo limpieza final (sin regenerar memoria ni .exe)",
    )
    modo.add_argument(
        "--solo-memoria",
        action="store_true",
        help="Figuras (si aplica) + exportación Word; después, limpieza final",
    )
    modo.add_argument(
        "--solo-figuras",
        action="store_true",
        help="Solo regenerar PNG en Docs/Figuras/ (incremental)",
    )
    modo.add_argument(
        "--solo-exe",
        action="store_true",
        help="Solo regenerar Juego/Distribucion/juego_grafico.exe; después, limpieza final",
    )
    modo.add_argument(
        "--solo-zip",
        action="store_true",
        help="Solo crear Juego/Distribucion/MATCAD_juego_portable.zip (Data/, Juego/, …)",
    )

    parser.add_argument(
        "--sin-figuras",
        action="store_true",
        help="No regenerar Docs/Figuras/*.png (reutilizar las existentes)",
    )
    parser.add_argument(
        "--sin-exe",
        action="store_true",
        help="No regenerar juego_grafico.exe (por defecto sí se regenera)",
    )
    parser.add_argument(
        "--sin-zip",
        action="store_true",
        help="No crear Juego/Distribucion/MATCAD_juego_portable.zip al final",
    )
    parser.add_argument(
        "--forzar-figuras",
        action="store_true",
        help="Reconstruir Docs/Figuras/*.png aunque no hayan cambiado datos ni scripts",
    )
    parser.add_argument(
        "--forzar-memoria",
        action="store_true",
        help="Reconstruir los .docx aunque no hayan cambiado Memoria_TFG.md/.tex ni figuras",
    )
    parser.add_argument(
        "--forzar-exe",
        action="store_true",
        help="Reconstruir juego_grafico.exe aunque no haya cambios en el código o datos",
    )
    parser.add_argument(
        "--forzar-zip",
        action="store_true",
        help="Reconstruir MATCAD_juego_portable.zip aunque no haya cambios en Data/ ni Juego/",
    )
    parser.add_argument(
        "--conservar-cache-exe",
        action="store_true",
        help="No borrar Juego/build/ (por defecto se elimina para ahorrar espacio)",
    )
    parser.add_argument(
        "--con-exe",
        action="store_true",
        help="Con --solo-memoria, también regenera el .exe (por defecto ya se regenera)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Limpieza: listar sin borrar (no afecta a la regeneración)",
    )
    grupo_limpieza = parser.add_mutually_exclusive_group()
    grupo_limpieza.add_argument("--solo-pycache", action="store_true", help="Limpieza: solo __pycache__")
    grupo_limpieza.add_argument("--solo-juego", action="store_true", help="Limpieza: solo JSON runtime en Data/Juego/")
    grupo_limpieza.add_argument("--solo-txt", action="store_true", help="Limpieza: solo .txt en Data/Juego/")
    grupo_limpieza.add_argument(
        "--solo-entrega",
        action="store_true",
        help="Limpieza: todos los artefactos regenerables en Docs/Entrega/ (incluye .docx)",
    )

    grupo_memoria = parser.add_mutually_exclusive_group()
    grupo_memoria.add_argument("--solo-markdown", action="store_true", help="Memoria: solo Word desde Markdown")
    grupo_memoria.add_argument("--solo-latex", action="store_true", help="Memoria: solo Word desde LaTeX")

    args = parser.parse_args(argv)
    regenerar_memoria, regenerar_figuras, regenerar_exe_flag, hacer_limpieza, crear_zip = (
        _planificar_tareas(args)
    )

    codigo = 0

    if regenerar_figuras:
        codigo = max(codigo, ejecutar_figuras_memoria(force=args.forzar_figuras))

    if regenerar_memoria:
        if regenerar_figuras:
            print()
        print("=== Exportación de memoria ===\n")
        codigo = max(
            codigo,
            ejecutar_exportacion(
                solo_markdown=args.solo_markdown,
                solo_latex=args.solo_latex,
                force=args.forzar_memoria,
            ),
        )

    if regenerar_exe_flag:
        if regenerar_memoria or regenerar_figuras:
            print()
        print("=== Regeneración del ejecutable ===\n")
        try:
            regenerar_exe(force=args.forzar_exe)
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"  Error:  {exc}", file=sys.stderr)
            codigo = max(codigo, 1)

    if hacer_limpieza:
        if regenerar_memoria or regenerar_figuras or regenerar_exe_flag:
            print()
        codigo = max(codigo, ejecutar_limpieza_final(args))

    if crear_zip:
        if regenerar_memoria or regenerar_figuras or regenerar_exe_flag or hacer_limpieza:
            print()
        codigo = max(codigo, ejecutar_zip_portable(force=args.forzar_zip))

    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
