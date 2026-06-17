#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hover de tooltips: valor central vs flechas, navegación y menú pausa."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_JUEGO = _ROOT / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))


def _evento_motion(pos: tuple[int, int]):
    import pygame

    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos})


class TestHoverTooltipsGrafico(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from Tests.Juego.helpers_navegacion_grafico import configurar_pygame_tests

        configurar_pygame_tests()

    @classmethod
    def tearDownClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        invalidar_cache_fuentes()
        if pygame.get_init():
            pygame.quit()

    def setUp(self) -> None:
        from Grafico.app import AplicacionGrafica, DatosJuego

        self.datos = DatosJuego(10, 2, [], {}, Path("."), Path("."))
        self.app = AplicacionGrafica(self.datos)
        self.ir_a = MagicMock()
        self.salir = MagicMock()

    def test_pausa_botones_llevan_tooltip(self) -> None:
        from Grafico.tooltips_ui import (
            TOOLTIP_PAUSA_SALIR,
            TOOLTIP_PAUSA_TITULO,
            tooltips_menu_pausa,
        )

        self.app._crear_botones_pausa()
        esperados = tooltips_menu_pausa(en_partida=False)
        for boton, tip in zip(self.app._botones_pausa, esperados, strict=True):
            self.assertEqual(boton.tooltip, tip)
        self.assertEqual(esperados[1], TOOLTIP_PAUSA_TITULO)
        self.assertEqual(esperados[2], TOOLTIP_PAUSA_SALIR)

    def test_pausa_en_partida_texto_continuar_distinto(self) -> None:
        from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion
        from Grafico.pantallas import PartidaModoLibre
        from Grafico.tooltips_ui import TOOLTIP_PAUSA_CONTINUAR_PARTIDA
        from Tests.Juego.helpers_navegacion_grafico import pregunta_minima

        p = pregunta_minima()
        reglas = ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
            correccion_al_final=False,
        )
        self.app.actual = PartidaModoLibre(
            nombre="Test",
            preguntas=[p],
            reglas=reglas,
            ir_a=self.ir_a,
            datos=self.datos,
            salir_app=self.salir,
            total_previsto=1,
        )
        self.app._crear_botones_pausa()
        self.assertEqual(
            self.app._botones_pausa[0].tooltip,
            TOOLTIP_PAUSA_CONTINUAR_PARTIDA,
        )

    def test_libre_flechas_sin_tooltip_valor_con_hover(self) -> None:
        from Grafico.pantallas_libre import ConfigOpcionesLibre
        from Grafico.tooltips_ui import TOOLTIP_ATRAS, TOOLTIP_SIGUIENTE

        pantalla = ConfigOpcionesLibre(self.datos, self.ir_a, self.salir)
        self.assertEqual(pantalla.boton_siguiente.tooltip, TOOLTIP_SIGUIENTE)
        self.assertEqual(pantalla.boton_atras.tooltip, TOOLTIP_ATRAS)

        izq, der = pantalla.botones_ciclo["banco"]
        self.assertIsNone(izq.tooltip)
        self.assertIsNone(der.tooltip)

        _, rect_val, _ = pantalla._rects_control_fila("banco")
        rect_izq, _, _ = pantalla._rects_control_fila("banco")

        pantalla.manejar_evento(_evento_motion(rect_val.center))
        self.assertEqual(pantalla._hover_opcion_valor, "banco")

        pantalla.manejar_evento(_evento_motion(rect_izq.center))
        self.assertIsNone(pantalla._hover_opcion_valor)

    def test_libre_vidas_sin_tooltip_en_valor(self) -> None:
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        pantalla = ConfigOpcionesLibre(self.datos, self.ir_a, self.salir)
        _, rect_val, _ = pantalla._rects_control_fila("vidas")
        pantalla.manejar_evento(_evento_motion(rect_val.center))
        self.assertIsNone(pantalla._hover_opcion_valor)

    def test_historia_config_hover_valor_y_navegacion(self) -> None:
        from Comun.presets_historia import cargar_presets_historia
        from Comun.rutas import resolver_presets_historia
        from Grafico.pantallas_historia import ConfigModoHistoria, ConfigOpcionesHistoria
        from Grafico.tooltips_ui import TOOLTIP_ATRAS, TOOLTIP_CONTINUAR, TOOLTIP_EMPEZAR

        presets = cargar_presets_historia(resolver_presets_historia())
        preset = next(p for p in presets if p.id == "simulacro_examen")

        carrusel = ConfigModoHistoria(self.datos, self.ir_a, self.salir)
        self.assertEqual(carrusel.boton_empezar.tooltip, TOOLTIP_CONTINUAR)

        config = ConfigOpcionesHistoria(
            self.datos,
            preset,
            "Test",
            self.ir_a,
            self.salir,
            volver=lambda _c: None,
        )
        self.assertEqual(config.boton_empezar.tooltip, TOOLTIP_EMPEZAR)
        self.assertEqual(config.boton_atras.tooltip, TOOLTIP_ATRAS)

        op_id = "estrategia_materias"
        self.assertIn(op_id, config.botones_ciclo)
        izq, der = config.botones_ciclo[op_id]
        self.assertIsNone(izq.tooltip)
        self.assertIsNone(der.tooltip)

        _, rect_val, _ = config._rects_control_fila(op_id)
        config.manejar_evento(_evento_motion(rect_val.center))
        self.assertEqual(config._hover_opcion_valor, op_id)

        config.manejar_evento(_evento_motion(der.rect.center))
        self.assertIsNone(config._hover_opcion_valor)


if __name__ == "__main__":
    unittest.main()
