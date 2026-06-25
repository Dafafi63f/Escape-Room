#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opciones configurables por preset del modo historia."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from Comun.reglas_partida import (
    MIN_PREGUNTAS_PARTIDA,
    PREGUNTAS_POR_MATERIA_HISTORIA,
    min_materias_para_minimo_preguntas,
)

# Plan MatCAD: 5 asignaturas por semestre, 2 semestres por curso (10 asignaturas).
MATERIAS_POR_SEMESTRE = 5
MATERIAS_POR_CURSO = 10

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


def etiqueta_grupo_tematico(grupo: str | int) -> str:
    """Nombre legible del bloque G1–G10 del plan de estudios."""
    clave = str(grupo).strip()
    return GRUPOS_TEMATICOS.get(clave, f"Grupo {clave}")

TIPOS_ENFOQUE_MIXTO = frozenset({"Teoria", "Calculo"})
TIPOS_ENFOQUE_TEORIA = frozenset({"Teoria"})
TIPOS_ENFOQUE_CALCULO = frozenset({"Calculo"})

ID_ESTRATEGIA_MATERIAS = "estrategia_materias"
ESTRATEGIA_MATERIAS_DEFECTO = "debilidades"

VALORES_PRIORIDAD_HISTORICA: tuple[tuple[str, str], ...] = (
    ("debilidades", "Debilidades (más suspensos)"),
    ("fortalezas", "Fortalezas (mejores medias)"),
    ("equilibrado", "Equilibrado (histórico suave)"),
    ("curricular", "Orden del plan de estudios"),
    ("sin_historico", "Reparto equilibrado (sin histórico)"),
)

VALORES_ESTRATEGIA_MATERIAS = frozenset(v for v, _ in VALORES_PRIORIDAD_HISTORICA)

# Orden fijo de filtros en la UI de configuración (solo entran las opciones del preset).
ORDEN_OPCIONES_HISTORIA: tuple[str, ...] = (
    "periodo",
    "curso",
    "semestre",
    "grupo",
    "materia",
    "origen_semilla",
    "semilla",
    ID_ESTRATEGIA_MATERIAS,
    "n_materias",
    "enfoque",
    "n_preguntas",
    "tiempo_total_min",
)

_ORDEN_OPCION_IDX = {op_id: i for i, op_id in enumerate(ORDEN_OPCIONES_HISTORIA)}


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


_OPCION_PRIORIDAD_HISTORICA = OpcionPreset(
    id=ID_ESTRATEGIA_MATERIAS,
    tipo="eleccion",
    etiqueta="Prioridad histórica",
    defecto=ESTRATEGIA_MATERIAS_DEFECTO,
    valores=VALORES_PRIORIDAD_HISTORICA,
)


def _ordenar_opciones_historia(
    opciones: tuple[OpcionPreset, ...],
) -> tuple[OpcionPreset, ...]:
    def clave(op: OpcionPreset) -> tuple[int, str]:
        return (_ORDEN_OPCION_IDX.get(op.id, 999), op.id)

    return tuple(sorted(opciones, key=clave))


def opciones_config_historia(preset) -> tuple[OpcionPreset, ...]:
    """Opciones del preset en orden global; prioridad histórica canónica si usa MatCAD."""
    base = tuple(o for o in preset.opciones if o.id != ID_ESTRATEGIA_MATERIAS)
    if preset.usa_analisis_historico:
        base = base + (_OPCION_PRIORIDAD_HISTORICA,)
    return _ordenar_opciones_historia(base)


def estrategia_materias_desde_config(cfg: ConfigPresetHistoria) -> str | None:
    return cfg.get_str(ID_ESTRATEGIA_MATERIAS)


def usar_analisis_historico_desde_config(preset, cfg: ConfigPresetHistoria) -> bool:
    if not preset.usa_analisis_historico:
        return False
    if estrategia_materias_desde_config(cfg) == "sin_historico":
        return False
    return True


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


