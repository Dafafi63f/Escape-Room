#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bucle principal pygame y enrutador de pantallas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pygame

from Comun.modelos import Pregunta
from Grafico.tema import ALTO, ANCHO, FPS, MARGEN, TITULO_VENTANA, crear_fuentes
from Grafico.ui import Boton, dibujar_panel
from Grafico.pantallas import MenuPrincipal, Pantalla, PantallaFeedback, PartidaModoLibre


@dataclass
class DatosJuego:
    num_preguntas: int
    num_materias: int
    preguntas: list[Pregunta]
    materias_meta: dict[str, dict[str, str]]
    path_preguntas_csv: Path
    path_plantillas_json: Path


class AplicacionGrafica:
    """Ventana pygame con menú y modos jugables."""

    def __init__(self, datos: DatosJuego) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO_VENTANA)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.datos = datos
        self.fuentes = crear_fuentes()
        self.ejecutando = True
        self.actual: Pantalla = MenuPrincipal(datos, self._ir_a, self._salir)
        self._menu_pausa_abierto = False
        self._vista_solo_titulo = False
        self._vista_solo_titulo_antes_pausa = False
        self._anterior: Pantalla | None = None
        self._botones_fijos = self._crear_botones_fijos()
        self._botones_pausa: list[Boton] = []

    def _ir_a(self, pantalla: Pantalla) -> None:
        self.actual = pantalla
        self._vista_solo_titulo = False

    def _salir(self) -> None:
        self.ejecutando = False

    def _en_partida(self) -> bool:
        return isinstance(self.actual, PartidaModoLibre)

    def _crear_botones_fijos(self) -> list[tuple[Boton, str]]:
        x, y = 16, 14
        gap = 10
        padding_x = 10
        padding_y = 6

        botones_cfg: list[tuple[str, Callable[[], None], str]] = [
            ("II", self._toggle_pausa, "pausa"),
            ("FB", self._abrir_feedback, "feedback"),
        ]

        resultado: list[tuple[Boton, str]] = []
        x_actual = x
        fuente_ref = self.fuentes["menu"]
        ancho_ref = max(fuente_ref.size(etiqueta)[0] for etiqueta, _handler, _tipo in botones_cfg)
        alto_ref = max(fuente_ref.size(etiqueta)[1] for etiqueta, _handler, _tipo in botones_cfg)
        w = max(40, ancho_ref + 2 * padding_x)
        h = max(30, alto_ref + 2 * padding_y)
        for _etiqueta_ref, handler, tipo_icono in botones_cfg:
            boton = Boton(
                "",
                pygame.Rect(x_actual, y, w, h),
                handler,
                mostrar_texto=False,
            )
            resultado.append((boton, tipo_icono))
            x_actual += w + gap
        return resultado

    def _crear_botones_pausa(self) -> None:
        en_partida = self._en_partida()
        etiquetas = [
            "Continuar la partida" if en_partida else "Continuar",
            "Pantalla de título",
            "Salir del programa",
        ]
        acciones = [
            self._continuar_desde_pausa,
            self._pantalla_titulo_desde_pausa,
            self._salir,
        ]
        ancho, alto = 420, 48
        x = (ANCHO - ancho) // 2
        y0 = 290
        self._botones_pausa = [
            Boton(
                etiqueta,
                pygame.Rect(x, y0 + i * (alto + 12), ancho, alto),
                accion,
            )
            for i, (etiqueta, accion) in enumerate(zip(etiquetas, acciones, strict=True))
        ]

    def _abrir_menu_pausa(self) -> None:
        self._vista_solo_titulo_antes_pausa = self._vista_solo_titulo
        self._vista_solo_titulo = False
        self._menu_pausa_abierto = True
        self._crear_botones_pausa()

    def _cerrar_menu_pausa(self) -> None:
        self._menu_pausa_abierto = False

    def _continuar_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._vista_solo_titulo = self._vista_solo_titulo_antes_pausa

    def _pantalla_titulo_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._vista_solo_titulo = True

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
        self._vista_solo_titulo = False
        self._anterior = self.actual

        def volver() -> None:
            if self._anterior is not None:
                self.actual = self._anterior
            self._anterior = None

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
        if self._vista_solo_titulo:
            if isinstance(self.actual, PantallaFeedback) and self._anterior is not None:
                self._anterior.dibujar_cabecera(self.pantalla)
            else:
                self.actual.dibujar_cabecera(self.pantalla)
        else:
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

        titulo = self.fuentes["titulo"].render("PAUSA", True, (25, 25, 30))
        self.pantalla.blit(titulo, titulo.get_rect(center=(ANCHO // 2, panel.y + 50)))

        contexto = self.fuentes["cuerpo"].render(
            f"Estás en: {self.actual.titulo_pausa()}",
            True,
            (70, 80, 95),
        )
        self.pantalla.blit(contexto, contexto.get_rect(center=(ANCHO // 2, panel.y + 100)))

        for boton in self._botones_pausa:
            boton.dibujar(self.pantalla, self.fuentes["menu"])

        ayuda = self.fuentes["pie"].render(
            "Usa el ratón: Continuar / Título / Salir",
            True,
            (90, 100, 115),
        )
        self.pantalla.blit(ayuda, ayuda.get_rect(center=(ANCHO // 2, panel.bottom - 28)))
