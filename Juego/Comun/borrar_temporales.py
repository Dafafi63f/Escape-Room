#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidad **externa**: elimina artefactos temporales y ficheros runtime del juego.

Política de limpieza (complemento de ``datos_locales_juego``)
--------------------------------------------------------------

Desde **fuera** (esta utilidad): borra del disco ``preferencias_*.json``,
``ranking_*.json`` y ``*.txt`` en ``Data/Juego/`` (raíz del repo), más ``__pycache__`` y cachés.
El árbol ``Juego/Data/`` creado por ``juego_grafico.exe`` se elimina **entero** (incluye
``Juego/Data/Juego/``). También se quitan **directorios vacíos** anidados en el repo
(p. ej. ``test/a/b/z``). Al abrir el juego, los JSON de runtime se recrean. Si
``Data/Juego/`` (raíz) queda vacía tras el borrado selectivo, también se elimina.

Desde **dentro** del juego: solo ``datos_locales_juego`` — borra ``.txt`` y vacía
el contenido de preferencias y rankings (los ``.json`` se conservan).

CLI: ``python utilidades_tfg.py`` (o ``--solo-limpieza``; lógica en este módulo).
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
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
    "dir_data_junto_al_exe",
    "dirs_data_juego",
    "eliminar_ficheros_runtime_juego",
    "listar_directorios_vacios",
    "listar_ficheros_runtime_juego",
    "main",
    "raiz_proyecto",
]


def raiz_proyecto() -> Path:
    return _PROYECTO


def dir_data_juego() -> Path:
    """``Data/Juego/`` canónico en la raíz del TFG (desarrollo con ``juego_grafico.py``)."""
    return raiz_proyecto() / "Data" / "Juego"


def dir_data_junto_al_exe(raiz: Path | None = None) -> Path:
    """``Juego/Data/`` junto a ``juego_grafico.exe`` (artefacto del empaquetado)."""
    base = raiz or raiz_proyecto()
    return base / "Juego" / "Data"


def dirs_data_juego() -> list[Path]:
    """Carpeta ``Data/Juego/`` canónica (raíz del repo)."""
    carpeta = dir_data_juego()
    return [carpeta] if carpeta.is_dir() else []


def listar_ficheros_runtime_junto_al_exe(
    raiz: Path | None = None,
) -> tuple[list[Path], list[Path], list[Path]]:
    """Runtime en ``Juego/Data/Juego/`` (solo informativo; el árbol ``Juego/Data/`` se borra entero)."""
    juego = dir_data_junto_al_exe(raiz) / "Juego"
    if not juego.is_dir():
        return [], [], []
    return _ficheros_runtime_en(juego)


def _ficheros_runtime_en(carpeta: Path) -> tuple[list[Path], list[Path], list[Path]]:
    preferencias = sorted(
        (
            *carpeta.glob("preferencias_grafico.json"),
            *carpeta.glob("preferencias_ranking.json"),
        )
    )
    rankings = sorted(p for p in carpeta.glob("ranking_*.json") if p.is_file())
    txt = sorted(p for p in carpeta.glob("*.txt") if p.is_file())
    return preferencias, rankings, txt


def _agregar_ficheros_unicos(
    destino: list[Path],
    origen: list[Path],
    *,
    vistos: set[Path],
) -> None:
    for fichero in origen:
        try:
            clave = fichero.resolve()
        except OSError:
            clave = fichero
        if clave in vistos:
            continue
        vistos.add(clave)
        destino.append(fichero)


def listar_ficheros_runtime_juego() -> tuple[list[Path], list[Path], list[Path]]:
    """``(preferencias, rankings, txt)`` en todas las carpetas ``Data/Juego/`` del repo."""
    preferencias: list[Path] = []
    rankings: list[Path] = []
    txt: list[Path] = []
    vistos: set[Path] = set()
    for carpeta in dirs_data_juego():
        p, r, t = _ficheros_runtime_en(carpeta)
        _agregar_ficheros_unicos(preferencias, p, vistos=vistos)
        _agregar_ficheros_unicos(rankings, r, vistos=vistos)
        _agregar_ficheros_unicos(txt, t, vistos=vistos)
    return sorted(preferencias), sorted(rankings), sorted(txt)


