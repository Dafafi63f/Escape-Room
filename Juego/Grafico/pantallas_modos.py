#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Menús de modos cortos: diarios / examen fijo y especiales (resistencia)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.modos_diarios import (
    ID_PRESET_EXAMEN_FIJO,
    config_atajo_aleatorio,
    config_atajo_diario,
    etiqueta_fecha_examen_dia,
)
from Comun.presets_historia import PresetHistoria, buscar_preset
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_preset import (
    construir_navegacion_fin_partida,
    iniciar_pantalla_partida,
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
DESCRIPCIONES_DIARIOS = (
    "Examen del día: misma selección de preguntas hoy (semilla de la fecha); orden distinto cada partida.",
    "Examen aleatorio: selección nueva cada partida; preguntas ordenadas F→M→D.",
)
GAP_TRAS_DESC = 28
MARGEN_INF = 22

_EMOJI_EXAMEN_DIA = _p("📕")
_EMOJI_EXAMEN_ALEATORIO = _p("🎲")


def _etiqueta_modo_diario(prefijo: str, fecha: str, emoji: EmojiPar) -> str:
    return con_emoji(
        f"{prefijo} — {fecha}",
        emoji,
        posicion="inicio",
    )


def abrir_config_examen_fijo(
    datos: DatosJuego,
    ir_a: Callable[[Pantalla], None],
    salir_app: Callable[[], None],
) -> None:
    """Pantalla de opciones del preset ``examen_fijo`` (igual que en el carrusel historia)."""
    from Comun.modos_diarios import ID_PRESET_EXAMEN_FIJO
    from Comun.presets_historia import buscar_preset
    from Comun.preferencias_grafico import nombre_jugador_grafico
    from Grafico.pantallas import MenuPrincipal
    from Grafico.pantallas_examen_fijo import ConfigOpcionesHistoria

    preset = buscar_preset(ID_PRESET_EXAMEN_FIJO)
    nombre = nombre_jugador_grafico()

    def volver(_cfg: ConfigPresetHistoria) -> None:
        ir_a(MenuPrincipal(datos, ir_a, salir_app))

    ir_a(
        ConfigOpcionesHistoria(
            datos,
            preset,
            nombre,
            ir_a,
            salir_app,
            volver,
        )
    )


class ConfigModosDiarios(Pantalla):
    """Atajos rápidos al examen del día y aleatorio (paquete completo)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        if not datos.perfil.modos_diarios_disponibles:
            ir_a(MenuPrincipal(datos, ir_a, salir_app))
            return
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.preset_examen_fijo = buscar_preset(ID_PRESET_EXAMEN_FIJO)
        self.config_examen_dia = config_atajo_diario()
        self.config_examen_aleatorio = config_atajo_aleatorio()

        fuente_menu = self.fuentes["menu"]
        etiquetas = [
            _etiqueta_modo_diario(
                "Examen del día",
                etiqueta_fecha_examen_dia(),
                _EMOJI_EXAMEN_DIA,
            ),
            con_emoji("Examen aleatorio", _EMOJI_EXAMEN_ALEATORIO, posicion="inicio"),
        ]
        y_botones = (
            Y_DESC_INICIO
            + len(DESCRIPCIONES_DIARIOS) * ALTURA_LINEA_DESC
            + GAP_TRAS_DESC
        )
        rects_modos = rects_botones_apilados(
            etiquetas,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=y_botones,
            gap=10,
            ancho_min=460,
            alto_min=48,
            margen_inferior=MARGEN_INF + 72,
        )
        self.boton_examen = Boton(
            etiquetas[0],
            rects_modos[0],
            self._iniciar_examen,
        )
        self.boton_examen_aleatorio = Boton(
            etiquetas[1],
            rects_modos[1],
            self._iniciar_examen_aleatorio,
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
            tooltip="Vuelve al menú principal.",
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
            return ConfigModosDiarios(self.datos, self.ir_a, self.salir_app)

        navegacion = construir_navegacion_fin_partida(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida(
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

    def _botones_ui(self) -> list[Boton]:
        return [
            self.boton_examen,
            self.boton_examen_aleatorio,
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
            titulo_pantalla("Modos diarios"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        y_botones = (
            Y_DESC_INICIO
            + len(DESCRIPCIONES_DIARIOS) * ALTURA_LINEA_DESC
            + GAP_TRAS_DESC
        )
        for i, texto in enumerate(DESCRIPCIONES_DIARIOS):
            subt = fuente_peq.render(texto, True, COLOR_TEXTO)
            superficie.blit(
                subt,
                subt.get_rect(midtop=(ANCHO // 2, Y_DESC_INICIO + i * ALTURA_LINEA_DESC)),
            )

        if self.mensaje:
            msg = fuente_peq.render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(msg, msg.get_rect(midtop=(ANCHO // 2, y_botones - 28)))

        for boton in self._botones_ui():
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones_ui())

    def titulo_pausa(self) -> str:
        return "Modos diarios"

# --- Modos especiales ---

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.presets_historia import PresetHistoria
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_especiales import cargar_catalogo_especiales
from Grafico.modo_preset import (
    construir_navegacion_fin_partida,
    iniciar_pantalla_partida,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import (
    BTN_VOLVER_MENU,
    con_emoji,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
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
from Grafico.texto import dibujar_texto_centro
from Grafico.tooltips_ui import tooltip_modo_especial
from Grafico.ui import (
    Boton,
    capturar,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_tooltip,
    dibujar_tooltips_botones,
    posicionar_botones_fila,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
    tamano_grupo_botones,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO = Y_INICIO_TITULO
Y_SUBTITULO = Y_TITULO + 32
Y_MODOS_LBL = Y_SUBTITULO + 36
Y_BOTONES_MODOS = Y_MODOS_LBL + 32
MARGEN_INF = 22

_EMOJI_RESISTENCIA = _p("💪")
_EMOJI_ESPECIAL_DEFECTO = _p("⚡")


def _emoji_modo_especial(preset_id: str) -> EmojiPar:
    if preset_id == "resistencia":
        return _EMOJI_RESISTENCIA
    if preset_id == "escape_room":
        from Comun.emojis_escape import EMOJI_MODO_ESCAPE

        return _p(EMOJI_MODO_ESCAPE)
    return _EMOJI_ESPECIAL_DEFECTO


class ConfigModosEspeciales(Pantalla):
    """Lista de modos especiales (un botón por preset)."""

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
        self.presets = cargar_catalogo_especiales(datos.perfil)

        fuente_menu = self.fuentes["menu"]
        etiquetas_modos = [preparar_etiqueta_modo(p) for p in self.presets]
        rects_modos = rects_botones_apilados(
            etiquetas_modos,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=Y_BOTONES_MODOS,
            gap=12,
            ancho_min=460,
            alto_min=52,
            margen_inferior=MARGEN_INF + 72,
        )
        self.botones_modo: list[Boton] = []
        for preset, rect, etiq in zip(self.presets, rects_modos, etiquetas_modos, strict=True):
            boton = Boton(
                etiq,
                rect,
                capturar(self._iniciar_modo, preset.id),
                tooltip=tooltip_modo_especial(preset.id, self.datos.perfil)
                or preset.descripcion,
            )
            if not self.datos.perfil.modo_especial_disponible(preset.id):
                boton.activo = False
            self.botones_modo.append(boton)

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

    def _pantalla_actual(self) -> ConfigModosEspeciales:
        return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

    def _preset_por_id(self, preset_id: str) -> PresetHistoria:
        for preset in self.presets:
            if preset.id == preset_id:
                return preset
        raise KeyError(preset_id)

    def _iniciar_modo(self, preset_id: str) -> None:
        if not self.datos.perfil.modo_especial_disponible(preset_id):
            self.mensaje = self.datos.perfil.motivo_modo_especial_no_disponible(preset_id)
            return
        preset = self._preset_por_id(preset_id)
        if preset_id == "escape_room":
            from Grafico.pantallas_escape import ConfigAjustesEscapeRoom

            self.mensaje = ""
            self.ir_a(
                ConfigAjustesEscapeRoom(
                    self.datos,
                    self.ir_a,
                    self.salir_app,
                    preset,
                )
            )
            return
        nombre = nombre_jugador_grafico()
        config = ConfigPresetHistoria()
        self.mensaje = ""

        def _pantalla_configuracion():
            return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

        navegacion = construir_navegacion_fin_partida(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida(
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
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        return [*self.botones_modo, self.boton_volver]

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
            titulo_pantalla("MODOS ESPECIALES"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_texto_centro(
            superficie,
            subtitulo("Escape room y resistencia", "⚡"),
            (ANCHO // 2, Y_SUBTITULO),
            self.fuentes["pequena"].get_height(),
            COLOR_TEXTO,
        )

        modos_lbl = self.fuentes["menu"].render(
            etiqueta_campo("modo_especial", "Elige un modo:"), True, COLOR_TEXTO
        )
        superficie.blit(modos_lbl, modos_lbl.get_rect(midtop=(ANCHO // 2, Y_MODOS_LBL)))

        for boton in self.botones_modo:
            boton.dibujar(superficie, self.fuentes["menu"])

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_volver.rect.y - 28)),
            )

        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            self._botones_ui(),
        )

    def titulo_pausa(self) -> str:
        return "Modos especiales"


def preparar_etiqueta_modo(preset: PresetHistoria) -> str:
    from Grafico.texto import preparar_texto_ui

    emoji = _emoji_modo_especial(preset.id)
    texto = preset.nombre
    return preparar_texto_ui(con_emoji(texto, emoji, posicion="inicio"))


