#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estadísticas locales agregadas del jugador (``Data/Juego/estadisticas_jugador.json``)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Comun.persistencia import estadisticas_jugador_vacio
from Comun.informe_examen import CierreInformePartida, RegistroRespuesta
from Comun.motor_nucleo import EstadoPartida, formatear_duracion_seg
from Comun.rutas import _ruta_json_escritura

__all__ = [
    "formatear_panel_estadisticas",
    "registrar_cierre_partida",
    "resolver_path_estadisticas_jugador",
    "vaciar_estadisticas_jugador",
]

_MAX_SESIONES = 120
_MIN_INTENTOS_MATERIA = 3


def resolver_path_estadisticas_jugador():
    return _ruta_json_escritura("estadisticas_jugador.json")


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hoy_local() -> str:
    return datetime.now().date().isoformat()


def _vacio() -> dict[str, Any]:
    return estadisticas_jugador_vacio()


def _cargar_raw() -> dict[str, Any]:
    path = resolver_path_estadisticas_jugador()
    if not path.is_file():
        return _vacio()
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _vacio()
    if not isinstance(datos, dict):
        return _vacio()
    return datos


def _guardar_raw(datos: dict[str, Any]) -> None:
    path = resolver_path_estadisticas_jugador()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def vaciar_estadisticas_jugador() -> None:
    _guardar_raw(_vacio())


def _modo_partida(cierre: CierreInformePartida) -> str:
    meta = cierre.meta or {}
    if cierre.prefijo == "escape":
        return "escape"
    if meta.get("tipo_actividad") == "resistencia" or cierre.prefijo == "resistencia":
        return "resistencia"
    if meta.get("modo") == "libre":
        return "libre"
    return "historia"


def _etiqueta_modo(modo: str, perfil=None) -> str:
    if perfil is not None and perfil.modo_minimo and modo == "historia":
        return "Examen fijo"
    return {
        "libre": "Libre",
        "historia": "Historia",
        "examen_fijo": "Examen fijo",
        "resistencia": "Resistencia",
        "escape": "Escape room",
    }.get(modo, modo.capitalize())


def _inc_bucket(contenedor: dict[str, Any], clave: str, *, aciertos: int, fallos: int) -> None:
    bucket = contenedor.setdefault(
        clave,
        {"intentos": 0, "aciertos": 0, "fallos": 0},
    )
    bucket["intentos"] += aciertos + fallos
    bucket["aciertos"] += aciertos
    bucket["fallos"] += fallos


def _inc_modo(
    contenedor: dict[str, Any],
    modo: str,
    *,
    preguntas: int,
    aciertos: int,
    segundos: int = 0,
) -> None:
    bucket = contenedor.setdefault(
        modo,
        {"partidas": 0, "preguntas": 0, "aciertos": 0, "segundos_jugados": 0},
    )
    bucket["partidas"] += 1
    bucket["preguntas"] += preguntas
    bucket["aciertos"] += aciertos
    if segundos > 0:
        bucket["segundos_jugados"] = int(bucket.get("segundos_jugados", 0)) + segundos


def _actualizar_records(
    records: dict[str, Any],
    *,
    modo: str,
    estado: EstadoPartida,
    meta: dict[str, Any],
    pct_sesion: float,
) -> None:
    if pct_sesion > float(records.get("mejor_porcentaje_sesion", 0)):
        records["mejor_porcentaje_sesion"] = round(pct_sesion, 1)

    if modo == "resistencia":
        racha = int(meta.get("racha") or estado.aciertos)
        records["resistencia_racha"] = max(int(records.get("resistencia_racha", 0)), racha)
        records["resistencia_puntos"] = max(
            int(records.get("resistencia_puntos", 0)),
            int(estado.puntos_arcade),
        )
        records["resistencia_preguntas"] = max(
            int(records.get("resistencia_preguntas", 0)),
            int(estado.respondidas),
        )

    if modo == "escape":
        salas = int(meta.get("salas_superadas") or 0)
        records["escape_salas"] = max(int(records.get("escape_salas", 0)), salas)
        records["escape_puntos_arcade"] = max(
            int(records.get("escape_puntos_arcade", 0)),
            int(estado.puntos_arcade),
        )


