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
    "cargar_estadisticas_locales",
    "formatear_panel_estadisticas",
    "formatear_tarjeta_sigue_por_aqui",
    "registrar_cierre_partida",
    "resolver_path_estadisticas_jugador",
    "vaciar_estadisticas_jugador",
]

_MAX_SESIONES = 120
_MIN_INTENTOS_MATERIA = 3
_MIN_INTENTOS_CONCEPTO = 3


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
    salas_superadas: int = 0,
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
    if salas_superadas > 0:
        bucket["salas_superadas"] = int(bucket.get("salas_superadas", 0)) + salas_superadas


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
    """Agrega una sesión cerrada al historial local (independiente del informe .txt)."""
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

    salas_sesion = (
        int(meta["salas_superadas"])
        if modo == "escape" and meta.get("salas_superadas") is not None
        else 0
    )
    if salas_sesion > 0:
        totales["salas_escape"] = int(totales.get("salas_escape", 0)) + salas_sesion

    _inc_modo(
        datos["por_modo"],
        modo,
        preguntas=preguntas_sesion,
        aciertos=aciertos_sesion,
        segundos=duracion_seg,
        salas_superadas=salas_sesion,
    )

    por_materia: dict[str, dict[str, int]] = {}
    por_tipo: dict[str, dict[str, int]] = {}
    por_concepto: dict[str, dict[str, int]] = {}
    for registro in cierre.registros:
        _agregar_registro_agregados(registro, por_materia, por_tipo, por_concepto)

    for materia, bucket in por_materia.items():
        _inc_bucket(
            datos["por_materia"],
            materia,
            aciertos=bucket["aciertos"],
            fallos=bucket["fallos"],
        )
    for concepto, bucket in por_concepto.items():
        _inc_bucket(
            datos.setdefault("por_concepto", {}),
            concepto,
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

    if modo == "resistencia":
        visto_raw = meta.get("resistencia_variedad_vista")
        if isinstance(visto_raw, (list, tuple, set, frozenset)):
            from Comun.pity_variedad_resistencia import PityVariedadResistencia

            pity_variedad = PityVariedadResistencia.desde_dict(
                datos.get("resistencia_variedad")
            )
            pity_variedad.registrar_partida(
                {str(x) for x in visto_raw if isinstance(x, str)}
            )
            datos["resistencia_variedad"] = pity_variedad.a_dict()
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

    from Comun.metadatos_inferidos import actualizar_desde_registros

    actualizar_desde_registros(cierre.registros)

    _guardar_raw(datos)


def _agregar_registro_agregados(
    registro: RegistroRespuesta,
    por_materia: dict[str, dict[str, int]],
    por_tipo: dict[str, dict[str, int]],
    por_concepto: dict[str, dict[str, int]],
) -> None:
    from Comun.cadena_examen_dirigido import conceptos_registro

    materia = (registro.pregunta.materia or "—").strip() or "—"
    tipo = (registro.pregunta.tipo or "—").strip() or "—"
    for clave, contenedor in ((materia, por_materia), (tipo, por_tipo)):
        bucket = contenedor.setdefault(clave, {"aciertos": 0, "fallos": 0})
        if registro.acierto:
            bucket["aciertos"] += 1
        else:
            bucket["fallos"] += 1
    for concepto in conceptos_registro(registro):
        bucket = por_concepto.setdefault(concepto, {"aciertos": 0, "fallos": 0})
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
_PLACEHOLDER_CONCEPTOS = (
    "  - (sin datos; min. 3 respuestas con la misma palabra clave)"
)


def _lineas_conceptos(
    por_concepto: dict[str, Any],
    *,
    peores: bool,
    limite: int = 5,
) -> list[str]:
    from Comun.cadena_examen_dirigido import etiqueta_concepto

    filas: list[tuple[str, float, int]] = []
    for concepto, bucket in por_concepto.items():
        intentos = int(bucket.get("intentos", 0))
        if intentos < _MIN_INTENTOS_CONCEPTO:
            continue
        aciertos = int(bucket.get("aciertos", 0))
        filas.append((concepto, _pct(aciertos, intentos), intentos))
    if peores:
        filas.sort(key=lambda x: (x[1], -x[2]))
    else:
        filas.sort(key=lambda x: (-x[1], -x[2]))
    lineas: list[str] = []
    for concepto, pct, intentos in filas[:limite]:
        etiqueta = etiqueta_concepto(concepto)
        lineas.append(f"  - {etiqueta}: {pct:.0f}% ({intentos} respuestas)")
    return lineas


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


def _mostrar_analisis_conceptos(perfil) -> bool:
    """CSV mínimo u otro banco sin metadatos curriculares: análisis por palabras clave."""
    return perfil is not None and perfil.csv_minimal


def _mostrar_records_escape(perfil) -> bool:
    return perfil is None or not perfil.modo_minimo


def _total_salas_escape(
    por_modo: dict[str, Any],
    sesiones: list[dict[str, Any]],
) -> int:
    bucket = por_modo.get("escape") or {}
    if bucket.get("salas_superadas") is not None:
        return int(bucket["salas_superadas"])
    return sum(
        int(s.get("salas_superadas") or 0)
        for s in sesiones
        if s.get("modo") == "escape"
    )


def _linea_modo_estadisticas(
    modo: str,
    bucket: dict[str, Any],
    *,
    perfil,
    sesiones: list[dict[str, Any]],
) -> str:
    n = int(bucket.get("partidas", 0))
    p = int(bucket.get("preguntas", 0))
    a = int(bucket.get("aciertos", 0))
    seg = int(bucket.get("segundos_jugados", 0))
    tiempo_modo = f", {formatear_duracion_seg(seg)}" if seg else ""
    etiqueta = _etiqueta_modo(modo, perfil)
    if modo == "escape":
        salas = _total_salas_escape({modo: bucket}, sesiones)
        return (
            f"  - {etiqueta}: {n} partidas, {salas} salas superadas, "
            f"{a}/{p} aciertos ({_pct(a, p):.0f}%){tiempo_modo}"
        )
    return (
        f"  - {etiqueta}: {n} partidas, {a}/{p} aciertos "
        f"({_pct(a, p):.0f}%){tiempo_modo}"
    )


def _dias_sin_actividad(dias: list[str]) -> int:
    if not dias:
        return 0
    hoy = datetime.now().date()
    ultimo = datetime.fromisoformat(max(dias)).date()
    return max(0, (hoy - ultimo).days)


def _concepto_mas_debil(por_concepto: dict[str, Any]) -> tuple[str, float, int] | None:
    from Comun.cadena_examen_dirigido import etiqueta_concepto

    peor: tuple[str, float, int] | None = None
    for concepto, bucket in por_concepto.items():
        intentos = int(bucket.get("intentos", 0))
        if intentos < _MIN_INTENTOS_CONCEPTO:
            continue
        aciertos = int(bucket.get("aciertos", 0))
        pct = _pct(aciertos, intentos)
        if peor is None or pct < peor[1] or (pct == peor[1] and intentos > peor[2]):
            peor = (etiqueta_concepto(concepto), pct, intentos)
    return peor


def _materia_mas_debil(por_materia: dict[str, Any]) -> tuple[str, float, int] | None:
    peor: tuple[str, float, int] | None = None
    for materia, bucket in por_materia.items():
        intentos = int(bucket.get("intentos", 0))
        if intentos < _MIN_INTENTOS_MATERIA:
            continue
        aciertos = int(bucket.get("aciertos", 0))
        pct = _pct(aciertos, intentos)
        if peor is None or pct < peor[1] or (pct == peor[1] and intentos > peor[2]):
            peor = (materia, pct, intentos)
    return peor


def _modo_menos_jugado(por_modo: dict[str, Any], modos: tuple[str, ...]) -> str | None:
    candidatos: list[tuple[int, str]] = []
    for modo in modos:
        partidas = int((por_modo.get(modo) or {}).get("partidas", 0))
        candidatos.append((partidas, modo))
    if not candidatos or all(n == 0 for n, _ in candidatos):
        return None
    candidatos.sort()
    return candidatos[0][1]


def formatear_tarjeta_sigue_por_aqui(perfil=None) -> list[str]:
    """Líneas de la tarjeta «Sigue por aquí» para el panel de estadísticas."""
    datos = _cargar_raw()
    totales = datos.get("totales") or {}
    sesiones: list[dict[str, Any]] = list(datos.get("sesiones") or [])
    dias: list[str] = list(datos.get("dias_activos") or [])
    por_modo: dict[str, Any] = dict(datos.get("por_modo") or {})
    por_materia: dict[str, Any] = dict(datos.get("por_materia") or {})
    por_concepto: dict[str, Any] = dict(datos.get("por_concepto") or {})

    partidas = int(totales.get("partidas", 0))
    lineas: list[str] = ["--- SIGUE POR AQUI ---"]

    if partidas == 0:
        lineas.append("  Juega tu primera partida para ver recomendaciones.")
        return lineas

    dias_sin = _dias_sin_actividad(dias)
    if dias_sin >= 2:
        lineas.append(
            f"  Llevas {dias_sin} dias sin practicar; un examen corto hoy ayuda a retomar."
        )

    debil_concepto = _concepto_mas_debil(por_concepto) if _mostrar_analisis_conceptos(perfil) else None
    debil_materia = _materia_mas_debil(por_materia) if not debil_concepto else None
    if debil_concepto is not None:
        concepto, pct, intentos = debil_concepto
        lineas.append(
            f"  Refuerza «{concepto}»: {pct:.0f}% de acierto ({intentos} respuestas)."
        )
    elif debil_materia is not None:
        materia, pct, intentos = debil_materia
        lineas.append(
            f"  Refuerza {materia}: {pct:.0f}% de acierto ({intentos} preguntas)."
        )

    p_act, a_act, p_prev, a_prev, delta_pp = _evolucion_semanal(sesiones)
    if p_act >= 5 and p_prev >= 5:
        if delta_pp <= -5:
            lineas.append(
                f"  Esta semana bajaste {abs(delta_pp):.0f} pp; conviene repasar."
            )
        elif delta_pp >= 5:
            lineas.append("  Vas mejor que la semana pasada; manten el ritmo.")

    if debil_concepto is None and debil_materia is None and _mostrar_analisis_contenido(perfil):
        lineas.append(
            "  Responde al menos 3 preguntas por materia para ver puntos debiles."
        )
    if debil_concepto is None and _mostrar_analisis_conceptos(perfil):
        lineas.append(
            "  Responde mas preguntas para ver que palabras clave conviene repasar."
        )

    modo_sugerido = _modo_menos_jugado(por_modo, _modos_estadisticas(perfil))
    if modo_sugerido is not None and int((por_modo.get(modo_sugerido) or {}).get("partidas", 0)) == 0:
        lineas.append(
            f"  Prueba el modo {_etiqueta_modo(modo_sugerido, perfil)}; aun no lo has usado."
        )

    if len(lineas) == 1:
        lineas.append("  Sigue practicando; aqui apareceran consejos personalizados.")
    return lineas


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
    por_concepto: dict[str, Any] = dict(datos.get("por_concepto") or {})

    partidas = int(totales.get("partidas", 0))
    preguntas = int(totales.get("preguntas", 0))
    aciertos = int(totales.get("aciertos", 0))
    segundos_jugados = int(totales.get("segundos_jugados", 0))
    salas_escape = _total_salas_escape(por_modo, sesiones)
    if salas_escape <= 0:
        salas_escape = int(totales.get("salas_escape", 0))
    pct_global = _pct(aciertos, preguntas)

    p_act, a_act, p_prev, a_prev, delta_pp = _evolucion_semanal(sesiones)
    signo_delta = "+" if delta_pp >= 0 else ""

    resumen_global = [
        f"  Partidas jugadas: {partidas}",
    ]
    if salas_escape > 0:
        resumen_global.append(f"  Salas superadas (escape): {salas_escape}")
    resumen_global.extend(
        [
            f"  Preguntas respondidas: {preguntas}",
            f"  Aciertos: {aciertos}/{preguntas} ({pct_global:.1f}%)",
            f"  Tiempo en partida: {formatear_duracion_seg(segundos_jugados)}",
            f"  Dias con actividad: {len(dias)} (racha maxima: {_racha_dias(dias)} dias)",
        ]
    )

    lineas: list[str] = [
        "Datos locales (solo en este PC). Se actualizan al cerrar cada partida.",
        "",
        *formatear_tarjeta_sigue_por_aqui(perfil),
        "",
        "--- RESUMEN GLOBAL ---",
        *resumen_global,
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
        lineas.append(
            _linea_modo_estadisticas(
                modo,
                bucket,
                perfil=perfil,
                sesiones=sesiones,
            )
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

    if _mostrar_analisis_conceptos(perfil):
        lineas.extend(
            [
                "",
                "--- ANALISIS POR CONCEPTOS ---",
                "  Palabras clave inferidas del enunciado (segun tu banco de preguntas):",
                "  Conceptos a reforzar:",
            ]
        )
        peores = _lineas_conceptos(por_concepto, peores=True)
        lineas.extend(peores if peores else [_PLACEHOLDER_CONCEPTOS])

        lineas.append("  Conceptos fuertes:")
        mejores = _lineas_conceptos(por_concepto, peores=False)
        lineas.extend(mejores if mejores else [_PLACEHOLDER_CONCEPTOS])

    return "\n".join(lineas)


def _bucket_a_estadistica_materia(clave: str, bucket: dict[str, Any]):
    from Comun.generador_examen_historia import EstadisticaMateria

    intentos = int(
        bucket.get("intentos")
        or int(bucket.get("aciertos", 0)) + int(bucket.get("fallos", 0))
    )
    if intentos <= 0:
        return None
    aciertos = int(bucket.get("aciertos", 0))
    tasa_acierto = aciertos / intentos
    indice = min(1.0, max(0.0, 1.0 - tasa_acierto))
    return EstadisticaMateria(
        materia=clave,
        n_registros=intentos,
        media=round(tasa_acierto * 10.0, 2),
        tasa_suspens=round(1.0 - tasa_acierto, 3),
        indice_dificultad=round(indice, 3),
    )


def cargar_estadisticas_locales(
    perfil=None,
    materias_meta: dict | None = None,
) -> dict:
    """Convierte ``estadisticas_jugador.json`` en stats del generador de exámenes."""
    datos = _cargar_raw()
    usar_conceptos = bool(perfil and perfil.csv_minimal)
    if not usar_conceptos:
        por_materia = datos.get("por_materia") or {}
        claves_utiles = [k for k in por_materia if k and k != "—"]
        if not claves_utiles and datos.get("por_concepto"):
            usar_conceptos = True

    fuente = (
        datos.get("por_concepto") if usar_conceptos else datos.get("por_materia")
    ) or {}
    stats: dict = {}
    for clave, bucket in fuente.items():
        if not clave or clave == "—":
            continue
        if materias_meta is not None and not usar_conceptos and clave not in materias_meta:
            continue
        est = _bucket_a_estadistica_materia(clave, bucket)
        if est is not None:
            stats[clave] = est
    return stats
