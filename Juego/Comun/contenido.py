#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bootstrap del juego, CSV, paquete, validación y manifiesto del zip mínimo."""

from __future__ import annotations

# --- csv_contenido ---


import csv
from pathlib import Path

_COLUMNAS_MINIMAS = frozenset({"Pregunta", "A", "B", "C", "D", "Correcta"})
_COLUMNAS_OPCIONALES = frozenset({"Id", "id"})
_COLUMNAS_CURRICULARES = frozenset(
    {
        "Materia",
        "Tema",
        "Dificultad",
        "Tipo",
        "Tematica",
        "Grupo",
        "Nivel",
        "Curso",
        "Año",
        "Ano",
        "Semestre",
    }
)


def leer_cabeceras_csv(path_csv: Path) -> set[str]:
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return {h.strip() for h in (reader.fieldnames or []) if h}


def es_csv_minimal(cabeceras: set[str]) -> bool:
    if not _COLUMNAS_MINIMAS.issubset(cabeceras):
        return False
    return not cabeceras.intersection(_COLUMNAS_CURRICULARES)


def exigir_csv_minimal(path_csv: Path) -> None:
    """Fallo si el CSV no cumple el formato mínimo (único admitido para datos de usuario)."""
    cabeceras = leer_cabeceras_csv(path_csv)
    if es_csv_minimal(cabeceras):
        return
    if not _COLUMNAS_MINIMAS.issubset(cabeceras):
        raise ValueError(
            f"CSV inválido ({path_csv.name}): faltan columnas obligatorias "
            f"{sorted(_COLUMNAS_MINIMAS)} (separador ';')."
        )
    raise ValueError(
        f"CSV con metadatos curriculares no admitido para datos de usuario ({path_csv.name}). "
        "Usa columnas mínimas: Id;Pregunta;A;B;C;D;Correcta. "
        "Ejemplo: Data/Plantillas/Preguntas.csv. "
        "Un paquete intermedio para bancos más complejos llegará en una versión futura."
    )

# --- paquete_distribucion ---


from pathlib import Path
from typing import Literal

from Comun.rutas import juego_dir

TipoPaquete = Literal["minimo", "completo", "desarrollo"]

_MARCADOR_MINIMO = ".matcad-paquete-minimo"
_MARCADOR_COMPLETO = ".matcad-paquete-completo"


def _bases_busqueda_marcador() -> list[Path]:
    bases: list[Path] = []
    vistos: set[Path] = set()
    for candidato in (Path.cwd(), juego_dir().parent):
        try:
            base = candidato.resolve()
        except OSError:
            continue
        if base not in vistos:
            vistos.add(base)
            bases.append(base)
    return bases


def detectar_tipo_paquete() -> TipoPaquete:
    """Detecta el paquete según marcadores de distribución (``.matcad-paquete-*``)."""
    for base in _bases_busqueda_marcador():
        if (base / _MARCADOR_MINIMO).is_file():
            return "minimo"
        if (base / _MARCADOR_COMPLETO).is_file():
            return "completo"
    return _detectar_minimo_por_layout() or "desarrollo"


def _detectar_minimo_por_layout() -> TipoPaquete | None:
    """Layout típico del zip mínimo sin marcador (``Preguntas.csv`` mínimo + motor ``Juego/``)."""
    for base in _bases_busqueda_marcador():
        if (base / _MARCADOR_COMPLETO).is_file():
            continue
        csv = base / "Preguntas.csv"
        if not csv.is_file() or not (base / "Juego" / "presets.json").is_file():
            continue
        try:
            if es_csv_minimal(leer_cabeceras_csv(csv)):
                return "minimo"
        except OSError:
            continue
    return None


def resolver_csv_paquete_minimo(path_csv: Path | None = None) -> Path:
    """Ruta al CSV del paquete mínimo (explícita o ``Preguntas.csv`` junto al marcador)."""
    if path_csv is not None:
        ruta = path_csv.resolve()
        if not ruta.is_file():
            raise FileNotFoundError(f"No se encontró el CSV: {ruta}")
        return ruta
    for base in _bases_busqueda_marcador():
        candidato = base / "Preguntas.csv"
        if candidato.is_file():
            return candidato.resolve()
    raise FileNotFoundError(
        "No se encontró Preguntas.csv junto al paquete mínimo. "
        "Usa: python Juego/juego_grafico.py --csv Preguntas.csv"
    )

# --- validacion_contenido ---


from dataclasses import dataclass
from pathlib import Path

from Comun.rutas import juego_dir, resolver_dataset


