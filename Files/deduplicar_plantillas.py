#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elimina plantillas duplicadas o muy parecidas en Data/plantillas.json.

Criterios:
- Duplicado exacto: misma pregunta + mismas opciones + misma correcta.
- Muy similar: alta similitud de enunciado y conjunto de opciones parecido.
"""

import json
import re
import shutil
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from borrar_pycache import borrar_pycache_en_proyecto


BASE = Path(__file__).resolve().parent.parent
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
BACKUPS_DIR = BASE / "Backups"


def norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("¿", "").replace("?", "")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> set[str]:
    return set(norm(text).split())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = len(a | b)
    return (len(a & b) / union) if union else 0.0


def options_set(t: dict) -> set[str]:
    return {
        norm(t.get("A", "")),
        norm(t.get("B", "")),
        norm(t.get("C", "")),
        norm(t.get("D", "")),
    }


def exact_key(t: dict) -> tuple:
    return (
        norm(t.get("pregunta", "")),
        norm(t.get("A", "")),
        norm(t.get("B", "")),
        norm(t.get("C", "")),
        norm(t.get("D", "")),
        norm(t.get("correcta", "")),
    )


def is_very_similar(a: dict, b: dict) -> bool:
    qa = norm(a.get("pregunta", ""))
    qb = norm(b.get("pregunta", ""))
    if not qa or not qb:
        return False

    ta = tokens(a.get("pregunta", ""))
    tb = tokens(b.get("pregunta", ""))
    seq = SequenceMatcher(None, qa, qb).ratio()
    jac_q = jaccard(ta, tb)
    jac_opt = jaccard(options_set(a), options_set(b))
    corr_eq = norm(a.get("correcta", "")) == norm(b.get("correcta", ""))

    # Enunciado casi igual y opciones muy parecidas.
    if seq >= 0.95 and jac_q >= 0.82 and jac_opt >= 0.60:
        return True
    # Misma idea + mismas opciones base aunque cambie el orden.
    if seq >= 0.92 and jac_q >= 0.78 and jac_opt >= 0.85 and corr_eq:
        return True

    return False


def main() -> None:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"plantillas_pre_dedup_{ts}.json"
    shutil.copy2(PATH_PLANTILLAS, backup_path)

    total_before = sum(len(v) for v in plantillas.values())
    exact_removed = 0
    similar_removed = 0

    cleaned = {}
    for tema, items in plantillas.items():
        kept = []
        seen_exact = set()

        # Priorizar conservar "general" y luego "dataset_400"
        priority = {"general": 0, "dataset_400": 1, "dificil": 2, "calculo": 3}
        ordered = sorted(items, key=lambda x: (priority.get(str(x.get("uso", "")).lower(), 9)))

        for t in ordered:
            k = exact_key(t)
            if k in seen_exact:
                exact_removed += 1
                continue

            duplicate_like = False
            for kpt in kept:
                if is_very_similar(t, kpt):
                    duplicate_like = True
                    break

            if duplicate_like:
                similar_removed += 1
                continue

            seen_exact.add(k)
            kept.append(t)

        cleaned[tema] = kept

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total_after = sum(len(v) for v in cleaned.values())
    safe_backup_path = str(backup_path).encode("ascii", "replace").decode("ascii")

    print(f"Total antes: {total_before}")
    print(f"Total despues: {total_after}")
    print(f"Eliminadas exactas: {exact_removed}")
    print(f"Eliminadas muy similares: {similar_removed}")
    print(f"Backup: {safe_backup_path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
