#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo y resolución de partidas del modo historia."""

from __future__ import annotations

from collections.abc import Callable
import json
from dataclasses import dataclass
from pathlib import Path

from Comun.config_historia import (
    MATERIAS_POR_SEMESTRE,
    ConfigPresetHistoria,
    OpcionPreset,
    contar_materias_ambito,
    defectos_config,
    max_materias_ambito,
    parse_opciones,
    slots_desde_enfoque,
    tiempo_total_seg_desde_config,
    validar_config,
)
from Comun.perfiles_historia import PerfilPedagogico
from Comun.politica_reglas import (
    ContextoPartida,
    PoliticaReglas,
    politica_historia_resistencia,
    politica_historia_reto,
    politica_historia_simulacro,
    validar_reglas,
)
from Comun.reglas_partida import ReglasPartida


@dataclass(frozen=True)
class PresetHistoria:
    """Plantilla de partida con reglas fijas y opciones acotadas."""

    id: str
    nombre: str
    descripcion: str
    categoria: str
    orden: int
    perfil: str
    contexto_reglas: str
    seleccion_determinista: bool
    n_materias: int | None
    curso_filtro: str | None
    semestre_filtro: str | None
    grupo_filtro: str | None
    slots: tuple[tuple[str, str], ...] | None
    opciones: tuple[OpcionPreset, ...]
    tiempo_por_pregunta_seg: int | None = None
    tiempo_total_seg: int | None = None
    orden_por_historico: str | None = None
    usa_analisis_historico: bool = False

    def contexto(self) -> ContextoPartida:
        return ContextoPartida(self.contexto_reglas)

    def tiene_opciones(self) -> bool:
        return bool(self.opciones)


def _parse_slots(raw: list | None) -> tuple[tuple[str, str], ...] | None:
    if not raw:
        return None
    out: list[tuple[str, str]] = []
    for par in raw:
        if not isinstance(par, list) or len(par) != 2:
            raise ValueError(f"Slot inválido: {par!r}")
        out.append((str(par[0]), str(par[1])))
    return tuple(out)


_IDS_PRESET_REPASOS: frozenset[str] = frozenset({
    "refuerzo_historico",
    "desafio_historico",
    "sesion_pre_entrega",
    "repaso_semestre",
    "repaso_curso",
})

_IDS_PRESET_SIMULACROS: frozenset[str] = frozenset({
    "simulacro_examen",
    "simulacro_solo_teoria",
    "parcial_materia",
    "parcial_grupo",
})


def _grupo_catalogo_historia(preset_id: str) -> int:
    """Orden de bloques en el carrusel: repasos, luego simulacros, luego el resto."""
    if preset_id in _IDS_PRESET_REPASOS:
        return 1
    if preset_id in _IDS_PRESET_SIMULACROS:
        return 2
    return 3


def _clave_orden_catalogo(preset: PresetHistoria) -> tuple[int, int, int, str]:
    """Diarios primero; dentro del catálogo, repasos y simulacros en bloques."""
    from Comun.modos_diarios import prioridad_orden_preset

    return (
        prioridad_orden_preset(preset.id),
        _grupo_catalogo_historia(preset.id),
        preset.orden,
        preset.nombre,
    )


def _cargar_presets_desde_json(
    path: Path,
    *,
    clave_orden: Callable[[PresetHistoria], tuple],
) -> list[PresetHistoria]:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el catálogo: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido en {path}: {e}") from e
    items = data.get("presets")
    if not isinstance(items, list) or not items:
        raise ValueError(f"El catálogo {path} no contiene presets.")
    presets = [_parse_preset(x) for x in items]
    presets.sort(key=clave_orden)
    ids = [p.id for p in presets]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Hay ids duplicados en {path.name}")
    return presets


def cargar_presets_historia(path: Path) -> list[PresetHistoria]:
    return _cargar_presets_desde_json(path, clave_orden=_clave_orden_catalogo)


