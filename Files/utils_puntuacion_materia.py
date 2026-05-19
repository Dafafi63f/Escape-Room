# -*- coding: utf-8 -*-
"""
Criterios de puntuación semántica por materia (solo keywords).

Fuente editable: Data/criterios_clasificacion_materia.csv (columna Palabras_clave).

Para Materia + Tipo + Dificultad a partir del enunciado completo, usar
`utils_clasificacion_pregunta.clasificar_pregunta` o `Files/clasificar_pregunta.py`.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATH_CRITERIOS = BASE / "Data" / "criterios_clasificacion_materia.csv"
PATH_LISTADO = BASE / "Data" / "listado_materias.csv"
SEP_KEYWORDS = " | "

MATERIAS: dict[int, str] = {}
with PATH_LISTADO.open("r", encoding="utf-8", newline="") as _f:
    for _row in csv.DictReader(_f, delimiter=";"):
        MATERIAS[int(_row["Id"])] = _row["Materia"]

MATERIA_TO_ID = {m: i for i, m in MATERIAS.items()}


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    t = str(texto).lower().strip()
    t = re.sub(r"[àáâãäå]", "a", t)
    t = re.sub(r"[èéêë]", "e", t)
    t = re.sub(r"[ìíîï]", "i", t)
    t = re.sub(r"[òóôõö]", "o", t)
    t = re.sub(r"[ùúûü]", "u", t)
    t = re.sub(r"[ñ]", "n", t)
    t = re.sub(r"[·]", "", t)
    return t


def _parse_keywords(celda: str) -> list[str]:
    if not celda or not str(celda).strip():
        return []
    return [p.strip() for p in str(celda).split("|") if p.strip()]


@lru_cache(maxsize=1)
def _cargar_criterios() -> tuple[
    dict[int, list[str]],
    dict[int, list[str]],
    dict[int, str],
    dict[int, str],
]:
    """keywords, keywords_norm, notas, criterio_resumen por Id."""
    keywords: dict[int, list[str]] = {i: [] for i in MATERIAS}
    keywords_norm: dict[int, list[str]] = {i: [] for i in MATERIAS}
    notas: dict[int, str] = {}
    criterio = ""

    if not PATH_CRITERIOS.is_file():
        raise FileNotFoundError(f"No existe {PATH_CRITERIOS}")

    with PATH_CRITERIOS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            mid = int(row["Id"])
            kws = _parse_keywords(row.get("Palabras_clave", ""))
            keywords[mid] = kws
            keywords_norm[mid] = [normalizar(k) for k in kws if normalizar(k)]
            notas[mid] = (row.get("Notas_desambiguacion") or "").strip()
            if not criterio:
                criterio = (row.get("Criterio_puntuacion_resumen") or "").strip()

    return keywords, keywords_norm, notas, criterio


def recargar_criterios() -> None:
    """Invalida caché tras editar el CSV."""
    global KEYWORDS
    _cargar_criterios.cache_clear()
    KEYWORDS = keywords_por_materia()


def keywords_por_materia() -> dict[int, list[str]]:
    return _cargar_criterios()[0]


def keywords_normalizadas_por_materia() -> dict[int, list[str]]:
    return _cargar_criterios()[1]


def notas_desambiguacion() -> dict[int, str]:
    return _cargar_criterios()[2]


def puntuar_texto_completo(pregunta: str, a: str, b: str, c: str, d: str) -> dict[int, float]:
    """Cuenta keywords (ya normalizadas) presentes en pregunta + opciones."""
    texto = normalizar(f"{pregunta} {a} {b} {c} {d}")
    scores: dict[int, float] = {}
    for id_mat, kws_norm in keywords_normalizadas_por_materia().items():
        if not kws_norm:
            continue
        s = sum(1.0 for kw in kws_norm if kw in texto)
        if s > 0:
            scores[id_mat] = s
    return scores


def mejor_materia_por_texto(
    pregunta: str,
    a: str = "",
    b: str = "",
    c: str = "",
    d: str = "",
) -> tuple[int | None, dict[int, float]]:
    """Materia con mayor puntuación; en empate, menor Id (orden del listado)."""
    scores = puntuar_texto_completo(pregunta, a, b, c, d)
    if not scores:
        return None, scores
    mejor = max(scores, key=lambda k: (scores[k], -k))
    return mejor, scores


def score_fila_para_materia(fila: dict, materia: str | None = None) -> float:
    """Puntuación de una fila del dataset respecto a su Materia (o la indicada)."""
    mat = materia or fila.get("Materia", "")
    mid = MATERIA_TO_ID.get(mat)
    if mid is None:
        return 0.0
    return puntuar_texto_completo(
        fila.get("Pregunta", ""),
        fila.get("A", ""),
        fila.get("B", ""),
        fila.get("C", ""),
        fila.get("D", ""),
    ).get(mid, 0.0)


# Compatibilidad: from utils_puntuacion_materia import KEYWORDS
KEYWORDS: dict[int, list[str]] = keywords_por_materia()
