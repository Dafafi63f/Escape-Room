#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flujos de menús gráficos: secuencias de botones y pantalla resultante."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_JUEGO = _ROOT / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Tests.Juego.helpers_navegacion_grafico import (
    SecuenciaNavegacion,
    configurar_pygame_tests,
    datos_prueba,
    pregunta_minima,
)


class TestFlujosMenusGrafico(unittest.TestCase):
    def setUp(self) -> None:
        configurar_pygame_tests()
        from Grafico.app import AplicacionGrafica

        self.datos = datos_prueba()
        self.app = AplicacionGrafica(self.datos)
        self.nav = SecuenciaNavegacion(self.app)

    def test_menu_libre_atras_menu(self) -> None:
        """Menú → Modo libre → Atrás → Menú."""
        from Grafico.pantallas import MenuPrincipal
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.nav.ejecutar(
            [
                ("Modo libre", lambda n: n.pulsar_menu("libre"), (ConfigOpcionesLibre,)),
                ("Atrás", lambda n: n.pulsar_texto("Atrás"), (MenuPrincipal,)),
            ]
        )

    def test_menu_historia_volver_menu(self) -> None:
        """Menú → Modo historia → Volver al menú → Menú."""
        from Grafico.pantallas import MenuPrincipal
        from Grafico.pantallas_historia import ConfigModoHistoria

        self.nav.ejecutar(
            [
                ("Modo historia", lambda n: n.pulsar_menu("historia"), (ConfigModoHistoria,)),
                (
                    "Volver al menú",
                    lambda n: n.pulsar_texto("Volver al menú"),
                    (MenuPrincipal,),
                ),
            ]
        )

    def test_libre_paso1_paso2_y_volver(self) -> None:
        """Menú → Libre (paso 1) → Siguiente → paso 2 → Atrás → paso 1."""
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        self.nav.ejecutar(
            [
                ("Modo libre", lambda n: n.pulsar_menu("libre"), (ConfigOpcionesLibre,)),
                (
                    "Nombre + Siguiente",
                    lambda n: (
                        n.establecer_nombre("Ana"),
                        n.pulsar_texto("Siguiente"),
                    ),
                    (ConfigFiltrosLibre,),
                ),
                ("Atrás al paso 1", lambda n: n.pulsar_texto("Atrás"), (ConfigOpcionesLibre,)),
            ]
        )
        self.assertEqual(self.nav.pantalla.campo_nombre.valor(), "Ana")

    def test_libre_sin_nombre_usa_anonimo(self) -> None:
        """Siguiente sin nombre rellena «Anonimo» y pasa al paso 2."""
        from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        self.nav.pulsar_menu("libre")
        self.nav.comprobar(ConfigOpcionesLibre)
        self.nav.pantalla.campo_nombre.texto = ""
        self.nav.pulsar_texto("Siguiente")
        self.nav.comprobar(ConfigFiltrosLibre)
        self.assertEqual(self.nav.pantalla.estado.nombre, NOMBRE_JUGADOR_DEFECTO)

    def test_libre_empezar_partida(self) -> None:
        """Menú → paso 1 → paso 2 → Empezar partida → partida."""
        from Grafico.pantallas import PartidaModoLibre
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        datos = datos_prueba(preguntas=[pregunta_minima()])
        from Grafico.app import AplicacionGrafica

        self.app = AplicacionGrafica(datos)
        self.nav = SecuenciaNavegacion(self.app)

        self.nav.ejecutar(
            [
                ("Modo libre", lambda n: n.pulsar_menu("libre"), (ConfigOpcionesLibre,)),
                (
                    "Siguiente",
                    lambda n: (
                        n.establecer_nombre("Bob"),
                        n.pulsar_texto("Siguiente"),
                    ),
                    (ConfigFiltrosLibre,),
                ),
                (
                    "Empezar partida",
                    lambda n: n.pulsar_texto("Empezar"),
                    (PartidaModoLibre,),
                ),
            ]
        )
        self.assertEqual(self.nav.pantalla.estado.nombre, "Bob")

    def test_pausa_continuar_restaura_pantalla(self) -> None:
        """En configuración: pausa → Continuar → misma pantalla."""
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.nav.pulsar_menu("libre")
        pantalla_antes = self.nav.pantalla
        self.nav.pulsar_pausa()
        self.assertTrue(self.app._menu_pausa_abierto)
        self.nav.pulsar_pausa_opcion(0)
        self.assertFalse(self.app._menu_pausa_abierto)
        self.assertIs(self.app.actual, pantalla_antes)
        self.nav.comprobar(ConfigOpcionesLibre)

    def test_pausa_pantalla_titulo_desde_libre(self) -> None:
        """En libre: pausa → Pantalla de título → menú principal."""
        from Grafico.pantallas import MenuPrincipal
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.nav.pulsar_menu("libre")
        self.nav.comprobar(ConfigOpcionesLibre)
        self.nav.pulsar_pausa_opcion(1)
        self.nav.comprobar(MenuPrincipal)

    def test_feedback_ida_y_vuelta(self) -> None:
        """En libre: feedback → Volver → misma pantalla de configuración."""
        from Grafico.pantallas import PantallaFeedback
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.nav.pulsar_menu("libre")
        pantalla_antes = self.nav.pantalla
        self.nav.pulsar_feedback_barra()
        self.nav.comprobar(PantallaFeedback)
        self.nav.pulsar_texto("Volver")
        self.assertIs(self.app.actual, pantalla_antes)
        self.nav.comprobar(ConfigOpcionesLibre)

    def test_historia_continuar_con_nombre(self) -> None:
        """Carrusel historia: nombre + Continuar → opciones o partida."""
        from Grafico.pantallas_historia import (
            ConfigModoHistoria,
            ConfigOpcionesHistoria,
            PartidaModoHistoria,
            PartidaResistenciaHistoria,
        )

        self.nav.pulsar_menu("historia")
        self.nav.comprobar(ConfigModoHistoria)
        if not self.nav.pantalla.presets:
            self.skipTest("Sin presets de historia en el entorno de test")
        self.nav.establecer_nombre("Carlos")
        self.nav.pulsar_texto("Continuar")
        self.nav.comprobar(
            ConfigOpcionesHistoria,
            PartidaModoHistoria,
            PartidaResistenciaHistoria,
        )

    def test_historia_atras_conserva_carrusel(self) -> None:
        """Opciones → Atrás vuelve al mismo preset y nombre en el carrusel."""
        from Grafico.pantallas_historia import ConfigModoHistoria, ConfigOpcionesHistoria

        self.nav.pulsar_menu("historia")
        self.nav.comprobar(ConfigModoHistoria)
        if not self.nav.pantalla.presets:
            self.skipTest("Sin presets de historia en el entorno de test")

        indice_objetivo = min(2, len(self.nav.pantalla.presets) - 1)
        self.nav.pantalla._ir_a_indice(indice_objetivo)
        preset = self.nav.pantalla.preset_actual
        if preset is None or not preset.tiene_opciones():
            self.skipTest("El preset de prueba no tiene pantalla de opciones")

        self.nav.establecer_nombre("Eva")
        self.nav.pulsar_texto("Continuar")
        self.nav.comprobar(ConfigOpcionesHistoria)
        self.nav.pulsar_texto("Atrás")
        self.nav.comprobar(ConfigModoHistoria)
        self.assertEqual(self.nav.pantalla.indice, indice_objetivo)
        self.assertEqual(self.nav.pantalla.campo_nombre.texto, "Eva")

    def test_salir_desde_menu(self) -> None:
        """Menú → Salir → la aplicación marca fin de ejecución."""
        self.nav.pulsar_menu("salir")
        self.assertFalse(self.app.ejecutando)


if __name__ == "__main__":
    unittest.main()
