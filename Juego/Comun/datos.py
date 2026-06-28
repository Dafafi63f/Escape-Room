#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga del banco de preguntas, materias y plantillas."""

# pyright: reportMissingImports=false

from __future__ import annotations

import csv
import json
from pathlib import Path

from Comun.modelos import BancoPreguntas, Pregunta
from Comun.preguntas_resistencia import USOS_PLANTILLA_BETA_JUEGO
from Comun.utils_plantillas_core import (
    clave_contenido,
    clave_contenido_sin_materia,
    claves_desde_csv,
    expandir_plantilla_instancias,
    quitar_etiqueta_materia_enunciado,
    tiene_placeholders,
)


def claves_dataset(path_csv: Path) -> set[tuple]:
    return claves_desde_csv(path_csv)


def _plantilla_a_pregunta(inst: dict, materias_meta: dict[str, dict[str, str]]) -> Pregunta | None:
    correcta = inst["correcta"]
    if correcta not in {"A", "B", "C", "D"}:
        return None
    texto = quitar_etiqueta_materia_enunciado(inst["pregunta"], inst["materia"])
    opciones = inst["opciones"]
    if not texto or not all(opciones.values()):
        return None
    bloque = texto + "".join(opciones.values())
    if tiene_placeholders(bloque):
        return None
    materia = inst["materia"]
    mm = materias_meta.get(materia, {})
    return Pregunta(
        texto=texto,
        materia=materia,
        tematica=mm.get("tematica", ""),
        dificultad=inst["dificultad"],
        tipo=inst["tipo"],
        grupo=mm.get("grupo", ""),
        nivel=mm.get("nivel", ""),
        curso=mm.get("curso", ""),
        semestre=mm.get("semestre", ""),
        opciones=opciones,
        correcta=correcta,
        fuente="plantilla",
    )


def claves_contenido_dataset(path_csv: Path) -> set[tuple]:
    """Claves de contenido del CSV sin materia (misma pregunta en otra asignatura)."""
    claves: set[tuple] = set()
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            opciones = {L: (row.get(L) or "").strip() for L in "ABCD"}
            correcta = (row.get("Correcta") or "").strip().upper()
            texto = (row.get("Pregunta") or "").strip()
            if not texto:
                continue
            claves.add(clave_contenido_sin_materia(texto, opciones, correcta))
    return claves