def registrar_cierre_partida(
    estado: EstadoPartida,
    cierre: CierreInformePartida,
) -> None:
    """Agrega una sesión cerrada al histórico local (independiente del informe .txt)."""
    if not cierre.registros:
        return

    datos = _cargar_raw()
    totales = datos["totales"]
    modo = _modo_partida(cierre)
    meta = dict(cierre.meta or {})

    aciertos_sesion = sum(1 for r in cierre.registros if r.acierto)
    preguntas_sesion = len(cierre.registros)
    fallos_sesion = preguntas_sesion - aciertos_sesion
    pct = (100.0 * aciertos_sesion / preguntas_sesion) if preguntas_sesion else 0.0
    duracion_seg = estado.duracion_partida_seg()

    totales["partidas"] = int(totales.get("partidas", 0)) + 1
    totales["preguntas"] = int(totales.get("preguntas", 0)) + preguntas_sesion
    totales["aciertos"] = int(totales.get("aciertos", 0)) + aciertos_sesion
    totales["fallos"] = int(totales.get("fallos", 0)) + fallos_sesion
    if duracion_seg > 0:
        totales["segundos_jugados"] = int(totales.get("segundos_jugados", 0)) + duracion_seg

    _inc_modo(
        datos["por_modo"],
        modo,
        preguntas=preguntas_sesion,
        aciertos=aciertos_sesion,
        segundos=duracion_seg,
    )

    por_materia: dict[str, dict[str, int]] = {}
    por_tipo: dict[str, dict[str, int]] = {}
    for registro in cierre.registros:
        _agregar_registro_agregados(registro, por_materia, por_tipo)

    for materia, bucket in por_materia.items():
        _inc_bucket(
            datos["por_materia"],
            materia,
            aciertos=bucket["aciertos"],
            fallos=bucket["fallos"],
        )
    for tipo, bucket in por_tipo.items():
        _inc_bucket(
            datos["por_tipo"],
            tipo,
            aciertos=bucket["aciertos"],
            fallos=bucket["fallos"],
        )

    _actualizar_records(
        datos["records"],
        modo=modo,
        estado=estado,
        meta=meta,
        pct_sesion=pct,
    )

    sesion = {
        "fecha_iso": _ahora_iso(),
        "modo": modo,
        "preguntas": preguntas_sesion,
        "aciertos": aciertos_sesion,
        "pct": round(pct, 1),
        "abandonado": bool(cierre.abandonado),
        "puntos_arcade": int(estado.puntos_arcade),
        "duracion_seg": duracion_seg,
    }
    if modo == "resistencia" and meta.get("racha") is not None:
        sesion["racha"] = int(meta["racha"])
    if modo == "escape" and meta.get("salas_superadas") is not None:
        sesion["salas_superadas"] = int(meta["salas_superadas"])

    sesiones: list[dict[str, Any]] = list(datos.get("sesiones") or [])
    sesiones.append(sesion)
    datos["sesiones"] = sesiones[-_MAX_SESIONES:]

    dias = list(datos.get("dias_activos") or [])
    hoy = _hoy_local()
    if hoy not in dias:
        dias.append(hoy)
    datos["dias_activos"] = dias[-400:]

    _guardar_raw(datos)


def _agregar_registro_agregados(
    registro: RegistroRespuesta,
    por_materia: dict[str, dict[str, int]],
    por_tipo: dict[str, dict[str, int]],
) -> None:
    materia = (registro.pregunta.materia or "—").strip() or "—"
    tipo = (registro.pregunta.tipo or "—").strip() or "—"
    for clave, contenedor in ((materia, por_materia), (tipo, por_tipo)):
        bucket = contenedor.setdefault(clave, {"aciertos": 0, "fallos": 0})
        if registro.acierto:
            bucket["aciertos"] += 1
        else:
            bucket["fallos"] += 1


def _pct(aciertos: int, intentos: int) -> float:
    if intentos <= 0:
        return 0.0
    return 100.0 * aciertos / intentos


