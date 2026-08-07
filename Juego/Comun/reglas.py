#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reglas de partida, dificultad, políticas y modo libre."""

from __future__ import annotations

# --- reglas_partida ---


from dataclasses import dataclass
from enum import Enum

class SistemaPuntuacion(str, Enum):
    """Cómo se evalúa el resultado."""

    ARCADE = "arcade"
    NOTA = "nota"
    PORCENTAJE = "porcentaje"
    NINGUNO = "ninguno"


@dataclass(frozen=True)
class ReglasPartida:
    """
    Configuración de una sesión de juego.

    vidas=None  → sin expulsión; se responden todas las preguntas previstas.
    tiempo_*    → None = sin límite; si ambos están definidos, aplica el más restrictivo.
    """

    vidas: int | None = None
    tiempo_por_pregunta_seg: int | None = None
    tiempo_total_seg: int | None = None
    sistema_puntuacion: SistemaPuntuacion = SistemaPuntuacion.ARCADE
    mostrar_solucion_tras_fallo: bool = True
    mostrar_aciertos_en_curso: bool = False
    correccion_al_final: bool = False
    dificultad_progresiva: bool = False

    def tiene_vidas(self) -> bool:
        return self.vidas is not None and self.vidas > 0

    def vidas_iniciales(self) -> int:
        """Vidas al empezar la partida (restantes = máximo en el arranque)."""
        if self.vidas is not None and self.vidas > 0:
            return self.vidas
        return 3

    def tiene_tiempo(self) -> bool:
        return (self.tiempo_por_pregunta_seg or 0) > 0 or (self.tiempo_total_seg or 0) > 0

    def describe(self) -> str:
        partes: list[str] = []
        if self.tiene_vidas():
            partes.append(f"{self.vidas} vidas")
        else:
            partes.append("sin vidas (completa todas las preguntas)")
        if self.tiempo_por_pregunta_seg:
            partes.append(f"{self.tiempo_por_pregunta_seg}s/pregunta")
        if self.tiempo_total_seg:
            partes.append(f"{self.tiempo_total_seg}s total")
        if not self.tiene_tiempo():
            partes.append("sin límite de tiempo")
        partes.append(f"puntuación: {self.sistema_puntuacion.value}")
        if self.correccion_al_final:
            partes.append("corrección al final (sin pistas durante el examen)")
        return "  ".join(partes)


def vidas_iniciales_partida(reglas: ReglasPartida) -> int:
    """Vidas de arranque: restantes y tope inicial coinciden."""
    return reglas.vidas_iniciales()


def preset_libre_arcade() -> ReglasPartida:
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
        dificultad_progresiva=True,
    )


def preset_libre_repaso() -> ReglasPartida:
    return ReglasPartida(
        vidas=None,
        sistema_puntuacion=SistemaPuntuacion.NOTA,
        mostrar_solucion_tras_fallo=True,
    )


def preset_libre_contrarreloj() -> ReglasPartida:
    return ReglasPartida(
        vidas=None,
        tiempo_por_pregunta_seg=90,
        sistema_puntuacion=SistemaPuntuacion.PORCENTAJE,
    )


def preset_historia_examen() -> ReglasPartida:
    """Simula un examen real: sin feedback hasta el final."""
    return ReglasPartida(
        vidas=None,
        sistema_puntuacion=SistemaPuntuacion.NOTA,
        mostrar_solucion_tras_fallo=False,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=True,
    )


def preset_historia_reto() -> ReglasPartida:
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
    )


def preset_escape() -> ReglasPartida:
    """Salas encadenadas: sin cronómetro global de partida (solo tiempo por pregunta en cada puerta)."""
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
        mostrar_solucion_tras_fallo=True,
        tiempo_por_pregunta_seg=None,
        tiempo_total_seg=None,
    )


preset_historia_escape = preset_escape


def preset_resistencia() -> ReglasPartida:
    """Varias vidas; la dificultad escala con el nº de pregunta; la racha solo bonifica puntos."""
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
        mostrar_solucion_tras_fallo=True,
        dificultad_progresiva=True,
    )


