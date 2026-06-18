#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bucle principal pygame y enrutador de pantallas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import math
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
from Grafico.tema import (
    ALTO,
    ANCHO,
    FPS,
    GAP_ICONOS_FIJOS,
    MARGEN,
    TITULO_VENTANA,
    X_ICONOS_FIJOS,
    Y_ICONOS_FIJOS,
    alto_icono_fijo,
    ancho_icono_fijo,
    crear_fuentes,
)
from Grafico.ui import Boton, dibujar_panel, dibujar_tooltips_botones, dibujar_overlay_atenuacion, rects_botones_apilados
from Grafico.tooltips_ui import (
    TOOLTIP_DIARIOS,
    TOOLTIP_FEEDBACK,
    TOOLTIP_OPCIONES,
    TOOLTIP_PAUSA,
    TOOLTIP_RANKING,
    tooltips_menu_pausa,
)
from Grafico.menu_opciones import OverlayOpcionesGrafico
from Comun.ranking_resistencia import finalizar_ranking_al_salir, inicializar_ranking_sesion
from Comun.preferencias_grafico import debe_saltar_bienvenida_grafico
from Grafico.pantallas import MenuPrincipal, Pantalla, PantallaFeedback, PartidaModoLibre
from Grafico.pantallas_bienvenida import PantallaBienvenida
from Grafico.pantallas_historia import PartidaModoHistoria, PartidaResistenciaHistoria

