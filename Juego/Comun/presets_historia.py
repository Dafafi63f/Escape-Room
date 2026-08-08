#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cat?logo de presets (historia y modos especiales) y resoluci?n de partidas."""

from __future__ import annotations

from collections.abc import Callable
import json
from dataclasses import dataclass, replace
from pathlib import Path

from Comun.config_historia import (
    MATERIAS_POR_SEMESTRE,
    ConfigPresetHistoria,
    OpcionPreset,
    curso_semestre_desde_valores,
    defectos_config,
    estrategia_efectiva_desde_config,
    opciones_config_historia,
    preset_usa_prioridad_materias,
    usar_ponderacion_desde_config,
    max_materias_ambito,
    parse_opciones,
    tipos_desde_enfoque,
    tiempo_total_seg_desde_config,
    validar_config,
)
from Comun.generador_examen_historia import OpcionesGeneracionExamen, PerfilPedagogico
from Comun.reglas import (
    ContextoPartida,
    PoliticaReglas,
    politica_escape,
    politica_resistencia,
    politica_historia_reto,
    politica_historia_simulacro,
    validar_reglas,
)
from Comun.reglas import ReglasPartida


ORDEN_PREGUNTAS_VALIDOS = frozenset({
    "aleatorio",
    "dificultad",
    "materia",
    "plantilla",
    "variar",
})


def resolver_orden_preguntas(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria | None = None,
) -> str:
    """Orden expl?cito de preguntas en partida (independiente del azar de contenido)."""
    from Comun.modos_diarios import es_id_examen_fijo, orden_preguntas_examen_fijo

    if cfg is not None and es_id_examen_fijo(preset.id):
        return orden_preguntas_examen_fijo(cfg)
    raw = preset.orden_preguntas
    if raw:
        if raw not in ORDEN_PREGUNTAS_VALIDOS:
            raise ValueError(
                f"orden_preguntas inv?lido en {preset.id!r}: {raw!r} "
                f"(use: {', '.join(sorted(ORDEN_PREGUNTAS_VALIDOS))})."
            )
        return raw
    if preset.variar_orden_cada_partida:
        return "variar"
    if preset.orden_preguntas_por_materia:
        return "materia"
    if preset.orden_preguntas_por_dificultad:
        return "dificultad"
    return "aleatorio"


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
    preguntas_por_materia: int | None
    opciones: tuple[OpcionPreset, ...]
    tiempo_por_pregunta_seg: int | None = None
    tiempo_total_seg: int | None = None
    orden_preguntas: str | None = None
    orden_preguntas_por_dificultad: bool = False
    orden_preguntas_por_materia: bool = False
    variar_orden_cada_partida: bool = False
    exigir_balance_completo: bool = False
    usar_plantillas_materia: bool = False
    solo_atajo: bool = False

    def contexto(self) -> ContextoPartida:
        return ContextoPartida(self.contexto_reglas)

    def tiene_opciones(self) -> bool:
        return bool(self.opciones)


def _parse_preguntas_por_materia(raw: int | None) -> int | None:
    if raw is None:
        return None
    n = int(raw)
    if n <= 0:
        raise ValueError(f"preguntas_por_materia debe ser positivo: {n!r}")
    return n

_IDS_PRESET_REPASOS: frozenset[str] = frozenset({
    "repaso",
    "repaso_area",
})

_IDS_PRESET_SIMULACROS: frozenset[str] = frozenset({
    "simulacro",
    "examen_asignatura",
    "examen_fijo",
})

_IDS_PRESET_EXAMEN_DIRIGIDO: frozenset[str] = frozenset({
    "simulacro",
    "examen_fijo",
})


def materias_unicas_en_registros(registros: list) -> set[str]:
    """Asignaturas distintas presentes en los registros de una sesión."""
    out: set[str] = set()
    for registro in registros:
        materia = (getattr(registro.pregunta, "materia", "") or "").strip()
        if materia:
            out.add(materia)
    return out


