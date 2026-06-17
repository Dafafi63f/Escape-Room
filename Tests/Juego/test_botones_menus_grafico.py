#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Botones de menús gráficos: rects válidos y clics en el centro."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parents[2]
_JUEGO = _ROOT / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))


def _evento_clic(centro: tuple[int, int]):
    import pygame

    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": centro, "button": 1})


class TestBotonesMenusGrafico(unittest.TestCase):
    def setUp(self) -> None:
        import pygame

        if pygame.get_init():
            pygame.quit()
        pygame.init()
        pygame.display.set_mode((960, 720))
        from Grafico.fuentes import invalidar_cache_fuentes

        invalidar_cache_fuentes()

        from Grafico.app import AplicacionGrafica, DatosJuego

        self.datos = DatosJuego(10, 2, [], {}, Path("."), Path("."))
        self.app = AplicacionGrafica(self.datos)
        self.ir_a = MagicMock()
        self.salir = MagicMock()

    def _assert_botones_validos(self, nombre: str, botones: list) -> None:
        from Grafico.tema import ALTO, ANCHO

        for i, boton in enumerate(botones):
            with self.subTest(pantalla=nombre, boton=i, etiqueta=boton.etiqueta[:24]):
                rect = boton.rect
                self.assertGreater(rect.width, 0)
                self.assertGreater(rect.height, 0)
                self.assertLessEqual(rect.bottom, ALTO, msg=str(rect))
                self.assertGreaterEqual(rect.left, 0, msg=str(rect))
                self.assertLessEqual(rect.right, ANCHO, msg=str(rect))
                if boton.activo:
                    self.assertTrue(
                        rect.collidepoint(rect.center),
                        msg=f"centro {rect.center} fuera de {rect}",
                    )

    def _assert_clic_activo(self, boton, pulsado: list[bool]) -> None:
        if not boton.activo:
            return
        boton.al_pulsar = lambda b=boton: pulsado.append(b.etiqueta)
        self.assertTrue(boton.manejar_clic(boton.rect.center, 1))
        self.assertTrue(pulsado, msg=boton.etiqueta)

    def test_menu_principal(self) -> None:
        from Grafico.pantallas import MenuPrincipal

        pantalla = MenuPrincipal(
            self.datos, self.ir_a, self.salir, self.app._abrir_feedback
        )
        self._assert_botones_validos("MenuPrincipal", pantalla.botones)

    def test_pausa_y_barra_fija(self) -> None:
        self.app._crear_botones_pausa()
        self._assert_botones_validos("Pausa", self.app._botones_pausa)
        fijos = [b for b, _ in self.app._botones_fijos]
        self._assert_botones_validos("BarraFija", fijos)

    def test_feedback(self) -> None:
        from Grafico.pantallas import PantallaFeedback

        pantalla = PantallaFeedback(lambda: None)
        self._assert_botones_validos("Feedback", [pantalla.boton_volver])

    def test_modo_libre_paso1(self) -> None:
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        pantalla = ConfigOpcionesLibre(
            self.datos, self.ir_a, self.salir, nombre_inicial="Test"
        )
        self._assert_botones_validos("LibreP1", pantalla._botones_ui())
        pantalla._toggle_dificultad_progresiva()
        self._assert_botones_validos("LibreP1Dif", pantalla._botones_ui())

    def test_modo_libre_paso2(self) -> None:
        from Comun.modelos import BancoPreguntas
        from Comun.reglas_partida import SistemaPuntuacion
        from Grafico.pantallas_libre import (
            ConfigFiltrosLibre,
            EstadoConfigLibrePaso1,
            _construir_reglas_paso1,
        )

        reglas = _construir_reglas_paso1(
            modo_infinito=False,
            total_elegido=10,
            sin_vidas=False,
            vidas_count=3,
            modo_tiempo="ninguno",
            tiempo_pregunta=90,
            tiempo_total=600,
            sistema_elegido=SistemaPuntuacion.ARCADE,
        )
        estado = EstadoConfigLibrePaso1(
            "Test",
            BancoPreguntas.DATASET,
            False,
            10,
            False,
            3,
            "ninguno",
            90,
            600,
            SistemaPuntuacion.ARCADE,
            reglas,
        )
        pantalla = ConfigFiltrosLibre(self.datos, self.ir_a, self.salir, estado)
        self._assert_botones_validos("LibreP2", pantalla._botones_ui())
        self._assert_botones_validos("LibreP2Dif", pantalla._botones_ui())

    def test_modo_historia_menus(self) -> None:
        from Grafico.pantallas_historia import (
            ConfigModoHistoria,
            ConfigOpcionesHistoria,
            RankingResistenciaHistoria,
        )

        carrusel = ConfigModoHistoria(self.datos, self.ir_a, self.salir)
        self._assert_botones_validos("HistoriaCarrusel", carrusel._botones_ui())

        pulsado: list[str] = []
        for boton in carrusel._botones_ui():
            self._assert_clic_activo(boton, pulsado)
        self.assertIn(carrusel.boton_volver.etiqueta, pulsado)

        if carrusel.presets:
            opciones = ConfigOpcionesHistoria(
                self.datos,
                carrusel.presets[0],
                "Test",
                self.ir_a,
                self.salir,
                lambda _cfg: None,
            )
            self._assert_botones_validos("HistoriaOpciones", opciones._botones_ui())

        ranking = RankingResistenciaHistoria(self.datos, self.ir_a, self.salir)
        self._assert_botones_validos("Ranking", [ranking.boton_volver])

    def test_manejar_evento_clic_navegacion_libre(self) -> None:
        import pygame

        from Grafico.pantallas_libre import ConfigOpcionesLibre

        pantalla = ConfigOpcionesLibre(
            self.datos, self.ir_a, self.salir, nombre_inicial="Test"
        )
        pulsado: list[bool] = []
        pantalla.boton_atras.al_pulsar = lambda: pulsado.append(True)
        pantalla.manejar_evento(_evento_clic(pantalla.boton_atras.rect.center))
        self.assertEqual(pulsado, [True])

        pantalla.manejar_evento(
            pygame.event.Event(pygame.MOUSEMOTION, {"pos": pantalla.boton_siguiente.rect.center})
        )
        self.assertTrue(pantalla.boton_siguiente.hover)


if __name__ == "__main__":
    unittest.main()