def cargar_presets_especiales(path: Path) -> list[PresetHistoria]:
    from Comun.modos_diarios import prioridad_orden_preset

    return _cargar_presets_desde_json(
        path,
        clave_orden=lambda preset: (
            prioridad_orden_preset(preset.id),
            preset.orden,
            preset.nombre,
        ),
    )


def buscar_preset(preset_id: str) -> PresetHistoria:
    """Busca un preset en historia o en modos especiales."""
    from Comun.rutas import resolver_presets_especiales, resolver_presets_historia

    for cargar, resolver in (
        (cargar_presets_historia, resolver_presets_historia),
        (cargar_presets_especiales, resolver_presets_especiales),
    ):
        for preset in cargar(resolver()):
            if preset.id == preset_id:
                return preset
    raise KeyError(f"Preset no encontrado: {preset_id!r}")


def _parse_preset(item: dict) -> PresetHistoria:
    for campo in ("id", "nombre", "descripcion", "perfil", "contexto_reglas"):
        if not item.get(campo):
            raise ValueError(f"Preset sin campo obligatorio {campo!r}: {item!r}")
    contexto = item["contexto_reglas"]
    if contexto not in {c.value for c in ContextoPartida if c.name.startswith("HISTORIA_")}:
        raise ValueError(f"contexto_reglas desconocido: {contexto!r}")
    return PresetHistoria(
        id=str(item["id"]),
        nombre=str(item["nombre"]),
        descripcion=str(item["descripcion"]),
        categoria=str(item.get("categoria") or "General"),
        orden=int(item.get("orden", 999)),
        perfil=str(item["perfil"]),
        contexto_reglas=contexto,
        seleccion_determinista=bool(item.get("seleccion_determinista", False)),
        n_materias=item.get("n_materias"),
        curso_filtro=item.get("curso_filtro"),
        semestre_filtro=item.get("semestre_filtro"),
        grupo_filtro=item.get("grupo_filtro"),
        slots=_parse_slots(item.get("slots")),
        opciones=parse_opciones(item.get("opciones")),
        tiempo_por_pregunta_seg=item.get("tiempo_por_pregunta_seg"),
        tiempo_total_seg=item.get("tiempo_total_seg"),
        orden_por_historico=item.get("orden_por_historico"),
        usa_analisis_historico=bool(item.get("usa_analisis_historico", False)),
    )


def config_defecto(
    preset: PresetHistoria,
    *,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
) -> ConfigPresetHistoria:
    return defectos_config(
        preset.opciones,
        materias_meta=materias_meta,
        materias_orden=materias_orden,
    )


def politica_desde_preset(
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
) -> PoliticaReglas:
    if preset.contexto_reglas == ContextoPartida.HISTORIA_RETO.value:
        base = politica_historia_reto()
    elif preset.contexto_reglas == ContextoPartida.HISTORIA_RESISTENCIA.value:
        base = politica_historia_resistencia()
    else:
        base = politica_historia_simulacro()
    reglas = _reglas_con_tiempo(base.reglas, preset, config)
    return PoliticaReglas(
        contexto=preset.contexto(),
        reglas=reglas,
        eleccion_jugador=bool(preset.opciones),
        mensaje=f"{preset.nombre}: {preset.descripcion}",
    )


def aplicar_preset(
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
) -> ReglasPartida:
    politica = politica_desde_preset(preset, config)
    return validar_reglas(politica.reglas, politica.contexto)


def _reglas_con_tiempo(
    base: ReglasPartida,
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None,
) -> ReglasPartida:
    tiempo_preg = preset.tiempo_por_pregunta_seg
    tiempo_tot = preset.tiempo_total_seg
    if config is not None:
        t_cfg = tiempo_total_seg_desde_config(config)
        if t_cfg is not None:
            tiempo_tot = t_cfg
    if not tiempo_preg and not tiempo_tot:
        return base
    return ReglasPartida(
        vidas=base.vidas,
        tiempo_por_pregunta_seg=tiempo_preg,
        tiempo_total_seg=tiempo_tot,
        sistema_puntuacion=base.sistema_puntuacion,
        mostrar_solucion_tras_fallo=base.mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=base.mostrar_aciertos_en_curso,
        correccion_al_final=base.correccion_al_final,
        dificultad_progresiva=base.dificultad_progresiva,
    )


