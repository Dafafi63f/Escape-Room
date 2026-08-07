#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades de distribución del juego: zips, esquemas y limpieza.

Flujo por defecto (**limpiar → zips de distribución**):

  python Docs/utilidades_distribucion.py

1. Limpia temporales (__pycache__, runtime del juego).
2. Crea ``MATCAD_juego_portable.zip`` y ``MATCAD_juego_minimal.zip``, **solo si cambió**
   el contenido empaquetado.

Solo una fase:

  python Docs/utilidades_distribucion.py --solo-limpieza
  python Docs/utilidades_distribucion.py --esquemas-juego
  python Docs/utilidades_distribucion.py --solo-zip

Atajos:

  python Docs/utilidades_distribucion.py --sin-zip           # no generar zips
  python Docs/utilidades_distribucion.py --forzar-zip        # reconstruir ambos zips

Limpieza (ver también ``Files/borrar_temporales.py``):

  python Docs/utilidades_distribucion.py --solo-limpieza --dry-run
  python Docs/utilidades_distribucion.py --solo-limpieza --solo-pycache
"""

from __future__ import annotations

import argparse
import shutil
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
JUEGO = _ROOT / "Juego"
DISTRIBUCION = JUEGO / "Distribucion"
DATA = _ROOT / "Data"
CHANGELOG_JUEGO = DOCS / "CHANGELOG_JUEGO.md"
ZIP_PORTABLE = DISTRIBUCION / "MATCAD_juego_portable.zip"
ZIP_MINIMAL = DISTRIBUCION / "MATCAD_juego_minimal.zip"
SCRIPT_ZIP_MINIMAL = JUEGO / "Scripts" / "crear_zip_minimal.py"

_ZIP_CARPETAS = (DATA, JUEGO)
_ZIP_EXCLUIR_DIRNAMES = frozenset({"__pycache__", "build", "dist"})
_ZIP_EXCLUIR_FICHEROS = frozenset({
    "juego_grafico.spec",
    "MATCAD_juego_portable.zip",
    "MATCAD_juego_minimal.zip",
    ".matcad-paquete-minimo",
    "creador_privado.json",
})
_ZIP_EXCLUIR_SUFIJOS = (".spec", ".pyc", ".ps1", ".exe")

# En Juego/: solo Comun/, Grafico/ y ficheros en la raíz (no Scripts/ ni Distribucion/).
_ZIP_JUEGO_EXCLUIR_DIRNAMES = frozenset({"Scripts", "Distribucion"})

# Duplicados en Juego/ que se publican en la raíz del zip (como el paquete mínimo).
_ZIP_JUEGO_DUPLICADOS_EN_RAIZ = frozenset({
    "LEEME.txt",
    "COMO_JUGAR.md",
    "Distribucion/Jugar.bat",
})

_JUGAR_BAT_RAIZ = """\
@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 Juego\\juego_grafico.py
    goto :fin
)

where python >nul 2>&1
if %errorlevel%==0 (
    python Juego\\juego_grafico.py
    goto :fin
)

echo.
echo No se encontro Python en el PATH.
echo Instala Python 3.10+ y ejecuta:
echo   pip install -r Juego\\requirements.txt
echo   python Juego\\juego_grafico.py
echo.
echo Lee LEEME.txt en esta carpeta.
echo.