def semestres_disponibles(materias_meta: dict[str, dict[str, str]]) -> list[str]:
    """Semestres presentes en el catálogo (todos los cursos)."""
    return sorted(
        {str(m.get("semestre")) for m in materias_meta.values() if m.get("semestre")}
    )


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


def periodos_academicos(
    materias_meta: dict[str, dict[str, str]],
) -> list[tuple[str, str, str]]:
    """Pares curso-semestre del plan: clave ``3-2`` = curso 3, semestre 2."""
    pares: set[tuple[str, str]] = set()
    for meta in materias_meta.values():
        curso = meta.get("curso")
        semestre = meta.get("semestre")
        if curso and semestre:
            pares.add((str(curso), str(semestre)))
    items = [(f"{c}-{s}", c, s) for c, s in pares]
    items.sort(key=lambda t: (int(t[1]), int(t[2])))
    return items


def parse_periodo(valor: str) -> tuple[str, str]:
    texto = (valor or "").strip()
    if "-" not in texto:
        raise ValueError(f"Periodo académico no válido: {valor!r} (use curso-semestre, p. ej. 3-2).")
    curso, semestre = texto.split("-", 1)
    curso = curso.strip()
    semestre = semestre.strip()
    if not curso or not semestre:
        raise ValueError(f"Periodo académico no válido: {valor!r}.")
    return curso, semestre


def periodo_valido(materias_meta: dict[str, dict[str, str]], valor: str) -> bool:
    return any(clave == str(valor) for clave, _, _ in periodos_academicos(materias_meta))


def curso_semestre_desde_valores(valores: dict[str, Any]) -> tuple[str | None, str | None]:
    """Resuelve filtros curso/semestre (incl. opción ``periodo`` tipo 3-2)."""
    periodo = valores.get("periodo")
    if periodo:
        curso, semestre = parse_periodo(str(periodo))
        return curso, semestre
    curso = valores.get("curso")
    semestre = valores.get("semestre")
    return (
        str(curso) if curso else None,
        str(semestre) if semestre else None,
    )


_IDS_FILTRO_AMBITO = frozenset({"curso", "semestre", "periodo"})
_IDS_FILTRO_GRUPO = frozenset({"grupo"})


def _tiene_filtro_curricular(valores: dict[str, Any]) -> bool:
    return bool(
        valores.get("periodo") or valores.get("curso") or valores.get("semestre")
    )


def _simulacro_ambito_curso_completo(valores: dict[str, Any]) -> bool:
    """Curso entero: curso elegido sin semestre académico ni semestre suelto."""
    return bool(valores.get("curso")) and not valores.get("periodo") and not valores.get("semestre")


def _simulacro_modo_semestre(valores: dict[str, Any]) -> bool:
    """Un semestre académico concreto o un semestre dentro de un curso."""
    if valores.get("periodo"):
        return True
    return bool(valores.get("curso")) and bool(valores.get("semestre"))


_PRESETS_AMBITO_SEMESTRE_ESTRICTO = frozenset({
    "simulacro",
})


def ids_filtro_ambito(opciones: tuple[OpcionPreset, ...]) -> frozenset[str]:
    tipos = frozenset({"curso", "semestre", "periodo"})
    return frozenset(o.id for o in opciones if o.id in _IDS_FILTRO_AMBITO or o.tipo in tipos)


def tiene_exclusion_periodo_curso_semestre(opciones: tuple[OpcionPreset, ...]) -> bool:
    ids = ids_filtro_ambito(opciones)
    return "periodo" in ids and ("curso" in ids or "semestre" in ids)


def modo_filtro_ambito(valores: dict[str, Any]) -> str:
    """``periodo`` (3-2) o ``curso_semestre`` (filtros separados) o ``ninguno``."""
    if valores.get("periodo"):
        return "periodo"
    if valores.get("curso") or valores.get("semestre"):
        return "curso_semestre"
    return "ninguno"


def _origen_semilla_examen_fijo(valores: dict[str, Any]) -> str:
    return str(valores.get("origen_semilla") or "diario")


