#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persistencia del ranking local del modo resistencia (tablas separadas)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from Comun.jugador import NOMBRE_JUGADOR_DEFECTO, nombre_jugador_efectivo
from Comun.preferencias_ranking import (
    ModoRetencionRanking,
    PreferenciasRanking,
    cargar_preferencias,
    guardar_preferencias,
)
from Comun.reto_dia_resistencia import ID_PRESET_RETO_DIA, es_id_reto_dia

__all__ = [
    "RecordResistencia",
    "RankingResistencia",
    "VARIANTES_RANKING",
    "cargar_ranking",
    "guardar_ranking",
    "registrar_partida",
    "top_records",
    "mejor_de_jugador",
    "vaciar_ranking",
    "vaciar_ranking_variante",
    "inicializar_ranking_sesion",
    "finalizar_ranking_al_salir",
    "aplicar_cambio_modo_retencion",
    "invalidar_cache_ranking",
    "variante_desde_preset",
    "path_ranking_para_preset",
    "path_ranking_para_variante",
    "etiqueta_variante_ranking",
    "ciclar_variante_ranking",
    "es_path_reto_dia",
]

_MAX_RECORDS = 500
_TOP_MOSTRAR = 50

VARIANTES_RANKING = ("infinita", "reto_dia")
_ID_PRESET_INFINITA = "ranking_resistencia"

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
    preset_id: str = _ID_PRESET_INFINITA

    @classmethod
    def nuevo(
        cls,
        *,
        nombre: str,
        racha: int,
        puntos: int,
        respondidas: int,
        preset_id: str = _ID_PRESET_INFINITA,
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
    return "reto_dia" if es_id_reto_dia(preset_id) else "infinita"


def path_ranking_para_variante(variante: str) -> Path:
    from Comun.rutas import resolver_ranking_reto_dia, resolver_ranking_resistencia_infinita

    if variante == "reto_dia":
        return resolver_ranking_reto_dia()
    return resolver_ranking_resistencia_infinita()


def path_ranking_para_preset(preset_id: str) -> Path:
    return path_ranking_para_variante(variante_desde_preset(preset_id))


def es_path_reto_dia(path: Path) -> bool:
    return path.name == "ranking_reto_dia.json"


def etiqueta_variante_ranking(variante: str) -> str:
    return {
        "infinita": "Resistencia infinita",
        "reto_dia": "Reto del día",
    }.get(variante, "Resistencia infinita")


def ciclar_variante_ranking(variante: str, delta: int) -> str:
    orden = list(VARIANTES_RANKING)
    try:
        idx = orden.index(variante)
    except ValueError:
        idx = 0
    return orden[(idx + delta) % len(orden)]


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


def _fecha_hoy_utc() -> date:
    return datetime.now(timezone.utc).date()


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
                    preset_id=str(item.get("preset_id", _ID_PRESET_INFINITA)),
                )
            )
        except (TypeError, ValueError):
            continue
    return _ordenar(records)


def _cargar_infinita_desde_disco(path: Path) -> RankingResistencia:
    if not path.exists():
        return RankingResistencia()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return RankingResistencia()
    records = _records_desde_raw(data.get("records", []))
    records = [r for r in records if not es_id_reto_dia(r.preset_id)]
    return RankingResistencia(version=int(data.get("version", 1)), records=records)


