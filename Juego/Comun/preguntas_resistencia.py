#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preguntas exclusivas del modo resistencia (no aparecen en otros modos)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from Comun.modelos import Pregunta
from Comun.rutas import resolver_preguntas_resistencia

__all__ = [
    "BancoResistencia",
    "ETIQUETAS_TIER_RESISTENCIA",
    "cargar_preguntas_exclusivas_resistencia",
    "construir_banco_resistencia",
    "construir_pool_resistencia",
    "pool_resistencia_desde_dataset",
]

ETIQUETAS_TIER_RESISTENCIA: dict[int, str] = {
    1: "Élite",
    2: "Maestro",
    3: "Legendario",
    4: "Imposible",
}


def _pregunta_valida_resistencia(p: Pregunta) -> bool:
    return (
        p.correcta in {"A", "B", "C", "D"}
        and any(p.opciones.get(letra) for letra in "ABCD")
        and not p.exclusiva_resistencia
    )


def pool_resistencia_desde_dataset(preguntas: list[Pregunta]) -> list[Pregunta]:
    """Preguntas del dataset revisado válidas para resistencia (sin exclusivas)."""
    return [p for p in preguntas if _pregunta_valida_resistencia(p)]


def pool_plantillas_resistencia(
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
    *,
    claves_dataset: set[tuple],
) -> list[Pregunta]:
    """Plantillas fuera del dataset revisado, válidas para resistencia."""
    from Comun.datos import cargar_preguntas_plantillas

    if not path_plantillas.exists():
        return []
    raw = cargar_preguntas_plantillas(
        path_plantillas,
        materias_meta,
        solo_fuera_dataset=True,
        claves_ds=claves_dataset,
    )
    validas = [p for p in raw if _pregunta_valida_resistencia(p)]
    return sorted(validas, key=lambda p: (p.materia, p.texto, p.correcta))


def _parse_opciones(raw: dict | None) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    return {k: str(v) for k, v in raw.items() if k in "ABCD"}


def cargar_preguntas_exclusivas_resistencia(
    materias_meta: dict[str, dict[str, str]],
    *,
    path: Path | None = None,
) -> list[Pregunta]:
    """Carga el banco extra solo para resistencia avanzada."""
    ruta = path or resolver_preguntas_resistencia()
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    items = data.get("preguntas", [])
    if not isinstance(items, list):
        return []

    resultado: list[Pregunta] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        correcta = str(item.get("correcta", "")).strip().upper()
        if correcta not in {"A", "B", "C", "D"}:
            continue
        opciones = _parse_opciones(item.get("opciones"))
        if not all(opciones.get(l) for l in "ABCD"):
            continue
        texto = str(item.get("pregunta", "")).strip()
        if not texto:
            continue
        materia = str(item.get("materia", "General")).strip() or "General"
        mm = materias_meta.get(materia, {})
        racha_min = int(item.get("racha_minima", 100))
        tier = int(item.get("tier", 1))
        resultado.append(
            Pregunta(
                texto=texto,
                materia=materia,
                tematica=str(item.get("tematica") or mm.get("tematica", "")),
                dificultad=str(item.get("dificultad", "Dificil")),
                tipo=str(item.get("tipo", "Teoria")),
                grupo=str(item.get("grupo") or mm.get("grupo", "")),
                nivel=str(item.get("nivel") or mm.get("nivel", "3")),
                curso=str(item.get("curso") or mm.get("curso", "")),
                semestre=str(item.get("semestre") or mm.get("semestre", "")),
                opciones=opciones,
                correcta=correcta,
                fuente="resistencia_exclusiva",
                exclusiva_resistencia=True,
                racha_minima_resistencia=max(1, racha_min),
                tier_resistencia=max(1, min(4, tier)),
            )
        )
    return sorted(
        resultado,
        key=lambda p: (p.racha_minima_resistencia, p.materia, p.texto, p.correcta),
    )


@dataclass(frozen=True)
class BancoResistencia:
    """Capas del banco: revisado → plantillas beta → exclusivas difíciles."""

    revisadas: tuple[Pregunta, ...]
    plantillas: tuple[Pregunta, ...]
    exclusivas: tuple[Pregunta, ...]

    @property
    def n_revisadas(self) -> int:
        return len(self.revisadas)

    def pool_completo(self) -> list[Pregunta]:
        return list(self.revisadas) + list(self.plantillas) + list(self.exclusivas)

    def indice_habilitado(self, idx: int, numero_pregunta: int) -> bool:
        from Comun.resistencia_motor import cuotas_banco_resistencia

        n_rev = self.n_revisadas
        n_pl = len(self.plantillas)
        cuotas = cuotas_banco_resistencia(
            numero_pregunta, n_pl, len(self.exclusivas)
        )
        if idx < n_rev:
            return True
        idx -= n_rev
        if idx < n_pl:
            return idx < cuotas.plantillas
        idx -= n_pl
        return idx < cuotas.exclusivas


def construir_banco_resistencia(
    preguntas_dataset: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    *,
    path_plantillas: Path | None = None,
    path_preguntas_csv: Path | None = None,
    path_exclusivas: Path | None = None,
) -> BancoResistencia:
    """Banco en capas: dataset revisado + plantillas beta + exclusivas."""
    revisadas = tuple(pool_resistencia_desde_dataset(preguntas_dataset))
    plantillas: tuple[Pregunta, ...] = ()
    if path_plantillas is not None:
        from Comun.datos import claves_dataset

        claves = (
            claves_dataset(path_preguntas_csv)
            if path_preguntas_csv is not None
            else set()
        )
        plantillas = tuple(
            pool_plantillas_resistencia(
                path_plantillas, materias_meta, claves_dataset=claves
            )
        )
    exclusivas = tuple(
        cargar_preguntas_exclusivas_resistencia(
            materias_meta, path=path_exclusivas
        )
    )
    return BancoResistencia(
        revisadas=revisadas,
        plantillas=plantillas,
        exclusivas=exclusivas,
    )


def construir_pool_resistencia(
    preguntas_dataset: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    *,
    path_plantillas: Path | None = None,
    path_preguntas_csv: Path | None = None,
    path_exclusivas: Path | None = None,
) -> list[Pregunta]:
    """Pool completo (todas las capas); la selección filtra por banco dinámico."""
    return construir_banco_resistencia(
        preguntas_dataset,
        materias_meta,
        path_plantillas=path_plantillas,
        path_preguntas_csv=path_preguntas_csv,
        path_exclusivas=path_exclusivas,
    ).pool_completo()