def _rutas_limpieza_data_juego(raiz: Path) -> list[tuple[Path, Path]]:
    """Pares (hoja, límite) para vaciar ``Data/Juego/`` canónico (no ``Juego/Data/`` del .exe)."""
    return [(raiz / "Data" / "Juego", raiz / "Data")]


def _onerror_rmtree(
    func: object,
    path: str,
    exc_info: tuple[type[BaseException], BaseException, object],
) -> None:
    exc = exc_info[1]
    if isinstance(exc, FileNotFoundError):
        return
    if isinstance(exc, PermissionError) or (
        isinstance(exc, OSError) and getattr(exc, "errno", None) in {13, 1}
    ):
        os.chmod(path, stat.S_IWRITE)
        if callable(func):
            func(path)
        return
    raise exc


def _limpiar_arbol_vacios(carpeta: Path) -> tuple[int, int]:
    """Elimina ``carpeta`` y descendientes vacíos (varias pasadas, de hoja a raíz)."""
    if not carpeta.is_dir():
        return 0, 0
    borradas = 0
    errores = 0
    while True:
        eliminadas_paso = 0
        descendientes = sorted(
            (p for p in carpeta.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts),
            reverse=True,
        )
        for actual in descendientes:
            try:
                if not any(actual.iterdir()):
                    actual.rmdir()
                    borradas += 1
                    eliminadas_paso += 1
            except OSError:
                errores += 1
        if carpeta.is_dir() and not any(carpeta.iterdir()):
            try:
                carpeta.rmdir()
                borradas += 1
                eliminadas_paso += 1
            except OSError:
                errores += 1
                break
        if eliminadas_paso == 0:
            break
    return borradas, errores


def _eliminar_data_junto_al_exe(raiz: Path) -> tuple[int, int]:
    """Elimina por completo ``Juego/Data/`` (estado local del ``.exe``)."""
    data_exe = dir_data_junto_al_exe(raiz)
    if not data_exe.is_dir():
        return 0, 0
    try:
        shutil.rmtree(data_exe, onerror=_onerror_rmtree)
        return 1, 0
    except OSError:
        pass
    borradas, errores = _limpiar_arbol_vacios(data_exe)
    if data_exe.is_dir():
        errores += 1
    elif borradas == 0:
        borradas = 1
    return borradas, errores


def _eliminar_carpetas_vacias_hacia_arriba(hoja: Path, limite: Path) -> tuple[int, int]:
    """Elimina ``hoja`` y ancestros vacíos hasta ``limite`` (sin borrar ``limite``)."""
    borradas = 0
    errores = 0
    try:
        limite_resuelto = limite.resolve()
    except OSError:
        limite_resuelto = limite

    actual = hoja
    while True:
        try:
            if actual.resolve() == limite_resuelto:
                break
        except OSError:
            if actual == limite:
                break
        if actual == actual.parent:
            break
        if not actual.is_dir():
            break
        try:
            if any(actual.iterdir()):
                break
            actual.rmdir()
            borradas += 1
        except OSError:
            errores += 1
            break
        actual = actual.parent
    return borradas, errores


def _limpiar_carpetas_data_juego_vacias(raiz: Path) -> tuple[int, int]:
    total_borradas = 0
    total_errores = 0
    for hoja, limite in _rutas_limpieza_data_juego(raiz):
        ok, err = _eliminar_carpetas_vacias_hacia_arriba(hoja, limite)
        total_borradas += ok
        total_errores += err
    return total_borradas, total_errores


def _carpeta_removible_tras_limpieza(carpeta: Path, limite: Path) -> bool:
    """True si la carpeta está vacía o solo contiene subcarpetas también removibles."""
    try:
        if carpeta.resolve() == limite.resolve():
            return False
    except OSError:
        if carpeta == limite:
            return False
    if not carpeta.is_dir():
        return False
    try:
        entradas = list(carpeta.iterdir())
    except OSError:
        return False
    for entrada in entradas:
        if entrada.is_file():
            return False
        if entrada.is_dir() and not _carpeta_removible_tras_limpieza(entrada, limite):
            return False
    return True