def _cargar_reto_dia_desde_disco(path: Path) -> RankingResistencia:
    hoy = _fecha_hoy_utc().isoformat()
    if not path.exists():
        return RankingResistencia(version=2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return RankingResistencia(version=2)
    if str(data.get("fecha_reto", "")) != hoy:
        return RankingResistencia(version=2)
    records = _records_desde_raw(data.get("records", []))
    records = [r for r in records if es_id_reto_dia(r.preset_id)]
    return RankingResistencia(version=2, records=records)


def _cargar_desde_disco(path: Path) -> RankingResistencia:
    if es_path_reto_dia(path):
        return _cargar_reto_dia_desde_disco(path)
    return _cargar_infinita_desde_disco(path)


def _migrar_ranking_legacy() -> None:
    from Comun.rutas import (
        resolver_ranking_reto_dia,
        resolver_ranking_resistencia_infinita,
        _ruta_json_escritura,
    )

    legacy = _ruta_json_escritura("ranking_resistencia.json")
    if not legacy.is_file():
        return
    try:
        data = json.loads(legacy.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        legacy.unlink(missing_ok=True)
        return

    records = _records_desde_raw(data.get("records", []))
    path_inf = resolver_ranking_resistencia_infinita()
    path_dia = resolver_ranking_reto_dia()
    hoy = _fecha_hoy_utc().isoformat()

    if not path_inf.exists() or path_inf.stat().st_size < 3:
        inf = [r for r in records if not es_id_reto_dia(r.preset_id)]
        guardar_ranking(path_inf, RankingResistencia(records=inf))

    if not path_dia.exists() or path_dia.stat().st_size < 3:
        dia = [r for r in records if es_id_reto_dia(r.preset_id)]
        guardar_ranking_reto_dia(path_dia, RankingResistencia(version=2, records=dia), fecha_reto=hoy)

    legacy.unlink(missing_ok=True)


def guardar_ranking_reto_dia(
    path: Path,
    ranking: RankingResistencia,
    *,
    fecha_reto: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordenados = _ordenar(ranking.records)[:_MAX_RECORDS]
    payload = {
        "version": 2,
        "fecha_reto": fecha_reto or _fecha_hoy_utc().isoformat(),
        "records": [asdict(r) for r in ordenados],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _obtener_estado(path: Path) -> RankingResistencia:
    global _estados
    key = _cache_key(path)
    if key in _estados:
        return _estados[key]
    if _modo_sesion_activo:
        ranking = RankingResistencia(version=2 if es_path_reto_dia(path) else 1)
    else:
        ranking = _cargar_desde_disco(path)
        if not es_path_reto_dia(path):
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
    if es_path_reto_dia(path):
        guardar_ranking_reto_dia(path, ranking)
        return
    prefs = cargar_preferencias()
    ranking_limpio = RankingResistencia(
        version=ranking.version,
        records=aplicar_retencion(list(ranking.records), prefs.modo),
    )
    guardar_ranking(path, ranking_limpio)
    ranking.records = ranking_limpio.records


def _paths_ranking() -> list[Path]:
    from Comun.rutas import resolver_ranking_reto_dia, resolver_ranking_resistencia_infinita

    return [resolver_ranking_resistencia_infinita(), resolver_ranking_reto_dia()]


def inicializar_ranking_sesion() -> None:
    """Carga preferencias y prepara los rankings al abrir el juego."""
    from Comun.datos_locales_juego import inicializar_datos_locales_juego

    global _modo_sesion_activo
    inicializar_datos_locales_juego()
    _migrar_ranking_legacy()
    prefs = cargar_preferencias()
    _modo_sesion_activo = prefs.modo == ModoRetencionRanking.SESION
    invalidar_cache_ranking()
    if _modo_sesion_activo:
        return
    for path in _paths_ranking():
        ranking = _cargar_desde_disco(path)
        if es_path_reto_dia(path):
            guardar_ranking_reto_dia(path, ranking)
        else:
            ranking.records = aplicar_retencion(ranking.records, prefs.modo)
            guardar_ranking(path, ranking)
        _estados[_cache_key(path)] = ranking


def finalizar_ranking_al_salir() -> None:
    """Aplica la política de retención al cerrar el juego."""
    prefs = cargar_preferencias()
    if prefs.modo == ModoRetencionRanking.SESION:
        for path in _paths_ranking():
            vaciar_ranking(path)
        return
    for path in _paths_ranking():
        _persistir_estado(path)
    invalidar_cache_ranking()


def aplicar_cambio_modo_retencion(modo: ModoRetencionRanking) -> None:
    """Cambia el modo de conservación del ranking infinita."""
    global _modo_sesion_activo
    path_inf = path_ranking_para_variante("infinita")
    prev_sesion = _modo_sesion_activo
    prev_estado = _estados.get(_cache_key(path_inf))
    guardar_preferencias(PreferenciasRanking(modo=modo))
    _modo_sesion_activo = modo == ModoRetencionRanking.SESION
    invalidar_cache_ranking()
    if _modo_sesion_activo:
        return
    ranking = _cargar_desde_disco(path_inf)
    if prev_sesion and prev_estado and prev_estado.records:
        ranking.records = _ordenar(ranking.records + list(prev_estado.records))[:_MAX_RECORDS]
    ranking.records = aplicar_retencion(ranking.records, modo)
    guardar_ranking(path_inf, ranking)
    _estados[_cache_key(path_inf)] = ranking


def cargar_ranking(path: Path) -> RankingResistencia:
    return _obtener_estado(path)


def guardar_ranking(path: Path, ranking: RankingResistencia) -> None:
    if es_path_reto_dia(path):
        guardar_ranking_reto_dia(path, ranking)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    ordenados = _ordenar(ranking.records)[:_MAX_RECORDS]
    payload = {
        "version": ranking.version,
        "records": [asdict(r) for r in ordenados],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def vaciar_ranking(path: Path) -> None:
    vacio = RankingResistencia(version=2 if es_path_reto_dia(path) else 1)
    if es_path_reto_dia(path):
        guardar_ranking_reto_dia(path, vacio)
    else:
        guardar_ranking(path, vacio)
    _estados[_cache_key(path)] = vacio


def vaciar_ranking_variante(variante: str) -> None:
    """Vacía el contenido del JSON de ranking (no elimina el fichero)."""
    if variante not in VARIANTES_RANKING:
        raise ValueError(f"Variante de ranking desconocida: {variante}")
    vaciar_ranking(path_ranking_para_variante(variante))


def registrar_partida(
    path: Path,
    *,
    nombre: str,
    racha: int,
    puntos: int,
    respondidas: int,
    preset_id: str = _ID_PRESET_INFINITA,
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
