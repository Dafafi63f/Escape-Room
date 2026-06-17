#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistencia del ranking local del modo resistencia (multijugador offline)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from Comun.jugador import NOMBRE_JUGADOR_DEFECTO, nombre_jugador_efectivo

__all__ = [
    "RecordResistencia",
    "RankingResistencia",
    "cargar_ranking",
    "guardar_ranking",
    "registrar_partida",
    "top_records",
    "mejor_de_jugador",
]

_MAX_RECORDS = 500
_TOP_MOSTRAR = 50


@dataclass
class RecordResistencia:
    id: str
    nombre: str
    racha: int
    puntos: int
    respondidas: int
    fecha_iso: str
    preset_id: str = "ranking_resistencia"

    @classmethod
    def nuevo(
        cls,
        *,
        nombre: str,
        racha: int,
        puntos: int,
        respondidas: int,
        preset_id: str = "ranking_resistencia",
    ) -> RecordResistencia:
        return cls(
            id=uuid.uuid4().hex[:12],
            nombre=nombre_jugador_efectivo(nombre),
            racha=racha,
            puntos=puntos,
            respondidas=respondidas,
            fecha_iso=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            preset_id=preset_id,
        )


@dataclass
class RankingResistencia:
    version: int = 1
    records: list[RecordResistencia] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.records is None:
            self.records = []


def _ordenar(records: list[RecordResistencia]) -> list[RecordResistencia]:
    return sorted(
        records,
        key=lambda r: (-r.respondidas, -r.puntos, -r.racha, r.fecha_iso),
    )


def cargar_ranking(path: Path) -> RankingResistencia:
    if not path.exists():
        return RankingResistencia()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return RankingResistencia()
    raw = data.get("records", [])
    records: list[RecordResistencia] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                records.append(
                    RecordResistencia(
                        id=str(item.get("id", uuid.uuid4().hex[:12])),
                        nombre=str(item.get("nombre", NOMBRE_JUGADOR_DEFECTO)),
                        racha=int(item.get("racha", 0)),
                        puntos=int(item.get("puntos", 0)),
                        respondidas=int(item.get("respondidas", 0)),
                        fecha_iso=str(item.get("fecha_iso", "")),
                        preset_id=str(item.get("preset_id", "ranking_resistencia")),
                    )
                )
            except (TypeError, ValueError):
                continue
    return RankingResistencia(version=int(data.get("version", 1)), records=_ordenar(records))


def guardar_ranking(path: Path, ranking: RankingResistencia) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordenados = _ordenar(ranking.records)[:_MAX_RECORDS]
    payload = {
        "version": ranking.version,
        "records": [asdict(r) for r in ordenados],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar_partida(
    path: Path,
    *,
    nombre: str,
    racha: int,
    puntos: int,
    respondidas: int,
    preset_id: str = "ranking_resistencia",
) -> tuple[RecordResistencia, int]:
    """Guarda la partida y devuelve el récord y su posición en el ranking (1-based)."""
    if respondidas <= 0:
        raise ValueError("No hay partida que registrar.")
    ranking = cargar_ranking(path)
    record = RecordResistencia.nuevo(
        nombre=nombre,
        racha=racha,
        puntos=puntos,
        respondidas=respondidas,
        preset_id=preset_id,
    )
    ranking.records.append(record)
    ranking.records = _ordenar(ranking.records)[:_MAX_RECORDS]
    guardar_ranking(path, ranking)
    posicion = next(
        (i + 1 for i, r in enumerate(ranking.records) if r.id == record.id),
        len(ranking.records),
    )
    return record, posicion


def top_records(path: Path, *, limite: int = _TOP_MOSTRAR) -> list[RecordResistencia]:
    return cargar_ranking(path).records[:limite]


def mejor_de_jugador(path: Path, nombre: str) -> RecordResistencia | None:
    clave = nombre.strip().casefold()
    if not clave:
        return None
    partidas_jugador = [
        r for r in cargar_ranking(path).records if r.nombre.strip().casefold() == clave
    ]
    if not partidas_jugador:
        return None
    return max(partidas_jugador, key=lambda r: (r.respondidas, r.puntos, r.racha))
