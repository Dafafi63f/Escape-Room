#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidad **externa**: elimina artefactos temporales y ficheros runtime del juego.

Política de limpieza (complemento de ``datos_locales_juego``)
--------------------------------------------------------------

Desde **fuera** (esta utilidad): borra del disco ``preferencias_*.json``,
``ranking_*.json`` y ``*.txt`` en ``Data/Juego/``, más ``__pycache__`` y cachés.
Al abrir el juego, los JSON de runtime se recrean.

Desde **dentro** del juego: solo ``datos_locales_juego`` — borra ``.txt`` y vacía
el contenido de preferencias y rankings (los ``.json`` se conservan).

CLI: ``python utilidades_tfg.py`` (o ``--solo-limpieza``; lógica en este módulo).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

_COMUN_DIR = Path(__file__).resolve().parent
_JUEGO_DIR = _COMUN_DIR.parent
_PROYECTO = _JUEGO_DIR.parent

_OMITIR_PARTES = frozenset({
    ".venv",
    "venv",
    ".git",
    "build",
    "dist",
    "node_modules",
})

_CARPETAS_CACHE_RAIZ = (
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".scannerwork",
)

__all__ = [
    "ResumenBorradoJson",
    "ResumenLimpieza",
    "borrar_temporales",
    "dir_data_juego",
    "eliminar_ficheros_runtime_juego",
    "listar_ficheros_runtime_juego",
    "main",
    "raiz_proyecto",
]


def raiz_proyecto() -> Path:
    return _PROYECTO


def dir_data_juego() -> Path:
    """``Data/Juego/`` resuelto desde la raíz del TFG (sin lógica del juego en ejecución)."""
    return raiz_proyecto() / "Data" / "Juego"


def listar_ficheros_runtime_juego() -> tuple[list[Path], list[Path], list[Path]]:
    """``(preferencias, rankings, txt)`` en ``Data/Juego/`` para borrado externo."""
    carpeta = dir_data_juego()
    if not carpeta.is_dir():
        return [], [], []
    preferencias = sorted(
        (
            *carpeta.glob("preferencias_grafico.json"),
            *carpeta.glob("preferencias_ranking.json"),
        )
    )
    rankings = sorted(p for p in carpeta.glob("ranking_*.json") if p.is_file())
    txt = sorted(p for p in carpeta.glob("*.txt") if p.is_file())
    return preferencias, rankings, txt


@dataclass
class ResumenBorradoTxt:
    borrados: int = 0
    errores: int = 0


@dataclass
class ResumenBorradoJson:
    preferencias: int = 0
    rankings: int = 0
    errores: int = 0

    @property
    def borrados(self) -> int:
        return self.preferencias + self.rankings


@dataclass
class ResumenLimpieza:
    pycache_borradas: int = 0
    pycache_errores: int = 0
    cache_herramientas_borradas: int = 0
    cache_herramientas_errores: int = 0
    txt_borrados: int = 0
    txt_errores: int = 0
    bytes_txt: int = 0
    json_preferencias_borrados: int = 0
    json_rankings_borrados: int = 0
    json_errores: int = 0
    bytes_json: int = 0

    @property
    def errores_totales(self) -> int:
        return (
            self.pycache_errores
            + self.cache_herramientas_errores
            + self.txt_errores
            + self.json_errores
        )


def eliminar_ficheros_runtime_juego() -> tuple[ResumenBorradoJson, ResumenBorradoTxt]:
    """Elimina del disco los ficheros runtime en ``Data/Juego/`` (solo utilidad externa)."""
    resumen_json = ResumenBorradoJson()
    resumen_txt = ResumenBorradoTxt()
    preferencias, rankings, txt = listar_ficheros_runtime_juego()

    for fichero in preferencias:
        try:
            fichero.unlink()
            resumen_json.preferencias += 1
        except OSError:
            resumen_json.errores += 1

    for fichero in rankings:
        try:
            fichero.unlink()
            resumen_json.rankings += 1
        except OSError:
            resumen_json.errores += 1

    for fichero in txt:
        try:
            fichero.unlink()
            resumen_txt.borrados += 1
        except OSError:
            resumen_txt.errores += 1

    return resumen_json, resumen_txt