:fin
if errorlevel 1 pause
"""


def _texto_leeme_portable_raiz() -> str:
    ruta = JUEGO / "LEEME.txt"
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe {ruta}")
    texto = ruta.read_text(encoding="utf-8")
    return (
        texto.replace("Juego\\Distribucion\\Jugar.bat", "Jugar.bat")
        .replace("Juego/Distribucion/Jugar.bat", "Jugar.bat")
        .replace(
            "Debes ver Data\\ y la carpeta Juego\\ (con LEEME.txt y COMO_JUGAR.md).",
            "Debes ver Data\\, Juego\\, LEEME.txt y COMO_JUGAR.md en esta carpeta.",
        )
    )


def _texto_como_jugar_portable_raiz() -> str:
    ruta = JUEGO / "COMO_JUGAR.md"
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe {ruta}")
    texto = ruta.read_text(encoding="utf-8")
    return (
        texto.replace("Juego/Distribucion/Jugar.bat", "Jugar.bat")
        .replace("Juego\\Distribucion\\Jugar.bat", "Jugar.bat")
        .replace("Lee [`LEEME.txt`](LEEME.txt).", "Lee LEEME.txt (esta carpeta).")
    )


def _escribir_entradas_raiz_zip_portable(zf: zipfile.ZipFile) -> None:
    """LEEME, guía, changelog y Jugar.bat en la raíz (misma idea que el zip mínimo)."""
    zf.writestr("LEEME.txt", _texto_leeme_portable_raiz())
    zf.writestr("COMO_JUGAR.md", _texto_como_jugar_portable_raiz())
    zf.writestr("Jugar.bat", _JUGAR_BAT_RAIZ)
    if CHANGELOG_JUEGO.is_file():
        zf.writestr("CHANGELOG_JUEGO.md", CHANGELOG_JUEGO.read_text(encoding="utf-8"))


def _entradas_regeneracion_zip_portable() -> list[Path]:
    """Fuentes del zip portable (árbol + textos de la raíz)."""
    from Comun.rutas import resolver_config_creador_privado

    entradas = [ruta for ruta, _ in _iterar_ficheros_zip_portable()]
    entradas.extend(
        p for p in (JUEGO / "LEEME.txt", JUEGO / "COMO_JUGAR.md", CHANGELOG_JUEGO) if p.is_file()
    )
    privado = resolver_config_creador_privado()
    if privado is not None:
        entradas.append(privado)
    entradas.append(Path(__file__).resolve())
    return entradas


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


def _zip_necesita_regeneracion(destino: Path) -> tuple[bool, str]:
    if not destino.is_file():
        return True, f"aún no existe {destino.name}"
    destino_mtime = _mtime(destino)
    for ruta in _entradas_regeneracion_zip_portable():
        if _mtime(ruta) > destino_mtime + 1e-6:
            return True, f"cambió {_rel(ruta)}"
    return False, ""


def _cargar_crear_zip_minimal():
    import importlib.util

    spec = importlib.util.spec_from_file_location("crear_zip_minimal", SCRIPT_ZIP_MINIMAL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {SCRIPT_ZIP_MINIMAL}")
    mod = importlib.util.module_from_spec(spec)
    prev_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev_bytecode
    return mod


def _zip_minimal_necesita_regeneracion(destino: Path) -> tuple[bool, str]:
    if not destino.is_file():
        return True, f"aún no existe {destino.name}"
    mod = _cargar_crear_zip_minimal()
    destino_mtime = _mtime(destino)
    for ruta in mod.entradas_zip_minimal():
        if not ruta.is_file():
            return True, f"falta {_rel(ruta)}"
        if _mtime(ruta) > destino_mtime + 1e-6:
            return True, f"cambió {_rel(ruta)}"
    return False, ""


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


def _limpiar_artefactos_build_legacy(*, dry_run: bool = False) -> bool:
    """Elimina restos antiguos de empaquetado (build/, dist/, *.spec) si existen."""
    borrado = False
    for carpeta in (JUEGO / "build", JUEGO / "dist"):
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


def ejecutar_limpieza_final(args: argparse.Namespace) -> int:
    argv = _argv_limpieza(args)
    print("=== Limpieza final ===\n")
    codigo = main_limpieza(argv)
    if _limpieza_tiene_filtro(argv):
        return codigo

    print()
    print("--- Restos build (Juego/) ---\n")
    _limpiar_artefactos_build_legacy(dry_run=args.dry_run)
    return codigo


def ejecutar_esquemas_juego() -> int:
    from Comun.persistencia import texto_referencia_datos_juego

    print(texto_referencia_datos_juego())
    return 0


def _planificar_tareas(args: argparse.Namespace) -> tuple[bool, bool]:
    """limpieza, zip."""
    filtros_limpieza = args.solo_pycache or args.solo_juego or args.solo_txt
    solo_limpieza = args.solo_limpieza or filtros_limpieza

    if args.solo_zip:
        return False, True
    if solo_limpieza:
        return True, not args.sin_zip
    return True, not args.sin_zip


def _excluir_del_zip_portable(ruta: Path, base: Path) -> bool:
    if not ruta.is_file():
        return True
    if ruta.name in _ZIP_EXCLUIR_FICHEROS:
        return True
    if base == DATA:
        from Comun.persistencia import es_fichero_runtime_juego

        rel = ruta.relative_to(DATA)
        if rel.parts and rel.parts[0] in ("Juego", "Privado"):
            return True
        if es_fichero_runtime_juego(ruta.name):
            return True
        if ruta.suffix.lower() == ".xlsx":
            return True
    if base == JUEGO:
        rel = ruta.relative_to(JUEGO)
        if rel.parts and rel.parts[0] in _ZIP_JUEGO_EXCLUIR_DIRNAMES:
            return True
        if rel.as_posix() in _ZIP_JUEGO_DUPLICADOS_EN_RAIZ:
            return True
    return ruta.suffix.lower() in _ZIP_EXCLUIR_SUFIJOS


def _iterar_ficheros_zip_portable() -> list[tuple[Path, str]]:
    """Pares (ruta_absoluta, nombre_dentro_del_zip) para Data/ y Juego/ (Comun, Grafico, raíz)."""
    entradas: list[tuple[Path, str]] = []
    for base in _ZIP_CARPETAS:
        if not base.is_dir():
            raise FileNotFoundError(f"No existe la carpeta necesaria: {base}")
        for ruta in sorted(base.rglob("*")):
            if not ruta.is_file():
                continue
            if any(part in _ZIP_EXCLUIR_DIRNAMES for part in ruta.relative_to(base).parts):
                continue
            if _excluir_del_zip_portable(ruta, base):
                continue
            entradas.append((ruta, f"{base.name}/{ruta.relative_to(base).as_posix()}"))
    entradas.sort(key=lambda par: par[1].lower())
    return entradas


def crear_zip_juego_portable(destino: Path = ZIP_PORTABLE) -> Path:
    """Empaqueta el juego para Python (sin .ps1 ni artefactos de build)."""
    if destino.exists():
        destino.unlink()
    ficheros = _iterar_ficheros_zip_portable()
    destino.parent.mkdir(parents=True, exist_ok=True)
    from Comun.feedback import escribir_creador_privado_en_zip, mensaje_aviso_smtp_zip

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".matcad-paquete-completo", "MATCAD paquete completo\n")
        _escribir_entradas_raiz_zip_portable(zf)
        for ruta, arcname in ficheros:
            zf.write(ruta, arcname)
        if escribir_creador_privado_en_zip(zf):
            print("  SMTP feedback: incluido (Data/Privado/creador_privado.json)")
        else:
            aviso = mensaje_aviso_smtp_zip()
            if aviso:
                print(f"  {aviso}")
    return destino


def ejecutar_zip_portable(destino: Path = ZIP_PORTABLE, *, force: bool = False) -> int:
    print("=== Zip portable (Python) ===\n")
    print("  Contenido: Data/, Juego/Comun/, Juego/Grafico/, raíz de Juego/, LEEME.txt, COMO_JUGAR.md, CHANGELOG_JUEGO.md y Jugar.bat en la raíz")
    print("  Excluye: Juego/Scripts/, Juego/Distribucion/, Data/Juego/, Data/Privado/, runtime del jugador en Data/, .ps1, .spec, build/, dist/, __pycache__, zip previo, .exe")
    print("  Requisito: Python 3.10+ en el PC destino (ver LEEME.txt en la raíz del zip)")
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
    print("    1. Descomprimir el zip y leer LEEME.txt")
    print("    2. pip install -r Juego/requirements.txt")
    print("    3. doble clic en Jugar.bat   (o python Juego/juego_grafico.py)")
    return 0


def ejecutar_zip_minimal(destino: Path = ZIP_MINIMAL, *, force: bool = False) -> int:
    print("=== Zip mínimo (Python) ===\n")
    print("  Contenido: Juego/ (código + CHANGELOG_JUEGO.md), Data/Preguntas.csv, Jugar.bat, LEEME.txt")
    print("  Excluye: Data/, Scripts/, Distribucion/, escape room, presets completos")
    print("  Requisito: Python 3.10+ en el PC destino (ver LEEME.txt dentro del zip)")
    try:
        mod = _cargar_crear_zip_minimal()
        motivo = ""
        if not force:
            necesita, motivo = _zip_minimal_necesita_regeneracion(destino)
            if not necesita:
                tam_kb = destino.stat().st_size / 1024
                print(f"  Sin cambios relevantes; se reutiliza {_rel(destino)} ({tam_kb:.0f} KiB)")
                print("  (usa --forzar-zip para reconstruir desde cero)")
                return 0
        if force:
            print("  Modo: reconstrucción forzada")
        elif motivo:
            print(f"  Motivo: {motivo}")
        salida, n_csv = mod.crear_zip_minimal(destino)
        n_py = sum(1 for _, n in mod._iter_codigo_juego() if n.endswith(".py"))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"  Error:  {exc}", file=sys.stderr)
        return 1
    tam_kb = salida.stat().st_size / 1024
    print(f"  Módulos Python: {n_py}")
    print(f"  CSV: Data/Preguntas.csv ({n_csv} preguntas)")
    print(f"  ZIP: {_rel(salida)} ({tam_kb:.0f} KiB)")
    print()
    print("  En el PC destino:")
    print("    1. Descomprimir en una carpeta (p. ej. MATCAD_minimal/)")
    print("    2. pip install -r Juego/requirements.txt")
    print("    3. Jugar.bat   (o python Juego/juego_grafico.py)")
    return 0


def ejecutar_zips(*, force: bool = False) -> int:
    codigo = ejecutar_zip_portable(force=force)
    print()
    return max(codigo, ejecutar_zip_minimal(force=force))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Limpia temporales del repo y crea los zips de distribución del juego."
        )
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--solo-limpieza",
        action="store_true",
        help="Solo limpieza final (sin regenerar zips salvo que no pases --sin-zip)",
    )
    modo.add_argument(
        "--esquemas-juego",
        action="store_true",
        help="Muestra esquemas de Data/Juego/ (preferencias, estadísticas, …)",
    )
    modo.add_argument(
        "--solo-zip",
        action="store_true",
        help="Solo crear MATCAD_juego_portable.zip y MATCAD_juego_minimal.zip",
    )

    parser.add_argument(
        "--sin-zip",
        action="store_true",
        help="No crear los zips en Juego/Distribucion/ al final",
    )
    parser.add_argument(
        "--forzar-zip",
        action="store_true",
        help="Reconstruir ambos zips aunque no haya cambios en Data/ ni Juego/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Limpieza: listar sin borrar",
    )
    grupo_limpieza = parser.add_mutually_exclusive_group()
    grupo_limpieza.add_argument("--solo-pycache", action="store_true", help="Limpieza: solo __pycache__")
    grupo_limpieza.add_argument("--solo-juego", action="store_true", help="Limpieza: solo JSON runtime en Data/Juego/")
    grupo_limpieza.add_argument("--solo-txt", action="store_true", help="Limpieza: solo .txt en Data/Juego/")

    args = parser.parse_args(argv)
    if args.esquemas_juego:
        return ejecutar_esquemas_juego()

    hacer_limpieza, crear_zip = _planificar_tareas(args)

    codigo = 0

    if hacer_limpieza:
        codigo = max(codigo, ejecutar_limpieza_final(args))

    if crear_zip:
        if hacer_limpieza:
            print()
        codigo = max(codigo, ejecutar_zips(force=args.forzar_zip))

    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