def preset_permite_examen_dirigido(preset_id: str, registros: list | None = None) -> bool:
    """«Otro examen dirigido»: simulacros multi-materia y examen fijo; no repasos ni una sola asignatura."""
    if preset_id not in _IDS_PRESET_EXAMEN_DIRIGIDO:
        return False
    if registros is None:
        return True
    if not registros:
        return False
    materias = materias_unicas_en_registros(registros)
    if len(materias) >= 2:
        return True
    # CSV mínimo sin columna Materia: el dirigido analiza el contenido del enunciado.
    if preset_id == "examen_fijo" and not materias:
        return True
    return False


# IDs retirados del cat?logo activo (documentaci?n, tests y tabla en Data/README.md).
PRESETS_HISTORIA_RETIRADOS = frozenset({
    "examen_dia_historia",
    "examen_aleatorio_historia",
    "repaso_express",
    "repaso_historico",
    "repaso_integral",
    "vuelta_grado",
    "semana_examenes",
    "simulacro_curso",
    "ranking_resistencia",
})

# Paquete mínimo: sin carrusel de historia (examen fijo vía barra superior).
PRESETS_HISTORIA_PORTABLE: frozenset[str] = frozenset()

PRESETS_ESPECIALES_PORTABLE = frozenset({
    "resistencia",
})

NUM_MODOS_HISTORIA_CARRUSEL = 5
NUM_MODOS_HISTORIA_CARRUSEL_PORTABLE = 0

PRESETS_JSON_MINIMO = frozenset({
    "examen_fijo",
})

_CONTEXTOS_ESPECIALES = frozenset({
    ContextoPartida.ESCAPE.value,
    ContextoPartida.RESISTENCIA.value,
})


def _es_preset_historia(preset: PresetHistoria) -> bool:
    return preset.contexto_reglas.startswith("historia_")


def _es_preset_especial(preset: PresetHistoria) -> bool:
    return preset.contexto_reglas in _CONTEXTOS_ESPECIALES


def es_preset_escape_room(preset) -> bool:
    return getattr(preset, "contexto_reglas", "") == ContextoPartida.ESCAPE.value


def _grupo_catalogo_historia(preset_id: str) -> int:
    """Orden de bloques en el carrusel: repasos, luego simulacros, luego el resto."""
    if preset_id in _IDS_PRESET_REPASOS:
        return 1
    if preset_id in _IDS_PRESET_SIMULACROS:
        return 2
    return 3


def _clave_orden_catalogo(preset: PresetHistoria) -> tuple[int, int, int, str]:
    """Diarios primero; dentro del cat?logo, repasos y simulacros en bloques."""
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
        raise FileNotFoundError(f"No se encontr? el cat?logo: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inv?lido en {path}: {e}") from e
    items = data.get("presets")
    if not isinstance(items, list) or not items:
        raise ValueError(f"El cat?logo {path} no contiene presets.")
    presets = [_parse_preset(x) for x in items]
    presets.sort(key=clave_orden)
    ids = [p.id for p in presets]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Hay ids duplicados en {path.name}")
    return presets


def _cargar_presets_historia_archivo(path: Path) -> list[PresetHistoria]:
    return _cargar_presets_desde_json(
        path,
        clave_orden=_clave_orden_catalogo,
    )


def _cargar_todos_presets(path: Path | None = None) -> list[PresetHistoria]:
    from Comun.rutas import resolver_presets

    ruta = path or resolver_presets()
    return _cargar_presets_historia_archivo(ruta)


def cargar_presets_historia(
    path: Path | None = None,
    *,
    perfil=None,
) -> list[PresetHistoria]:
    """Cat?logo del carrusel (modos historia visibles, sin atajos ni especiales)."""
    if perfil is not None and perfil.historia_restringida:
        return []
    visibles = [
        p
        for p in _cargar_todos_presets(path)
        if _es_preset_historia(p) and not p.solo_atajo
    ]
    visibles.sort(key=_clave_orden_catalogo)
    if len(visibles) != NUM_MODOS_HISTORIA_CARRUSEL:
        ids = [p.id for p in visibles]
        raise ValueError(
            f"El carrusel de historia debe tener exactamente {NUM_MODOS_HISTORIA_CARRUSEL} "
            f"modos visibles; hay {len(visibles)}: {ids}"
        )
    return visibles


# --- modos_especiales ---


from functools import lru_cache