def cargar_preguntas_plantillas(
    path_json: Path,
    materias_meta: dict[str, dict[str, str]],
    *,
    solo_fuera_dataset: bool,
    claves_ds: set[tuple],
    usos_permitidos: frozenset[str] | None = None,
    claves_contenido_ds: set[tuple] | None = None,
) -> list[Pregunta]:
    if not path_json.exists():
        raise FileNotFoundError(f"No se encontró plantillas: {path_json}")

    try:
        data = json.loads(path_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Plantillas JSON inválidas ({path_json}): {e}") from e
    preguntas: list[Pregunta] = []
    vistos: set[tuple] = set()

    for tema, items in data.items():
        if not tema:
            continue
        for t in items:
            for inst in expandir_plantilla_instancias(tema, t):
                uso = (inst.get("uso") or "").strip().lower()
                if usos_permitidos is not None and uso not in usos_permitidos:
                    continue
                k = clave_contenido(
                    inst["materia"],
                    inst["pregunta"],
                    inst["opciones"],
                    inst["correcta"],
                )
                if solo_fuera_dataset and k in claves_ds:
                    continue
                if claves_contenido_ds is not None:
                    k_sin = clave_contenido_sin_materia(
                        inst["pregunta"],
                        inst["opciones"],
                        inst["correcta"],
                    )
                    if k_sin in claves_contenido_ds:
                        continue
                if k in vistos:
                    continue
                p = _plantilla_a_pregunta(inst, materias_meta)
                if p:
                    vistos.add(k)
                    preguntas.append(p)
    return preguntas


def cargar_banco_todo(
    path_csv: Path,
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
) -> list[Pregunta]:
    claves = claves_dataset(path_csv)
    revisadas = cargar_preguntas(path_csv, materias_meta)
    extra = cargar_preguntas_plantillas(
        path_plantillas,
        materias_meta,
        solo_fuera_dataset=True,
        claves_ds=claves,
        usos_permitidos=USOS_PLANTILLA_BETA_JUEGO,
        claves_contenido_ds=claves_contenido_dataset(path_csv),
    )
    return revisadas + extra


def contar_bancos(
    path_csv: Path,
    path_plantillas: Path | None,
    materias_meta: dict,
) -> dict[BancoPreguntas, int]:
    n_ds = len(cargar_preguntas(path_csv, materias_meta))
    if path_plantillas is None:
        return {
            BancoPreguntas.DATASET: n_ds,
            BancoPreguntas.PLANTILLAS_TODO: n_ds,
        }
    claves = claves_dataset(path_csv)
    n_extra = len(
        cargar_preguntas_plantillas(
            path_plantillas,
            materias_meta,
            solo_fuera_dataset=True,
            claves_ds=claves,
            usos_permitidos=USOS_PLANTILLA_BETA_JUEGO,
            claves_contenido_ds=claves_contenido_dataset(path_csv),
        )
    )
    return {
        BancoPreguntas.DATASET: n_ds,
        BancoPreguntas.PLANTILLAS_TODO: n_ds + n_extra,
    }


def cargar_orden_materias(path_csv: Path) -> list[str]:
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el listado de materias: {path_csv}")
    orden: list[str] = []
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            materia = (row.get("Materia") or "").strip()
            if materia:
                orden.append(materia)
    return orden


def cargar_materias(path_csv: Path) -> dict[str, dict[str, str]]:
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el listado de materias: {path_csv}")

    materias: dict[str, dict[str, str]] = {}
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            materia = (row.get("Materia") or "").strip()
            if not materia:
                continue
            materias[materia] = {
                "grupo": (row.get("Grupo") or "").strip(),
                "nivel": (row.get("Nivel") or "").strip(),
                "tematica": (row.get("Tematica") or "").strip(),
                "curso": (
                    row.get("Curso")
                    or row.get("Año")
                    or row.get("Ano")
                    or ""
                ).strip(),
                "semestre": (row.get("Semestre") or "").strip(),
            }
    return materias


def cargar_plantillas_materia(path_json: Path | None, materia: str) -> list[dict]:
    """Plantillas base de ``plantillas.json`` para una asignatura (sin expandir)."""
    if path_json is None or not path_json.exists():
        return []
    try:
        data = json.loads(path_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Plantillas JSON inválidas ({path_json}): {e}") from e
    items = data.get(materia)
    if not isinstance(items, list):
        return []
    return list(items)


def cargar_preguntas(path_csv: Path, materias_meta: dict[str, dict[str, str]]) -> list[Pregunta]:
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {path_csv}")

    from Comun.contenido import es_csv_minimal, leer_cabeceras_csv

    csv_minimal = es_csv_minimal(leer_cabeceras_csv(path_csv))
    preguntas: list[Pregunta] = []
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            correcta = (row.get("Correcta") or "").strip().upper()
            if correcta not in {"A", "B", "C", "D"}:
                continue
            materia_raw = (row.get("Materia") or row.get("Tema") or "").strip()
            if not materia_raw and not csv_minimal:
                materia_raw = "Sin materia"
            mm = materias_meta.get(materia_raw, {})

            def _campo(csv_key: str, meta_key: str) -> str:
                v = (row.get(csv_key) or "").strip()
                return v if v else mm.get(meta_key, "")

            dificultad_raw = (row.get("Dificultad") or "").strip()
            if not dificultad_raw and not csv_minimal:
                dificultad_raw = "Desconocida"
            tipo_raw = (row.get("Tipo") or "").strip()
            if not tipo_raw and not csv_minimal:
                tipo_raw = "General"

            pregunta = Pregunta(
                texto=(row.get("Pregunta") or "").strip(),
                materia=materia_raw,
                tematica=_campo("Tematica", "tematica"),
                dificultad=dificultad_raw,
                tipo=tipo_raw,
                grupo=_campo("Grupo", "grupo"),
                nivel=_campo("Nivel", "nivel"),
                curso=_campo("Curso", "curso"),
                semestre=_campo("Semestre", "semestre"),
                opciones={
                    "A": (row.get("A") or "").strip(),
                    "B": (row.get("B") or "").strip(),
                    "C": (row.get("C") or "").strip(),
                    "D": (row.get("D") or "").strip(),
                },
                correcta=correcta,
            )
            if pregunta.texto and all(pregunta.opciones.values()):
                preguntas.append(pregunta)
    return preguntas
