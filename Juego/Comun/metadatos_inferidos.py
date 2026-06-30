#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metadatos inferidos para CSV mínimo (dataset intermedio artificial en memoria)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Comun.informe_examen import RegistroRespuesta
from Comun.modelos import Pregunta
from Comun.rutas import _ruta_json_escritura

__all__ = [
    "ResultadoExportDatasetIntermedio",
    "actualizar_desde_registros",
    "cobertura_metadatos_inferidos",
    "construir_materias_meta_artificiales",
    "enriquecer_preguntas_minimal",
    "exportar_csv_intermedio",
    "exportar_dataset_intermedio",
    "exportar_listado_materias_intermedio",
    "huella_pregunta",
    "reconstruir_catalogo_artificial",
    "resolver_path_metadatos_inferidos",
    "vaciar_metadatos_inferidos",
]

_VERSION = 2
_MIN_PREGUNTAS_POR_MATERIA = 2
_MAX_GRUPOS_ARTIFICIALES = 10
_PREFIJO_MATERIA = "Tema "
_MIN_INTENTOS_DIFICULTAD = 3
_MIN_INTENTOS_TIPO = 3
_MIN_PREGUNTAS_COBERTURA = 8
_FRACCION_COBERTURA_DATASET = 0.12

_COLUMNAS_MINIMAS = frozenset({"Pregunta", "A", "B", "C", "D", "Correcta"})
_COLUMNAS_INTERMEDIO = (
    "Id",
    "Pregunta",
    "A",
    "B",
    "C",
    "D",
    "Correcta",
    "Materia",
    "Grupo",
    "Dificultad",
    "Tipo",
    "Tematica",
)
COLUMNAS_CSV_INTERMEDIO = _COLUMNAS_INTERMEDIO

_COLUMNAS_LISTADO_MATERIAS = ("Materia", "Grupo", "Tematica", "Nivel", "Curso", "Semestre")

_RE_CALCULO = re.compile(
    r"(?i)(?:"
    r"\d+\s*[%=+\-*/^]|"
    r"\b(?:calcular?|calcula|resuelve|hallar|determina|evalua|integral|derivad|"
    r"matri[zx]|determinant|limite|ecuacion|sistema\s+de\s+ecuaciones|"
    r"probabilidad\s+de|media\s+de|varianza|desviacion)\b|"
    r"[∫∑√±≤≥]"
    r")"
)


def resolver_path_metadatos_inferidos() -> Path:
    return _ruta_json_escritura("metadatos_inferidos.json")


def huella_pregunta(pregunta: Pregunta | object) -> str:
    texto = (getattr(pregunta, "texto", "") or "").strip().lower()
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _vacio() -> dict[str, Any]:
    return {"version": _VERSION, "preguntas": {}, "catalogo": {}}


def _catalogo_vacio() -> dict[str, Any]:
    return {"materias": {}, "asignaciones": {}}


def _cargar_raw() -> dict[str, Any]:
    path = resolver_path_metadatos_inferidos()
    if not path.is_file():
        return _vacio()
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _vacio()
    if not isinstance(datos, dict):
        return _vacio()
    datos.setdefault("version", _VERSION)
    datos.setdefault("preguntas", {})
    datos.setdefault("catalogo", _catalogo_vacio())
    return datos


def _guardar_raw(datos: dict[str, Any]) -> None:
    path = resolver_path_metadatos_inferidos()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def vaciar_metadatos_inferidos() -> None:
    _guardar_raw(_vacio())


def inferir_tipo_desde_enunciado(texto: str) -> str:
    """Heurística léxica Teoria vs Calculo (sin columna Tipo en el CSV)."""
    if _RE_CALCULO.search(texto or ""):
        return "Calculo"
    return "Teoria"


def inferir_dificultad_desde_tasa(aciertos: int, intentos: int) -> str:
    if intentos <= 0:
        return ""
    tasa = aciertos / intentos
    if tasa >= 0.72:
        return "Facil"
    if tasa >= 0.42:
        return "Media"
    return "Dificil"


