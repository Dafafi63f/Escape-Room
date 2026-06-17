#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opciones configurables por preset del modo historia."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Plan MatCAD: 5 asignaturas por semestre, 2 semestres por curso (10 asignaturas).
# Por semestre hay 5 parciales (mitad) y 5 finales (cierre) → 10 exámenes / semestre.
MATERIAS_POR_SEMESTRE = 5
MATERIAS_POR_CURSO = 10
EXAMENES_POR_SEMESTRE = 10
EXAMENES_POR_CURSO = 20

GRUPOS_TEMATICOS: dict[str, str] = {
    "1": "G1 — Álgebra y geometría",
    "2": "G2 — Cálculo y ecuaciones",
    "3": "G3 — Sistemas y seguridad",
    "4": "G4 — Programación",
    "5": "G5 — Algoritmia",
    "6": "G6 — Métodos numéricos",
    "7": "G7 — Probabilidad y datos",
    "8": "G8 — Bases de datos",
    "9": "G9 — Inteligencia artificial",
    "10": "G10 — Modelización física",
}

SLOTS_ENFOQUE_MIXTO: None = None

SLOTS_ENFOQUE_TEORIA: tuple[tuple[str, str], ...] = (
    ("Teoria", "Facil"),
    ("Teoria", "Facil"),
    ("Teoria", "Media"),
    ("Teoria", "Media"),
)

SLOTS_ENFOQUE_CALCULO: tuple[tuple[str, str], ...] = (
    ("Calculo", "Facil"),
    ("Calculo", "Facil"),
    ("Calculo", "Media"),
    ("Calculo", "Media"),
)


@dataclass(frozen=True)
class OpcionPreset:
    id: str
    tipo: str
    etiqueta: str
    obligatorio: bool = False
    defecto: str | int | None = None
    min: int | None = None
    max: int | None = None
    valores: tuple[tuple[str, str], ...] = ()

    def etiquetas_eleccion(self) -> list[tuple[str, str]]:
        return [(v, e) for v, e in self.valores]


@dataclass
class ConfigPresetHistoria:
    """Valores elegidos por el jugador para un preset concreto."""

    valores: dict[str, Any] = field(default_factory=dict)

    def get_str(self, clave: str) -> str | None:
        v = self.valores.get(clave)
        if v is None or v == "":
            return None
        return str(v)

    def get_int(self, clave: str, defecto: int = 0) -> int:
        v = self.valores.get(clave)
        if v is None or v == "":
            return defecto
        return int(v)


def _parse_opcion(raw: dict) -> OpcionPreset:
    valores_raw = raw.get("valores") or []
    valores: list[tuple[str, str]] = []
    for item in valores_raw:
        if isinstance(item, dict):
            valores.append((str(item["valor"]), str(item.get("etiqueta", item["valor"]))))
    return OpcionPreset(
        id=str(raw["id"]),
        tipo=str(raw["tipo"]),
        etiqueta=str(raw.get("etiqueta", raw["id"])),
        obligatorio=bool(raw.get("obligatorio", False)),
        defecto=raw.get("defecto"),
        min=raw.get("min"),
        max=raw.get("max"),
        valores=tuple(valores),
    )


def parse_opciones(raw: list | None) -> tuple[OpcionPreset, ...]:
    if not raw:
        return ()
    return tuple(_parse_opcion(x) for x in raw)


def cursos_disponibles(materias_meta: dict[str, dict[str, str]]) -> list[str]:
    return sorted({m.get("curso", "") for m in materias_meta.values() if m.get("curso")})


def semestres_para_curso(
    materias_meta: dict[str, dict[str, str]],
    curso: str,
) -> list[str]:
    return sorted(
        {
            m.get("semestre", "")
            for m in materias_meta.values()
            if m.get("curso") == curso and m.get("semestre")
        }
    )


def contar_materias_ambito(
    materias_meta: dict[str, dict[str, str]],
    *,
    curso: str | None,
    semestre: str | None,
    grupo: str | None,
) -> int:
    n = 0
    for meta in materias_meta.values():
        if curso and (meta.get("curso") or "") != curso:
            continue
        if semestre and (meta.get("semestre") or "") != semestre:
            continue
        if grupo and (meta.get("grupo") or "") != str(grupo):
            continue
        n += 1
    return n


