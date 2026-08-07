#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bootstrap del juego: CSV, detección de paquete y carga de contenido."""

from __future__ import annotations

# --- csv_contenido ---


import csv
from pathlib import Path

_COLUMNAS_MINIMAS = frozenset({"Pregunta", "A", "B", "C", "D", "Correcta"})
_COLUMNAS_OPCIONALES = frozenset({"Id", "id"})
_COLUMNAS_PEDAGOGICAS = frozenset(
    {
        "Materia",
        "Tema",
        "Dificultad",
        "Tipo",
        "Tematica",
        "Grupo",
    }
)
_COLUMNAS_CURRICULARES_PLAN = frozenset(
    {
        "Nivel",
        "Curso",
        "Año",
        "Ano",
        "Semestre",
    }
)
_COLUMNAS_CURRICULARES = _COLUMNAS_PEDAGOGICAS | _COLUMNAS_CURRICULARES_PLAN


def leer_cabeceras_csv(path_csv: Path) -> set[str]:
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return {h.strip() for h in (reader.fieldnames or []) if h}


def es_csv_minimal(cabeceras: set[str]) -> bool:
    if not _COLUMNAS_MINIMAS.issubset(cabeceras):
        return False
    return not cabeceras.intersection(_COLUMNAS_CURRICULARES)


def es_csv_intermedio(cabeceras: set[str]) -> bool:
    """CSV exportado tras jugar el mínimo: metadatos inferidos + materias/grupos artificiales."""
    if not _COLUMNAS_MINIMAS.issubset(cabeceras):
        return False
    if cabeceras.intersection(_COLUMNAS_CURRICULARES_PLAN):
        return False
    # Distingue del CSV de autor MatCAD (Materia/Dificultad/Tipo sin Grupo/Tematica).
    return {"Grupo", "Tematica"}.issubset(cabeceras)


def exigir_csv_minimal(path_csv: Path) -> None:
    """Fallo si el CSV no cumple el formato mínimo o intermedio (datos de usuario)."""
    cabeceras = leer_cabeceras_csv(path_csv)
    if es_csv_minimal(cabeceras) or es_csv_intermedio(cabeceras):
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
        "Mientras juegas, el juego infiere dificultad y tipo en metadatos_inferidos.json."
    )

# --- paquete_distribucion ---


from pathlib import Path
from typing import Any, Literal

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
    """Layout típico del paquete mínimo sin marcador (``Data/Preguntas.csv`` + motor ``Juego/``)."""
    for base in _bases_busqueda_marcador():
        if (base / _MARCADOR_COMPLETO).is_file():
            continue
        if not (base / "Juego" / "presets.json").is_file():
            continue
        csv = base / "Data" / "Preguntas.csv"
        if not csv.is_file():
            continue
        try:
            if es_csv_minimal(leer_cabeceras_csv(csv)):
                return "minimo"
        except OSError:
            continue
    return None


