#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolución de rutas a datos y persistencia (script, exe, PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path

_COMUN_DIR = Path(__file__).resolve().parent
_JUEGO_DIR = _COMUN_DIR.parent
_SCRIPTS_DIR = _JUEGO_DIR.parent / "Files" / "Scripts"


def registrar_scripts_en_path() -> None:
    """Añade ``Files/Scripts`` al path para importar utilidades compartidas con el juego."""
    if _SCRIPTS_DIR.is_dir() and str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))


def juego_dir() -> Path:
    return _JUEGO_DIR


def _roots_busqueda() -> list[Path]:
    candidatos: list[Path] = []
    vistos: set[Path] = set()

    rutas_base = [_JUEGO_DIR, Path.cwd()]
    if getattr(sys, "frozen", False):
        rutas_base.append(Path(sys.executable).resolve().parent)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        rutas_base.append(Path(meipass))

    for base in rutas_base:
        try:
            base = base.resolve()
        except OSError:
            continue
        for ruta in (base, *base.parents):
            if ruta not in vistos and ruta.exists():
                vistos.add(ruta)
                candidatos.append(ruta)
    return candidatos


def _subdirs_data_por_nombre(nombre: str) -> list[str]:
    ext = Path(nombre).suffix.lower()
    if ext == ".csv":
        return ["CSV", "csv"]
    if ext == ".json":
        return ["JSON", "json"]
    return []


def _candidatos_bajo_data(raiz: Path, nombre: str) -> list[Path]:
    data = raiz / "Data"
    if not data.is_dir():
        return []
    orden: list[Path] = []
    for subdir in _subdirs_data_por_nombre(nombre):
        orden.append(data / subdir / nombre)
    orden.append(data / nombre)
    return orden


def _buscar_archivo(
    nombre: str,
    preferidas: tuple[str, ...],
    *,
    bajo_data: bool = True,
) -> Path:
    candidatos_raiz: list[Path] = []
    vistos: set[Path] = set()
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos_raiz.append(raiz)

    if bajo_data:
        for raiz in candidatos_raiz:
            for p in _candidatos_bajo_data(raiz, nombre):
                if p.exists():
                    return p

    for raiz in candidatos_raiz:
        p = raiz / nombre
        if p.exists():
            return p

    for raiz in candidatos_raiz:
        coincidencias = sorted(
            raiz.rglob(nombre),
            key=lambda p: (
                0 if p.parent.name.lower() in {"data", "csv", "json"} else 1,
                len(p.parts),
                str(p),
            ),
        )
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError(f"No se encontró '{nombre}' en rutas accesibles.")


def _dir_data_escritura() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "Data"
    return _JUEGO_DIR.parent / "Data"


def _ruta_json_escritura(nombre: str) -> Path:
    destino = _dir_data_escritura() / "JSON" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino


def resolver_dataset() -> Path:
    return _buscar_archivo("Preguntas.csv", ("Preguntas.csv",))


def resolver_listado_materias() -> Path:
    return _buscar_archivo("listado_materias.csv", ("listado_materias.csv",))


def resolver_plantillas() -> Path:
    return _buscar_archivo("plantillas.json", ("plantillas.json",))


def resolver_preguntas_resistencia() -> Path:
    return _buscar_archivo("preguntas_resistencia.json", ("preguntas_resistencia.json",))


def resolver_presets_historia() -> Path:
    return _buscar_archivo("presets_historia.json", ("presets_historia.json",))


def resolver_ranking_resistencia() -> Path:
    """JSON local del ranking del modo resistencia (lectura/escritura)."""
    base = _ruta_json_escritura("ranking_resistencia.json")
    if not base.exists():
        try:
            empaquetado = _buscar_archivo(
                "ranking_resistencia.json",
                ("ranking_resistencia.json",),
            )
            if empaquetado.exists() and empaquetado != base:
                base.write_text(empaquetado.read_text(encoding="utf-8"), encoding="utf-8")
        except FileNotFoundError:
            base.write_text(
                '{"version": 1, "records": []}',
                encoding="utf-8",
            )
    return base


def resolver_historico_qualificacions() -> Path:
    return _buscar_archivo(
        "Historic_qualificacions_MatCAD_completo.csv",
        ("Historic_qualificacions_MatCAD_completo.csv",),
    )


def resolver_config_creador_privado() -> Path | None:
    """JSON local del creador (datos personales y secretos; no se versiona)."""
    try:
        return _buscar_archivo(
            "creador_privado.json",
            ("creador_privado.json",),
        )
    except FileNotFoundError:
        return None


def resolver_ruta_creador_privado_defecto() -> Path:
    """Ruta canónica para crear ``creador_privado.json`` si no existe."""
    existente = resolver_config_creador_privado()
    if existente is not None:
        return existente
    return _ruta_json_escritura("creador_privado.json")


def resolver_dir_informes() -> Path:
    """Carpeta donde se guardan los informes de examen (.txt)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent / "Informes"
    else:
        base = _JUEGO_DIR / "Informes"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ruta_informe_para_usuario(archivo: Path) -> str:
    """Ruta corta sin caracteres problemáticos para la consola de Windows."""
    return f"Juego/Informes/{archivo.name}"


def resolver_dir_feedback() -> Path:
    """Carpeta donde se guardan los avisos del modo feedback."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent / "Feedback"
    else:
        base = _JUEGO_DIR / "Feedback"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ruta_feedback_para_usuario(archivo: Path) -> str:
    return f"Juego/Feedback/{archivo.name}"


_path_preguntas: Path | None = None
_path_materias: Path | None = None


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