def filtro_ambito_bloqueado(
    op_id: str,
    valores: dict[str, Any],
    opciones: tuple[OpcionPreset, ...],
    *,
    preset_id: str | None = None,
) -> bool:
    if preset_id == "examen_fijo" and op_id == "semilla":
        return _origen_semilla_examen_fijo(valores) != "semilla"
    if op_id not in _IDS_FILTRO_AMBITO and op_id not in _IDS_FILTRO_GRUPO:
        if preset_id == "simulacro" and _simulacro_ambito_curso_completo(valores):
            if op_id in ("periodo", "semestre"):
                return True
        return False
    if not tiene_exclusion_periodo_curso_semestre(opciones):
        pass
    elif op_id in _IDS_FILTRO_AMBITO:
        modo = modo_filtro_ambito(valores)
        if modo == "periodo":
            if op_id in ("curso", "semestre"):
                return True
        elif modo == "curso_semestre":
            if op_id == "periodo":
                return True
    if valores.get("grupo"):
        if op_id in _IDS_FILTRO_AMBITO:
            return True
    if _tiene_filtro_curricular(valores) and op_id == "grupo":
        return True
    if preset_id == "simulacro" and _simulacro_ambito_curso_completo(valores):
        if op_id in ("periodo", "semestre"):
            return True
    return False


def aplicar_exclusion_al_cambiar_ambito(
    valores: dict[str, Any],
    op_id: str,
    *,
    preset_id: str | None = None,
    materias_meta: dict[str, dict[str, str]] | None = None,
    n_materias_max: int = 40,
) -> None:
    if op_id == "periodo" and valores.get("periodo"):
        valores.pop("curso", None)
        valores.pop("semestre", None)
        valores.pop("grupo", None)
    elif op_id in ("curso", "semestre") and (valores.get("curso") or valores.get("semestre")):
        valores.pop("periodo", None)
        valores.pop("grupo", None)
    elif op_id == "grupo" and valores.get("grupo"):
        valores.pop("periodo", None)
        valores.pop("curso", None)
        valores.pop("semestre", None)
    elif op_id == "origen_semilla":
        if _origen_semilla_examen_fijo(valores) == "semilla":
            from Comun.modos_diarios import semilla_defecto_examen_fijo

            valores.setdefault("semilla", semilla_defecto_examen_fijo())
    if preset_id == "simulacro" and op_id in ("curso", "periodo", "semestre"):
        if op_id == "curso" and valores.get("curso") and not valores.get("semestre"):
            valores.pop("periodo", None)
            valores.pop("semestre", None)
        ajustar_defectos_simulacro(
            valores,
            materias_meta=materias_meta,
            plantilla_max=n_materias_max,
        )


def validar_coherencia_filtros_ambito(
    opciones: tuple[OpcionPreset, ...],
    valores: dict[str, Any],
    *,
    preset_id: str | None = None,
) -> None:
    ids = ids_filtro_ambito(opciones)
    if not ids:
        return
    tiene_periodo = bool(valores.get("periodo"))
    tiene_curso = bool(valores.get("curso"))
    tiene_semestre = bool(valores.get("semestre"))

    if tiene_exclusion_periodo_curso_semestre(opciones):
        if tiene_periodo and (tiene_curso or tiene_semestre):
            raise ValueError(
                "Usa semestre académico (3-2) o curso y semestre por separado, no ambos a la vez."
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
) -> int:
    """Asignaturas disponibles según los filtros activos (vacío = todo el catálogo)."""
    return contar_materias_ambito(
        materias_meta,
        curso=curso,
        semestre=semestre,
        grupo=grupo,
    )


