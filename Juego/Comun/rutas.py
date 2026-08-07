#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolución de rutas a datos y persistencia (repo o zip jugable)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

_COMUN_DIR = Path(__file__).resolve().parent
_JUEGO_DIR = _COMUN_DIR.parent

_ZonaDatos = Literal["banco", "juego"]
_LEGACY_DATA_SUBDIRS = ("CSV", "csv", "JSON", "json", "Informes", "Feedback")


def juego_dir() -> Path:
    return _JUEGO_DIR


def _raiz_paquete() -> Path:
    """Raíz del paquete desplegado (repo o zip jugable)."""
    return _JUEGO_DIR.parent


def _roots_busqueda() -> list[Path]:
    candidatos: list[Path] = []
    vistos: set[Path] = set()
    try:
        paquete = _raiz_paquete().resolve()
    except OSError:
        paquete = _raiz_paquete()

    def _añadir(ruta: Path) -> None:
        try:
            resuelta = ruta.resolve()
        except OSError:
            return
        if resuelta in vistos or not resuelta.exists():
            return
        vistos.add(resuelta)
        candidatos.append(resuelta)

    _añadir(paquete)
    _añadir(_JUEGO_DIR)

    try:
        cwd = Path.cwd().resolve()
    except OSError:
        return candidatos

    try:
        cwd.relative_to(paquete)
        dentro = True
    except ValueError:
        dentro = False

    if dentro:
        for ruta in (cwd, *cwd.parents):
            _añadir(ruta)
            try:
                if ruta.resolve() == paquete:
                    break
            except OSError:
                if ruta == paquete:
                    break
    else:
        _añadir(cwd)
        try:
            paquete.relative_to(cwd)
        except ValueError:
            pass
        else:
            for ruta in (cwd, *cwd.parents):
                _añadir(ruta)
                try:
                    if ruta.resolve() == paquete:
                        break
                except OSError:
                    if ruta == paquete:
                        break

    return candidatos


def _bases_rglob_acotado(raiz: Path) -> list[Path]:
    """Subárboles del proyecto donde tiene sentido buscar datos (nunca todo el perfil del usuario)."""
    bases: list[Path] = []
    for candidato in (raiz / "Data", raiz / "Juego", raiz):
        try:
            candidato = candidato.resolve()
        except OSError:
            continue
        if not candidato.is_dir():
            continue
        if candidato in bases:
            continue
        if candidato == raiz and not (raiz / "Juego").is_dir() and not (raiz / "Data").is_dir():
            continue
        bases.append(candidato)
    return bases


def _data_root() -> Path:
    return _JUEGO_DIR.parent / "Data"


def _ancestros_desde_hoja(carpeta: Path) -> list[Path]:
    partes: list[Path] = []
    actual = carpeta
    while True:
        partes.append(actual)
        if actual.parent == actual:
            break
        actual = actual.parent
    return list(reversed(partes))


def _crear_directorio_si_falta(ruta: Path) -> None:
    if ruta.is_file():
        ruta.unlink()
    if ruta.is_dir():
        return
    try:
        ruta.mkdir(exist_ok=True)
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if (winerror == 183 or isinstance(exc, FileExistsError)) and ruta.is_dir():
            return
        raise


def _asegurar_directorio(carpeta: Path) -> Path:
    """Crea ``carpeta`` y corrige ficheros anómalos en la ruta (p. ej. tras limpieza parcial)."""
    for ruta in _ancestros_desde_hoja(carpeta):
        _crear_directorio_si_falta(ruta)
    return carpeta


def _dir_banco() -> Path:
    """Banco de preguntas: ``Data/`` plano (mínimo) o ``Data/Banco/`` (completo)."""
    if layout_datos_jugador_plano():
        return _asegurar_directorio(_data_root())
    return _asegurar_directorio(_data_root() / "Banco")


_layout_datos_plano: bool | None = None


def configurar_layout_datos_jugador(*, plano: bool | None) -> None:
    """En el paquete mínimo todo ``Data/`` es plano; en el completo usa ``Data/Banco/``, ``Data/Juego/``…

    Pasa ``plano=None`` para volver a la autodetección (útil en tests).
    """
    global _layout_datos_plano
    _layout_datos_plano = plano