@dataclass(frozen=True)
class ResultadoValidacion:
    """Resultado de comprobar si el paquete MATCAD completo está disponible."""

    completo: bool
    faltas: tuple[str, ...]
    path_preguntas: Path | None = None

    @property
    def avisos(self) -> tuple[str, ...]:
        if self.completo:
            return ()
        return tuple(f"Requisito no cumplido: {f}" for f in self.faltas)


def _comprobar_archivo(resolver, etiqueta: str, faltas: list[str]) -> Path | None:
    try:
        return resolver()
    except FileNotFoundError:
        faltas.append(etiqueta)
        return None


def _comprobar_fichero_paquete(
    nombre: str,
    etiqueta: str,
    faltas: list[str],
    *,
    bajo_data: bool = True,
) -> Path | None:
    from Comun.rutas import _candidatos_bajo_data, _raiz_paquete

    raiz = _raiz_paquete()
    if bajo_data:
        for p in _candidatos_bajo_data(raiz, nombre, zona="banco"):
            if p.is_file():
                return p
    candidato = raiz / nombre
    if candidato.is_file():
        return candidato
    faltas.append(etiqueta)
    return None


def evaluar_requisitos_completo() -> ResultadoValidacion:
    """Comprueba dataset, listado, presets y CSV con metadatos curriculares.

    ``plantillas.json`` no es obligatorio: es herramienta del autor (revisado vs pendiente).
    Si existe, activa el banco ampliado y el pool de resistencia con plantillas.
    """
    faltas: list[str] = []
    path_csv = _comprobar_archivo(resolver_dataset, "Preguntas.csv", faltas)
    _comprobar_fichero_paquete("listado_materias.csv", "listado_materias.csv", faltas)
    presets = juego_dir() / "presets.json"
    if not presets.is_file():
        faltas.append("Juego/presets.json")

    if path_csv is not None and path_csv.is_file():
        cabeceras = leer_cabeceras_csv(path_csv)
        if es_csv_minimal(cabeceras):
            faltas.append(
                "Preguntas.csv con columnas curriculares (Materia, Dificultad, Tipo, …)"
            )

    return ResultadoValidacion(
        completo=len(faltas) == 0,
        faltas=tuple(faltas),
        path_preguntas=path_csv,
    )

# --- carga_contenido ---


from dataclasses import dataclass
from pathlib import Path

from Comun.datos import cargar_materias, cargar_preguntas
from Comun.modelos import Pregunta
from Comun.perfil_contenido import PerfilContenido
from Comun.rutas import (
    juego_dir,
    resolver_dataset,
    resolver_historico_qualificacions,
    resolver_listado_materias,
    resolver_plantillas,
    resolver_presets,
)


@dataclass
class ContenidoJuego:
    preguntas: list[Pregunta]
    materias_meta: dict[str, dict[str, str]]
    path_preguntas_csv: Path
    path_plantillas_json: Path | None
    perfil: PerfilContenido
    path_listado_materias: Path | None = None
    path_historico: Path | None = None
    avisos_carga: tuple[str, ...] = ()


def inferir_materias_meta(preguntas: list[Pregunta]) -> dict[str, dict[str, str]]:
    vacio = {
        "grupo": "",
        "nivel": "",
        "tematica": "",
        "curso": "",
        "semestre": "",
    }
    meta: dict[str, dict[str, str]] = {}
    for p in preguntas:
        if p.materia not in meta:
            meta[p.materia] = dict(vacio)
    return meta


def _archivo_historico_junto(path_csv: Path) -> Path | None:
    for nombre in (
        "Historic_qualificacions_MatCAD_completo.csv",
        "historico_qualificacions.csv",
        "historico.csv",
    ):
        candidato = _archivo_junto(path_csv, nombre)
        if candidato:
            return candidato
    return None


def _inferir_capacidades_datos(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    cabeceras: set[str],
    *,
    path_historico: Path | None,
) -> dict[str, bool]:
    tiene_metadatos_curriculares = any(
        m.get("curso") and m.get("semestre") for m in materias_meta.values()
    )
    tiene_grupos = any(str(m.get("grupo", "")).strip() for m in materias_meta.values())
    tipos = {p.tipo for p in preguntas if p.tipo and p.tipo not in {"General", ""}}
    tiene_tipos_csv = "Tipo" in cabeceras or "tipo" in cabeceras
    tiene_tipos = tiene_tipos_csv and {"Teoria", "Calculo"}.issubset(tipos)

    analisis_historico = False
    tiene_historico = path_historico is not None and path_historico.is_file()
    if tiene_historico:
        try:
            from Comun.generador_examen_historia import cargar_estadisticas_historicas

            stats = cargar_estadisticas_historicas(
                path_historico,
                materias_validas=set(materias_meta),
            )
            analisis_historico = len(stats) > 0
        except (FileNotFoundError, OSError, ValueError, KeyError):
            analisis_historico = False

    return {
        "tiene_historico": tiene_historico,
        "tiene_metadatos_curriculares": tiene_metadatos_curriculares,
        "tiene_grupos_tematicos": tiene_grupos,
        "tiene_tipos_pregunta": tiene_tipos,
        "analisis_historico_disponible": analisis_historico,
    }


