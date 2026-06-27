# -*- coding: utf-8 -*-
"""Lógica compartida de plantillas: claves de contenido y formato de instancias."""

from __future__ import annotations

import csv
import re
from pathlib import Path

_LETRAS = ("A", "B", "C", "D")


def norm_clave_texto(texto: str) -> str:
    return (texto or "").strip().lower()


def clave_contenido(
    materia: str, texto: str, opciones: dict[str, str], correcta: str
) -> tuple:
    return (
        norm_clave_texto(materia),
        norm_clave_texto(texto),
        norm_clave_texto(opciones.get("A", "")),
        norm_clave_texto(opciones.get("B", "")),
        norm_clave_texto(opciones.get("C", "")),
        norm_clave_texto(opciones.get("D", "")),
        norm_clave_texto(correcta),
    )


def clave_contenido_sin_materia(
    texto: str, opciones: dict[str, str], correcta: str
) -> tuple:
    """Igual que ``clave_contenido`` pero sin materia (dedup entre asignaturas)."""
    return (
        norm_clave_texto(texto),
        norm_clave_texto(opciones.get("A", "")),
        norm_clave_texto(opciones.get("B", "")),
        norm_clave_texto(opciones.get("C", "")),
        norm_clave_texto(opciones.get("D", "")),
        norm_clave_texto(correcta),
    )


def tiene_placeholders(texto: str) -> bool:
    return bool(re.search(r"\{[^{}]+\}", texto or ""))


def quitar_etiqueta_materia_enunciado(texto: str, materia: str) -> str:
    """Quita el sufijo `` [Materia]`` del catálogo internet (no es parte del enunciado)."""
    if not texto or not materia:
        return texto
    sufijo = f" [{materia}]"
    if texto.endswith(sufijo):
        return texto[: -len(sufijo)].rstrip()
    return texto


def expandir_plantilla_base(t: dict) -> list[dict]:
    """Una fila JSON = una pregunta (sin expansión de ``variaciones``)."""
    base_opts = {L: (t.get(L) or "").strip() for L in _LETRAS}
    return [
        {
            "pregunta": (t.get("pregunta") or "").strip(),
            "opciones": dict(base_opts),
            "correcta": (t.get("correcta") or "").strip().upper(),
            "dificultad": (t.get("dificultad") or "Media").strip(),
            "tipo": (t.get("tipo") or "Teoria").strip(),
            "uso": (t.get("uso") or "").strip(),
        }
    ]


def expandir_plantilla_instancias(materia: str, t: dict) -> list[dict]:
    """Como ``expandir_plantilla_base`` con campo ``materia`` en cada instancia."""
    return [{**inst, "materia": materia} for inst in expandir_plantilla_base(t)]


def expandir_plantilla_csv_filas(template: dict) -> list[dict]:
    """Formato fila CSV (``Pregunta``, ``A``…``D``, ``Correcta``) para scripts de dedup."""
    filas: list[dict] = []
    for inst in expandir_plantilla_base(template):
        filas.append(
            {
                "Pregunta": inst["pregunta"],
                "A": inst["opciones"]["A"],
                "B": inst["opciones"]["B"],
                "C": inst["opciones"]["C"],
                "D": inst["opciones"]["D"],
                "Correcta": inst["correcta"],
                "Dificultad": inst["dificultad"],
                "Tipo": inst["tipo"],
            }
        )
    return filas


def claves_desde_csv(path_csv: Path) -> set[tuple]:
    claves: set[tuple] = set()
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            materia = (row.get("Materia") or row.get("Tema") or "").strip()
            opciones = {L: (row.get(L) or "").strip() for L in _LETRAS}
            correcta = (row.get("Correcta") or "").strip().upper()
            if not materia or not (row.get("Pregunta") or "").strip():
                continue
            claves.add(
                clave_contenido(materia, row.get("Pregunta", ""), opciones, correcta)
            )
    return claves
