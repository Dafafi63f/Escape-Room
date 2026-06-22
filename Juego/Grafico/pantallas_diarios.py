#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atajos del menú principal: examen del día, examen aleatorio y reto del día."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.examen_dia_historia import etiqueta_fecha_examen_dia
from Comun.examen_fijo_historia import (
    ID_PRESET_EXAMEN_FIJO,
    config_atajo_aleatorio,
    config_atajo_diario,
)
from Comun.modos_diarios import ID_PRESET_RETO_DIA
from Comun.presets_historia import PresetHistoria, buscar_preset
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_historia import (
    construir_navegacion_fin_partida_historia,
    iniciar_pantalla_partida_historia,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import (
    BTN_VOLVER_MENU,
    con_emoji,
    etiqueta,
    titulo_pantalla,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_AVISO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.ui import (
    Boton,
    dibujar_tooltips_botones,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO = Y_INICIO_TITULO
Y_DESC_INICIO = Y_TITULO + 54
ALTURA_LINEA_DESC = 22
DESCRIPCIONES = (
    "Examen del día: misma semilla para todos hoy (comparable entre jugadores).",
    "Examen aleatorio: nueva semilla cada vez que empiezas o repites.",
    "Reto del día: resistencia con ranking diario.",
)
GAP_TRAS_DESC = 28
Y_BOTONES_MODOS = Y_DESC_INICIO + len(DESCRIPCIONES) * ALTURA_LINEA_DESC + GAP_TRAS_DESC
    "Mismo examen para todos hoy: 4 asignaturas, 24 preguntas balanceadas. "
    "El orden cambia en cada partida."
)
_TOOLTIP_EXAMEN_ALEATORIO = (
    "Misma plantilla balanceada (4 materias, 24 preguntas), "
    "con contenido nuevo cada partida y orden fijo por dificultad (F→M→D)."
)

_EMOJI_EXAMEN_DIA = _p("📕")
_EMOJI_EXAMEN_ALEATORIO = _p("🎲")
_EMOJI_RETO_DIA = _p("🔥")


def _etiqueta_modo_diario(prefijo: str, fecha: str, emoji: EmojiPar) -> str:
    return con_emoji(
        f"{prefijo} — {fecha}",
        emoji,
        posicion="inicio",
    )


class ConfigModosDiarios(Pantalla):
    """Examen del día, examen aleatorio y reto del día desde el menú principal."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.preset_examen_fijo = buscar_preset(ID_PRESET_EXAMEN_FIJO)
        self.config_examen_dia = config_atajo_diario()
        self.config_examen_aleatorio = config_atajo_aleatorio()
        self.preset_reto = buscar_preset(ID_PRESET_RETO_DIA)

        fuente_menu = self.fuentes["menu"]
        etiquetas = [
            _etiqueta_modo_diario(
                "Examen del día",
                etiqueta_fecha_examen_dia(),
                _EMOJI_EXAMEN_DIA,
            ),
            con_emoji("Examen aleatorio", _EMOJI_EXAMEN_ALEATORIO, posicion="inicio"),
            _etiqueta_modo_diario(
                "Reto del día",
                etiqueta_fecha_reto_dia(),
                _EMOJI_RETO_DIA,
            ),
        ]
        rects_modos = rects_botones_apilados(
            etiquetas,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=Y_BOTONES_MODOS,
            gap=10,
            ancho_min=460,
            alto_min=48,
            margen_inferior=MARGEN_INF + 72,
        )
        self.boton_examen = Boton(
            etiquetas[0],
            rects_modos[0],
            self._iniciar_examen,
            tooltip=_TOOLTIP_EXAMEN_DIA,
        )
        self.boton_examen_aleatorio = Boton(
            etiquetas[1],
            rects_modos[1],
            self._iniciar_examen_aleatorio,
            tooltip=_TOOLTIP_EXAMEN_ALEATORIO,
        )
        self.boton_reto = Boton(
            etiquetas[2],
            rects_modos[2],
            self._iniciar_reto,
            tooltip=self.preset_reto.descripcion,
        )

        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        self.boton_volver = Boton(
            etiq_volver,
            rect_boton_etiqueta(
                etiq_volver,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=420,
                alto_min=44,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=14,
            margen_inferior=MARGEN_INF,
        )

    def _iniciar_partida_diaria(
        self,
        preset: PresetHistoria,
        config: ConfigPresetHistoria,
    ) -> None:
        nombre = nombre_jugador_grafico()

        def _pantalla_configuracion():
            return ConfigModosDiarios(self.datos, self.ir_a, self.salir)

        navegacion = construir_navegacion_fin_partida_historia(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=navegacion,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        self.ir_a(pantalla)

    def _iniciar_examen(self) -> None:
        self._iniciar_partida_diaria(self.preset_examen_fijo, self.config_examen_dia)

    def _iniciar_examen_aleatorio(self) -> None:
        self._iniciar_partida_diaria(
            self.preset_examen_fijo,
            self.config_examen_aleatorio,
        )

    def _iniciar_reto(self) -> None:
        self._iniciar_partida_diaria(self.preset_reto, ConfigPresetHistoria())

    def _botones_ui(self) -> list[Boton]:
        return [
            self.boton_examen,
            self.boton_examen_aleatorio,
            self.boton_reto,
            self.boton_volver,
        ]

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("Retos del día"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        for i, texto in enumerate(DESCRIPCIONES):
            subt = fuente_peq.render(texto, True, COLOR_TEXTO)
            superficie.blit(
                subt,
                subt.get_rect(midtop=(ANCHO // 2, Y_DESC_INICIO + i * ALTURA_LINEA_DESC)),
            )

        if self.mensaje:
            msg = fuente_peq.render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(msg, msg.get_rect(midtop=(ANCHO // 2, Y_BOTONES_MODOS - 28)))

        for boton in self._botones_ui():
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones_ui())

    def titulo_pausa(self) -> str:
        return "Retos del día"