ID_MODO_RESISTENCIA = "resistencia"
ID_MODO_ESCAPE_ROOM = "escape_room"

_MODOS_ESPECIALES_ORDEN = (ID_MODO_ESCAPE_ROOM, ID_MODO_RESISTENCIA)


@lru_cache(maxsize=1)
def modos_especiales_builtin():
    """Instancias ``PresetHistoria`` de resistencia y escape room."""
    return [
        PresetHistoria(
            id=ID_MODO_ESCAPE_ROOM,
            nombre="Escape room",
            descripcion=(
                "30 salas, 3 puertas. Descanso, tienda y botín. Inventario de objetos "
                "como en resistencia. Tres vidas por partida."
            ),
            categoria="Escape room",
            orden=0,
            perfil="balanceado",
            contexto_reglas="escape",
            seleccion_determinista=True,
            n_materias=None,
            curso_filtro=None,
            semestre_filtro=None,
            grupo_filtro=None,
            preguntas_por_materia=None,
            opciones=(),
        ),
        PresetHistoria(
            id=ID_MODO_RESISTENCIA,
            nombre="Resistencia",
            descripcion=(
                "Banco completo, 3 vidas. Escalada, rachas y eventos aleatorios. "
                "Sin tope de preguntas."
            ),
            categoria="Resistencia",
            orden=1,
            perfil="balanceado",
            contexto_reglas="resistencia",
            seleccion_determinista=False,
            n_materias=None,
            curso_filtro=None,
            semestre_filtro=None,
            grupo_filtro=None,
            preguntas_por_materia=None,
            opciones=(),
        ),
    ]


def buscar_modo_especial(modo_id: str):
    for modo in modos_especiales_builtin():
        if modo.id == modo_id:
            return modo
    raise KeyError(f"Modo especial no encontrado: {modo_id!r}")


def catalogo_modos_especiales(*, perfil=None):
    del perfil  # firma estable para callers que pasan perfil=
    from Comun.modos_diarios import prioridad_orden_preset

    modos = list(modos_especiales_builtin())
    modos.sort(
        key=lambda preset: (
            prioridad_orden_preset(preset.id),
            preset.orden,
            preset.nombre,
        )
    )
    return modos


def cargar_presets_especiales(
    path: Path | None = None,
    *,
    perfil=None,
) -> list[PresetHistoria]:
    _ = path  # compatibilidad; los especiales ya no vienen del JSON
    return catalogo_modos_especiales(perfil=perfil)


def buscar_preset(preset_id: str) -> PresetHistoria:
    """Busca un preset del JSON o un modo especial definido en c?digo."""
    for preset in _cargar_todos_presets():
        if preset.id == preset_id:
            return preset
    return buscar_modo_especial(preset_id)


def _parse_preset(item: dict) -> PresetHistoria:
    for campo in ("id", "nombre", "descripcion", "perfil", "contexto_reglas"):
        if not item.get(campo):
            raise ValueError(f"Preset sin campo obligatorio {campo!r}: {item!r}")
    contexto = item["contexto_reglas"]
    if contexto not in {
        c.value
        for c in ContextoPartida
        if c.name.startswith("HISTORIA_")
        or c in (ContextoPartida.RESISTENCIA, ContextoPartida.ESCAPE)
    }:
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
        preguntas_por_materia=_parse_preguntas_por_materia(item.get("preguntas_por_materia")),
        opciones=parse_opciones(item.get("opciones")),
        tiempo_por_pregunta_seg=item.get("tiempo_por_pregunta_seg"),
        tiempo_total_seg=item.get("tiempo_total_seg"),
        orden_preguntas=item.get("orden_preguntas"),
        orden_preguntas_por_dificultad=bool(item.get("orden_preguntas_por_dificultad", False)),
        orden_preguntas_por_materia=bool(item.get("orden_preguntas_por_materia", False)),
        variar_orden_cada_partida=bool(item.get("variar_orden_cada_partida", False)),
        exigir_balance_completo=bool(item.get("exigir_balance_completo", False)),
        usar_plantillas_materia=bool(item.get("usar_plantillas_materia", False)),
        solo_atajo=bool(item.get("solo_atajo", False)),
    )