def resolver_csv_paquete_minimo() -> Path:
    """Ruta al CSV del paquete mínimo (``Data/Preguntas.csv`` junto al marcador)."""
    for base in _bases_busqueda_marcador():
        candidato = base / "Data" / "Preguntas.csv"
        if candidato.is_file():
            return candidato.resolve()
    raise FileNotFoundError(
        "No se encontró Data/Preguntas.csv en el paquete mínimo."
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
        materia = (p.materia or "").strip()
        if not materia:
            continue
        if materia not in meta:
            meta[materia] = dict(vacio)
        bucket = meta[materia]
        if p.grupo and not bucket["grupo"]:
            bucket["grupo"] = p.grupo.strip()
        if p.tematica and not bucket["tematica"]:
            bucket["tematica"] = p.tematica.strip()
        if p.curso and not bucket["curso"]:
            bucket["curso"] = p.curso.strip()
        if p.semestre and not bucket["semestre"]:
            bucket["semestre"] = p.semestre.strip()
        if p.nivel and not bucket["nivel"]:
            bucket["nivel"] = p.nivel.strip()
    return meta


def _inferir_capacidades_datos(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    cabeceras: set[str],
    *,
    csv_minimal: bool = False,
    dataset_intermedio: bool = False,
    cobertura: dict | None = None,
) -> dict[str, bool]:
    tiene_metadatos_curriculares = any(
        m.get("curso") and m.get("semestre") for m in materias_meta.values()
    )
    tiene_grupos = any(str(m.get("grupo", "")).strip() for m in materias_meta.values())
    tipos = {p.tipo for p in preguntas if p.tipo and p.tipo not in {"General", ""}}
    tiene_tipos_csv = "Tipo" in cabeceras or "tipo" in cabeceras
    tiene_tipos = tiene_tipos_csv and {"Teoria", "Calculo"}.issubset(tipos)
    if dataset_intermedio and cobertura:
        tiene_grupos = tiene_grupos or bool(cobertura.get("tiene_grupos_tematicos"))
        if not tiene_tipos_csv:
            tiene_tipos = bool(cobertura.get("tiene_tipos_pregunta"))

    return {
        "tiene_metadatos_curriculares": tiene_metadatos_curriculares,
        "tiene_grupos_tematicos": tiene_grupos,
        "tiene_tipos_pregunta": tiene_tipos,
    }


def _archivo_junto(path_csv: Path, nombre: str) -> Path | None:
    candidato = path_csv.parent / nombre
    return candidato if candidato.exists() else None


def _presets_en_carpeta_paquete(path_csv: Path) -> bool:
    paquete = path_csv.parent
    candidatos = [paquete / "Juego" / "presets.json", paquete / "presets.json"]
    if paquete.name == "Data":
        candidatos[:0] = [
            paquete.parent / "Juego" / "presets.json",
            paquete.parent / "presets.json",
        ]
    return any(p.is_file() for p in candidatos)


def _presets_juego_minimo(path_csv: Path, *, paquete_zip: bool) -> bool:
    """Presets del paquete mínimo (``Juego/presets.json`` junto a ``Data/Preguntas.csv``)."""
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
    tiene_presets: bool,
    tiene_plantillas: bool,
    tipo_paquete: TipoPaquete,
    solo_csv: bool,
    modo_minimo: bool,
    avisos: tuple[str, ...],
) -> ContenidoJuego:
    from Comun.rutas import _raiz_paquete, configurar_layout_datos_jugador

    # En el repo completo (con Data/Banco/) no forzar layout plano aunque se
    # cargue un CSV mínimo de fixture: si no, el estado del jugador acaba en
    # Data/ en lugar de Data/Juego/ y ensucia el health check.
    if tipo_paquete == "minimo" and not (_raiz_paquete() / "Data" / "Banco").is_dir():
        configurar_layout_datos_jugador(plano=True)
    else:
        configurar_layout_datos_jugador(plano=None)

    cabeceras = leer_cabeceras_csv(path_preguntas)
    csv_minimal = es_csv_minimal(cabeceras)
    csv_intermedio = es_csv_intermedio(cabeceras)

    if path_listado is not None:
        materias_meta = cargar_materias(path_listado)
        tiene_listado = True
    else:
        materias_meta = {}
        tiene_listado = False

    preguntas = cargar_preguntas(path_preguntas, materias_meta)
    if not preguntas:
        raise ValueError(f"El CSV no contiene preguntas válidas: {path_preguntas}")

    dataset_intermedio = False
    cobertura: dict[str, Any] = {}
    if csv_minimal or csv_intermedio:
        from Comun.metadatos_inferidos import (
            cobertura_metadatos_inferidos,
            enriquecer_preguntas_minimal,
        )

        if csv_minimal:
            enriquecer_preguntas_minimal(preguntas)
        cobertura = cobertura_metadatos_inferidos(preguntas)
        dataset_intermedio = csv_intermedio or bool(cobertura.get("dataset_intermedio"))
        if csv_minimal and dataset_intermedio:
            enriquecer_preguntas_minimal(preguntas, aplicar_catalogo=True)
            cobertura = cobertura_metadatos_inferidos(preguntas)

    if not tiene_listado:
        materias_meta = inferir_materias_meta(preguntas)

    caps = _inferir_capacidades_datos(
        preguntas,
        materias_meta,
        cabeceras,
        csv_minimal=csv_minimal,
        dataset_intermedio=dataset_intermedio,
        cobertura=cobertura,
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
        tiene_preguntas_resistencia=tiene_preg_res,
        tiene_metadatos_curriculares=caps["tiene_metadatos_curriculares"],
        tiene_grupos_tematicos=caps["tiene_grupos_tematicos"],
        tiene_tipos_pregunta=caps["tiene_tipos_pregunta"],
        dataset_intermedio=dataset_intermedio,
    )

    return ContenidoJuego(
        preguntas=preguntas,
        materias_meta=materias_meta,
        path_preguntas_csv=path_preguntas,
        path_plantillas_json=path_plantillas,
        path_listado_materias=path_listado,
        perfil=perfil,
        avisos_carga=avisos,
    )


def _cargar_juego_minimo(path_preguntas: Path, *, paquete_zip: bool) -> ContenidoJuego:
    """Datos de usuario: solo CSV mínimo; sin listado ni plantillas externos."""
    path_preguntas = path_preguntas.resolve()
    if not path_preguntas.is_file():
        raise FileNotFoundError(f"No se encontró el CSV: {path_preguntas}")
    exigir_csv_minimal(path_preguntas)

    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=None,
        path_plantillas=None,
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
            "Revisa Data/Banco/ (Preguntas.csv, listado_materias.csv) "
            "o arranca con --csv para el modo mínimo."
        )
    path_preguntas = validacion.path_preguntas or resolver_dataset()
    path_plantillas = _resolver_opcional(resolver_plantillas)
    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=resolver_listado_materias(),
        path_plantillas=path_plantillas,
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
    else:
        path_listado = resolver_listado_materias()
        path_plantillas = _resolver_opcional(resolver_plantillas)
        tiene_presets = True
        tiene_plantillas = path_plantillas is not None

    return _construir_contenido(
        path_preguntas=path_preguntas,
        path_listado=path_listado,
        path_plantillas=path_plantillas,
        tiene_presets=tiene_presets,
        tiene_plantillas=tiene_plantillas,
        tipo_paquete="desarrollo",
        solo_csv=False,
        modo_minimo=modo_minimo,
        avisos=avisos,
    )


def cargar_contenido_juego(*, path_csv: Path | None = None) -> ContenidoJuego:
    """Carga preguntas y deduce capacidades del motor.

    **Usuario (datos propios):** paquete mínimo → ``Data/Preguntas.csv`` (o marcador
    ``.matcad-paquete-minimo``) con columnas mínimas; juego acotado.

    **Desarrollo / completo:** marcador ``.matcad-paquete-completo`` o repo con ``Data/``
    completo → juego MATCAD completo.
    """
    if path_csv is not None:
        return _cargar_juego_minimo(path_csv, paquete_zip=False)

    tipo = detectar_tipo_paquete()
    if tipo == "completo":
        return _cargar_paquete_completo()
    if tipo == "minimo":
        return _cargar_juego_minimo(
            resolver_csv_paquete_minimo(),
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
        perfil=contenido.perfil,
        avisos_carga=contenido.avisos_carga,
    )
