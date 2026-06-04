# -*- coding: utf-8 -*-
"""Sincronización de ``plantillas.json`` con el CSV cerrado (sin tocar Preguntas.csv)."""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"

from objetivos_balanceo import (  # noqa: E402
    MIN_PLANTILLAS_POR_MATERIA_FACTOR,
    TARGET_TOTAL_PREGUNTAS,
    USO_PLANTILLA_DATASET,
    plantillas_minimas_por_materia,
    preguntas_por_materia,
)
from plantillas_repuesto_catalogo import REPUESTO_CATALOGO  # noqa: E402
from utils_deduplicacion import clave_enunciado, deduplicar_plantillas_dict, quitar_plantillas_presentes_en_dataset  # noqa: E402
from utils_orden_temas import cargar_orden_temas  # noqa: E402


def _norm_key(text: str) -> str:
    return (text or "").strip().lower()


def _key_template(tema: str, t: dict) -> tuple:
    return (
        _norm_key(tema),
        _norm_key(t.get("pregunta", "")),
        _norm_key(t.get("A", "")),
        _norm_key(t.get("B", "")),
        _norm_key(t.get("C", "")),
        _norm_key(t.get("D", "")),
        _norm_key(t.get("correcta", "")),
    )


def _key_row(r: dict) -> tuple:
    return (
        _norm_key(r.get("Materia") or r.get("Tema", "")),
        _norm_key(r.get("Pregunta", "")),
        _norm_key(r.get("A", "")),
        _norm_key(r.get("B", "")),
        _norm_key(r.get("C", "")),
        _norm_key(r.get("D", "")),
        _norm_key(r.get("Correcta", "")),
    )


def inyectar_dataset() -> int:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))

    existing_keys = {_key_template(tema, t) for tema, items in plantillas.items() for t in items}
    added = already_present = missing_topic = skipped_variantes = 0

    for r in rows:
        if re.search(r"\(\s*variante(?:\s+\d+)?\s*\)\s*$", (r.get("Pregunta") or ""), flags=re.I):
            skipped_variantes += 1
            continue
        tema = (r.get("Materia") or r.get("Tema") or "").strip()
        if not tema:
            continue
        if tema not in plantillas:
            plantillas[tema] = []
            missing_topic += 1
        k = _key_row(r)
        if k in existing_keys:
            already_present += 1
            continue
        plantillas[tema].append(
            {
                "pregunta": r["Pregunta"],
                "A": r["A"],
                "B": r["B"],
                "C": r["C"],
                "D": r["D"],
                "correcta": r["Correcta"],
                "dificultad": r["Dificultad"],
                "tipo": r["Tipo"],
                "uso": USO_PLANTILLA_DATASET,
            }
        )
        existing_keys.add(k)
        added += 1

    final_keys = {_key_template(tema, t) for tema, items in plantillas.items() for t in items}
    missing_from_dataset = sum(1 for r in rows if _key_row(r) not in final_keys)

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Filas dataset: {len(rows)}")
    print(f"Añadidas a plantillas: {added}")
    print(f"Ya presentes: {already_present}")
    print(f"Temas creados: {missing_topic}")
    print(f"Saltadas variante: {skipped_variantes}")
    print(f"Faltantes tras inyección: {missing_from_dataset}")
    return 0 if missing_from_dataset == 0 else 1


