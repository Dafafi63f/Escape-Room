#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generación y guardado del informe de examen (estadísticas + corrección)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from Comun.modelos import Pregunta
from .motor_partida import EstadoPartida
from Comun.reglas_partida import (
    SistemaPuntuacion,
    formatear_resultado_puntuacion,
    nota_sobre_diez,
    porcentaje_aciertos,
)
from Comun.rutas import resolver_dir_informes, ruta_informe_para_usuario


@dataclass
class RegistroRespuesta:
    indice: int
    pregunta: Pregunta
    respuesta: str
    acierto: bool
    tiempo_agotado: bool = False


def generar_id_sesion() -> str:
    """Identificador único por intento (mismo examen repetido = otro id y otro .txt)."""
    ahora = datetime.now()
    return f"MATCAD-{ahora:%Y%m%d}-{ahora:%H%M%S}-{secrets.token_hex(2)}"


def _slug_fragmento(texto: str, max_len: int = 20) -> str:
    limpio = "".join(c if c.isalnum() else "_" for c in (texto or "").strip())
    while "__" in limpio:
        limpio = limpio.replace("__", "_")
    limpio = limpio.strip("_") or "sin"
    return limpio[:max_len]


def _tokens_prefijo(prefijo_slug: str) -> set[str]:
    return {t for t in prefijo_slug.lower().split("_") if t}


_ETIQUETA_TIPO_ARCHIVO: dict[str, str] = {
    "libre_infinito": "infinito",
    "libre_finito": "finito",
    "resistencia": "resistencia",
}


def _fragmento_modo_archivo(modo: str, *, tokens_prefijo: set[str]) -> str | None:
    slug = _slug_fragmento(modo, 12)
    if not slug or slug == "sin":
        return None
    if slug.lower() in tokens_prefijo:
        return None
    return slug


def _fragmento_tipo_archivo(tipo: str, *, tokens_prefijo: set[str]) -> str | None:
    clave = (tipo or "").strip().lower()
    if not clave:
        return None
    if clave in _ETIQUETA_TIPO_ARCHIVO:
        return _ETIQUETA_TIPO_ARCHIVO[clave]
    slug = _slug_fragmento(clave, 14)
    if not slug or slug == "sin":
        return None
    partes_slug = {p for p in slug.lower().split("_") if p}
    if partes_slug and partes_slug <= tokens_prefijo:
        return None
    return slug


def construir_nombre_archivo_informe(
    *,
    prefijo: str,
    nombre_jugador: str,
    id_sesion: str,
    meta: dict | None = None,
) -> str:
    """
    Nombre de archivo legible + único.
    Incluye prefijo, subtipo (si aporta), jugador, fecha-hora y sufijo del id.
    """
    meta = meta or {}
    prefijo_slug = _slug_fragmento(prefijo, 20)
    tokens_prefijo = _tokens_prefijo(prefijo_slug)
    partes = [prefijo_slug]

    modo = _fragmento_modo_archivo(str(meta.get("modo", "")), tokens_prefijo=tokens_prefijo)
    if modo:
        partes.append(modo)
        tokens_prefijo |= _tokens_prefijo(modo)

    if meta.get("perfil"):
        partes.append(_slug_fragmento(str(meta["perfil"]), 14))
    if meta.get("preset"):
        partes.append(_slug_fragmento(str(meta["preset"]), 18))

    tipo = _fragmento_tipo_archivo(
        str(meta.get("tipo_actividad", "")),
        tokens_prefijo=tokens_prefijo,
    )
    if tipo:
        partes.append(tipo)

    partes.append(_slug_fragmento(nombre_jugador, 16))
    partes.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
    partes.append(id_sesion.split("-")[-1])
    return "_".join(partes) + ".txt"


def _linea_opcion(letra: str, opciones: dict[str, str]) -> str:
    texto = opciones.get(letra, "").strip()
    return f"{letra}) {texto}" if texto else f"{letra}) (sin texto)"


def _feedback_pregunta(reg: RegistroRespuesta) -> str:
    p = reg.pregunta
    correcta = p.correcta if p.correcta in {"A", "B", "C", "D"} else ""
    if reg.tiempo_agotado:
        return "Tiempo agotado: se contabiliza como fallo."
    if not correcta:
        return "No hay respuesta correcta registrada en el banco para esta pregunta."
    if reg.acierto:
        return f"Respuesta correcta. { _linea_opcion(correcta, p.opciones) }"
    return (
        f"Respuesta incorrecta. La solución es { _linea_opcion(correcta, p.opciones) }. "
        f"Marcaste { _linea_opcion(reg.respuesta, p.opciones) }."
    )


