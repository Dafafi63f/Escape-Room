#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bucle principal pygame y enrutador de pantallas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from Comun.modelos import Pregunta
from Grafico.textos_grafico import (
    BTN_CONTINUAR,
    BTN_CONTINUAR_PARTIDA,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    emoji_icono,
    etiqueta_menu,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.tema import ALTO, ANCHO, FPS, MARGEN, TITULO_VENTANA, crear_fuentes
from Grafico.ui import Boton, dibujar_panel, dibujar_tooltips_botones, rects_botones_apilados
from Grafico.tooltips_ui import TOOLTIP_FEEDBACK, TOOLTIP_PAUSA, tooltips_menu_pausa
from Grafico.pantallas import MenuPrincipal, Pantalla, PantallaFeedback, PartidaModoLibre
from Grafico.pantallas_historia import PartidaModoHistoria, PartidaResistenciaHistoria


@dataclass
class DatosJuego:
    num_preguntas: int
    num_materias: int
    preguntas: list[Pregunta]
    materias_meta: dict[str, dict[str, str]]
    path_preguntas_csv: Path
    path_plantillas_json: Path
    abrir_feedback: Callable[[], None] | None = field(default=None, repr=False, compare=False)


class AplicacionGrafica:
    """Ventana pygame con menú y modos jugables."""

    def __init__(self, datos: DatosJuego) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO_VENTANA)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.datos = datos
        datos.abrir_feedback = self._abrir_feedback
        self.fuentes = crear_fuentes()
        self.ejecutando = True
        self.actual: Pantalla = MenuPrincipal(datos, self._ir_a, self._salir)
        self._menu_pausa_abierto = False
        self._anterior: Pantalla | None = None
        self._botones_fijos = self._crear_botones_fijos()
        self._botones_pausa: list[Boton] = []

    def _ir_a(self, pantalla: Pantalla) -> None:
        self.actual = pantalla
        if not isinstance(pantalla, PantallaFeedback):
            self._anterior = None

    def _salir(self) -> None:
        self.ejecutando = False

    def _restaurar_vista_actual(self) -> None:
        """Vista completa de la pantalla en curso (como reimprimir_contexto en consola)."""
        self.actual.restaurar_vista_completa()

    def _pantalla_en_contexto(self) -> Pantalla:
        if isinstance(self.actual, PantallaFeedback) and self._anterior is not None:
            return self._anterior
        return self.actual

    def _ir_a_menu_principal(self) -> None:
        self._ir_a(MenuPrincipal(self.datos, self._ir_a, self._salir))

    def _en_partida(self) -> bool:
        return isinstance(
            self._pantalla_en_contexto(),
            (PartidaModoLibre, PartidaModoHistoria, PartidaResistenciaHistoria),
        )

    def _crear_botones_fijos(self) -> list[tuple[Boton, str]]:
        x, y = 16, 14
        gap = 10
        padding_x = 10
        padding_y = 6

        botones_cfg: list[tuple[str, Callable[[], None], str, str]] = [
            ("II", self._toggle_pausa, "pausa", TOOLTIP_PAUSA),
            ("FB", self._abrir_feedback, "feedback", TOOLTIP_FEEDBACK),
        ]

        resultado: list[tuple[Boton, str]] = []
        x_actual = x
        fuente_ref = self.fuentes["menu"]
        ancho_ref = max(fuente_ref.size(etiqueta)[0] for etiqueta, _handler, _tipo, _tip in botones_cfg)
        alto_ref = max(fuente_ref.size(etiqueta)[1] for etiqueta, _handler, _tipo, _tip in botones_cfg)
        w = max(40, ancho_ref + 2 * padding_x)
        h = max(30, alto_ref + 2 * padding_y)
        for _etiqueta_ref, handler, tipo_icono, tooltip in botones_cfg:
            boton = Boton(
                "",
                pygame.Rect(x_actual, y, w, h),
                handler,
                mostrar_texto=False,
                tooltip=tooltip,
            )
            resultado.append((boton, tipo_icono))
            x_actual += w + gap
        return resultado

    def _crear_botones_pausa(self) -> None:
        en_partida = self._en_partida()
        etiquetas = [
            etiqueta_menu(*(BTN_CONTINUAR_PARTIDA if en_partida else BTN_CONTINUAR)),
            etiqueta_menu(*BTN_PANTALLA_TITULO),
            etiqueta_menu(*BTN_SALIR_PROGRAMA),
        ]
        acciones = [
            self._continuar_desde_pausa,
            self._pantalla_titulo_desde_pausa,
            self._salir,
        ]
        rects = rects_botones_apilados(
            etiquetas,
            self.fuentes["menu"],
            x_centro=ANCHO // 2,
            y0=290,
            gap=12,
            ancho_min=420,
            alto_min=48,
        )
        tip_cont, tip_titulo, tip_salir = tooltips_menu_pausa(en_partida=en_partida)
        self._botones_pausa = [
            Boton(etiq, rect, accion, tooltip=tip)
            for etiq, rect, accion, tip in zip(
                etiquetas,
                rects,
                acciones,
                (tip_cont, tip_titulo, tip_salir),
                strict=True,
            )
        ]

    def _abrir_menu_pausa(self) -> None:
        self._menu_pausa_abierto = True
        self._crear_botones_pausa()

    def _cerrar_menu_pausa(self) -> None:
        self._menu_pausa_abierto = False

    def _continuar_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._restaurar_vista_actual()

    def _pantalla_titulo_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._ir_a_menu_principal()

    def _toggle_pausa(self) -> None:
        if self._menu_pausa_abierto:
            self._continuar_desde_pausa()
            return
        self._abrir_menu_pausa()

    def _abrir_feedback(self) -> None:
        if self._menu_pausa_abierto:
            return
        if isinstance(self.actual, PantallaFeedback):
            return
        self._anterior = self.actual

        def volver() -> None:
            pantalla_previa = self._anterior
            self._anterior = None
            if pantalla_previa is None:
                return
            self.actual = pantalla_previa
            pantalla_previa.restaurar_vista_completa()

        self.actual = PantallaFeedback(volver)

    def _manejar_hover_fijos(self, pos: tuple[int, int]) -> None:
        for b, _tipo in self._botones_fijos:
            b.actualizar_hover(pos)

    def _manejar_clic_fijos(self, pos: tuple[int, int], boton: int) -> bool:
        for b, tipo in self._botones_fijos:
            if not b.manejar_clic(pos, boton):
                continue
            if tipo == "feedback" and isinstance(self.actual, PantallaFeedback):
                return True
            return True
        return False

    def _manejar_eventos_pausa(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.MOUSEMOTION:
            self._manejar_hover_fijos(evento.pos)
            for boton in self._botones_pausa:
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_fijos(evento.pos, evento.button):
                return
            for boton in self._botones_pausa:
                if boton.manejar_clic(evento.pos, evento.button):
                    break

    def _dibujar_pantalla_actual(self) -> None:
        self.actual.dibujar(self.pantalla)

    def ejecutar(self) -> None:
        while self.ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.ejecutando = False
                    break

                if self._menu_pausa_abierto:
                    self._manejar_eventos_pausa(evento)
                    continue

                if evento.type == pygame.MOUSEMOTION:
                    self._manejar_hover_fijos(evento.pos)
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if self._manejar_clic_fijos(evento.pos, evento.button):
                        continue

                nueva = self.actual.manejar_evento(evento)
                if nueva is not None:
                    self.actual = nueva

            if not self._menu_pausa_abierto:
                cambio = self.actual.actualizar()
                if cambio is not None:
                    self.actual = cambio

            self._dibujar_pantalla_actual()

            for b, tipo in self._botones_fijos:
                b.dibujar(self.pantalla, self.fuentes["menu"])
                self._dibujar_icono_fijo(tipo, b.rect)

            if self._menu_pausa_abierto:
                self._dibujar_menu_pausa()

            dibujar_tooltips_botones(
                self.pantalla,
                self.fuentes["pequena"],
                [b for b, _tipo in self._botones_fijos],
            )

            pygame.display.flip()
            self.reloj.tick(FPS)
        pygame.quit()

    def _dibujar_icono_fijo(self, tipo: str, rect: pygame.Rect) -> None:
        color = (25, 25, 30)
        if tipo == "pausa":
            bar_w = max(3, rect.width // 8)
            bar_h = rect.height // 2
            cx = rect.centerx
            y = rect.centery - bar_h // 2
            pygame.draw.rect(
                self.pantalla,
                color,
                pygame.Rect(cx - bar_w - 3, y, bar_w, bar_h),
                border_radius=2,
            )
            pygame.draw.rect(
                self.pantalla,
                color,
                pygame.Rect(cx + 3, y, bar_w, bar_h),
                border_radius=2,
            )
        else:
            chip = rect.inflate(-4, -4)
            pygame.draw.rect(self.pantalla, (248, 252, 255), chip, border_radius=6)
            fuente = self.fuentes.get("icono_emoji") or self.fuentes["menu"]
            texto = emoji_icono("feedback")
            try:
                surf = fuente.render(texto, True, (25, 25, 30))
                if surf.get_width() > 4:
                    self.pantalla.blit(
                        surf,
                        surf.get_rect(center=rect.center),
                    )
                    return
            except Exception:
                pass
            margin = max(4, rect.width // 10)
            envelope = pygame.Rect(
                rect.x + margin,
                rect.y + margin,
                rect.width - 2 * margin,
                rect.height - 2 * margin,
            )
            pygame.draw.rect(self.pantalla, color, envelope, width=2, border_radius=3)
            pygame.draw.line(
                self.pantalla,
                color,
                (envelope.left + 2, envelope.top + 2),
                (envelope.centerx, envelope.centery + 1),
                2,
            )
            pygame.draw.line(
                self.pantalla,
                color,
                (envelope.right - 2, envelope.top + 2),
                (envelope.centerx, envelope.centery + 1),
                2,
            )

    def _dibujar_menu_pausa(self) -> None:
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.pantalla.blit(overlay, (0, 0))

        panel = pygame.Rect(MARGEN + 40, 150, ANCHO - 2 * (MARGEN + 40), 380)
        dibujar_panel(self.pantalla, panel, color=(255, 255, 255))

        dibujar_texto_centro(
            self.pantalla,
            "PAUSA",
            (ANCHO // 2, panel.y + 50),
            self.fuentes["titulo"].get_height(),
            (25, 25, 30),
            bold=True,
        )

        dibujar_texto_centro(
            self.pantalla,
            f"Estás en: {self._pantalla_en_contexto().titulo_pausa()}",
            (ANCHO // 2, panel.y + 100),
            self.fuentes["cuerpo"].get_height(),
            (70, 80, 95),
        )

        for boton in self._botones_pausa:
            boton.dibujar(self.pantalla, self.fuentes["menu"])
        dibujar_tooltips_botones(
            self.pantalla, self.fuentes["pequena"], self._botones_pausa
        )
