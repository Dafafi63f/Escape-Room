#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reduce el dataset al objetivo manteniendo balance por tema y evitando:
- Duplicados exactos.
- Preguntas muy similares (mismo enunciado con leves cambios o distractores distintos).

Uso:
  python Files/reducir_dataset_objetivo.py --target-total 400 --inplace
"""

import argparse
import csv
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import guardar_filas_csv, materia_de_fila
from borrar_pycache import borrar_pycache_en_proyecto


BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
BACKUP_DIR = BASE / "Data" / "backups"


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("¿", "").replace("?", "")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> set[str]:
    return set(normalize_text(text).split())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def option_set(row: dict) -> set[str]:
    return {
        normalize_text(row.get("A", "")),
        normalize_text(row.get("B", "")),
        normalize_text(row.get("C", "")),
        normalize_text(row.get("D", "")),
    }


def is_too_similar(candidate: dict, selected: list[dict]) -> bool:
    cand_q = normalize_text(candidate["Pregunta"])
    cand_tokens = tokenize(candidate["Pregunta"])
    cand_opts = option_set(candidate)

    for s in selected:
        sel_q = normalize_text(s["Pregunta"])
        sel_tokens = tokenize(s["Pregunta"])
        sel_opts = option_set(s)

        # Exacto por enunciado y mismo tema
        if cand_q == sel_q:
            return True

        seq = SequenceMatcher(None, cand_q, sel_q).ratio()
        jac_q = jaccard(cand_tokens, sel_tokens)
        jac_opts = jaccard(cand_opts, sel_opts)

        # Misma idea con redacción muy parecida + distractores cercanos
        if seq >= 0.93 and jac_q >= 0.75:
            return True

        # Enunciado casi idéntico aunque cambien distractores
        if seq >= 0.95 and jac_q >= 0.82:
            return True

        # Misma plantilla con pequeñas variaciones léxicas + mismas opciones base
        if jac_q >= 0.88 and jac_opts >= 0.75:
            return True

    return False


def dedup_exact(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        key = (
            materia_de_fila(r),
            normalize_text(r["Pregunta"]),
            normalize_text(r.get("A", "")),
            normalize_text(r.get("B", "")),
            normalize_text(r.get("C", "")),
            normalize_text(r.get("D", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def pick_diverse_rows(rows: list[dict], k: int) -> list[dict]:
    # Priorizamos combinación Tipo+Dificultad para conservar variedad.
    buckets = defaultdict(list)
    for r in rows:
        buckets[(r.get("Tipo", ""), r.get("Dificultad", ""))].append(r)

    # Round-robin entre buckets para no sesgar.
    bucket_keys = sorted(buckets.keys(), key=lambda x: (x[0], x[1]))
    for key in bucket_keys:
        buckets[key].sort(key=lambda r: int(r["Id"]))

    selected = []
    i = 0
    while len(selected) < k:
        progressed = False
        for key in bucket_keys:
            if i < len(buckets[key]):
                cand = buckets[key][i]
                if not is_too_similar(cand, selected):
                    selected.append(cand)
                    if len(selected) >= k:
                        break
                progressed = True
        if not progressed:
            break
        i += 1

    # Si faltan por filtros estrictos, rellenar con los menos similares restantes.
    if len(selected) < k:
        leftovers = [r for r in rows if r not in selected]
        for cand in leftovers:
            if len(selected) >= k:
                break
            if not is_too_similar(cand, selected):
                selected.append(cand)
        for cand in leftovers:
            if len(selected) >= k:
                break
            # Último recurso: completar cupo sin filtro de similitud.
            if cand not in selected:
                selected.append(cand)

    return selected[:k]


def reduce_dataset(rows: list[dict], target_total: int) -> list[dict]:
    by_topic = defaultdict(list)
    for r in rows:
        by_topic[materia_de_fila(r)].append(r)

    ordered_topics, _ = cargar_orden_temas()
    topics = [t for t in ordered_topics if t in by_topic] + [
        t for t in by_topic.keys() if t not in set(ordered_topics)
    ]
    n_topics = len(topics)
    if n_topics == 0:
        return []

    base = target_total // n_topics
    remainder = target_total % n_topics
    target_per_topic = {t: base for t in topics}
    for t in topics[:remainder]:
        target_per_topic[t] += 1

    reduced = []
    for topic in topics:
        topic_rows = dedup_exact(by_topic[topic])
        keep = min(target_per_topic[topic], len(topic_rows))
        chosen = pick_diverse_rows(topic_rows, keep)
        reduced.extend(chosen)

    # Si por falta de filas en algún tema no llegamos al total, rellenar desde temas con sobrante.
    if len(reduced) < target_total:
        current_by_topic = defaultdict(int)
        for r in reduced:
            current_by_topic[materia_de_fila(r)] += 1

        deficit = target_total - len(reduced)
        extras = []
        for topic in topics:
            topic_rows = dedup_exact(by_topic[topic])
            already = current_by_topic[topic]
            if already >= len(topic_rows):
                continue
            extras.extend(topic_rows[already:])

        extras = sorted(extras, key=lambda r: int(r["Id"]))
        for cand in extras:
            if deficit <= 0:
                break
            if not is_too_similar(cand, reduced):
                reduced.append(cand)
                deficit -= 1

        for cand in extras:
            if deficit <= 0:
                break
            if cand not in reduced:
                reduced.append(cand)
                deficit -= 1

    reduced = reduced[:target_total]
    topic_rank = {t: i for i, t in enumerate(ordered_topics)}
    fallback = len(topic_rank)
    reduced = sorted(reduced, key=lambda r: (topic_rank.get(materia_de_fila(r), fallback), int(r["Id"])))
    for i, r in enumerate(reduced, start=1):
        r["Id"] = str(i)
    return reduced


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-total", type=int, default=400)
    parser.add_argument("--inplace", action="store_true", help="Sobrescribe Data/Preguntas.csv")
    parser.add_argument("--output", type=str, default="Data/Preguntas_reducido.csv")
    args = parser.parse_args()

    if args.target_total <= 0:
        raise ValueError("target-total debe ser > 0")

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    reduced = reduce_dataset(rows, args.target_total)

    output_path = PATH_PREGUNTAS if args.inplace else (BASE / args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.inplace:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"Preguntas_backup_{stamp}.csv"
        shutil.copy2(PATH_PREGUNTAS, backup_path)
        safe_backup_path = str(backup_path).encode("ascii", "replace").decode("ascii")
        print(f"Backup creado: {safe_backup_path}")

    guardar_filas_csv(fieldnames, reduced, output_path)

    by_topic = defaultdict(int)
    for r in reduced:
        by_topic[materia_de_fila(r)] += 1

    print(f"Entrada: {len(rows)} | Salida: {len(reduced)}")
    print(f"Temas: {len(by_topic)} | min={min(by_topic.values())} | max={max(by_topic.values())}")
    safe_output_path = str(output_path).encode("ascii", "replace").decode("ascii")
    print(f"Escrito en: {safe_output_path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