def limpiar_plantillas(*, inplace: bool, dry_run: bool) -> int:
    if not inplace and not dry_run:
        print("Indica --inplace o --dry-run")
        return 2
    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))

    antes = sum(len(v) for v in plantillas.values())
    limpias, ex, sim = deduplicar_plantillas_dict(plantillas)
    final, cruce = quitar_plantillas_presentes_en_dataset(limpias, rows)
    despues = sum(len(v) for v in final.values())

    print(f"Antes: {antes}")
    print(f"Tras dedup: {sum(len(v) for v in limpias.values())} (exactas -{ex}, similares -{sim})")
    print(f"Quitadas vs dataset (pool): {cruce}")
    print(f"Final: {despues}")

    if inplace:
        with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
            json.dump(final, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Guardado: {PATH_PLANTILLAS}")
    return 0


def _norm_corpus(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _corpus_por_materia() -> dict[str, str]:
    out: dict[str, list[str]] = {}
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            bloque = " ".join(row.get(k, "") for k in ("Pregunta", "A", "B", "C", "D"))
            out.setdefault(row["Materia"], []).append(_norm_corpus(bloque))
    return {m: " ".join(parts) for m, parts in out.items()}


def sincronizar_repuesto(*, inplace: bool, dry_run: bool) -> None:
    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas: dict[str, list] = json.load(f)

    corpus = _corpus_por_materia()
    temas, _ = cargar_orden_temas()
    claves_globales = {
        clave_enunciado({"Pregunta": t.get("pregunta", ""), **t})
        for items in plantillas.values()
        for t in items
    }

    renombrados = anadidos = omitidos_cubiertos = omitidos_dup = 0

    for items in plantillas.values():
        for t in items:
            if t.get("uso") == "reserva":
                t["uso"] = "repuesto"
                renombrados += 1

    for materia in temas:
        for entrada in REPUESTO_CATALOGO.get(materia, []):
            corp = corpus.get(materia, "")
            if any(
                (len(_norm_corpus(et)) <= 6 and f" {_norm_corpus(et)} " in f" {corp} ")
                or (len(_norm_corpus(et)) > 6 and _norm_corpus(et) in corp)
                for et in entrada.get("etiquetas", [])
                if len(_norm_corpus(et)) >= 3
            ):
                omitidos_cubiertos += 1
                continue
            tpl = {k: entrada[k] for k in ("pregunta", "A", "B", "C", "D", "correcta", "dificultad", "tipo")}
            tpl["uso"] = "repuesto"
            clave = clave_enunciado({"Pregunta": tpl["pregunta"], **tpl})
            if clave in claves_globales:
                omitidos_dup += 1
                continue
            if materia not in plantillas:
                plantillas[materia] = []
            plantillas[materia].append(tpl)
            claves_globales.add(clave)
            anadidos += 1

    print(f"reserva→repuesto: {renombrados}")
    print(f"Nuevas plantillas repuesto: {anadidos}")
    print(f"Omitidas (tema ya en dataset): {omitidos_cubiertos}")
    print(f"Omitidas (duplicado): {omitidos_dup}")

    if dry_run or not inplace:
        if not inplace:
            print("(dry-run: no se guardó plantillas.json)")
        return

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Guardado: {PATH_PLANTILLAS}")


def comprobar_cobertura(*, solo_comprobar: bool) -> int:
    if not solo_comprobar:
        print("Inyectando dataset en plantillas…")
        rc = inyectar_dataset()
        if rc != 0:
            return rc

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plant = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))
    por_plant = {m: len(plant.get(m, [])) for m in plant}
    por_ds = Counter(r["Materia"] for r in rows)
    minimo = plantillas_minimas_por_materia()
    temas, _ = cargar_orden_temas()

    msgs: list[str] = []
    total_plant = sum(por_plant.values())
    if total_plant <= TARGET_TOTAL_PREGUNTAS:
        msgs.append(f"Total plantillas ({total_plant}) no supera el dataset ({TARGET_TOTAL_PREGUNTAS})")
    for tema in temas:
        n_plant = por_plant.get(tema, 0)
        n_ds = por_ds.get(tema, preguntas_por_materia())
        if n_plant <= n_ds:
            msgs.append(f"{tema!r}: {n_plant} plantillas <= {n_ds} en dataset")
        elif n_plant < minimo:
            msgs.append(
                f"{tema!r}: {n_plant} < mínimo {minimo} ({MIN_PLANTILLAS_POR_MATERIA_FACTOR}× dataset)"
            )

    print(f"Dataset: {TARGET_TOTAL_PREGUNTAS} preguntas ({preguntas_por_materia()}/materia)")
    print(f"Plantillas: {total_plant} (mínimo {minimo}/materia)")
    if not msgs:
        print("OK: cobertura de plantillas adecuada.")
        return 0
    print("Desviaciones:")
    for m in msgs:
        print(f"  - {m}")
    return 1


def pipeline_completo() -> int:
    """limpiar → inyectar → repuesto → dedup plantillas (duplicados)."""
    from duplicados_lib import ejecutar_plantillas

    rc = limpiar_plantillas(inplace=True, dry_run=False)
    if rc:
        return rc
    rc = inyectar_dataset()
    if rc:
        return rc
    sincronizar_repuesto(inplace=True, dry_run=False)
    return ejecutar_plantillas()