def perfil_desde_preset(preset: PresetHistoria) -> PerfilPedagogico:
    try:
        return PerfilPedagogico(preset.perfil)
    except ValueError as e:
        raise ValueError(f"Perfil desconocido en preset {preset.id!r}: {preset.perfil!r}") from e


_ESTRATEGIA_MATERIAS: dict[str, tuple[PerfilPedagogico, bool]] = {
    "curricular": (PerfilPedagogico.BALANCEADO, True),
    "debilidades": (PerfilPedagogico.REFUERZO, False),
    "fortalezas": (PerfilPedagogico.DESAFIO, False),
}


def _resolver_perfil_y_seleccion(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
) -> tuple[PerfilPedagogico, bool]:
    estrategia = cfg.get_str("estrategia_materias")
    if estrategia and estrategia in _ESTRATEGIA_MATERIAS:
        perfil, seleccion_det = _ESTRATEGIA_MATERIAS[estrategia]
        return perfil, seleccion_det
    return perfil_desde_preset(preset), preset.seleccion_determinista


def semilla_desde_preset(preset: PresetHistoria) -> int | None:
    from Comun.examen_dia_historia import es_id_examen_dia, semilla_examen_dia

    if es_id_examen_dia(preset.id):
        return semilla_examen_dia()
    return None


def argumentos_generador(
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
    *,
    materias_meta: dict[str, dict[str, str]] | None = None,
) -> dict:
    """Parámetros nombrados para ``generar_examen``."""
    cfg = config or ConfigPresetHistoria()
    curso = cfg.get_str("curso") or preset.curso_filtro
    semestre = cfg.get_str("semestre") or preset.semestre_filtro
    grupo = cfg.get_str("grupo") or preset.grupo_filtro
    materia = cfg.get_str("materia")

    n_materias = preset.n_materias
    if any(o.id == "n_materias" for o in preset.opciones):
        for op in preset.opciones:
            if op.id == "n_materias":
                n_materias = cfg.get_int("n_materias", int(op.defecto or MATERIAS_POR_SEMESTRE))
                break

    slots = preset.slots
    enfoque = cfg.get_str("enfoque")
    if enfoque:
        slots = slots_desde_enfoque(enfoque)

    usar_todas = preset.n_materias is None and "n_materias" not in {o.id for o in preset.opciones}
    if materia:
        usar_todas = False
        n_materias = 1

    perfil, seleccion_det = _resolver_perfil_y_seleccion(preset, cfg)

    if (
        not usar_todas
        and n_materias is not None
        and materias_meta is not None
        and semestre
        and curso
        and n_materias >= MATERIAS_POR_SEMESTRE
    ):
        en_semestre = contar_materias_ambito(
            materias_meta, curso=curso, semestre=semestre, grupo=None
        )
        if en_semestre > 0 and n_materias >= en_semestre:
            n_materias = en_semestre

    if (
        not usar_todas
        and n_materias is not None
        and materias_meta is not None
        and curso
        and not semestre
        and not grupo
        and not materia
        and preset.id in {"refuerzo_historico", "desafio_historico"}
    ):
        tope = max_materias_ambito(
            materias_meta, curso=curso, semestre=None, grupo=None
        )
        if tope is not None:
            n_materias = min(n_materias, tope)

    return {
        "perfil": perfil,
        "n_materias": n_materias if n_materias is not None else MATERIAS_POR_SEMESTRE,
        "curso_filtro": curso,
        "semestre_filtro": semestre,
        "grupo_filtro": grupo,
        "materia_fija": materia,
        "slots": slots,
        "usar_todas_materias_ambito": usar_todas,
        "seleccion_determinista": seleccion_det,
        "orden_por_historico": preset.orden_por_historico,
    }