def _dentro_de_omitidos(ruta: Path, raiz: Path) -> bool:
    try:
        relativa = ruta.relative_to(raiz)
    except ValueError:
        return True
    return any(parte in _OMITIR_PARTES for parte in relativa.parts)


def _formatear_tamano(bytes_total: int) -> str:
    if bytes_total < 1024:
        return f"{bytes_total} B"
    if bytes_total < 1024 * 1024:
        return f"{bytes_total / 1024:.1f} KiB"
    return f"{bytes_total / (1024 * 1024):.2f} MiB"


def listar_pycache(base: Path | None = None) -> list[Path]:
    raiz = base or raiz_proyecto()
    return sorted(
        p
        for p in raiz.rglob("__pycache__")
        if p.is_dir() and not _dentro_de_omitidos(p, raiz)
    )


def listar_cache_herramientas(base: Path | None = None) -> list[Path]:
    raiz = base or raiz_proyecto()
    return sorted(
        raiz / nombre
        for nombre in _CARPETAS_CACHE_RAIZ
        if (raiz / nombre).is_dir()
    )


def _eliminar_carpetas(carpetas: list[Path]) -> tuple[int, int]:
    borradas = 0
    errores = 0
    for carpeta in carpetas:
        try:
            shutil.rmtree(carpeta)
            borradas += 1
        except OSError:
            errores += 1
    return borradas, errores


def _eliminar_ficheros_txt(ficheros: list[Path], resumen: ResumenLimpieza) -> None:
    for fichero in ficheros:
        try:
            resumen.bytes_txt += fichero.stat().st_size
            fichero.unlink()
            resumen.txt_borrados += 1
        except OSError:
            resumen.txt_errores += 1


def _eliminar_ficheros_json(
    ficheros: list[Path],
    resumen: ResumenLimpieza,
    *,
    contador: str,
) -> None:
    for fichero in ficheros:
        try:
            resumen.bytes_json += fichero.stat().st_size
            fichero.unlink()
            setattr(resumen, contador, getattr(resumen, contador) + 1)
        except OSError:
            resumen.json_errores += 1


def borrar_temporales(
    base: Path | None = None,
    *,
    incluir_pycache: bool = True,
    incluir_txt: bool = True,
    incluir_json: bool = True,
) -> ResumenLimpieza:
    raiz = base or raiz_proyecto()
    resumen = ResumenLimpieza()

    if incluir_pycache:
        ok, err = _eliminar_carpetas(listar_pycache(raiz))
        resumen.pycache_borradas += ok
        resumen.pycache_errores += err
        ok, err = _eliminar_carpetas(listar_cache_herramientas(raiz))
        resumen.cache_herramientas_borradas += ok
        resumen.cache_herramientas_errores += err

    preferencias, rankings, txt = listar_ficheros_runtime_juego()

    if incluir_txt:
        _eliminar_ficheros_txt(txt, resumen)

    if incluir_json:
        _eliminar_ficheros_json(preferencias, resumen, contador="json_preferencias_borrados")
        _eliminar_ficheros_json(rankings, resumen, contador="json_rankings_borrados")

    return resumen


def _imprimir_rutas(titulo: str, rutas: list[Path]) -> bool:
    if not rutas:
        return False
    print(f"{titulo}: {len(rutas)} carpetas")
    for p in rutas:
        print(f" - {p}")
    return True


def _imprimir_listado(
    *,
    pycache: list[Path],
    cache_herramientas: list[Path],
    preferencias: list[Path],
    rankings: list[Path],
    txt: list[Path],
    incluir_pycache: bool,
    incluir_txt: bool,
    incluir_json: bool,
) -> bool:
    hay_algo = False

    if incluir_pycache:
        hay_algo |= _imprimir_rutas("__pycache__", pycache)
        hay_algo |= _imprimir_rutas("cachés de herramientas", cache_herramientas)

    if incluir_txt and txt:
        hay_algo = True
        bytes_total = sum(p.stat().st_size for p in txt)
        print(f".txt: {len(txt)} ficheros ({_formatear_tamano(bytes_total)})")
        for p in txt:
            print(f" - {p}")

    if incluir_json and (preferencias or rankings):
        hay_algo = True
        json_locales = [*preferencias, *rankings]
        bytes_total = sum(p.stat().st_size for p in json_locales)
        print(
            f"JSON runtime (se eliminarán): {len(json_locales)} ficheros "
            f"({_formatear_tamano(bytes_total)})"
        )
        for p in json_locales:
            print(f" - {p}")

    return hay_algo