_ETIQUETA_ICONO_FIJO_SIN_EMOJI: dict[str, str] = {
    "pausa": "PA",
    "diarios": "DI",
    "ranking": "RK",
    "feedback": "FB",
    "opciones": "OP",
}


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

    def __init__(self, datos: DatosJuego, *, saltar_bienvenida: bool = False) -> None:
        inicializar_ranking_sesion()
        pygame.init()
        pygame.display.set_caption(TITULO_VENTANA)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.datos = datos
        datos.abrir_feedback = self._abrir_feedback
        self.fuentes = crear_fuentes()
        self.ejecutando = True
        if saltar_bienvenida or debe_saltar_bienvenida_grafico():
            self.actual: Pantalla = MenuPrincipal(datos, self._ir_a, self._salir)
        else:
            self.actual = PantallaBienvenida(datos, self._ir_a, self._salir)
        self._menu_pausa_abierto = False
        self._menu_opciones_abierto = False
        self._overlay_opciones: OverlayOpcionesGrafico | None = None
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
        botones_cfg: list[tuple[str, Callable[[], None], str, str]] = [
            ("II", self._toggle_pausa, "pausa", TOOLTIP_PAUSA),
            ("DI", self._abrir_diarios, "diarios", TOOLTIP_DIARIOS),
            ("RK", self._abrir_ranking, "ranking", TOOLTIP_RANKING),
            ("FB", self._abrir_feedback, "feedback", TOOLTIP_FEEDBACK),
            ("OP", self._toggle_opciones, "opciones", TOOLTIP_OPCIONES),
        ]

        fuente_ref = self.fuentes["menu"]
        w = ancho_icono_fijo(fuente_ref)
        h = alto_icono_fijo(fuente_ref)
        resultado: list[tuple[Boton, str]] = []
        x_actual = X_ICONOS_FIJOS
        for _etiqueta_ref, handler, tipo_icono, tooltip in botones_cfg:
            boton = Boton(
                "",
                pygame.Rect(x_actual, Y_ICONOS_FIJOS, w, h),
                handler,
                mostrar_texto=False,
                tooltip=tooltip,
            )
            resultado.append((boton, tipo_icono))
            x_actual += w + GAP_ICONOS_FIJOS
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

    def _overlay_abierto(self) -> bool:
        return self._menu_pausa_abierto or self._menu_opciones_abierto

    def _barra_fija_bloqueada(self) -> bool:
        """Popups modales: bienvenida, pausa, opciones y avisos en partida."""
        return self._overlay_abierto() or self.actual.popup_bloqueante()

    def _reset_hover_barra_fija(self) -> None:
        for boton, _tipo in self._botones_fijos:
            boton.hover = False

    def _abrir_menu_opciones(self) -> None:
        if self._menu_pausa_abierto:
            return
        self._menu_opciones_abierto = True
        self._overlay_opciones = OverlayOpcionesGrafico(on_cerrar=self._cerrar_menu_opciones)

    def _cerrar_menu_opciones(self) -> None:
        self._menu_opciones_abierto = False
        self._overlay_opciones = None
        self._refrescar_tras_opciones()

    def _refrescar_tras_opciones(self) -> None:
        from Grafico.pantallas import MenuPrincipal

        pantalla = self.actual
        if isinstance(pantalla, MenuPrincipal):
            self.actual = MenuPrincipal(self.datos, self._ir_a, self._salir)
        elif hasattr(pantalla, "_pantalla_actual"):
            self.actual = pantalla._pantalla_actual()
        else:
            self._restaurar_vista_actual()

    def _toggle_opciones(self) -> None:
        if self._menu_opciones_abierto:
            if self._overlay_opciones is not None:
                self._overlay_opciones.guardar_y_cerrar()
            else:
                self._cerrar_menu_opciones()
            return
        if self._menu_pausa_abierto:
            return
        self._abrir_menu_opciones()

    def _abrir_menu_pausa(self) -> None:
        if self._menu_opciones_abierto:
            return
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
        if self._overlay_abierto():
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

    def _abrir_diarios(self) -> None:
        if self._overlay_abierto():
            return
        from Grafico.pantallas_diarios import ConfigModosDiarios

        if isinstance(self.actual, ConfigModosDiarios):
            return
        self._ir_a(ConfigModosDiarios(self.datos, self._ir_a, self._salir))

    def _preset_ranking_desde_pantalla(self, pantalla: Pantalla) -> str | None:
        from Comun.modos_diarios import ID_PRESET_RETO_DIA
        from Grafico.pantallas_diarios import ConfigModosDiarios
        from Grafico.pantallas_especiales import ConfigModosEspeciales
        from Grafico.pantallas_historia import ResumenResistenciaHistoria

        if isinstance(pantalla, ResumenResistenciaHistoria):
            return pantalla.preset.id
        if isinstance(pantalla, ConfigModosDiarios):
            return ID_PRESET_RETO_DIA
        if isinstance(pantalla, ConfigModosEspeciales):
            return "ranking_resistencia"
        return None

    def _abrir_ranking(self) -> None:
        if self._overlay_abierto():
            return
        from Grafico.pantallas_historia import RankingResistenciaHistoria

        if isinstance(self.actual, RankingResistenciaHistoria):
            return

        pantalla_previa = self.actual
        preset_id = self._preset_ranking_desde_pantalla(pantalla_previa)

        def volver() -> None:
            self.actual = pantalla_previa
            pantalla_previa.restaurar_vista_completa()

        self._ir_a(
            RankingResistenciaHistoria(
                self.datos,
                self._ir_a,
                self._salir,
                volver_a=volver,
                preset_id_inicial=preset_id,
            )
        )

    def _manejar_hover_fijos(self, pos: tuple[int, int]) -> None:
        if self._barra_fija_bloqueada():
            self._reset_hover_barra_fija()
            return
        for b, _tipo in self._botones_fijos:
            b.actualizar_hover(pos)

    def _manejar_clic_fijos(self, pos: tuple[int, int], boton: int) -> bool:
        if self._barra_fija_bloqueada():
            return False
        for b, tipo in self._botones_fijos:
            if not b.manejar_clic(pos, boton):
                continue
            if tipo == "feedback" and isinstance(self.actual, PantallaFeedback):
                return True
            if tipo == "diarios":
                from Grafico.pantallas_diarios import ConfigModosDiarios

                if isinstance(self.actual, ConfigModosDiarios):
                    return True
            if tipo == "ranking":
                from Grafico.pantallas_historia import RankingResistenciaHistoria

                if isinstance(self.actual, RankingResistenciaHistoria):
                    return True
            return True
        return False

    def _manejar_eventos_overlay(self, evento: pygame.event.Event) -> None:
        if self._menu_opciones_abierto and self._overlay_opciones is not None:
            self._overlay_opciones.manejar_evento(evento)
            return
        if self._menu_pausa_abierto:
            if evento.type == pygame.MOUSEMOTION:
                for boton in self._botones_pausa:
                    boton.actualizar_hover(evento.pos)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                for boton in self._botones_pausa:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break

    def _manejar_eventos_pausa(self, evento: pygame.event.Event) -> None:
        self._manejar_eventos_overlay(evento)

    def _dibujar_pantalla_actual(self) -> None:
        self.actual.dibujar(self.pantalla)

    def ejecutar(self) -> None:
        while self.ejecutando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.ejecutando = False
                    break

                if self._overlay_abierto():
                    self._manejar_eventos_overlay(evento)
                    continue

                if evento.type == pygame.MOUSEMOTION:
                    self._manejar_hover_fijos(evento.pos)
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if self._manejar_clic_fijos(evento.pos, evento.button):
                        continue

                nueva = self.actual.manejar_evento(evento)
                if nueva is not None:
                    self.actual = nueva

            if not self._overlay_abierto():
                cambio = self.actual.actualizar()
                if cambio is not None:
                    self.actual = cambio

            self._dibujar_pantalla_actual()

            for b, tipo in self._botones_fijos:
                b.dibujar(self.pantalla, self.fuentes["menu"])
                self._dibujar_icono_fijo(tipo, b.rect)

            if self._barra_fija_bloqueada():
                dibujar_overlay_atenuacion(self.pantalla)

            if self._menu_pausa_abierto:
                self._dibujar_contenido_menu_pausa()
            elif self._menu_opciones_abierto and self._overlay_opciones is not None:
                self._overlay_opciones.dibujar_contenido(self.pantalla)
            elif self.actual.popup_bloqueante():
                self.actual.dibujar_contenido_popup_bloqueante(self.pantalla)

            if not self._barra_fija_bloqueada():
                dibujar_tooltips_botones(
                    self.pantalla,
                    self.fuentes["pequena"],
                    [b for b, _tipo in self._botones_fijos],
                )

            pygame.display.flip()
            self.reloj.tick(FPS)
        finalizar_ranking_al_salir()
        pygame.quit()

    def _dibujar_icono_fijo(self, tipo: str, rect: pygame.Rect) -> None:
        color = (25, 25, 30)
        chip = rect.inflate(-4, -4)
        pygame.draw.rect(self.pantalla, (248, 252, 255), chip, border_radius=6)
        fuente = self.fuentes.get("icono_emoji") or self.fuentes["menu"]
        texto = emoji_icono(tipo) or _ETIQUETA_ICONO_FIJO_SIN_EMOJI.get(tipo, "")
        try:
            surf = fuente.render(texto, True, color)
            if surf.get_width() > 4:
                self.pantalla.blit(surf, surf.get_rect(center=rect.center))
                return
        except Exception:
            pass
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
            return
        if tipo == "opciones":
            cx, cy = rect.center
            r = max(6, min(rect.width, rect.height) // 4)
            pygame.draw.circle(self.pantalla, color, (cx, cy), r, width=2)
            for i in range(8):
                ang = i * math.pi / 4
                x1 = cx + int((r + 2) * math.cos(ang))
                y1 = cy + int((r + 2) * math.sin(ang))
                pygame.draw.circle(self.pantalla, color, (x1, y1), 2)
            return
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

    def _dibujar_contenido_menu_pausa(self) -> None:
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