def _racha_dias(dias: list[str]) -> int:
    if not dias:
        return 0
    ordenados = sorted(set(dias))
    mejor = 1
    actual = 1
    for i in range(1, len(ordenados)):
        prev = datetime.fromisoformat(ordenados[i - 1]).date()
        cur = datetime.fromisoformat(ordenados[i]).date()
        if (cur - prev).days == 1:
            actual += 1
        else:
            actual = 1
        mejor = max(mejor, actual)
    return mejor


def _semana_iso(fecha_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
        y, w, _ = dt.isocalendar()
        return f"{y}-W{w:02d}"
    except ValueError:
        return ""


def _stats_semana(sesiones: list[dict[str, Any]], semana: str) -> tuple[int, int]:
    preguntas = 0
    aciertos = 0
    for s in sesiones:
        if _semana_iso(str(s.get("fecha_iso", ""))) != semana:
            continue
        preguntas += int(s.get("preguntas", 0))
        aciertos += int(s.get("aciertos", 0))
    return preguntas, aciertos


_MODOS_ORDEN_COMPLETO: tuple[str, ...] = ("libre", "historia", "resistencia", "escape")
_MODOS_ORDEN_MINIMO: tuple[str, ...] = ("libre", "historia", "resistencia")
_TIPOS_ORDEN: tuple[str, ...] = ("Teoria", "Calculo")
_PLACEHOLDER_MATERIAS = "  - (sin datos; min. 3 preguntas por materia)"


def _lineas_materias(
    por_materia: dict[str, Any],
    *,
    peores: bool,
    limite: int = 5,
) -> list[str]:
    filas: list[tuple[str, float, int]] = []
    for materia, bucket in por_materia.items():
        intentos = int(bucket.get("intentos", 0))
        if intentos < _MIN_INTENTOS_MATERIA:
            continue
        aciertos = int(bucket.get("aciertos", 0))
        filas.append((materia, _pct(aciertos, intentos), intentos))
    if peores:
        filas.sort(key=lambda x: (x[1], -x[2]))
    else:
        filas.sort(key=lambda x: (-x[1], -x[2]))
    lineas: list[str] = []
    for materia, pct, intentos in filas[:limite]:
        lineas.append(f"  - {materia}: {pct:.0f}% ({intentos} preguntas)")
    return lineas


def _evolucion_semanal(sesiones: list[dict[str, Any]]) -> tuple[int, int, int, int, float]:
    """Devuelve preg/aciertos semana actual, anterior y delta de %."""
    if not sesiones:
        return 0, 0, 0, 0, 0.0
    semana_actual = _semana_iso(str(sesiones[-1].get("fecha_iso", "")))
    semanas_vistas = sorted(
        {_semana_iso(str(s.get("fecha_iso", ""))) for s in sesiones if s.get("fecha_iso")}
    )
    semana_prev = ""
    if len(semanas_vistas) >= 2:
        if semanas_vistas[-1] == semana_actual:
            semana_prev = semanas_vistas[-2]
        else:
            semana_prev = semanas_vistas[-1]
    p_act, a_act = _stats_semana(sesiones, semana_actual) if semana_actual else (0, 0)
    p_prev, a_prev = _stats_semana(sesiones, semana_prev) if semana_prev else (0, 0)
    delta = _pct(a_act, p_act) - _pct(a_prev, p_prev)
    return p_act, a_act, p_prev, a_prev, delta


def _modos_estadisticas(perfil) -> tuple[str, ...]:
    if perfil is not None and perfil.modo_minimo:
        return _MODOS_ORDEN_MINIMO
    return _MODOS_ORDEN_COMPLETO


def _mostrar_analisis_contenido(perfil) -> bool:
    if perfil is not None and perfil.modo_minimo:
        return False
    if perfil is not None and not perfil.tiene_tipos_pregunta:
        return False
    return True


def _mostrar_records_escape(perfil) -> bool:
    return perfil is None or not perfil.modo_minimo


def formatear_panel_estadisticas(perfil=None) -> str:
    """Texto multilínea para la pantalla «Mis estadísticas»."""
    datos = _cargar_raw()
    totales = datos.get("totales") or {}
    records = datos.get("records") or {}
    sesiones: list[dict[str, Any]] = list(datos.get("sesiones") or [])
    dias: list[str] = list(datos.get("dias_activos") or [])
    por_modo: dict[str, Any] = dict(datos.get("por_modo") or {})
    por_materia: dict[str, Any] = dict(datos.get("por_materia") or {})
    por_tipo: dict[str, Any] = dict(datos.get("por_tipo") or {})

    partidas = int(totales.get("partidas", 0))
    preguntas = int(totales.get("preguntas", 0))
    aciertos = int(totales.get("aciertos", 0))
    segundos_jugados = int(totales.get("segundos_jugados", 0))
    pct_global = _pct(aciertos, preguntas)

    p_act, a_act, p_prev, a_prev, delta_pp = _evolucion_semanal(sesiones)
    signo_delta = "+" if delta_pp >= 0 else ""

    lineas: list[str] = [
        "Datos locales (solo en este PC). Se actualizan al cerrar cada partida.",
        "",
        "--- RESUMEN GLOBAL ---",
        f"  Partidas jugadas: {partidas}",
        f"  Preguntas respondidas: {preguntas}",
        f"  Aciertos: {aciertos}/{preguntas} ({pct_global:.1f}%)",
        f"  Tiempo en partida: {formatear_duracion_seg(segundos_jugados)}",
        f"  Dias con actividad: {len(dias)} (racha maxima: {_racha_dias(dias)} dias)",
        "",
        "--- EVOLUCION SEMANAL ---",
        f"  Esta semana: {_pct(a_act, p_act):.0f}% ({p_act} preguntas, {a_act}/{p_act} aciertos)",
        f"  Semana anterior: {_pct(a_prev, p_prev):.0f}% ({p_prev} preguntas, {a_prev}/{p_prev} aciertos)",
        f"  Cambio: {signo_delta}{delta_pp:.1f} puntos porcentuales",
        "",
        "--- POR MODO ---",
    ]

    for modo in _modos_estadisticas(perfil):
        bucket = por_modo.get(modo, {})
        n = int(bucket.get("partidas", 0))
        p = int(bucket.get("preguntas", 0))
        a = int(bucket.get("aciertos", 0))
        seg = int(bucket.get("segundos_jugados", 0))
        tiempo_modo = f", {formatear_duracion_seg(seg)}" if seg else ""
        lineas.append(
            f"  - {_etiqueta_modo(modo, perfil)}: {n} partidas, {a}/{p} aciertos "
            f"({_pct(a, p):.0f}%){tiempo_modo}"
        )

    lineas.append("")
    lineas.append("--- RECORDS ---")
    lineas.append(
        f"  Resistencia - max preguntas: {int(records.get('resistencia_preguntas', 0))} | "
        f"max puntos: {int(records.get('resistencia_puntos', 0))}"
    )
    if _mostrar_records_escape(perfil):
        lineas.append(
            f"  Escape - max salas: {int(records.get('escape_salas', 0))} | "
            f"max puntos: {int(records.get('escape_puntos_arcade', 0))}"
        )
    lineas.append(
        f"  Mejor sesion (% acierto): {float(records.get('mejor_porcentaje_sesion', 0)):.1f}%"
    )

    if _mostrar_analisis_contenido(perfil):
        lineas.extend(
            [
                "",
                "--- ANALISIS POR CONTENIDO ---",
                "  Teoria vs calculo:",
            ]
        )
        for tipo in _TIPOS_ORDEN:
            bucket = por_tipo.get(tipo, {})
            intentos = int(bucket.get("intentos", 0))
            aciertos_tipo = int(bucket.get("aciertos", 0))
            etiqueta = "Teoria" if tipo == "Teoria" else "Calculo"
            lineas.append(
                f"    - {etiqueta}: {aciertos_tipo}/{intentos} aciertos "
                f"({_pct(aciertos_tipo, intentos):.0f}%)"
            )

        lineas.append("  Materias a reforzar:")
        peores = _lineas_materias(por_materia, peores=True)
        lineas.extend(peores if peores else [_PLACEHOLDER_MATERIAS])

        lineas.append("  Materias fuertes:")
        mejores = _lineas_materias(por_materia, peores=False)
        lineas.extend(mejores if mejores else [_PLACEHOLDER_MATERIAS])

    return "\n".join(lineas)
