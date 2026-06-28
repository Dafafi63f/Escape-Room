#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptador de dominio para tests del juego gráfico.

Replica el arranque de ``Juego/juego_grafico.py`` y expone operaciones de
dominio para comprobar reglas, datos y evaluación sin levantar la UI.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

_ROOT = Path(__file__).resolve().parents[1]
_JUEGO = _ROOT / "Juego"


def bootstrap_juego() -> None:
    """Mismo ``sys.path`` que ``juego_grafico.py``."""
    s = str(_JUEGO)
    if s not in sys.path:
        sys.path.insert(0, s)


@dataclass(frozen=True)
class ConfigReglasLibre:
    modo_infinito: bool
    n_preguntas: int
    vidas: int | None
    sistema: Any
    tiempo_por_pregunta_seg: int | None = None
    tiempo_total_seg: int | None = None
    mostrar_solucion_tras_fallo: bool = True
    mostrar_aciertos_en_curso: bool = True
    dificultad_progresiva: bool = False


@dataclass(frozen=True)
class ResumenDatosJuego:
    num_preguntas: int
    num_materias: int
    muestra_texto: str
    muestra_materia: str


@dataclass(frozen=True)
class ResultadoEvaluacion:
    mensaje: str
    solucion: str | None
    aciertos: int
    respondidas: int
    puntos_arcade: int
    vidas_restantes: int | None


def tupla_reglas(reglas: Any) -> tuple:
    return (
        reglas.vidas,
        reglas.tiempo_por_pregunta_seg,
        reglas.tiempo_total_seg,
        reglas.sistema_puntuacion,
        reglas.mostrar_solucion_tras_fallo,
        reglas.mostrar_aciertos_en_curso,
        reglas.correccion_al_final,
        reglas.dificultad_progresiva,
    )


def tupla_opciones(opts: Any) -> tuple:
    return (
        opts.sistemas,
        opts.permitir_sin_vidas,
        opts.permitir_con_vidas,
        opts.permitir_dificultad_progresiva,
    )


class BackendJuego(Protocol):
    nombre: str

    def cargar_datos(self) -> ResumenDatosJuego: ...

    def contexto_libre(self, *, modo_infinito: bool, n_preguntas: int) -> Any: ...

    def reglas_libre(self, cfg: ConfigReglasLibre) -> Any: ...

    def opciones_libre(
        self,
        *,
        modo_infinito: bool,
        n_preguntas: int,
        sin_vidas: bool,
        sistema: Any,
    ) -> Any: ...

    def evaluar_respuesta(
        self,
        *,
        reglas: Any,
        pregunta: Any,
        acierto: bool,
        letra: str = "B",
        tiempo_agotado: bool = False,
    ) -> ResultadoEvaluacion: ...

    def linea_estado_partida(
        self,
        *,
        reglas: Any,
        progreso: str,
        aciertos: int = 0,
        respondidas: int = 0,
        puntos: int = 0,
        vidas: int | None = None,
        segundos_pregunta: int | None = None,
    ) -> str: ...

    def nombre_jugador_defecto(self) -> str: ...

    def catalogo_historia_ids(self) -> tuple[str, ...]: ...

    def reglas_historia_preset(self, preset_id: str) -> tuple: ...