def _max_n_materias_simulacro(
    valores: dict[str, Any],
    *,
    materias_meta: dict[str, dict[str, str]] | None = None,
    plantilla_max: int = 40,
) -> int:
    """Tope efectivo de asignaturas según filtros: 40, 20, 10 o 5."""
    curso, semestre = curso_semestre_desde_valores(valores)
    if materias_meta is None:
        if _simulacro_modo_semestre(valores):
            return 5
        if _simulacro_ambito_curso_completo(valores):
            return 10
        if valores.get("semestre"):
            return 20
        return plantilla_max
    tope = max_materias_ambito(
        materias_meta,
        curso=curso,
        semestre=semestre,
        grupo=None,
    )
    if tope <= 0:
        return 0
    return min(plantilla_max, tope)


def limites_n_materias(
    op: OpcionPreset,
    valores: dict[str, Any],
    *,
    materias_meta: dict[str, dict[str, str]],
    preset_id: str | None = None,
) -> tuple[int, int]:
    """Mínimo y máximo efectivos de ``n_materias`` según curso/semestre/grupo."""
    min_v = op.min if op.min is not None else 1
    if preset_id in ("repaso", "simulacro"):
        min_v = max(min_v, min_materias_para_minimo_preguntas(PREGUNTAS_POR_MATERIA_HISTORIA))
    max_plantilla = op.max if op.max is not None else 9999
    curso, semestre = curso_semestre_desde_valores(valores)
    tope = max_materias_ambito(
        materias_meta,
        curso=curso,
        semestre=semestre,
        grupo=str(valores.get("grupo") or "") or None,
    )
    max_v = min(max_plantilla, tope)
    if tope <= 0:
        return 0, 0
    if max_v < min_v:
        return 0, 0
    return min_v, max_v


def contar_plantillas_elegibles(
    plantillas: list[dict],
    enfoque: str | None,
) -> int:
    """Plantillas de una materia que encajan con el tipo de preguntas elegido (teoría/cálculo)."""
    tipos = tipos_desde_enfoque(enfoque)
    return sum(
        1
        for plantilla in plantillas
        if (plantilla.get("tipo") or "Teoria").strip() in tipos
    )


def limites_n_preguntas(
    op: OpcionPreset,
    valores: dict[str, Any],
    *,
    plantillas_materia: list[dict] | None,
) -> tuple[int, int]:
    """Mínimo y máximo efectivos de ``n_preguntas`` según materia y tipo de preguntas."""
    min_v = max(op.min if op.min is not None else 1, MIN_PREGUNTAS_PARTIDA)
    max_plantilla = op.max if op.max is not None else 9999
    if plantillas_materia is not None:
        tope = contar_plantillas_elegibles(plantillas_materia, valores.get("enfoque"))
        max_v = min(max_plantilla, tope) if tope > 0 else 0
    else:
        max_v = max_plantilla
    if max_v <= 0 or max_v < min_v:
        return 0, 0
    return min_v, max_v


def ajustar_n_preguntas_examen_asignatura(
    valores: dict[str, Any],
    opciones: tuple[OpcionPreset, ...],
    plantillas_materia: list[dict],
) -> None:
    """Recorta N preguntas si la materia o el tipo de preguntas reducen las plantillas disponibles."""
    op = next((o for o in opciones if o.id == "n_preguntas"), None)
    if op is None:
        return
    min_v, max_v = limites_n_preguntas(op, valores, plantillas_materia=plantillas_materia)
    if max_v <= 0:
        valores.pop("n_preguntas", None)
        return
    defecto = int(op.defecto if op.defecto is not None else min_v)
    actual = int(valores.get("n_preguntas", defecto))
    valores["n_preguntas"] = min(max(actual, min_v), max_v)


def max_tiempo_total_min(
    op: OpcionPreset,
    valores: dict[str, Any],
    *,
    preset_id: str | None = None,
) -> int:
    max_v = op.max if op.max is not None else 9999
    if preset_id == "simulacro":
        return 180 if _simulacro_modo_semestre(valores) else 240
    return max_v