def _archivo_junto(path_csv: Path, nombre: str) -> Path | None:
    candidato = path_csv.parent / nombre
    return candidato if candidato.exists() else None


def _presets_en_carpeta_paquete(path_csv: Path) -> bool:
    raiz = path_csv.parent
    return (raiz / "Juego" / "presets.json").is_file() or (raiz / "presets.json").is_file()


def _presets_juego_minimo(path_csv: Path, *, paquete_zip: bool) -> bool:
    """Presets del zip mínimo (junto al CSV) o del motor ``Juego/`` en desarrollo con ``--csv``."""
    if _presets_en_carpeta_paquete(path_csv):
        return True
    if paquete_zip:
        return False
    return (juego_dir() / "presets.json").is_file()


def _resolver_opcional(resolver) -> Path | None:
    try:
        return resolver()
    except FileNotFoundError:
        return None


def _construir_contenido(
    *,
    path_preguntas: Path,
    path_listado: Path | None,
    path_plantillas: Path | None,
    path_historico: Path | None,
    tiene_presets: bool,
    tiene_plantillas: bool,
    tipo_paquete: TipoPaquete,
    solo_csv: bool,
    modo_minimo: bool,
    avisos: tuple[str, ...],
) -> ContenidoJuego:
    cabeceras = leer_cabeceras_csv(path_preguntas)
    csv_minimal = es_csv_minimal(cabeceras)

    if path_listado is not None:
        materias_meta = cargar_materias(path_listado)
        tiene_listado = True
    else:
        materias_meta = {}
        tiene_listado = False

    preguntas = cargar_preguntas(path_preguntas, materias_meta)
    if not preguntas:
        raise ValueError(f"El CSV no contiene preguntas válidas: {path_preguntas}")

    if not tiene_listado:
        materias_meta = inferir_materias_meta(preguntas)

    caps = _inferir_capacidades_datos(
        preguntas,
        materias_meta,
        cabeceras,
        path_historico=path_historico,
    )

    tiene_preg_res = True  # exclusivas embebidas en preguntas_resistencia_exclusivas_datos.py

    perfil = PerfilContenido(
        solo_csv=solo_csv,
        csv_minimal=csv_minimal,
        modo_minimo=modo_minimo,
        tipo_paquete=tipo_paquete,
        tiene_listado_materias=tiene_listado,
        tiene_plantillas=tiene_plantillas,
        tiene_presets=tiene_presets,
        tiene_historico=caps["tiene_historico"],
        tiene_preguntas_resistencia=tiene_preg_res,
        tiene_metadatos_curriculares=caps["tiene_metadatos_curriculares"],
        tiene_grupos_tematicos=caps["tiene_grupos_tematicos"],
        tiene_tipos_pregunta=caps["tiene_tipos_pregunta"],
        analisis_historico_disponible=caps["analisis_historico_disponible"],
    )

    return ContenidoJuego(
        preguntas=preguntas,
        materias_meta=materias_meta,
        path_preguntas_csv=path_preguntas,
        path_plantillas_json=path_plantillas,
        path_listado_materias=path_listado,
        path_historico=path_historico,
        perfil=perfil,
        avisos_carga=avisos,
    )


def _cargar_juego_minimo(path_preguntas: Path, *, paquete_zip: bool) -> ContenidoJuego:
    """Datos de usuario: solo CSV mínimo; sin listado, plantillas ni histórico externos."""
    path_preguntas = path_preguntas.resolve()
    if not path_preguntas.is_file():
        raise FileNotFoundError(f"No se encontró el CSV: {path_preguntas}")
    exigir_csv_minimal(path_preguntas)

    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=None,
        path_plantillas=None,
        path_historico=None,
        tiene_presets=_presets_juego_minimo(path_preguntas, paquete_zip=paquete_zip),
        tiene_plantillas=False,
        tipo_paquete="minimo",
        solo_csv=True,
        modo_minimo=True,
        avisos=(),
    )


