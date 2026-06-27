#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistencia del ranking local del modo resistencia."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from Comun.preferencias_grafico import NOMBRE_JUGADOR_DEFECTO, nombre_jugador_efectivo
from Comun.preferencias_ranking import (
    ModoRetencionRanking,
    PreferenciasRanking,
    cargar_preferencias,
    guardar_preferencias,
)

__all__ = [
    "RecordResistencia",
    "RankingResistencia",
    "VARIANTES_RANKING",
    "aplicar_cambio_modo_retencion",
    "cargar_ranking",
    "ciclar_variante_ranking",
    "etiqueta_variante_ranking",
    "finalizar_ranking_al_salir",
    "guardar_ranking",
    "inicializar_ranking_sesion",
    "invalidar_cache_ranking",
    "mejor_de_jugador",
    "path_ranking_para_preset",
    "path_ranking_para_variante",
    "registrar_partida",
    "top_records",
    "vaciar_ranking",
    "vaciar_ranking_variante",
    "variante_desde_preset",
]

_MAX_RECORDS = 500
_TOP_MOSTRAR = 50

VARIANTES_RANKING = ("resistencia",)
_ID_PRESET_RESISTENCIA = "ranking_resistencia"

_estados: dict[str, RankingResistencia] = {}
_modo_sesion_activo: bool = False


@dataclass
class RecordResistencia:
    id: str
    nombre: str
    racha: int
    puntos: int
    respondidas: int
    fecha_iso: str
    preset_id: str = _ID_PRESET_RESISTENCIA

    @classmethod
    def nuevo(
        cls,
        *,
        nombre: str,
        racha: int,
        puntos: int,
        respondidas: int,
        preset_id: str = _ID_PRESET_RESISTENCIA,
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


def variante_desde_preset(preset_id: str) -> str:
    del preset_id
    return "resistencia"


def path_ranking_para_variante(variante: str) -> Path:
    if variante != "resistencia":
        raise ValueError(f"Variante de ranking desconocida: {variante}")
    from Comun.rutas import resolver_ranking_resistencia

    return resolver_ranking_resistencia()


def path_ranking_para_preset(preset_id: str) -> Path:
    return path_ranking_para_variante(variante_desde_preset(preset_id))


def etiqueta_variante_ranking(variante: str) -> str:
    del variante
    return "Resistencia"


def ciclar_variante_ranking(variante: str, delta: int) -> str:
    del variante, delta
    return "resistencia"


def _ordenar(records: list[RecordResistencia]) -> list[RecordResistencia]:
    return sorted(
        records,
        key=lambda r: (-r.respondidas, -r.puntos, -r.racha, r.fecha_iso),
    )


def _parse_fecha(fecha_iso: str) -> datetime | None:
    if not fecha_iso:
        return None
    try:
        return datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _dias_retencion(modo: ModoRetencionRanking) -> int | None:
    if modo == ModoRetencionRanking.DIAS_7:
        return 7
    if modo == ModoRetencionRanking.DIAS_30:
        return 30
    return None


def aplicar_retencion(
    records: list[RecordResistencia],
    modo: ModoRetencionRanking,
) -> list[RecordResistencia]:
    dias = _dias_retencion(modo)
    if dias is None:
        return _ordenar(records)
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    filtrados: list[RecordResistencia] = []
    for rec in records:
        fecha = _parse_fecha(rec.fecha_iso)
        if fecha is None or fecha >= corte:
            filtrados.append(rec)
    return _ordenar(filtrados)


def invalidar_cache_ranking() -> None:
    global _estados
    _estados = {}


def _cache_key(path: Path) -> str:
    return str(path.resolve())


def _records_desde_raw(raw: object) -> list[RecordResistencia]:
    records: list[RecordResistencia] = []
    if not isinstance(raw, list):
        return records
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
                    preset_id=str(item.get("preset_id", _ID_PRESET_RESISTENCIA)),
                )
            )
        except (TypeError, ValueError):
            continue
    return _ordenar(records)


def _cargar_desde_disco(path: Path) -> RankingResistencia:
    if not path.exists():
        return RankingResistencia()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return RankingResistencia()
    records = _records_desde_raw(data.get("records", []))
    return RankingResistencia(version=int(data.get("version", 1)), records=records)


def _fusionar_ranking(path_destino: Path, records: list[RecordResistencia]) -> None:
    if not records:
        return
    if not path_destino.exists() or path_destino.stat().st_size < 3:
        guardar_ranking(path_destino, RankingResistencia(records=records))
        return
    ranking = _cargar_desde_disco(path_destino)
    merged = _ordenar(ranking.records + records)[:_MAX_RECORDS]
    guardar_ranking(path_destino, RankingResistencia(records=merged))


def _migrar_archivos_ranking() -> None:
    from Comun.rutas import _ruta_json_escritura, resolver_ranking_resistencia

    path_canon = resolver_ranking_resistencia()

    for nombre_antiguo in ("ranking_resistencia_infinita.json",):
        path_antiguo = _ruta_json_escritura(nombre_antiguo)
        if not path_antiguo.is_file():
            continue
        try:
            data = json.loads(path_antiguo.read_text(encoding="utf-8"))
            records = _records_desde_raw(data.get("records", []))
        except (json.JSONDecodeError, OSError):
            records = []
        _fusionar_ranking(path_canon, records)
        path_antiguo.unlink(missing_ok=True)


