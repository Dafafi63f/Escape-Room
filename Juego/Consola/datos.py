#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga del banco de preguntas, materias y plantillas."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from . import _scripts_path  # noqa: F401 — registra Files/Scripts en sys.path
from .modelos import BancoPreguntas, ETIQUETA_BANCO, Pregunta
from utils_plantillas_core import (  # noqa: E402
    clave_contenido,
    expandir_plantilla_instancias,
    claves_desde_csv,
    tiene_placeholders,
)


def claves_dataset(path_csv: Path) -> set[tuple]:
    return claves_desde_csv(path_csv)


def _plantilla_a_pregunta(inst: dict, materias_meta: dict[str, dict[str, str]]) -> Pregunta | None:
    correcta = inst["correcta"]
    if correcta not in {"A", "B", "C", "D"}:
        return None
    texto = inst["pregunta"]
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


def cargar_preguntas_plantillas(
    path_json: Path,
    materias_meta: dict[str, dict[str, str]],
    *,
    solo_fuera_dataset: bool,
    claves_ds: set[tuple],
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
                k = clave_contenido(
                    inst["materia"],
                    inst["pregunta"],
                    inst["opciones"],
                    inst["correcta"],
                )
                if solo_fuera_dataset and k in claves_ds:
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
        path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
    )
    return revisadas + extra


def contar_bancos(
    path_csv: Path, path_plantillas: Path, materias_meta: dict
) -> dict[BancoPreguntas, int]:
    n_ds = len(cargar_preguntas(path_csv, materias_meta))
    claves = claves_dataset(path_csv)
    n_extra = len(
        cargar_preguntas_plantillas(
            path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
        )
    )
    return {
        BancoPreguntas.DATASET: n_ds,
        BancoPreguntas.PLANTILLAS_EXTRA: n_extra,
        BancoPreguntas.PLANTILLAS_TODO: n_ds + n_extra,
    }


def elegir_banco_preguntas(
    path_csv: Path,
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
) -> tuple[list[Pregunta], BancoPreguntas]:
    try:
        conteos = contar_bancos(path_csv, path_plantillas, materias_meta)
    except FileNotFoundError as e:
        print(str(e))
        print("Usando solo el dataset revisado.")
        return cargar_preguntas(path_csv, materias_meta), BancoPreguntas.DATASET

    n_ds = conteos[BancoPreguntas.DATASET]
    n_extra = conteos[BancoPreguntas.PLANTILLAS_EXTRA]
    n_todo = conteos[BancoPreguntas.PLANTILLAS_TODO]

    from .entrada_menu import elegir_indice_menu
    from .navegacion import ContextoPantalla, VolverAtras

    def _mostrar_menu_banco() -> None:
        print("\nBanco de preguntas:")
        print(
            f"  1) Dataset revisado — MODO SEGURO ({n_ds} preguntas) [por defecto, recomendado]"
        )
        print(
            f"  2) Todo — MODO BETA ({n_ds} + {n_extra} = {n_todo}): "
            "dataset + plantillas no revisadas"
        )
        print(f"  3) Solo plantillas extra — MODO BETA ({n_extra} no revisadas)")
        print("     La opcion 1 es el banco seguro. Las opciones 2 y 3 incluyen contenido beta.")

    mapa_banco = {
        1: BancoPreguntas.DATASET,
        2: BancoPreguntas.PLANTILLAS_TODO,
        3: BancoPreguntas.PLANTILLAS_EXTRA,
    }

    from .navegacion import mostrar_transicion

    mostrar_transicion(
        _mostrar_menu_banco,
        contexto=ContextoPantalla(titulo="Banco de preguntas", reimprimir=_mostrar_menu_banco),
    )

    while True:
        try:
            idx = elegir_indice_menu(
                3,
                defecto=1,
                permitir_atras=True,
                prompt="Selecciona banco",
            )
        except VolverAtras:
            raise
        banco = mapa_banco[idx]
        n = conteos[banco]
        if n == 0:
            print("Ese banco no tiene preguntas jugables. Prueba otra opcion.")
            continue
        break

    modo_txt, desc = ETIQUETA_BANCO[banco]
    print(f"\n>>> {modo_txt}: {desc} ({n} preguntas cargadas)")
    if banco != BancoPreguntas.DATASET:
        print(
            "AVISO: incluye preguntas no revisadas. "
            "Usa el banco 1 (modo seguro) para evaluación fiable del TFG."
        )

    if banco == BancoPreguntas.DATASET:
        preguntas = cargar_preguntas(path_csv, materias_meta)
    elif banco == BancoPreguntas.PLANTILLAS_TODO:
        preguntas = cargar_banco_todo(path_csv, path_plantillas, materias_meta)
    else:
        claves = claves_dataset(path_csv)
        preguntas = cargar_preguntas_plantillas(
            path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
        )
    return preguntas, banco


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


def cargar_preguntas(path_csv: Path, materias_meta: dict[str, dict[str, str]]) -> list[Pregunta]:
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {path_csv}")

    preguntas: list[Pregunta] = []
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            correcta = (row.get("Correcta") or "").strip().upper()
            if correcta not in {"A", "B", "C", "D"}:
                continue
            materia = (row.get("Materia") or row.get("Tema") or "Sin materia").strip()
            mm = materias_meta.get(materia, {})

            def _campo(csv_key: str, meta_key: str) -> str:
                v = (row.get(csv_key) or "").strip()
                return v if v else mm.get(meta_key, "")

            pregunta = Pregunta(
                texto=(row.get("Pregunta") or "").strip(),
                materia=materia,
                tematica=_campo("Tematica", "tematica"),
                dificultad=(row.get("Dificultad") or "Desconocida").strip(),
                tipo=(row.get("Tipo") or "General").strip(),
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
