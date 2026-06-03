# -*- coding: utf-8 -*-
"""Similitud léxica entre enunciados (variedad temática por materia)."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

STOP = {
    "qué", "que", "cual", "cuál", "como", "cómo", "para", "una", "uno", "del", "de", "la", "el",
    "en", "es", "son", "con", "por", "se", "un", "los", "las", "al", "más", "mas", "tiene", "hay",
}

UMBRAL_VALIDACION = 0.38
UMBRAL_INFORME = 0.35


def stem_words(texto: str) -> set[str]:
    t = re.sub(r"[^\w\s]", " ", str(texto).lower())
    t = re.sub(r"[àáâãä]", "a", t)
    t = re.sub(r"[èéêë]", "e", t)
    t = re.sub(r"[ìíîï]", "i", t)
    t = re.sub(r"[òóôõö]", "o", t)
    t = re.sub(r"[ùúûü]", "u", t)
    t = re.sub(r"ñ", "n", t)
    return {w for w in t.split() if len(w) > 3 and w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def agrupar_por_materia(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[str(r.get("Materia", ""))].append(r)
    return out


def pares_similares_en_materia(
    items: list[dict],
    umbral: float,
    max_pares: int | None = None,
) -> list[tuple[float, int, int, str, str]]:
    stems = [
        (int(r["Id"]), stem_words(r["Pregunta"]), str(r["Pregunta"])[:70])
        for r in items
    ]
    pairs: list[tuple[float, int, int, str, str]] = []
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            sim = jaccard(stems[i][1], stems[j][1])
            if sim >= umbral:
                pairs.append((sim, stems[i][0], stems[j][0], stems[i][2], stems[j][2]))
    pairs.sort(reverse=True)
    if max_pares is not None:
        return pairs[:max_pares]
    return pairs


def alertas_variedad_csv(rows: list[dict], umbral: float = UMBRAL_VALIDACION) -> list[tuple[str, int, int, float]]:
    alertas: list[tuple[str, int, int, float]] = []
    for materia, items in agrupar_por_materia(rows).items():
        for sim, id_a, id_b, _, _ in pares_similares_en_materia(items, umbral):
            alertas.append((materia, id_a, id_b, round(sim, 2)))
    return alertas


def palabras_frecuentes_por_materia(
    items: list[dict],
    min_count: int = 4,
    top_n: int = 8,
) -> list[tuple[str, int]]:
    words: list[str] = []
    for r in items:
        words.extend(stem_words(r["Pregunta"]))
    c = Counter(words)
    return [(w, n) for w, n in c.most_common(top_n) if n >= min_count]