def config_defecto(
    preset: PresetHistoria,
    *,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
    path_plantillas: Path | None = None,
    perfil=None,
) -> ConfigPresetHistoria:
    return defectos_config(
        opciones_config_historia(preset, perfil=perfil),
        materias_meta=materias_meta,
        materias_orden=materias_orden,
        path_plantillas=path_plantillas,
        perfil=perfil,
    )


def politica_desde_preset(
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
) -> PoliticaReglas:
    if preset.contexto_reglas == ContextoPartida.HISTORIA_RETO.value:
        base = politica_historia_reto()
    elif preset.contexto_reglas == ContextoPartida.RESISTENCIA.value:
        base = politica_resistencia()
    elif preset.contexto_reglas == ContextoPartida.ESCAPE.value:
        base = politica_escape()
    else:
        base = politica_historia_simulacro()
    if preset.contexto_reglas == ContextoPartida.ESCAPE.value:
        reglas = base.reglas
    else:
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
    "equilibrado": (PerfilPedagogico.BALANCEADO, False),
    "sin_historico": (PerfilPedagogico.BALANCEADO, False),
}


def _resolver_perfil_y_seleccion(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
    *,
    perfil_datos=None,
) -> tuple[PerfilPedagogico, bool]:
    if preset_usa_prioridad_materias(preset, perfil_datos):
        estrategia = estrategia_efectiva_desde_config(cfg, perfil=perfil_datos)
        if estrategia in _ESTRATEGIA_MATERIAS:
            perfil, seleccion_det = _ESTRATEGIA_MATERIAS[estrategia]
            return perfil, seleccion_det
    return perfil_desde_preset(preset), preset.seleccion_determinista


def semilla_desde_preset(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria | None = None,
) -> int | None:
    from Comun.modos_diarios import es_id_examen_fijo
    from Comun.semillas import resolver_semillas_partida

    if cfg is not None and es_id_examen_fijo(preset.id):
        semilla = resolver_semillas_partida(
            preset_id=preset.id,
            cfg=cfg,
            orden_preguntas=resolver_orden_preguntas(preset, cfg),
        )
        return semilla
    return None


def contenido_examen_estable(
    preset: PresetHistoria,
    *,
    cfg: ConfigPresetHistoria | None = None,
    semilla: int | None = None,
) -> bool:
    """True si las preguntas no cambian entre entradas (p. ej. examen del d?a).

    Solo entonces tiene sentido ``variar_orden_cada_partida``: una sola fuente de azar.
    """
    from Comun.modos_diarios import contenido_estable_examen_fijo, es_id_examen_fijo

    if semilla is not None:
        return True
    if cfg is not None and es_id_examen_fijo(preset.id):
        return contenido_estable_examen_fijo(cfg)
    return False


def _ajustes_generador_examen_fijo_csv_minimo(
    preset: PresetHistoria,
    perfil_datos,
    cfg: ConfigPresetHistoria,
) -> tuple[bool, int, bool, str] | None:
    """CSV mínimo: muestra plana de N preguntas; la semilla define la selección."""
    from Comun.modos_diarios import (
        PREGUNTAS_EXAMEN_BALANCEADO,
        es_id_examen_fijo,
        orden_preguntas_examen_fijo,
    )

    if perfil_datos is None or not perfil_datos.csv_minimal:
        return None
    if not es_id_examen_fijo(preset.id):
        return None

    orden = orden_preguntas_examen_fijo(cfg)
    if orden == "dificultad" and not (
        perfil_datos is not None and perfil_datos.dataset_intermedio
    ):
        orden = "aleatorio"

    return True, PREGUNTAS_EXAMEN_BALANCEADO, False, orden


def _n_materias_desde_preset_cfg(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
) -> int | None:
    n_materias = preset.n_materias
    if any(o.id == "n_materias" for o in preset.opciones):
        for op in preset.opciones:
            if op.id == "n_materias":
                return cfg.get_int("n_materias", int(op.defecto or MATERIAS_POR_SEMESTRE))
    return n_materias


def _n_preguntas_desde_preset_cfg(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
) -> int | None:
    for op in preset.opciones:
        if op.id == "n_preguntas":
            return cfg.get_int("n_preguntas", int(op.defecto or 12))
    return None