def calcular_puntos_arcade(dificultad: str, acierto: bool) -> int:
    base = {"Facil": 10, "Media": 20, "Dificil": 30}.get(dificultad, 15)
    return base if acierto else -max(5, base // 2)


def sumar_puntos_arcade(saldo: int, delta: int) -> tuple[int, int]:
    """Aplica delta al saldo sin permitir negativos. Devuelve (nuevo_saldo, delta_aplicado)."""
    nuevo = max(0, saldo + delta)
    return nuevo, nuevo - saldo


def nota_sobre_diez(aciertos: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(10.0 * aciertos / total, 1)


def porcentaje_aciertos(aciertos: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * aciertos / total, 1)


def formatear_resultado_puntuacion(
    reglas: ReglasPartida,
    *,
    aciertos: int,
    total: int,
    puntos_arcade: int,
) -> str:
    if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
        return f"Puntos arcade: {puntos_arcade}"
    if reglas.sistema_puntuacion == SistemaPuntuacion.NOTA:
        return f"Nota (0-10): {nota_sobre_diez(aciertos, total)}"
    if reglas.sistema_puntuacion == SistemaPuntuacion.PORCENTAJE:
        return f"Aciertos: {porcentaje_aciertos(aciertos, total)}%"
    return f"Aciertos: {aciertos}/{total}"


# --- Límites globales de partida y examen ---

MIN_PREGUNTAS_PARTIDA = 5

# Repaso y simulacro (perfil balanceado): preguntas por materia en el generador.
PREGUNTAS_POR_MATERIA_HISTORIA = 4


def min_materias_para_minimo_preguntas(
    preguntas_por_materia: int = PREGUNTAS_POR_MATERIA_HISTORIA,
) -> int:
    """Materias mínimas para alcanzar ``MIN_PREGUNTAS_PARTIDA`` preguntas."""
    if preguntas_por_materia <= 0:
        return MIN_PREGUNTAS_PARTIDA
    return (MIN_PREGUNTAS_PARTIDA + preguntas_por_materia - 1) // preguntas_por_materia


def validar_total_preguntas(n: int, *, contexto: str = "") -> None:
    if n < MIN_PREGUNTAS_PARTIDA:
        msg = f"El examen debe tener al menos {MIN_PREGUNTAS_PARTIDA} preguntas."
        if contexto:
            msg = f"{msg} {contexto}"
        raise ValueError(msg)

# --- dificultad ---


from Comun.modelos import Pregunta


def dificultad_base(dificultad: str) -> int:
    return {"Facil": 1, "Media": 2, "Dificil": 3}.get(dificultad, 2)


def nivel_materia(nivel: str) -> int:
    try:
        return max(1, int(nivel))
    except (TypeError, ValueError):
        return 1


def complejidad_pregunta(pregunta: Pregunta) -> int:
    return nivel_materia(pregunta.nivel) + dificultad_base(pregunta.dificultad) - 1


def dificultad_global_actual(
    respondidas: int,
    global_inicial: int,
    max_global: int,
    cada_n: int = 40,
) -> int:
    subida = respondidas // max(1, cada_n)
    return min(global_inicial + subida, max_global)


def max_complejidad_pool(pool: list[Pregunta]) -> int:
    if not pool:
        return 1
    return max(complejidad_pregunta(p) for p in pool)


def niveles_en_pool(pool: list[Pregunta]) -> frozenset[int]:
    if not pool:
        return frozenset({1})
    return frozenset(complejidad_pregunta(p) for p in pool)


def normalizar_niveles_seleccionados(
    seleccion: set[int] | frozenset[int] | None,
    pool: list[Pregunta],
) -> frozenset[int]:
    disponibles = niveles_en_pool(pool)
    if not seleccion:
        return disponibles
    elegidos = frozenset(n for n in seleccion if n in disponibles)
    return elegidos if elegidos else disponibles


def niveles_seleccion_ordenados(niveles: frozenset[int]) -> list[int]:
    return sorted(niveles)


def describe_niveles_seleccion(niveles: frozenset[int]) -> str:
    ordenados = niveles_seleccion_ordenados(niveles)
    if len(ordenados) == 1:
        return str(ordenados[0])
    return ",".join(str(n) for n in ordenados)


def techo_complejidad_partida(
    *,
    dificultad_progresiva: bool,
    respondidas: int,
    niveles_seleccion: frozenset[int],
    cada_n: int = 40,
) -> int:
    ordenados = niveles_seleccion_ordenados(niveles_seleccion)
    if not ordenados:
        return 1
    if not dificultad_progresiva or len(ordenados) == 1:
        return ordenados[-1]
    indice = min(respondidas // max(1, cada_n), len(ordenados) - 1)
    return ordenados[indice]


def debe_filtrar_por_nivel(
    pool: list[Pregunta],
    niveles_seleccion: frozenset[int],
    dificultad_progresiva: bool,
) -> bool:
    disponibles = niveles_en_pool(pool)
    if len(disponibles) <= 1:
        return False
    if dificultad_progresiva:
        return bool(niveles_seleccion)
    return niveles_seleccion != disponibles


def pregunta_permitida_por_nivel(
    pregunta: Pregunta,
    *,
    niveles_seleccion: frozenset[int],
    techo: int,
    dificultad_progresiva: bool,
) -> bool:
    complejidad = complejidad_pregunta(pregunta)
    if complejidad not in niveles_seleccion:
        return False
    if dificultad_progresiva:
        return complejidad <= techo
    return True

# --- politica_reglas ---


from dataclasses import dataclass
from enum import Enum


class ContextoPartida(str, Enum):
    HISTORIA_SIMULACRO = "historia_simulacro"
    HISTORIA_RETO = "historia_reto"
    RESISTENCIA = "resistencia"
    ESCAPE = "escape"
    LIBRE_INFINITO = "libre_infinito"
    LIBRE_BLOQUE_CORTO = "libre_bloque_corto"
    LIBRE_BLOQUE_NORMAL = "libre_bloque_normal"
    FEEDBACK = "feedback"


@dataclass(frozen=True)
class PoliticaReglas:
    contexto: ContextoPartida
    reglas: ReglasPartida
    eleccion_jugador: bool
    mensaje: str


def clasificar_libre(*, modo_infinito: bool, n_preguntas: int) -> ContextoPartida:
    if modo_infinito:
        return ContextoPartida.LIBRE_INFINITO
    if n_preguntas < MIN_PREGUNTAS_PARTIDA:
        raise ValueError(
            f"El modo libre finito requiere al menos {MIN_PREGUNTAS_PARTIDA} preguntas."
        )
    if n_preguntas <= MIN_PREGUNTAS_PARTIDA:
        return ContextoPartida.LIBRE_BLOQUE_CORTO
    return ContextoPartida.LIBRE_BLOQUE_NORMAL


def _politica_fija(
    contexto: ContextoPartida,
    reglas: ReglasPartida,
    mensaje: str,
) -> PoliticaReglas:
    return PoliticaReglas(
        contexto=contexto,
        reglas=reglas,
        eleccion_jugador=False,
        mensaje=mensaje,
    )


def politica_historia_simulacro() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.HISTORIA_SIMULACRO,
        preset_historia_examen(),
        "Examen cerrado: sin vidas ni pistas al responder; nota y corrección al final.",
    )


def politica_historia_reto() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.HISTORIA_RETO,
        preset_historia_reto(),
        "Variante reto: 3 vidas y puntuación arcade (no es un simulacro de examen oficial).",
    )


def politica_escape() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.ESCAPE,
        preset_escape(),
        "Escape room: 3 vidas; sin cronómetro global de partida; el tiempo (si hay) "
        "es solo por pregunta dentro de cada puerta.",
    )