def listar_carpetas_data_juego_vacias(raiz: Path | None = None) -> list[Path]:
    """Carpetas en ``Data/Juego/`` (raíz y junto al ``.exe``) que se eliminarían."""
    base = raiz or raiz_proyecto()
    resultado: list[Path] = []
    vistos: set[Path] = set()
    for hoja, limite in _rutas_limpieza_data_juego(base):
        actual = hoja
        while True:
            try:
                if actual.resolve() == limite.resolve():
                    break
            except OSError:
                if actual == limite:
                    break
            if actual == actual.parent:
                break
            if not _carpeta_removible_tras_limpieza(actual, limite):
                break
            try:
                clave = actual.resolve()
            except OSError:
                clave = actual
            if clave not in vistos:
                vistos.add(clave)
                resultado.append(actual)
            actual = actual.parent
    return resultado


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
    carpetas_vacias_borradas: int = 0
    carpetas_vacias_errores: int = 0

    @property
    def errores_totales(self) -> int:
        return (
            self.pycache_errores
            + self.cache_herramientas_errores
            + self.txt_errores
            + self.json_errores
            + self.carpetas_vacias_errores
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


def _clave_ruta(ruta: Path) -> Path:
    try:
        return ruta.resolve()
    except OSError:
        return ruta


def _directorios_bajo_raiz(raiz: Path) -> list[Path]:
    return sorted(
        (
            p
            for p in raiz.rglob("*")
            if p.is_dir() and not _dentro_de_omitidos(p, raiz)
        ),
        key=lambda p: len(p.parts),
        reverse=True,
    )


def _es_data_exe(carpeta: Path, raiz: Path) -> bool:
    data_exe = dir_data_junto_al_exe(raiz)
    try:
        carpeta.resolve().relative_to(data_exe.resolve())
        return True
    except ValueError:
        return False


def listar_directorios_vacios(
    raiz: Path | None = None,
    *,
    omitir_data_exe: bool = False,
) -> list[Path]:
    """Directorios que se pueden borrar en cascada (de hoja a raíz).

    Solo entra un directorio si no tiene ficheros y todos sus subdirectorios
    también son eliminables. Un ancestro con contenido (p. ej. ``test/a`` con
    un ``.txt``) no se lista ni se borra aunque cuelgue una rama vacía
    ``test/a/b/z``; en ese caso solo se eliminan ``z`` y ``b``.
    Si toda la cadena está vacía (``test/a/b/z``), se elimina hasta ``test``.
    Varias ramas vacías hermanas bajo el mismo padre (p. ej. ``test/a/b`` y
    ``test/a/c`` sin ficheros) se eliminan todas; si ``a`` solo contenía esas
    ramas, también se borra ``a`` y, en cascada, sus ancestros vacíos.
    Con ``omitir_data_exe=True``, no lista ``Juego/Data/`` (ya cubierto por
    ``_eliminar_data_junto_al_exe`` en la limpieza de runtime).
    """
    base = raiz or raiz_proyecto()
    candidatos = [
        p
        for p in base.rglob("*")
        if p.is_dir()
        and not _dentro_de_omitidos(p, base)
        and not (omitir_data_exe and _es_data_exe(p, base))
    ]
    eliminables: set[Path] = set()
    changed = True
    while changed:
        changed = False
        for carpeta in sorted(candidatos, key=lambda p: len(p.parts), reverse=True):
            if _clave_ruta(carpeta) in eliminables:
                continue
            try:
                entradas = list(carpeta.iterdir())
            except OSError:
                continue
            if not entradas:
                vacio = True
            elif any(entrada.is_file() for entrada in entradas):
                vacio = False
            else:
                vacio = all(
                    _clave_ruta(entrada) in eliminables
                    for entrada in entradas
                    if entrada.is_dir()
                )
            if vacio:
                eliminables.add(_clave_ruta(carpeta))
                changed = True
    return sorted(
        (p for p in candidatos if _clave_ruta(p) in eliminables),
        key=lambda p: len(p.parts),
        reverse=True,
    )


def _limpiar_directorios_vacios(raiz: Path, *, omitir_data_exe: bool = False) -> tuple[int, int]:
    """Elimina directorios vacíos anidados (varias pasadas, de hoja a raíz).

    Un directorio solo se borra cuando ``iterdir()`` está vacío en disco; no se
    eliminan ancestros que sigan teniendo ficheros o subcarpetas con contenido.
    """
    borradas = 0
    errores = 0
    while True:
        eliminadas_paso = 0
        for carpeta in _directorios_bajo_raiz(raiz):
            if omitir_data_exe and _es_data_exe(carpeta, raiz):
                continue
            try:
                if not any(carpeta.iterdir()):
                    carpeta.rmdir()
                    borradas += 1
                    eliminadas_paso += 1
            except OSError:
                errores += 1
        if eliminadas_paso == 0:
            break
    return borradas, errores


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

    if incluir_txt or incluir_json:
        ok, err = _limpiar_carpetas_data_juego_vacias(raiz)
        resumen.carpetas_vacias_borradas += ok
        resumen.carpetas_vacias_errores += err
        ok, err = _eliminar_data_junto_al_exe(raiz)
        resumen.carpetas_vacias_borradas += ok
        resumen.carpetas_vacias_errores += err

    if incluir_pycache:
        ok, err = _limpiar_directorios_vacios(
            raiz,
            omitir_data_exe=incluir_txt or incluir_json,
        )
        resumen.carpetas_vacias_borradas += ok
        resumen.carpetas_vacias_errores += err

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
    carpetas_vacias: list[Path],
    data_junto_al_exe: Path | None,
    directorios_vacios: list[Path],
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

    if (incluir_txt or incluir_json) and carpetas_vacias:
        hay_algo = True
        print(f"carpetas vacías en Data/Juego/ (raíz): {len(carpetas_vacias)}")
        for p in carpetas_vacias:
            print(f" - {p}")

    if (incluir_txt or incluir_json) and data_junto_al_exe is not None:
        hay_algo = True
        print("Juego/Data/ (árbol del .exe, se eliminará entero):")
        print(f" - {data_junto_al_exe}")

    if incluir_pycache and directorios_vacios:
        hay_algo = True
        print(f"directorios vacíos en el repo: {len(directorios_vacios)}")
        for p in directorios_vacios:
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
            "ficheros runtime en Data/Juego/ (raíz del repo): preferencias_*.json, "
            "ranking_*.json, *.txt; elimina también Juego/Data/ (árbol del .exe) y "
            "directorios vacíos anidados en el repo. "
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
    if resumen.carpetas_vacias_borradas:
        print(
            f"  carpetas/árboles eliminados: {resumen.carpetas_vacias_borradas} | "
            f"errores: {resumen.carpetas_vacias_errores}"
        )


def main(argv: list[str] | None = None) -> int:
    _configurar_stdout_utf8()
    args = _parser_borrar_temporales().parse_args(argv)
    incluir_pycache, incluir_txt, incluir_json = _alcance_borrado(args)

    raiz = raiz_proyecto()
    preferencias, rankings, txt = listar_ficheros_runtime_juego()
    pycache = listar_pycache(raiz) if incluir_pycache else []
    cache_herramientas = listar_cache_herramientas(raiz) if incluir_pycache else []
    carpetas_vacias = (
        listar_carpetas_data_juego_vacias(raiz) if (incluir_txt or incluir_json) else []
    )
    data_exe = (
        dir_data_junto_al_exe(raiz)
        if (incluir_txt or incluir_json) and dir_data_junto_al_exe(raiz).is_dir()
        else None
    )
    directorios_vacios = (
        listar_directorios_vacios(raiz, omitir_data_exe=incluir_txt or incluir_json)
        if incluir_pycache
        else []
    )

    if not _imprimir_listado(
        pycache=pycache,
        cache_herramientas=cache_herramientas,
        preferencias=preferencias if incluir_json else [],
        rankings=rankings if incluir_json else [],
        txt=txt if incluir_txt else [],
        carpetas_vacias=carpetas_vacias,
        data_junto_al_exe=data_exe,
        directorios_vacios=directorios_vacios,
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