def layout_datos_jugador_plano() -> bool:
    if _layout_datos_plano is not None:
        return _layout_datos_plano
    raiz = _raiz_paquete()
    if (raiz / "Data" / "Banco").is_dir():
        return False
    if (raiz / ".matcad-paquete-minimo").is_file():
        return True
    tiene_presets = (raiz / "Juego" / "presets.json").is_file()
    if (raiz / "Data" / "Preguntas.csv").is_file() and tiene_presets:
        return True
    return False


def etiqueta_dir_datos_jugador() -> str:
    return "Data" if layout_datos_jugador_plano() else "Data/Juego"


def _dir_juego_datos() -> Path:
    """Directorio de estado local del jugador (``Data/`` plano o ``Data/Juego/``)."""
    if layout_datos_jugador_plano():
        return _asegurar_directorio(_data_root())
    return _asegurar_directorio(_data_root() / "Juego")


def _dir_privado() -> Path:
    """Config privada del autor: ``Data/`` plano (mínimo) o ``Data/Privado/`` (completo)."""
    if layout_datos_jugador_plano():
        return _asegurar_directorio(_data_root())
    return _asegurar_directorio(_data_root() / "Privado")


def resolver_dir_privado() -> Path:
    """Ruta a ``Data/Privado/`` (crea la carpeta si hace falta)."""
    return _dir_privado()


def resolver_preguntas_minimal() -> Path:
    """CSV mínimo del banco (480 filas) para tests y paquete mínimo."""
    return _dir_privado() / "Preguntas_minimal.csv"


def _dir_data_escritura() -> Path:
    return _dir_juego_datos()


def _candidatos_bajo_data(raiz: Path, nombre: str, *, zona: _ZonaDatos) -> list[Path]:
    """Candidatos de lectura bajo ``Data/``.

    El layout plano solo afecta a rutas de *escritura* del jugador
    (``_dir_juego_datos`` / ``_dir_privado``). La búsqueda del banco debe
    seguir viendo ``Data/Banco/`` si existe (p. ej. tests del repo completo
    tras cargar un paquete mínimo en el mismo proceso).
    """
    data = raiz / "Data"
    if not data.is_dir():
        return []
    principal = "Banco" if zona == "banco" else "Juego"
    secundario = "Juego" if zona == "banco" else "Banco"
    orden = [
        data / principal / nombre,
        data / secundario / nombre,
    ]
    for subdir in _LEGACY_DATA_SUBDIRS:
        orden.append(data / subdir / nombre)
    orden.append(data / nombre)
    return orden


def _buscar_archivo(
    nombre: str,
    preferidas: tuple[str, ...],
    *,
    bajo_data: bool = True,
    zona: _ZonaDatos = "banco",
) -> Path:
    try:
        paquete_key = str(_raiz_paquete().resolve())
    except OSError:
        paquete_key = str(_raiz_paquete())
    clave = (paquete_key, nombre, zona, bajo_data)
    if clave in _archivos_no_encontrados:
        raise FileNotFoundError(f"No se encontró '{nombre}' en rutas accesibles.")

    candidatos_raiz: list[Path] = []
    vistos: set[Path] = set()
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos_raiz.append(raiz)

    if bajo_data:
        for raiz in candidatos_raiz:
            for p in _candidatos_bajo_data(raiz, nombre, zona=zona):
                if p.exists():
                    return p

    for raiz in candidatos_raiz:
        p = raiz / nombre
        if p.exists():
            return p

    coincidencias: list[Path] = []
    for base in _bases_rglob_acotado(_raiz_paquete()):
        try:
            coincidencias.extend(base.rglob(nombre))
        except OSError:
            continue
    if coincidencias:
        elegida = sorted(
            coincidencias,
            key=lambda p: (
                0 if p.parent.name.lower() in {"data", "banco", "juego", "csv", "json"} else 1,
                len(p.parts),
                str(p),
            ),
        )[0]
        return elegida

    _archivos_no_encontrados.add(clave)
    raise FileNotFoundError(f"No se encontró '{nombre}' en rutas accesibles.")


def _ruta_juego_escritura(nombre: str) -> Path:
    return _dir_juego_datos() / nombre