politica_historia_escape = politica_escape


def politica_resistencia() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.RESISTENCIA,
        preset_resistencia(),
        "Resistencia: 3 vidas; dificultad por nº de pregunta; la partida solo "
        "termina cuando el jugador falla (o abandona); la racha bonifica puntos y, si crece "
        "mucho, endurece la pregunta sin castigos automáticos.",
    )


def _fusionar_tiempo_preset(base: ReglasPartida, reglas: ReglasPartida) -> ReglasPartida:
    if not reglas.tiempo_por_pregunta_seg and not reglas.tiempo_total_seg:
        return base
    return ReglasPartida(
        vidas=base.vidas,
        tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
        tiempo_total_seg=reglas.tiempo_total_seg,
        sistema_puntuacion=base.sistema_puntuacion,
        mostrar_solucion_tras_fallo=base.mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=base.mostrar_aciertos_en_curso,
        correccion_al_final=base.correccion_al_final,
        dificultad_progresiva=base.dificultad_progresiva,
    )


def validar_reglas(
    reglas: ReglasPartida,
    contexto: ContextoPartida,
    *,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    if contexto == ContextoPartida.HISTORIA_SIMULACRO:
        return _fusionar_tiempo_preset(preset_historia_examen(), reglas)
    if contexto == ContextoPartida.HISTORIA_RETO:
        return _fusionar_tiempo_preset(preset_historia_reto(), reglas)
    if contexto == ContextoPartida.RESISTENCIA:
        return preset_resistencia()
    if contexto == ContextoPartida.ESCAPE:
        return preset_escape()
    if contexto in {
        ContextoPartida.LIBRE_INFINITO,
        ContextoPartida.LIBRE_BLOQUE_CORTO,
        ContextoPartida.LIBRE_BLOQUE_NORMAL,
    }:
        reglas = sanitizar_reglas_libre(
            reglas,
            modo_infinito=modo_infinito or contexto == ContextoPartida.LIBRE_INFINITO,
            n_preguntas=n_preguntas,
        )
    if reglas.correccion_al_final:
        reglas = ReglasPartida(
            vidas=reglas.vidas,
            tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
            tiempo_total_seg=reglas.tiempo_total_seg,
            sistema_puntuacion=reglas.sistema_puntuacion,
            mostrar_solucion_tras_fallo=reglas.mostrar_solucion_tras_fallo,
            mostrar_aciertos_en_curso=reglas.mostrar_aciertos_en_curso,
            correccion_al_final=False,
            dificultad_progresiva=reglas.dificultad_progresiva,
        )
    elif contexto != ContextoPartida.HISTORIA_SIMULACRO:
        reglas = ReglasPartida(
            vidas=reglas.vidas,
            tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
            tiempo_total_seg=reglas.tiempo_total_seg,
            sistema_puntuacion=reglas.sistema_puntuacion,
            mostrar_solucion_tras_fallo=True,
            mostrar_aciertos_en_curso=reglas.mostrar_aciertos_en_curso,
            correccion_al_final=reglas.correccion_al_final,
            dificultad_progresiva=reglas.dificultad_progresiva,
        )
    return reglas

# --- reglas_libre ---


from dataclasses import dataclass
from typing import TYPE_CHECKING

MIN_PREGUNTAS_CALIFICACION = MIN_PREGUNTAS_PARTIDA

ETIQUETAS_SISTEMA: dict[SistemaPuntuacion, str] = {
    SistemaPuntuacion.ARCADE: "Arcade",
    SistemaPuntuacion.NOTA: "Nota 0-10",
    SistemaPuntuacion.PORCENTAJE: "Porcentaje",
}


@dataclass(frozen=True)
class OpcionesReglasLibre:
    """Qué controles están habilitados según la selección actual."""

    sistemas: tuple[SistemaPuntuacion, ...]
    permitir_sin_vidas: bool
    permitir_con_vidas: bool
    permitir_dificultad_progresiva: bool
    permitir_tiempo_pregunta: bool = True
    permitir_tiempo_total: bool = True


def _calificacion_viable(*, modo_infinito: bool, n_preguntas: int) -> bool:
    return not modo_infinito and n_preguntas >= MIN_PREGUNTAS_CALIFICACION


def sistemas_disponibles(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
) -> tuple[SistemaPuntuacion, ...]:
    if modo_infinito or not sin_vidas:
        return (SistemaPuntuacion.ARCADE,)
    if not _calificacion_viable(modo_infinito=modo_infinito, n_preguntas=n_preguntas):
        return (SistemaPuntuacion.ARCADE,)
    return (
        SistemaPuntuacion.ARCADE,
        SistemaPuntuacion.NOTA,
        SistemaPuntuacion.PORCENTAJE,
    )


def normalizar_vidas_y_sistema(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
    sistema: SistemaPuntuacion,
) -> tuple[bool, SistemaPuntuacion]:
    if modo_infinito:
        return sin_vidas, SistemaPuntuacion.ARCADE
    if not sin_vidas:
        return False, SistemaPuntuacion.ARCADE

    sis = sistema
    if sis in {SistemaPuntuacion.NOTA, SistemaPuntuacion.PORCENTAJE}:
        if not _calificacion_viable(modo_infinito=modo_infinito, n_preguntas=n_preguntas):
            sis = SistemaPuntuacion.ARCADE
    return True, sis


def opciones_reglas_libre(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
    sistema: SistemaPuntuacion,
) -> OpcionesReglasLibre:
    sin, sis = normalizar_vidas_y_sistema(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    sistemas = sistemas_disponibles(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
    )
    progresiva = (
        sis == SistemaPuntuacion.ARCADE
        and (modo_infinito or n_preguntas >= MIN_PREGUNTAS_PARTIDA)
    )
    return OpcionesReglasLibre(
        sistemas=sistemas,
        permitir_sin_vidas=True,
        permitir_con_vidas=sis == SistemaPuntuacion.ARCADE,
        permitir_dificultad_progresiva=progresiva,
    )


def sanitizar_reglas_libre(
    reglas: ReglasPartida,
    *,
    modo_infinito: bool,
    n_preguntas: int,
) -> ReglasPartida:
    sin = reglas.vidas is None
    sin, sis = normalizar_vidas_y_sistema(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
        sistema=reglas.sistema_puntuacion,
    )
    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
        sistema=sis,
    )
    vidas = None if sin else (reglas.vidas if reglas.vidas and reglas.vidas > 0 else 3)
    dif = reglas.dificultad_progresiva if opts.permitir_dificultad_progresiva else False
    return ReglasPartida(
        vidas=vidas,
        tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
        tiempo_total_seg=reglas.tiempo_total_seg,
        sistema_puntuacion=sis,
        mostrar_solucion_tras_fallo=True,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dif,
    )


_TITULOS_LIBRE: dict[object, str] = {}


def _titulos_libre() -> dict[object, str]:
    global _TITULOS_LIBRE
    if not _TITULOS_LIBRE:
        _TITULOS_LIBRE = {
            ContextoPartida.LIBRE_BLOQUE_CORTO: f"Bloque mínimo ({MIN_PREGUNTAS_PARTIDA} preguntas)",
            ContextoPartida.LIBRE_BLOQUE_NORMAL: "Bloque amplio (6+ preguntas)",
            ContextoPartida.LIBRE_INFINITO: "Modo infinito",
        }
    return _TITULOS_LIBRE


@dataclass(frozen=True)
class AlcanceConfigLibre:
    """Opciones disponibles en el asistente de reglas del modo libre."""

    contexto: object
    titulo: str
    permitir_sin_vidas: bool = True
    min_vidas: int = 1
    max_vidas: int = 10
    sistemas: tuple[SistemaPuntuacion, ...] = (
        SistemaPuntuacion.ARCADE,
        SistemaPuntuacion.NOTA,
        SistemaPuntuacion.PORCENTAJE,
    )
    permitir_tiempo_pregunta: bool = True
    permitir_tiempo_total: bool = True
    permitir_dificultad_progresiva: bool = True


def alcance_para_contexto(ctx) -> AlcanceConfigLibre | None:
    titulo = _titulos_libre().get(ctx)
    if titulo is None:
        return None
    return AlcanceConfigLibre(contexto=ctx, titulo=titulo)


def construir_reglas_personalizadas(
    ctx,
    *,
    vidas: int | None,
    sistema: SistemaPuntuacion,
    tiempo_por_pregunta_seg: int | None = None,
    tiempo_total_seg: int | None = None,
    dificultad_progresiva: bool = False,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    if alcance_para_contexto(ctx) is None:
        raise ValueError(f"Configuración personalizada no permitida para {ctx.value}")

    reglas = ReglasPartida(
        vidas=vidas,
        tiempo_por_pregunta_seg=tiempo_por_pregunta_seg,
        tiempo_total_seg=tiempo_total_seg,
        sistema_puntuacion=sistema,
        mostrar_solucion_tras_fallo=True,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dificultad_progresiva,
    )
    return sanitizar_reglas_libre(
        reglas,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )


def contexto_partida(*, modo_infinito: bool, n_preguntas: int) -> ContextoPartida:
    return clasificar_libre(modo_infinito=modo_infinito, n_preguntas=n_preguntas)


def reglas_desde_combinacion(
    contexto: ContextoPartida,
    *,
    vidas: int | None,
    sistema: SistemaPuntuacion,
    tiempo_por_pregunta_seg: int | None = None,
    tiempo_total_seg: int | None = None,
    dificultad_progresiva: bool = False,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    reglas = construir_reglas_personalizadas(
        contexto,
        vidas=vidas,
        sistema=sistema,
        tiempo_por_pregunta_seg=tiempo_por_pregunta_seg,
        tiempo_total_seg=tiempo_total_seg,
        dificultad_progresiva=dificultad_progresiva,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )
    return validar_reglas(
        reglas,
        contexto,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )


def alcance(contexto: ContextoPartida):
    return alcance_para_contexto(contexto)