def mostrar_correccion_en_consola(registros: list[RegistroRespuesta]) -> None:
    """Corrección pregunta a pregunta tras un examen cerrado (sin pistas durante)."""
    print("\n" + "=" * 60)
    print("CORRECCIÓN DEL EXAMEN")
    print("=" * 60)
    for reg in registros:
        p = reg.pregunta
        if reg.tiempo_agotado:
            marca = "FALLO (tiempo)"
        elif reg.acierto:
            marca = "ACIERTO"
        else:
            marca = "FALLO"
        print(f"\n[{reg.indice}] {marca} — {p.materia}")
        print(f"  Pregunta: {p.texto[:120]}{'…' if len(p.texto) > 120 else ''}")
        print(f"  Tu respuesta: {_linea_opcion(reg.respuesta, p.opciones)}")
        if p.correcta in {"A", "B", "C", "D"}:
            print(f"  Solución: {_linea_opcion(p.correcta, p.opciones)}")
        print(f"  {_feedback_pregunta(reg)}")


def _lineas_cabecera_informe(
    estado: EstadoPartida,
    meta: dict,
    *,
    generado: str,
) -> list[str]:
    """Cabecera breve: sin repetir reglas, modo ni nombre de archivo."""
    ctx = meta.get("etiqueta_sesion") or meta.get("modo") or "Partida"
    lineas = [
        "INFORME — CUESTIONARIO MATCAD",
        "=" * 50,
        f"ID: {meta.get('id_sesion', '?')}  ·  {generado}  ·  {estado.nombre}",
        f"{ctx}",
        f"Reglas: {estado.reglas.describe()}",
    ]
    if meta.get("perfil"):
        lineas.append(f"Perfil: {meta['perfil']}")
    if meta.get("materias"):
        lineas.append(f"Materias: {meta['materias']}")
    if meta.get("banco"):
        lineas.append(f"Banco: {meta['banco']}")
    if meta.get("filtro"):
        lineas.append(f"Filtro: {meta['filtro']}")
    if meta.get("abandonado"):
        lineas.append("Estado: abandonada antes de completar el bloque")
    return lineas


def _lineas_resumen(
    estado: EstadoPartida,
    *,
    total: int,
    total_previsto: int,
    incompleto: bool,
) -> list[str]:
    resultado = formatear_resultado_puntuacion(
        estado.reglas,
        aciertos=estado.aciertos,
        total=total,
        puntos_arcade=estado.puntos_arcade,
    )
    prev = f"{total}/{total_previsto}"
    if incompleto:
        prev += " (incompleto)"
    return [
        "",
        "RESUMEN",
        "-" * 40,
        resultado,
        f"Preguntas: {prev} · Aciertos: {estado.aciertos}/{total}",
    ]


def _estadisticas_por_materia(registros: list[RegistroRespuesta]) -> list[str]:
    totales: dict[str, list[bool]] = {}
    for reg in registros:
        totales.setdefault(reg.pregunta.materia, []).append(reg.acierto)
    if not totales:
        return []
    lineas = ["", "ESTADÍSTICAS POR MATERIA", "-" * 40]
    for materia in sorted(totales):
        vals = totales[materia]
        ok = sum(1 for v in vals if v)
        n = len(vals)
        pct = porcentaje_aciertos(ok, n)
        lineas.append(f"  · {materia}: {ok}/{n} aciertos ({pct}%)")
    return lineas