def ajustar_defectos_simulacro(
    valores: dict[str, Any],
    *,
    materias_meta: dict[str, dict[str, str]] | None = None,
    plantilla_max: int = 40,
) -> None:
    """Recorta N materias y tiempo si el ámbito ya no admite el valor actual."""
    max_n = _max_n_materias_simulacro(
        valores, materias_meta=materias_meta, plantilla_max=plantilla_max
    )
    if max_n <= 0:
        return
    valores["n_materias"] = min(int(valores.get("n_materias", max_n)), max_n)
    if _simulacro_modo_semestre(valores):
        if int(valores.get("tiempo_total_min", 90)) > 180:
            valores["tiempo_total_min"] = 90
    elif int(valores.get("tiempo_total_min", 120)) > 240:
        valores["tiempo_total_min"] = 120


def materias_ordenadas(materias_orden: list[str]) -> list[str]:
    return list(materias_orden)


def defectos_config(
    opciones: tuple[OpcionPreset, ...],
    *,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
) -> ConfigPresetHistoria:
    valores: dict[str, Any] = {}
    exclusion = tiene_exclusion_periodo_curso_semestre(opciones)
    for op in opciones:
        if op.defecto is not None:
            valores[op.id] = op.defecto
        elif op.tipo == "materia" and materias_orden:
            valores[op.id] = materias_orden[0]
        elif op.tipo == "curso" and (op.obligatorio or not exclusion):
            cursos = cursos_disponibles(materias_meta)
            if cursos:
                valores[op.id] = cursos[0]
        elif op.tipo == "grupo":
            if op.defecto is not None:
                valores[op.id] = op.defecto
            elif op.obligatorio:
                valores[op.id] = "1"
        elif op.tipo == "periodo" and op.defecto is None and not exclusion:
            periodos = periodos_academicos(materias_meta)
            if periodos:
                valores[op.id] = periodos[0][0]
    if exclusion:
        if valores.get("periodo"):
            valores.pop("curso", None)
            valores.pop("semestre", None)
        elif valores.get("curso") or valores.get("semestre"):
            valores.pop("periodo", None)
    if valores.get("grupo"):
        valores.pop("periodo", None)
        valores.pop("curso", None)
        valores.pop("semestre", None)
    elif _tiene_filtro_curricular(valores):
        valores.pop("grupo", None)
    if any(o.id == "enfoque" for o in opciones):
        op_nm = next((o for o in opciones if o.id == "n_materias"), None)
        plantilla_max = op_nm.max if op_nm and op_nm.max is not None else 40
        ajustar_defectos_simulacro(
            valores,
            materias_meta=materias_meta,
            plantilla_max=plantilla_max,
        )
    if any(o.id == "origen_semilla" for o in opciones):
        from Comun.modos_diarios import semilla_defecto_examen_fijo

        valores["semilla"] = semilla_defecto_examen_fijo()
    if any(o.id == "n_preguntas" for o in opciones):
        from Comun.datos import cargar_plantillas_materia
        from Comun.rutas import resolver_plantillas

        materia = valores.get("materia")
        if materia:
            plantillas = cargar_plantillas_materia(resolver_plantillas(), str(materia))
            ajustar_n_preguntas_examen_asignatura(valores, opciones, plantillas)
    return ConfigPresetHistoria(valores=valores)