def _obtener_estado(path: Path) -> RankingResistencia:
    global _estados
    key = _cache_key(path)
    if key in _estados:
        return _estados[key]
    if _modo_sesion_activo:
        ranking = RankingResistencia()
    else:
        ranking = _cargar_desde_disco(path)
        prefs = cargar_preferencias()
        ranking.records = aplicar_retencion(ranking.records, prefs.modo)
    _estados[key] = ranking
    return ranking


def _persistir_estado(path: Path) -> None:
    if _modo_sesion_activo:
        return
    key = _cache_key(path)
    ranking = _estados.get(key)
    if ranking is None:
        return
    prefs = cargar_preferencias()
    ranking_limpio = RankingResistencia(
        version=ranking.version,
        records=aplicar_retencion(list(ranking.records), prefs.modo),
    )
    guardar_ranking(path, ranking_limpio)
    ranking.records = ranking_limpio.records


def _path_ranking() -> Path:
    return path_ranking_para_variante("resistencia")


def inicializar_ranking_sesion() -> None:
    """Carga preferencias y prepara el ranking al abrir el juego."""
    from Comun.datos_locales_juego import inicializar_datos_locales_juego

    global _modo_sesion_activo
    inicializar_datos_locales_juego()
    _migrar_archivos_ranking()
    prefs = cargar_preferencias()
    _modo_sesion_activo = prefs.modo == ModoRetencionRanking.SESION
    invalidar_cache_ranking()
    if _modo_sesion_activo:
        return
    path = _path_ranking()
    ranking = _cargar_desde_disco(path)
    ranking.records = aplicar_retencion(ranking.records, prefs.modo)
    guardar_ranking(path, ranking)
    _estados[_cache_key(path)] = ranking


def finalizar_ranking_al_salir() -> None:
    """Aplica la política de retención al cerrar el juego."""
    prefs = cargar_preferencias()
    path = _path_ranking()
    if prefs.modo == ModoRetencionRanking.SESION:
        vaciar_ranking(path)
        return
    _persistir_estado(path)
    invalidar_cache_ranking()


def aplicar_cambio_modo_retencion(modo: ModoRetencionRanking) -> None:
    """Cambia el modo de conservación del ranking."""
    global _modo_sesion_activo
    path = _path_ranking()
    prev_sesion = _modo_sesion_activo
    prev_estado = _estados.get(_cache_key(path))
    guardar_preferencias(PreferenciasRanking(modo=modo))
    _modo_sesion_activo = modo == ModoRetencionRanking.SESION
    invalidar_cache_ranking()
    if _modo_sesion_activo:
        return
    ranking = _cargar_desde_disco(path)
    if prev_sesion and prev_estado and prev_estado.records:
        ranking.records = _ordenar(ranking.records + list(prev_estado.records))[:_MAX_RECORDS]
    ranking.records = aplicar_retencion(ranking.records, modo)
    guardar_ranking(path, ranking)
    _estados[_cache_key(path)] = ranking


def cargar_ranking(path: Path) -> RankingResistencia:
    return _obtener_estado(path)


def guardar_ranking(path: Path, ranking: RankingResistencia) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordenados = _ordenar(ranking.records)[:_MAX_RECORDS]
    payload = {
        "version": ranking.version,
        "records": [asdict(r) for r in ordenados],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def vaciar_ranking(path: Path) -> None:
    vacio = RankingResistencia()
    guardar_ranking(path, vacio)
    _estados[_cache_key(path)] = vacio


def vaciar_ranking_variante(variante: str) -> None:
    """Vacía el contenido del JSON de ranking (no elimina el fichero)."""
    if variante != "resistencia":
        raise ValueError(f"Variante de ranking desconocida: {variante}")
    vaciar_ranking(path_ranking_para_variante(variante))


def registrar_partida(
    path: Path,
    *,
    nombre: str,
    racha: int,
    puntos: int,
    respondidas: int,
    preset_id: str = _ID_PRESET_RESISTENCIA,
) -> tuple[RecordResistencia, int]:
    """Guarda la partida y devuelve el récord y su posición en el ranking (1-based)."""
    if respondidas <= 0:
        raise ValueError("No hay partida que registrar.")
    ranking = _obtener_estado(path)
    record = RecordResistencia.nuevo(
        nombre=nombre,
        racha=racha,
        puntos=puntos,
        respondidas=respondidas,
        preset_id=preset_id,
    )
    ranking.records.append(record)
    ranking.records = _ordenar(ranking.records)[:_MAX_RECORDS]
    _estados[_cache_key(path)] = ranking
    _persistir_estado(path)
    posicion = next(
        (i + 1 for i, r in enumerate(ranking.records) if r.id == record.id),
        len(ranking.records),
    )
    return record, posicion


def top_records(path: Path, *, limite: int = _TOP_MOSTRAR) -> list[RecordResistencia]:
    return _obtener_estado(path).records[:limite]


def mejor_de_jugador(path: Path, nombre: str) -> RecordResistencia | None:
    clave = nombre.strip().casefold()
    if not clave:
        return None
    partidas_jugador = [
        r for r in _obtener_estado(path).records if r.nombre.strip().casefold() == clave
    ]
    if not partidas_jugador:
        return None
    return max(partidas_jugador, key=lambda r: (r.respondidas, r.puntos, r.racha))