def _configurar_stdout_utf8() -> None:
    if sys.platform != "win32":
        return
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def _parser_borrar_temporales() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Utilidad externa: borra __pycache__, cachés y elimina del disco los "
            "ficheros runtime en Data/Juego/ (preferencias_*.json, ranking_*.json, *.txt). "
            "Desde el juego solo se vacía el contenido de los JSON, no se borran."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo lista, sin borrar")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--solo-pycache",
        action="store_true",
        help="Solo carpetas __pycache__ y cachés de herramientas",
    )
    grupo.add_argument(
        "--solo-juego",
        action="store_true",
        help="Solo elimina ficheros runtime en Data/Juego/ (.txt y JSON)",
    )
    grupo.add_argument(
        "--solo-txt",
        action="store_true",
        help="Solo elimina ficheros .txt en Data/Juego/",
    )
    return parser


def _alcance_borrado(args: argparse.Namespace) -> tuple[bool, bool, bool]:
    incluir_pycache = not args.solo_txt and not args.solo_juego
    incluir_txt = not args.solo_pycache
    incluir_json = not args.solo_pycache and not args.solo_txt
    return incluir_pycache, incluir_txt, incluir_json


def _imprimir_resumen_post_borrado(
    resumen: ResumenLimpieza,
    *,
    incluir_pycache: bool,
    incluir_txt: bool,
    incluir_json: bool,
) -> None:
    print("\nResumen:")
    if incluir_pycache:
        print(
            f"  __pycache__: {resumen.pycache_borradas} borradas | "
            f"errores: {resumen.pycache_errores}"
        )
        print(
            f"  cachés herramientas: {resumen.cache_herramientas_borradas} borradas | "
            f"errores: {resumen.cache_herramientas_errores}"
        )
    if incluir_txt:
        print(
            f"  .txt eliminados: {resumen.txt_borrados} | errores: {resumen.txt_errores} | "
            f"liberados: {_formatear_tamano(resumen.bytes_txt)}"
        )
    if incluir_json:
        print(
            f"  JSON eliminados: {resumen.json_preferencias_borrados} preferencias, "
            f"{resumen.json_rankings_borrados} rankings | errores: {resumen.json_errores} | "
            f"liberados: {_formatear_tamano(resumen.bytes_json)}"
        )
        if resumen.json_preferencias_borrados or resumen.json_rankings_borrados:
            print("  (Al abrir el juego se recrearán con valores por defecto.)")


def main(argv: list[str] | None = None) -> int:
    _configurar_stdout_utf8()
    args = _parser_borrar_temporales().parse_args(argv)
    incluir_pycache, incluir_txt, incluir_json = _alcance_borrado(args)

    raiz = raiz_proyecto()
    preferencias, rankings, txt = listar_ficheros_runtime_juego()
    pycache = listar_pycache(raiz) if incluir_pycache else []
    cache_herramientas = listar_cache_herramientas(raiz) if incluir_pycache else []

    if not _imprimir_listado(
        pycache=pycache,
        cache_herramientas=cache_herramientas,
        preferencias=preferencias if incluir_json else [],
        rankings=rankings if incluir_json else [],
        txt=txt if incluir_txt else [],
        incluir_pycache=incluir_pycache,
        incluir_txt=incluir_txt,
        incluir_json=incluir_json,
    ):
        print("No se encontraron artefactos temporales en el proyecto.")
        return 0

    if args.dry_run:
        print("\nDry-run: no se ha borrado nada.")
        if incluir_json and (preferencias or rankings):
            print("Nota: al abrir el juego se recrearán los JSON de runtime.")
        return 0

    resumen = borrar_temporales(
        raiz,
        incluir_pycache=incluir_pycache,
        incluir_txt=incluir_txt,
        incluir_json=incluir_json,
    )
    _imprimir_resumen_post_borrado(
        resumen,
        incluir_pycache=incluir_pycache,
        incluir_txt=incluir_txt,
        incluir_json=incluir_json,
    )
    return 1 if resumen.errores_totales else 0