def validar_config(
    opciones: tuple[OpcionPreset, ...],
    config: ConfigPresetHistoria,
    *,
    materias_meta: dict[str, dict[str, str]],
    preset_id: str | None = None,
    plantillas_materia: list[dict] | None = None,
) -> ConfigPresetHistoria:
    valores = dict(config.valores)
    if tiene_exclusion_periodo_curso_semestre(opciones):
        if valores.get("periodo"):
            valores.pop("curso", None)
            valores.pop("semestre", None)
        elif valores.get("curso") or valores.get("semestre"):
            valores.pop("periodo", None)
    if valores.get("grupo"):
        valores.pop("periodo", None)
        valores.pop("curso", None)
        valores.pop("semestre", None)
    elif _tiene_filtro_curricular(valores):
        valores.pop("grupo", None)
    for op in opciones:
        if filtro_ambito_bloqueado(
            op.id, valores, opciones, preset_id=preset_id
        ):
            continue
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
                min_v, max_v = limites_n_materias(
                    op,
                    valores,
                    materias_meta=materias_meta,
                    preset_id=preset_id,
                )
                if max_v <= 0:
                    raise ValueError(
                        f"No se puede montar un examen de al menos {MIN_PREGUNTAS_PARTIDA} "
                        "preguntas con el ámbito elegido."
                    )
            elif op.id == "n_preguntas":
                min_v, max_v = limites_n_preguntas(
                    op,
                    valores,
                    plantillas_materia=plantillas_materia,
                )
                if max_v <= 0:
                    raise ValueError(
                        f"No hay suficientes plantillas para un examen de al menos "
                        f"{MIN_PREGUNTAS_PARTIDA} preguntas con la materia y el tipo de preguntas "
                        "elegidos."
                    )
            elif op.id == "tiempo_total_min":
                max_v = max_tiempo_total_min(op, valores, preset_id=preset_id)
            if not (min_v <= n <= max_v):
                raise ValueError(f"{op.etiqueta}: valor entre {min_v} y {max_v}.")
            valores[op.id] = n
        elif op.tipo == "curso":
            if not raw:
                if op.obligatorio or (
                    preset_id == "simulacro" and _simulacro_ambito_curso_completo(valores)
                ):
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
                semestre = str(raw)
                if curso:
                    if semestre not in semestres_para_curso(materias_meta, str(curso)):
                        raise ValueError(f"Semestre no válido para el curso {curso}.")
                elif semestre not in semestres_disponibles(materias_meta):
                    raise ValueError(f"Semestre no válido: {semestre!r}.")
                valores[op.id] = semestre
        elif op.tipo == "periodo":
            if not raw:
                if op.obligatorio:
                    raise ValueError(f"Elige {op.etiqueta.lower()}.")
            elif not periodo_valido(materias_meta, str(raw)):
                raise ValueError(f"Periodo no válido: {raw!r} (use curso-semestre, p. ej. 3-2).")
            else:
                valores[op.id] = str(raw)
        elif op.tipo == "grupo":
            if not raw:
                if op.obligatorio:
                    raise ValueError(f"Elige {op.etiqueta.lower()}.")
            elif str(raw) not in GRUPOS_TEMATICOS:
                raise ValueError(f"Grupo no válido: {raw!r}.")
            else:
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
    validar_coherencia_filtros_ambito(opciones, valores, preset_id=preset_id)
    return ConfigPresetHistoria(valores=valores)


def tipos_desde_enfoque(enfoque: str | None) -> frozenset[str]:
    if enfoque == "teoria":
        return TIPOS_ENFOQUE_TEORIA
    if enfoque == "calculo":
        return TIPOS_ENFOQUE_CALCULO
    return TIPOS_ENFOQUE_MIXTO


def tiempo_total_seg_desde_config(config: ConfigPresetHistoria) -> int | None:
    minutos = config.get_int("tiempo_total_min", 0)
    if minutos <= 0:
        return None
    return minutos * 60


_PASOS_ENTERO_HISTORIA: dict[str, int] = {
    "n_materias": 5,
    "n_preguntas": 5,
    "tiempo_total_min": 15,
}


def paso_entero_opcion_historia(op_id: str) -> int:
    """Incremento ◀ ▶ de opciones enteras en la configuración de historia."""
    return _PASOS_ENTERO_HISTORIA.get(op_id, 1)


def siguiente_entero_ciclo(
    actual: int,
    delta: int,
    *,
    min_v: int,
    max_v: int,
    paso: int = 1,
) -> int:
    """Nuevo valor al pulsar ◀ o ▶, con paso fijo y tope en min/max."""
    if paso <= 0:
        paso = 1
    incremento = paso if delta > 0 else -paso
    return min(max(actual + incremento, min_v), max_v)