class BackendGrafico:
    """Ruta ``juego_grafico.py`` → ``Comun`` + ``Grafico``."""

    nombre = "grafico"

    def __init__(self) -> None:
        bootstrap_juego()
        from Comun.contenido import cargar_contenido_juego, construir_datos_juego
        from Comun.reglas import opciones_reglas_libre, contexto_partida, reglas_desde_combinacion
        from Comun.modelos import Pregunta
        from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta, evaluar_respuesta, linea_estado
        from Comun.presets_historia import cargar_presets_historia
        from Comun.rutas import resolver_presets
        from Grafico.app import DatosJuego

        self._opciones_reglas_libre = opciones_reglas_libre
        self._contexto_partida = contexto_partida
        self._reglas_desde_combinacion = reglas_desde_combinacion
        self._datos_juego = DatosJuego
        self._cargar_contenido = cargar_contenido_juego
        self._construir_datos = construir_datos_juego
        self._cargar_presets_historia = cargar_presets_historia
        self._resolver_presets = resolver_presets
        self._pregunta = Pregunta
        self._estado_partida = EstadoPartida
        self._resultado_respuesta = ResultadoRespuesta
        self._evaluar_respuesta = evaluar_respuesta
        self._linea_estado = linea_estado
        self._datos: DatosJuego | None = None

    def _datos_cargados(self) -> DatosJuego:
        if self._datos is None:
            self._datos = self._construir_datos(self._cargar_contenido())
        return self._datos

    def cargar_datos(self) -> ResumenDatosJuego:
        datos = self._datos_cargados()
        p0 = datos.preguntas[0]
        return ResumenDatosJuego(
            num_preguntas=datos.num_preguntas,
            num_materias=datos.num_materias,
            muestra_texto=p0.texto,
            muestra_materia=p0.materia,
        )

    def contexto_libre(self, *, modo_infinito: bool, n_preguntas: int) -> Any:
        return self._contexto_partida(
            modo_infinito=modo_infinito,
            n_preguntas=n_preguntas,
        )

    def reglas_libre(self, cfg: ConfigReglasLibre) -> Any:
        ctx = self.contexto_libre(
            modo_infinito=cfg.modo_infinito,
            n_preguntas=cfg.n_preguntas,
        )
        return self._reglas_desde_combinacion(
            ctx,
            vidas=cfg.vidas,
            sistema=cfg.sistema,
            tiempo_por_pregunta_seg=cfg.tiempo_por_pregunta_seg,
            tiempo_total_seg=cfg.tiempo_total_seg,
            dificultad_progresiva=cfg.dificultad_progresiva,
            modo_infinito=cfg.modo_infinito,
            n_preguntas=cfg.n_preguntas,
        )

    def opciones_libre(
        self,
        *,
        modo_infinito: bool,
        n_preguntas: int,
        sin_vidas: bool,
        sistema: Any,
    ) -> Any:
        return self._opciones_reglas_libre(
            modo_infinito=modo_infinito,
            n_preguntas=n_preguntas,
            sin_vidas=sin_vidas,
            sistema=sistema,
        )

    def evaluar_respuesta(
        self,
        *,
        reglas: Any,
        pregunta: Any,
        acierto: bool,
        letra: str = "B",
        tiempo_agotado: bool = False,
    ) -> ResultadoEvaluacion:
        estado = self._estado_partida(
            nombre="Test",
            reglas=reglas,
            vidas_restantes=reglas.vidas,
        )
        resultado = self._resultado_respuesta(
            acierto=acierto,
            respuesta=letra,
            tiempo_agotado=tiempo_agotado,
        )
        fb = self._evaluar_respuesta(pregunta, estado, resultado)
        return ResultadoEvaluacion(
            mensaje=fb.mensaje,
            solucion=fb.solucion,
            aciertos=estado.aciertos,
            respondidas=estado.respondidas,
            puntos_arcade=estado.puntos_arcade,
            vidas_restantes=estado.vidas_restantes,
        )

    def linea_estado_partida(
        self,
        *,
        reglas: Any,
        progreso: str,
        aciertos: int = 0,
        respondidas: int = 0,
        puntos: int = 0,
        vidas: int | None = None,
        segundos_pregunta: int | None = None,
    ) -> str:
        estado = self._estado_partida(
            nombre="Test",
            reglas=reglas,
            vidas_restantes=vidas if vidas is not None else reglas.vidas,
            aciertos=aciertos,
            respondidas=respondidas,
            puntos_arcade=puntos,
        )
        return self._linea_estado(
            estado,
            progreso,
            segundos_pregunta_restantes=segundos_pregunta,
        )

    def pregunta_ejemplo(self) -> Any:
        return self._pregunta(
            texto="¿Cuál es 2+2?",
            materia="Test",
            tematica="T",
            dificultad="Facil",
            tipo="Teoria",
            grupo="g",
            nivel="1",
            curso="1",
            semestre="1",
            opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
            correcta="B",
        )

    def nombre_jugador_defecto(self) -> str:
        from Comun.preferencias_grafico import nombre_jugador_efectivo

        return nombre_jugador_efectivo("")

    def catalogo_historia_ids(self) -> tuple[str, ...]:
        datos = self._datos_cargados()
        presets = self._cargar_presets_historia(
            self._resolver_presets(),
            perfil=datos.perfil,
        )
        return tuple(p.id for p in presets)

    def reglas_historia_preset(self, preset_id: str) -> tuple:
        from Comun.presets_historia import aplicar_preset, buscar_preset, config_defecto
        from Grafico.modo_historia import orden_materias_juego

        datos = self._datos_cargados()
        preset = buscar_preset(preset_id)
        orden_materias = orden_materias_juego(datos)
        config = config_defecto(
            preset,
            materias_meta=datos.materias_meta,
            materias_orden=orden_materias,
            perfil=datos.perfil,
            path_plantillas=datos.path_plantillas_json,
        )
        return tupla_reglas(aplicar_preset(preset, config))


def crear_backend(nombre: str = "grafico") -> BackendJuego:
    if nombre == "grafico":
        return BackendGrafico()
    raise ValueError(f"Backend desconocido: {nombre}")