def _ruta_json_escritura(nombre: str) -> Path:
    """JSON de estado local del jugador (``Data/`` o ``Data/Juego/`` según paquete)."""
    return _ruta_juego_escritura(nombre)


def resolver_dataset() -> Path:
    return _buscar_archivo("Preguntas.csv", ("Preguntas.csv",), zona="banco")


def resolver_listado_materias() -> Path:
    return _buscar_archivo("listado_materias.csv", ("listado_materias.csv",), zona="banco")


def resolver_plantillas() -> Path:
    return _buscar_archivo("plantillas.json", ("plantillas.json",), zona="banco")


def resolver_presets() -> Path:
    """Catálogo de modos (historia, escape, resistencia…). Vive en ``Juego/presets.json``."""
    canonico = _JUEGO_DIR / "presets.json"
    if canonico.is_file():
        return canonico
    for nombre in ("presets.json", "presets_historia.json"):
        for zona in ("juego", "banco"):
            try:
                return _buscar_archivo(nombre, (nombre,), zona=zona)
            except FileNotFoundError:
                continue
    raise FileNotFoundError(
        "No se encontró el catálogo de presets (Juego/presets.json; "
        "presets_historia.json solo como nombre legacy)."
    )


def resolver_presets_historia() -> Path:
    return resolver_presets()


def resolver_presets_especiales() -> Path:
    return resolver_presets()

def resolver_config_creador_privado() -> Path | None:
    """JSON local del creador (datos personales y secretos; no se versiona)."""
    global _path_creador_privado
    if _path_creador_privado is not _CREADOR_PRIVADO_SIN_RESOLVER:
        return _path_creador_privado if isinstance(_path_creador_privado, Path) else None
    canonico = _dir_privado() / "creador_privado.json"
    if canonico.is_file():
        _path_creador_privado = canonico
        return canonico
    if layout_datos_jugador_plano():
        _path_creador_privado = None
        return None
    legado = _data_root() / "Banco" / "creador_privado.json"
    if legado.is_file():
        _path_creador_privado = legado
        return legado
    for p in _candidatos_bajo_data(_raiz_paquete(), "creador_privado.json", zona="banco"):
        if p.is_file():
            _path_creador_privado = p
            return p
    _path_creador_privado = None
    return None


def resolver_ruta_creador_privado_defecto() -> Path:
    """Ruta canónica para crear ``creador_privado.json`` si no existe."""
    existente = resolver_config_creador_privado()
    if existente is not None:
        return existente
    return _dir_privado() / "creador_privado.json"


def resolver_dir_informes() -> Path:
    """Carpeta donde se guardan los informes de examen (.txt)."""
    return _dir_juego_datos()


def ruta_informe_para_usuario(archivo: Path) -> str:
    """Ruta corta sin caracteres problemáticos para la terminal de Windows."""
    return f"{etiqueta_dir_datos_jugador()}/{archivo.name}"


def resolver_dir_feedback() -> Path:
    """Carpeta donde se guardan los avisos del modo feedback."""
    return _dir_juego_datos()


def ruta_feedback_para_usuario(archivo: Path) -> str:
    return f"{etiqueta_dir_datos_jugador()}/{archivo.name}"


_path_preguntas: Path | None = None
_path_materias: Path | None = None
_CREADOR_PRIVADO_SIN_RESOLVER: object = object()
_path_creador_privado: Path | None | object = _CREADOR_PRIVADO_SIN_RESOLVER
_archivos_no_encontrados: set[tuple[str, str, _ZonaDatos, bool]] = set()


def path_preguntas() -> Path:
    """Ruta a ``Preguntas.csv`` (resuelve en la primera llamada)."""
    global _path_preguntas
    if _path_preguntas is None:
        _path_preguntas = resolver_dataset()
    return _path_preguntas


def path_materias() -> Path:
    """Ruta a ``listado_materias.csv`` (resuelve en la primera llamada)."""
    global _path_materias
    if _path_materias is None:
        _path_materias = resolver_listado_materias()
    return _path_materias


def __getattr__(name: str) -> Path:
    if name == "PATH_PREGUNTAS":
        return path_preguntas()
    if name == "PATH_MATERIAS":
        return path_materias()
    raise AttributeError(f"module {name!r} has no attribute {name!r}")