def _cargar_paquete_completo() -> ContenidoJuego:
    validacion = evaluar_requisitos_completo()
    if not validacion.completo:
        faltas = "\n".join(f"  · {f}" for f in validacion.faltas)
        raise ValueError(
            "Paquete MATCAD completo incompleto. Faltan:\n"
            f"{faltas}\n\n"
            "Reinstala MATCAD_juego_portable.zip (juego del autor) "
            "o usa tu CSV con MATCAD_juego_minimal.zip / --csv."
        )
    path_preguntas = validacion.path_preguntas or resolver_dataset()
    path_plantillas = _resolver_opcional(resolver_plantillas)
    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=resolver_listado_materias(),
        path_plantillas=path_plantillas,
        path_historico=_resolver_opcional(resolver_historico_qualificacions),
        tiene_presets=True,
        tiene_plantillas=path_plantillas is not None,
        tipo_paquete="completo",
        solo_csv=False,
        modo_minimo=False,
        avisos=(),
    )


def _cargar_paquete_desarrollo() -> ContenidoJuego:
    """Repositorio del autor: juego completo si ``Data/`` cumple requisitos; si no, avisos."""
    avisos: tuple[str, ...] = ()
    validacion = evaluar_requisitos_completo()
    modo_minimo = not validacion.completo
    if modo_minimo:
        avisos = validacion.avisos
    path_preguntas = validacion.path_preguntas or resolver_dataset()

    if modo_minimo:
        path_listado = None
        path_plantillas = None
        tiene_presets = _presets_juego_minimo(path_preguntas, paquete_zip=False)
        tiene_plantillas = False
        path_historico = None
    else:
        path_listado = resolver_listado_materias()
        path_plantillas = _resolver_opcional(resolver_plantillas)
        tiene_presets = True
        tiene_plantillas = path_plantillas is not None
        path_historico = _resolver_opcional(resolver_historico_qualificacions)

    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=path_listado,
        path_plantillas=path_plantillas,
        path_historico=path_historico,
        tiene_presets=tiene_presets,
        tiene_plantillas=tiene_plantillas,
        tipo_paquete="desarrollo",
        solo_csv=False,
        modo_minimo=modo_minimo,
        avisos=avisos,
    )


def cargar_contenido_juego(*, path_csv: Path | None = None) -> ContenidoJuego:
    """Carga preguntas y deduce capacidades del motor.

    **Usuario (datos propios):** ``--csv`` o zip mínimo → solo CSV con columnas mínimas;
    juego mínimo (libre simplificado, historia acotada, resistencia con eventos).

    **Autor:** zip completo (``.matcad-paquete-completo``) o repo de desarrollo con ``Data/``
    completo → juego MATCAD completo.
    """
    if path_csv is not None:
        return _cargar_juego_minimo(path_csv, paquete_zip=False)

    tipo = detectar_tipo_paquete()
    if tipo == "completo":
        return _cargar_paquete_completo()
    if tipo == "minimo":
        return _cargar_juego_minimo(
            resolver_csv_paquete_minimo(None),
            paquete_zip=True,
        )
    return _cargar_paquete_desarrollo()


def construir_datos_juego(contenido: ContenidoJuego):
    """Instancia ``DatosJuego`` a partir del contenido cargado."""
    from Grafico.app import DatosJuego

    return DatosJuego(
        num_preguntas=len(contenido.preguntas),
        num_materias=len(contenido.materias_meta),
        preguntas=contenido.preguntas,
        materias_meta=contenido.materias_meta,
        path_preguntas_csv=contenido.path_preguntas_csv,
        path_plantillas_json=contenido.path_plantillas_json,
        path_listado_materias=contenido.path_listado_materias,
        path_historico=contenido.path_historico,
        perfil=contenido.perfil,
        avisos_carga=contenido.avisos_carga,
    )

# --- contenido_minimo ---


MODULOS_EXCLUIDOS_MINIMO: frozenset[str] = frozenset({
    "Comun/escape_room.py",
    "Comun/escape_partida.py",
    "Comun/tienda_escape.py",
    "Grafico/pantallas_escape.py",
    "Grafico/pantallas_historia.py",
})

RUTAS_EXCLUIDAS_MINIMO = MODULOS_EXCLUIDOS_MINIMO

RAICES_FLUJO_MINIMO: frozenset[str] = frozenset({
    "Comun.contenido",
    "Comun.persistencia",
    "Grafico.app",
    "Grafico.pantallas_libre",
    "Grafico.pantallas_modos",
    "Grafico.pantallas_examen_fijo",
    "Grafico.pantallas_resistencia_partida",
    "Grafico.modo_preset",
    "Grafico.modo_especiales",
    "Grafico.modo_historia",
    "Grafico.pantallas_sistema",
    "Comun.modos_diarios",
})

__all__ = [
    "MODULOS_EXCLUIDOS_MINIMO",
    "RAICES_FLUJO_MINIMO",
    "RUTAS_EXCLUIDAS_MINIMO",
]
