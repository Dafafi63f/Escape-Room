#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_JUEGO = _ROOT / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))


class TestAppPausaGrafico(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import pygame

        pygame.init()
        pygame.display.set_mode((800, 600))

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

    def test_continuar_cierra_pausa(self) -> None:
        self.app._abrir_menu_pausa()
        self.app._continuar_desde_pausa()
        self.assertFalse(self.app._menu_pausa_abierto)

    def test_pausa_tres_opciones(self) -> None:
        self.app._crear_botones_pausa()
        self.assertEqual(len(self.app._botones_pausa), 3)
        self.assertTrue(all(b.tooltip for b in self.app._botones_pausa))

    def test_pantalla_titulo_vuelve_al_menu_principal(self) -> None:
        from Grafico.pantallas import MenuPrincipal
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.app.actual = ConfigOpcionesLibre(
            self.datos, self.app._ir_a, self.app._salir
        )
        self.app._pantalla_titulo_desde_pausa()
        self.assertIsInstance(self.app.actual, MenuPrincipal)

    def test_pantalla_titulo_desde_menu_sigue_en_menu(self) -> None:
        from Grafico.pantallas import MenuPrincipal

        self.app._pantalla_titulo_desde_pausa()
        self.assertIsInstance(self.app.actual, MenuPrincipal)

    def test_feedback_abre_y_volver_restaura(self) -> None:
        from Grafico.pantallas import MenuPrincipal, PantallaFeedback
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.app.actual = ConfigOpcionesLibre(
            self.datos, self.app._ir_a, self.app._salir
        )
        self.app._abrir_feedback()
        self.assertIsInstance(self.app.actual, PantallaFeedback)
        self.app.actual.volver()
        self.assertIsInstance(self.app.actual, ConfigOpcionesLibre)


if __name__ == "__main__":
    unittest.main()