def _usar_todas_y_n_materias(
    preset: PresetHistoria,
    materia: str | None,
    n_materias: int | None,
) -> tuple[bool, int | None]:
    usar_todas = (
        preset.n_materias is None
        and "n_materias" not in {o.id for o in preset.opciones}
    )
    if materia:
        return False, 1
    return usar_todas, n_materias


def _perfil_seleccion_argumentos(
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
    *,
    usar_todas: bool,
    perfil_datos,
):
    if usar_todas:
        estrategia = estrategia_efectiva_desde_config(cfg, perfil=perfil_datos)
        if estrategia in _ESTRATEGIA_MATERIAS:
            perfil, _ = _ESTRATEGIA_MATERIAS[estrategia]
        else:
            perfil = PerfilPedagogico.POR_CURSO
        return perfil, True
    return _resolver_perfil_y_seleccion(preset, cfg, perfil_datos=perfil_datos)


def _acotar_n_materias_ambito(
    n_materias: int | None,
    *,
    usar_todas: bool,
    materias_meta: dict[str, dict[str, str]] | None,
    curso,
    semestre,
    grupo,
) -> int | None:
    if usar_todas or n_materias is None or materias_meta is None:
        return n_materias
    tope = max_materias_ambito(
        materias_meta, curso=curso, semestre=semestre, grupo=grupo
    )
    if tope > 0:
        return min(n_materias, tope)
    return n_materias


def argumentos_generador(
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
    *,
    materias_meta: dict[str, dict[str, str]] | None = None,
    perfil_datos=None,
) -> OpcionesGeneracionExamen:
    """Opciones nombradas para ``generar_examen``."""
    cfg = config or ConfigPresetHistoria()
    curso, semestre = curso_semestre_desde_valores(cfg.valores)
    curso = curso or preset.curso_filtro
    semestre = semestre or preset.semestre_filtro
    grupo = cfg.get_str("grupo") or preset.grupo_filtro
    materia = cfg.get_str("materia")

    n_materias = _n_materias_desde_preset_cfg(preset, cfg)
    tipos_permitidos = tipos_desde_enfoque(cfg.get_str("enfoque"))
    usar_todas, n_materias = _usar_todas_y_n_materias(preset, materia, n_materias)
    perfil, seleccion_det = _perfil_seleccion_argumentos(
        preset, cfg, usar_todas=usar_todas, perfil_datos=perfil_datos
    )
    n_materias = _acotar_n_materias_ambito(
        n_materias,
        usar_todas=usar_todas,
        materias_meta=materias_meta,
        curso=curso,
        semestre=semestre,
        grupo=grupo,
    )
    n_preguntas = _n_preguntas_desde_preset_cfg(preset, cfg)

    opciones = OpcionesGeneracionExamen(
        perfil=perfil,
        n_materias=n_materias if n_materias is not None else MATERIAS_POR_SEMESTRE,
        curso_filtro=curso,
        semestre_filtro=semestre,
        grupo_filtro=grupo,
        materia_fija=materia,
        preguntas_por_materia=preset.preguntas_por_materia,
        tipos_permitidos=tipos_permitidos,
        usar_todas_materias_ambito=usar_todas,
        seleccion_determinista=seleccion_det,
        orden_preguntas=resolver_orden_preguntas(preset, cfg),
        exigir_balance_completo=preset.exigir_balance_completo,
        usar_analisis_historico=usar_ponderacion_desde_config(
            preset, cfg, perfil=perfil_datos
        ),
        usar_plantillas_materia=preset.usar_plantillas_materia,
        n_preguntas=n_preguntas,
        seleccion_plana=False,
    )
    ajustes = _ajustes_generador_examen_fijo_csv_minimo(preset, perfil_datos, cfg)
    if ajustes is not None:
        seleccion_plana, n_preg, exigir_balance, orden = ajustes
        opciones = replace(
            opciones,
            seleccion_plana=seleccion_plana,
            n_preguntas=n_preg,
            exigir_balance_completo=exigir_balance,
            orden_preguntas=orden,
        )
    return opciones