def inferir_tematica_desde_enunciado(texto: str) -> str:
    from types import SimpleNamespace

    from Comun.cadena_examen_dirigido import tokens_enunciado

    tokens = sorted(tokens_enunciado(SimpleNamespace(texto=texto)))
    for token in tokens:
        if not token.startswith("#"):
            return token
    if tokens:
        return tokens[0].lstrip("#")
    return ""


def _token_principal(texto: str) -> str:
    return inferir_tematica_desde_enunciado(texto) or "general"


def _nombre_materia_artificial(token: str) -> str:
    from Comun.cadena_examen_dirigido import etiqueta_concepto

    if token == "general":
        return f"{_PREFIJO_MATERIA}general"
    etiqueta = etiqueta_concepto(token)
    return f"{_PREFIJO_MATERIA}{etiqueta}"


def _asignar_grupos_artificiales(
    materias_meta: dict[str, dict[str, str]],
) -> None:
    """Reparte materias en bloques G1–G10 sin curso ni semestre."""
    orden = sorted(materias_meta.keys())
    if not orden:
        return
    n_grupos = min(_MAX_GRUPOS_ARTIFICIALES, max(1, len(orden)))
    tam_bloque = max(1, (len(orden) + n_grupos - 1) // n_grupos)
    for i, materia in enumerate(orden):
        grupo = min(_MAX_GRUPOS_ARTIFICIALES, i // tam_bloque + 1)
        materias_meta[materia]["grupo"] = str(grupo)


def reconstruir_catalogo_artificial(
    preguntas: list[Pregunta],
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """Agrupa preguntas en materias y grupos temáticos artificiales por contenido."""
    por_token: dict[str, list[Pregunta]] = defaultdict(list)
    for pregunta in preguntas:
        por_token[_token_principal(pregunta.texto)].append(pregunta)

    materias_meta: dict[str, dict[str, str]] = {}
    asignaciones: dict[str, str] = {}
    tokens_ordenados = sorted(por_token.keys(), key=lambda t: (-len(por_token[t]), t))
    variado_lote = 0

    for token in tokens_ordenados:
        bloque = por_token[token]
        if len(bloque) < _MIN_PREGUNTAS_POR_MATERIA and len(por_token) > 4:
            variado_lote += 1
            materia = f"{_PREFIJO_MATERIA}variado {(variado_lote - 1) // 5 + 1}"
            tematica = token
        else:
            materia = _nombre_materia_artificial(token)
            tematica = token

        if materia not in materias_meta:
            materias_meta[materia] = {
                "grupo": "",
                "nivel": "",
                "tematica": tematica,
                "curso": "",
                "semestre": "",
            }
        for pregunta in bloque:
            asignaciones[huella_pregunta(pregunta)] = materia

    _asignar_grupos_artificiales(materias_meta)
    return materias_meta, asignaciones


def construir_materias_meta_artificiales(
    preguntas: list[Pregunta],
) -> dict[str, dict[str, str]]:
    materias_meta, _ = reconstruir_catalogo_artificial(preguntas)
    return materias_meta


def _persistir_catalogo(
    materias_meta: dict[str, dict[str, str]],
    asignaciones: dict[str, str],
) -> None:
    datos = _cargar_raw()
    datos["catalogo"] = {
        "materias": materias_meta,
        "asignaciones": asignaciones,
    }
    _guardar_raw(datos)


def _catalogo_desde_datos(datos: dict[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    catalogo = datos.get("catalogo") or {}
    materias = dict(catalogo.get("materias") or {})
    asignaciones = dict(catalogo.get("asignaciones") or {})
    return materias, asignaciones


@dataclass(frozen=True)
class EntradaMetadatosInferidos:
    huella: str
    intentos: int
    aciertos: int
    fallos: int
    dificultad: str
    dificultad_fuente: str
    tipo: str
    tipo_fuente: str
    tematica: str
    tematica_fuente: str
    materia: str
    grupo: str


def _entrada_desde_bucket(
    huella: str,
    bucket: dict[str, Any],
    *,
    texto: str,
    materia: str = "",
    grupo: str = "",
) -> EntradaMetadatosInferidos:
    intentos = int(bucket.get("intentos") or 0)
    aciertos = int(bucket.get("aciertos") or 0)
    fallos = int(bucket.get("fallos") or max(0, intentos - aciertos))

    dificultad = ""
    dificultad_fuente = ""
    if intentos >= _MIN_INTENTOS_DIFICULTAD:
        dificultad = inferir_dificultad_desde_tasa(aciertos, intentos)
        dificultad_fuente = "estadisticas"

    tipo_heur = inferir_tipo_desde_enunciado(texto)
    tipo = tipo_heur
    tipo_fuente = "heuristica"
    tipos_obs = bucket.get("tipos_observados") or {}
    if isinstance(tipos_obs, dict) and intentos >= _MIN_INTENTOS_TIPO:
        mejor_tipo = ""
        mejor_n = 0
        for etiqueta, n in tipos_obs.items():
            n_int = int(n)
            if n_int > mejor_n:
                mejor_tipo = str(etiqueta)
                mejor_n = n_int
        if mejor_tipo in {"Teoria", "Calculo"} and mejor_n >= _MIN_INTENTOS_TIPO:
            tipo = mejor_tipo
            tipo_fuente = "estadisticas"

    tematica = (bucket.get("tematica") or "").strip()
    tematica_fuente = (bucket.get("tematica_fuente") or "").strip()
    if not tematica:
        tematica = inferir_tematica_desde_enunciado(texto)
        tematica_fuente = "heuristica" if tematica else ""

    return EntradaMetadatosInferidos(
        huella=huella,
        intentos=intentos,
        aciertos=aciertos,
        fallos=fallos,
        dificultad=dificultad,
        dificultad_fuente=dificultad_fuente,
        tipo=tipo,
        tipo_fuente=tipo_fuente,
        tematica=tematica,
        tematica_fuente=tematica_fuente,
        materia=materia,
        grupo=grupo,
    )


def _fusionar_bucket(bucket: dict[str, Any], registro: RegistroRespuesta) -> None:
    bucket["intentos"] = int(bucket.get("intentos") or 0) + 1
    if registro.acierto:
        bucket["aciertos"] = int(bucket.get("aciertos") or 0) + 1
    else:
        bucket["fallos"] = int(bucket.get("fallos") or 0) + 1
    bucket["texto"] = (registro.pregunta.texto or "").strip()

    tipo_obs = inferir_tipo_desde_enunciado(registro.pregunta.texto)
    tipos_obs = bucket.setdefault("tipos_observados", {})
    if isinstance(tipos_obs, dict):
        tipos_obs[tipo_obs] = int(tipos_obs.get(tipo_obs) or 0) + 1

    tematica = inferir_tematica_desde_enunciado(registro.pregunta.texto)
    if tematica and not bucket.get("tematica"):
        bucket["tematica"] = tematica
        bucket["tematica_fuente"] = "heuristica"


def actualizar_desde_registros(registros: list[RegistroRespuesta]) -> None:
    """Acumula intentos por enunciado y recalcula metadatos inferidos."""
    if not registros:
        return
    datos = _cargar_raw()
    preguntas: dict[str, Any] = datos["preguntas"]
    for registro in registros:
        huella = huella_pregunta(registro.pregunta)
        bucket = preguntas.setdefault(
            huella,
            {"intentos": 0, "aciertos": 0, "fallos": 0, "texto": ""},
        )
        _fusionar_bucket(bucket, registro)
        entrada = _entrada_desde_bucket(
            huella,
            bucket,
            texto=bucket.get("texto") or registro.pregunta.texto,
        )
        preguntas[huella] = {
            "intentos": entrada.intentos,
            "aciertos": entrada.aciertos,
            "fallos": entrada.fallos,
            "texto": bucket.get("texto") or "",
            "dificultad": entrada.dificultad,
            "dificultad_fuente": entrada.dificultad_fuente,
            "tipo": entrada.tipo,
            "tipo_fuente": entrada.tipo_fuente,
            "tematica": entrada.tematica,
            "tematica_fuente": entrada.tematica_fuente,
            "tipos_observados": bucket.get("tipos_observados") or {},
        }
    _guardar_raw(datos)


def _entrada_para_pregunta(
    pregunta: Pregunta,
    datos: dict[str, Any],
) -> EntradaMetadatosInferidos | None:
    huella = huella_pregunta(pregunta)
    bucket = (datos.get("preguntas") or {}).get(huella)
    if not bucket:
        tipo = inferir_tipo_desde_enunciado(pregunta.texto)
        tematica = inferir_tematica_desde_enunciado(pregunta.texto)
        return EntradaMetadatosInferidos(
            huella=huella,
            intentos=0,
            aciertos=0,
            fallos=0,
            dificultad="",
            dificultad_fuente="",
            tipo=tipo,
            tipo_fuente="heuristica",
            tematica=tematica,
            tematica_fuente="heuristica" if tematica else "",
            materia="",
            grupo="",
        )
    return _entrada_desde_bucket(
        huella,
        bucket,
        texto=bucket.get("texto") or pregunta.texto,
    )


def enriquecer_preguntas_minimal(
    preguntas: list[Pregunta],
    *,
    aplicar_catalogo: bool = False,
) -> list[Pregunta]:
    """Aplica metadatos inferidos sobre CSV mínimo; catálogo artificial opcional en preguntas."""
    if not preguntas:
        return preguntas
    materias_meta, asignaciones = reconstruir_catalogo_artificial(preguntas)
    _persistir_catalogo(materias_meta, asignaciones)
    datos = _cargar_raw()
    for pregunta in preguntas:
        entrada = _entrada_para_pregunta(pregunta, datos)
        if entrada is None:
            continue
        if entrada.dificultad:
            pregunta.dificultad = entrada.dificultad
        if entrada.tipo:
            pregunta.tipo = entrada.tipo
        if entrada.tematica:
            pregunta.tematica = entrada.tematica
        if aplicar_catalogo:
            huella = huella_pregunta(pregunta)
            materia = asignaciones.get(huella, "")
            if materia:
                pregunta.materia = materia
                grupo = str(materias_meta.get(materia, {}).get("grupo") or "")
                if grupo:
                    pregunta.grupo = grupo
    return preguntas


def cobertura_metadatos_inferidos(
    preguntas: list[Pregunta],
) -> dict[str, Any]:
    """Cuántas preguntas tienen dificultad/tipo inferidos con confianza suficiente."""
    datos = _cargar_raw()
    total = len(preguntas)
    con_dificultad = 0
    con_tipo_stats = 0
    con_tematica = 0
    tipos: set[str] = set()
    dificultades: set[str] = set()
    for pregunta in preguntas:
        entrada = _entrada_para_pregunta(pregunta, datos)
        if entrada is None:
            continue
        if entrada.dificultad and entrada.dificultad_fuente == "estadisticas":
            con_dificultad += 1
            dificultades.add(entrada.dificultad)
        if entrada.tipo:
            tipos.add(entrada.tipo)
            if entrada.tipo_fuente == "estadisticas":
                con_tipo_stats += 1
        if entrada.tematica:
            con_tematica += 1
    umbral = max(_MIN_PREGUNTAS_COBERTURA, int(total * _FRACCION_COBERTURA_DATASET))
    materias_meta, _ = reconstruir_catalogo_artificial(preguntas)
    n_materias = len(materias_meta)
    con_materia = sum(1 for p in preguntas if (p.materia or "").strip())
    tiene_grupos = any(str(m.get("grupo") or "").strip() for m in materias_meta.values())
    dataset_intermedio = total > 0 and con_dificultad >= umbral
    return {
        "total": total,
        "con_dificultad": con_dificultad,
        "con_tipo_stats": con_tipo_stats,
        "con_tematica": con_tematica,
        "con_materia": con_materia,
        "n_materias": n_materias,
        "tipos": tipos,
        "dificultades": dificultades,
        "dataset_intermedio": dataset_intermedio,
        "tiene_tipos_pregunta": {"Teoria", "Calculo"}.issubset(tipos),
        "tiene_grupos_tematicos": tiene_grupos and n_materias >= 2,
    }


def exportar_csv_intermedio(
    preguntas: list[Pregunta],
    destino: Path,
    *,
    incluir_sin_datos: bool = True,
) -> int:
    """Escribe CSV intermedio usable en el juego completo (sin curso/semestre)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    copia = [
        Pregunta(
            texto=p.texto,
            materia=p.materia,
            tematica=p.tematica,
            dificultad=p.dificultad,
            tipo=p.tipo,
            grupo=p.grupo,
            nivel=p.nivel,
            curso=p.curso,
            semestre=p.semestre,
            opciones=dict(p.opciones),
            correcta=p.correcta,
            fuente=p.fuente,
        )
        for p in preguntas
    ]
    enriquecer_preguntas_minimal(copia, aplicar_catalogo=True)
    filas = 0
    with destino.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(
            f_out,
            fieldnames=list(_COLUMNAS_INTERMEDIO),
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        for i, pregunta in enumerate(copia, start=1):
            if not incluir_sin_datos and not (
                pregunta.dificultad or pregunta.materia
            ):
                continue
            writer.writerow(
                {
                    "Id": str(i),
                    "Pregunta": pregunta.texto,
                    "A": pregunta.opciones.get("A", ""),
                    "B": pregunta.opciones.get("B", ""),
                    "C": pregunta.opciones.get("C", ""),
                    "D": pregunta.opciones.get("D", ""),
                    "Correcta": pregunta.correcta,
                    "Materia": pregunta.materia or "",
                    "Grupo": pregunta.grupo or "",
                    "Dificultad": pregunta.dificultad or "",
                    "Tipo": pregunta.tipo or "",
                    "Tematica": pregunta.tematica or "",
                }
            )
            filas += 1
    return filas


def exportar_listado_materias_intermedio(
    preguntas: list[Pregunta],
    destino: Path,
) -> int:
    """Listado de materias artificiales (Grupo G1–G10) para repaso por área."""
    copia = [
        Pregunta(
            texto=p.texto,
            materia=p.materia,
            tematica=p.tematica,
            dificultad=p.dificultad,
            tipo=p.tipo,
            grupo=p.grupo,
            nivel=p.nivel,
            curso=p.curso,
            semestre=p.semestre,
            opciones=dict(p.opciones),
            correcta=p.correcta,
            fuente=p.fuente,
        )
        for p in preguntas
    ]
    enriquecer_preguntas_minimal(copia, aplicar_catalogo=True)
    meta = construir_materias_meta_artificiales(copia)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(
            f_out,
            fieldnames=list(_COLUMNAS_LISTADO_MATERIAS),
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        for materia in sorted(meta.keys()):
            bucket = meta[materia]
            writer.writerow(
                {
                    "Materia": materia,
                    "Grupo": bucket.get("grupo", ""),
                    "Tematica": bucket.get("tematica", ""),
                    "Nivel": "",
                    "Curso": "",
                    "Semestre": "",
                }
            )
    return len(meta)


@dataclass(frozen=True)
class ResultadoExportDatasetIntermedio:
    csv: Path
    listado: Path
    n_preguntas: int
    n_materias: int
    con_dificultad: int
    total: int


def exportar_dataset_intermedio(
    preguntas: list[Pregunta],
    *,
    carpeta: Path | None = None,
) -> ResultadoExportDatasetIntermedio:
    """Exporta CSV intermedio + listado de materias junto al banco de preguntas."""
    from Comun.rutas import path_preguntas

    base = (carpeta or path_preguntas().parent).resolve()
    csv_path = base / "Preguntas_intermedio.csv"
    listado_path = base / "listado_materias_intermedio.csv"
    n_csv = exportar_csv_intermedio(preguntas, csv_path)
    n_list = exportar_listado_materias_intermedio(preguntas, listado_path)
    cobertura = cobertura_metadatos_inferidos(preguntas)
    return ResultadoExportDatasetIntermedio(
        csv=csv_path,
        listado=listado_path,
        n_preguntas=n_csv,
        n_materias=n_list,
        con_dificultad=int(cobertura.get("con_dificultad") or 0),
        total=int(cobertura.get("total") or len(preguntas)),
    )