def max_materias_ambito(
    materias_meta: dict[str, dict[str, str]],
    *,
    curso: str | None,
    semestre: str | None,
    grupo: str | None,
) -> int | None:
    """Tope natural de asignaturas según curso/semestre/grupo elegidos."""
    if semestre and curso:
        return min(MATERIAS_POR_SEMESTRE, contar_materias_ambito(
            materias_meta, curso=curso, semestre=semestre, grupo=None
        ))
    if curso and not semestre and not grupo:
        return min(MATERIAS_POR_CURSO, contar_materias_ambito(
            materias_meta, curso=curso, semestre=None, grupo=None
        ))
    if grupo:
        return contar_materias_ambito(
            materias_meta, curso=None, semestre=None, grupo=grupo
        )
    return None


def materias_ordenadas(materias_orden: list[str]) -> list[str]:
    return list(materias_orden)


def defectos_config(
    opciones: tuple[OpcionPreset, ...],
    *,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
) -> ConfigPresetHistoria:
    valores: dict[str, Any] = {}
    for op in opciones:
        if op.defecto is not None:
            valores[op.id] = op.defecto
        elif op.tipo == "materia" and materias_orden:
            valores[op.id] = materias_orden[0]
        elif op.tipo == "curso":
            cursos = cursos_disponibles(materias_meta)
            if cursos:
                valores[op.id] = cursos[0]
        elif op.tipo == "grupo":
            valores[op.id] = "1"
    return ConfigPresetHistoria(valores=valores)


def validar_config(
    opciones: tuple[OpcionPreset, ...],
    config: ConfigPresetHistoria,
    *,
    materias_meta: dict[str, dict[str, str]],
) -> ConfigPresetHistoria:
    valores = dict(config.valores)
    for op in opciones:
        raw = valores.get(op.id)
        if op.tipo == "entero":
            if raw is None or raw == "":
                if op.obligatorio:
                    raise ValueError(f"Falta {op.etiqueta}.")
                valores[op.id] = op.defecto if op.defecto is not None else 0
                continue
            n = int(raw)
            min_v = op.min if op.min is not None else 0
            max_v = op.max if op.max is not None else 9999
            if op.id == "n_materias":
                tope = max_materias_ambito(
                    materias_meta,
                    curso=str(valores.get("curso") or "") or None,
                    semestre=str(valores.get("semestre") or "") or None,
                    grupo=str(valores.get("grupo") or "") or None,
                )
                if tope is not None:
                    max_v = min(max_v, tope)
            if not (min_v <= n <= max_v):
                raise ValueError(f"{op.etiqueta}: valor entre {min_v} y {max_v}.")
            valores[op.id] = n
        elif op.tipo == "curso":
            if not raw:
                if op.obligatorio:
                    raise ValueError(f"Elige {op.etiqueta.lower()}.")
            elif raw not in cursos_disponibles(materias_meta):
                raise ValueError(f"Curso no válido: {raw!r}.")
            else:
                valores[op.id] = str(raw)
        elif op.tipo == "semestre":
            curso = valores.get("curso")
            if not raw:
                if op.obligatorio:
                    if not curso:
                        raise ValueError("Indica el curso antes del semestre.")
                    raise ValueError(f"Elige {op.etiqueta.lower()}.")
            else:
                if curso and raw not in semestres_para_curso(materias_meta, str(curso)):
                    raise ValueError(f"Semestre no válido para el curso {curso}.")
                valores[op.id] = str(raw)
        elif op.tipo == "grupo":
            if not raw:
                raise ValueError(f"Elige {op.etiqueta.lower()}.")
            if str(raw) not in GRUPOS_TEMATICOS:
                raise ValueError(f"Grupo no válido: {raw!r}.")
            valores[op.id] = str(raw)
        elif op.tipo == "materia":
            if not raw:
                raise ValueError("Elige una materia.")
            if str(raw) not in materias_meta:
                raise ValueError(f"Materia no válida: {raw!r}.")
            valores[op.id] = str(raw)
        elif op.tipo == "eleccion":
            if not raw:
                valores[op.id] = op.defecto or (op.valores[0][0] if op.valores else "")
            elif op.valores and str(raw) not in {v for v, _ in op.valores}:
                raise ValueError(f"Opción no válida para {op.etiqueta}.")
            else:
                valores[op.id] = str(raw)
    return ConfigPresetHistoria(valores=valores)


def slots_desde_enfoque(enfoque: str | None) -> tuple[tuple[str, str], ...] | None:
    if enfoque == "teoria":
        return SLOTS_ENFOQUE_TEORIA
    if enfoque == "calculo":
        return SLOTS_ENFOQUE_CALCULO
    return SLOTS_ENFOQUE_MIXTO


def tiempo_total_seg_desde_config(config: ConfigPresetHistoria) -> int | None:
    minutos = config.get_int("tiempo_total_min", 0)
    if minutos <= 0:
        return None
    return minutos * 60
