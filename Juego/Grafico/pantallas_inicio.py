#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas de inicio (bienvenida y nombre del jugador)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.preferencias_grafico import es_nombre_anonimo, nombre_jugador_efectivo
from Comun.preferencias_grafico import (
    PreferenciasGrafico,
    cargar_preferencias_grafico,
    guardar_preferencias_grafico,
    nombre_inicial_grafico,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import BTN_CONTINUAR, etiqueta
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_AVISO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.ui import Boton, CampoTexto, dibujar_panel, rect_boton_etiqueta

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

_COLOR_ETIQUETA_PANEL = (70, 80, 95)


class PantallaBienvenida(Pantalla):
    """Pide el nombre la primera vez; si ya hay uno guardado, la app salta esta pantalla."""

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
        self.panel = pygame.Rect(MARGEN + 48, 228, ANCHO - 2 * (MARGEN + 48), 220)
        self.campo_nombre = CampoTexto(
            pygame.Rect(self.panel.x + 40, self.panel.y + 88, self.panel.width - 80, 44),
            texto_inicial=nombre_inicial_grafico(),
            placeholder="Tu nombre",
        )
        etiq = etiqueta(*BTN_CONTINUAR)
        self.boton_empezar = Boton(
            etiq,
            rect_boton_etiqueta(
                etiq,
                self.fuentes["menu"],
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=240,
                alto_min=48,
            ),
            self._entrar_al_menu,
            tooltip="Guarda tu nombre y abre el menú principal.",
        )
        self.boton_empezar.rect.midtop = (ANCHO // 2, self.campo_nombre.rect.bottom + 28)

    def _entrar_al_menu(self) -> None:
        nombre_efectivo = nombre_jugador_efectivo(self.campo_nombre.texto)
        nombre_guardado = (
            "" if es_nombre_anonimo(nombre_efectivo) else nombre_efectivo
        )
        prefs = cargar_preferencias_grafico()
        guardar_preferencias_grafico(
            PreferenciasGrafico(
                nombre_jugador=nombre_guardado,
                mostrar_tooltips=prefs.mostrar_tooltips,
                mostrar_emojis=prefs.mostrar_emojis,
            )
        )
        self.mensaje = ""
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        self.campo_nombre.manejar_evento(evento)
        if evento.type == pygame.MOUSEMOTION:
            self.boton_empezar.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.campo_nombre.manejar_evento(evento):
                return None
            self.boton_empezar.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        self.dibujar_fondo(superficie)

    def dibujar_fondo(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            "Cuestionario MATCAD",
            (ANCHO // 2, 88),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        subt = self.fuentes["cuerpo"].render(
            "Introduce tu nombre para partidas e informes.",
            True,
            COLOR_TEXTO,
        )
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, 138)))
        nota = self.fuentes["pequena"].render(
            "Podrás cambiarlo después en Opciones (⚙️).",
            True,
            COLOR_TEXTO,
        )
        superficie.blit(nota, nota.get_rect(midtop=(ANCHO // 2, 168)))

    def dibujar_contenido_popup_bloqueante(self, superficie: pygame.Surface) -> None:
        dibujar_panel(superficie, self.panel, color=(255, 255, 255))

        titulo_panel = self.fuentes["subtitulo"].render(
            "¿Cómo te llamas?",
            True,
            (25, 25, 30),
        )
        superficie.blit(
            titulo_panel,
            titulo_panel.get_rect(midtop=(self.panel.centerx, self.panel.y + 24)),
        )

        lbl = self.fuentes["pequena"].render(
            "Nombre (teclado):",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(
            lbl,
            lbl.get_rect(midbottom=(self.campo_nombre.rect.centerx, self.campo_nombre.rect.y - 6)),
        )
        self.campo_nombre.dibujar(superficie, self.fuentes["menu"])
        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])

        if self.mensaje:
            aviso = self.fuentes["pequena"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(midtop=(ANCHO // 2, self.panel.bottom + 16)))

    def popup_bloqueante(self) -> bool:
        return True

    def titulo_pausa(self) -> str:
        return "Bienvenida"