def formatear_informe_examen(
    estado: EstadoPartida,
    registros: list[RegistroRespuesta],
    *,
    titulo: str,
    meta: dict | None = None,
    total_previsto: int,
    fallos_por_materia: dict[str, int] | None = None,
    stats_historicas: dict | None = None,
) -> str:
    meta = meta or {}
    total = estado.respondidas
    incompleto = total_previsto > total
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

    lineas = _lineas_cabecera_informe(estado, meta, generado=ahora)
    lineas.extend(_lineas_resumen(estado, total=total, total_previsto=total_previsto, incompleto=incompleto))
    lineas.extend(_estadisticas_por_materia(registros))
    lineas.extend(["", "CORRECCIÓN DETALLADA (pregunta a pregunta)", "=" * 60])

    for reg in registros:
        p = reg.pregunta
        estado_txt = "ACIERTO" if reg.acierto else "FALLO"
        if reg.tiempo_agotado:
            estado_txt = "FALLO (tiempo)"
        lineas.extend(
            [
                "",
                f"[{reg.indice}] {estado_txt}",
                f"Materia: {p.materia} | {p.tipo} / {p.dificultad}",
                f"Temática: {p.tematica or '-'} | Curso {p.curso or '-'} · Sem. {p.semestre or '-'}",
                "",
                p.texto,
                "",
                f"  {_linea_opcion('A', p.opciones)}",
                f"  {_linea_opcion('B', p.opciones)}",
                f"  {_linea_opcion('C', p.opciones)}",
                f"  {_linea_opcion('D', p.opciones)}",
                "",
                f"Tu respuesta: {_linea_opcion(reg.respuesta, p.opciones)}",
            ]
        )
        if p.correcta in {"A", "B", "C", "D"}:
            lineas.append(f"Solución: {_linea_opcion(p.correcta, p.opciones)}")
        lineas.append(f"Feedback: {_feedback_pregunta(reg)}")

    if fallos_por_materia:
        lineas.extend(["", "MATERIAS A REFORZAR (este intento)", "-" * 40])
        for materia, n in sorted(fallos_por_materia.items(), key=lambda x: -x[1]):
            extra = ""
            if stats_historicas and materia in stats_historicas:
                st = stats_historicas[materia]
                extra = f" — histórico: media {st.media:.2f}"
            lineas.append(f"  · {materia}: {n} error(es){extra}")

    lineas.append("")
    lineas.append("Fin del informe.")
    return "\n".join(lineas) + "\n"


def publicar_informe_partida(
    estado: EstadoPartida,
    registros: list[RegistroRespuesta],
    *,
    titulo: str,
    total_previsto: int,
    nombre_jugador: str,
    meta: dict | None = None,
    stats_historicas: dict | None = None,
    prefijo: str = "examen",
    mostrar_en_consola: bool = True,
) -> Path | None:
    """Guarda el .txt y, si procede, muestra corrección en consola."""
    if not registros:
        return None

    if mostrar_en_consola and estado.reglas.correccion_al_final:
        mostrar_correccion_en_consola(registros)

    id_sesion = generar_id_sesion()
    meta_completa = {
        **(meta or {}),
        "id_sesion": id_sesion,
        "n_preguntas": meta.get("n_preguntas", total_previsto) if meta else total_previsto,
    }
    if not meta_completa.get("etiqueta_sesion"):
        meta_completa["etiqueta_sesion"] = titulo
    nombre_archivo = construir_nombre_archivo_informe(
        prefijo=prefijo,
        nombre_jugador=nombre_jugador,
        id_sesion=id_sesion,
        meta=meta_completa,
    )
    meta_completa["nombre_archivo"] = nombre_archivo

    texto = formatear_informe_examen(
        estado,
        registros,
        titulo=titulo,
        meta=meta_completa,
        total_previsto=total_previsto,
        fallos_por_materia=estado.fallos_por_materia or None,
        stats_historicas=stats_historicas,
    )
    try:
        ruta = guardar_informe_examen(texto, nombre_archivo=nombre_archivo)
    except OSError:
        if mostrar_en_consola:
            print("\nNo se pudo guardar el informe en disco (permisos o ruta).")
        return None

    if mostrar_en_consola:
        _imprimir_aviso_informe_guardado(ruta)
    return ruta


def _imprimir_aviso_informe_guardado(ruta: Path) -> None:
    """Mensaje en consola (evita rutas absolutas con Unicode en Windows cp1252)."""
    import sys

    rel = ruta_informe_para_usuario(ruta)
    lineas = (
        "",
        "=== INFORME DE PARTIDA / EXAMEN ===",
        f"Archivo: {rel}",
        f"(nombre unico por intento; ver ID de sesion dentro del .txt)",
        "Contenido: estadisticas, nota o puntos, correccion pregunta a pregunta.",
        "(Historial personal en Data/Juego/ — un .txt por actividad cerrada)",
    )
    for linea in lineas:
        try:
            print(linea)
        except UnicodeEncodeError:
            sys.stdout.buffer.write((linea + "\n").encode("utf-8", errors="replace"))


def guardar_informe_examen(texto: str, *, nombre_archivo: str) -> Path:
    directorio = resolver_dir_informes()
    nombre = Path(nombre_archivo).name
    path = directorio / nombre
    path.write_text(texto, encoding="utf-8")
    return path
