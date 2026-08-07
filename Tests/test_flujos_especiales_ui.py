#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Navegación UI de modos especiales (escape / resistencia) con semilla fija."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Tests.Fixtures.helpers_navegacion_grafico import (  # noqa: E402
    SecuenciaNavegacion,
    configurar_pygame_tests,
    crear_app_grafica_pruebas,
    datos_juego_completos,
    preferencias_grafico_aisladas,
)

_SEMILLA_FIJA = 424242


class TestFlujosEspecialesUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configurar_pygame_tests()

    def setUp(self) -> None:
        self._prefs_cm = preferencias_grafico_aisladas()
        self._prefs_cm.__enter__()
        self.datos = datos_juego_completos()
        self.app = crear_app_grafica_pruebas(self.datos, nombre_jugador="NaveUI")
        self.nav = SecuenciaNavegacion(self.app)

    def tearDown(self) -> None:
        self._prefs_cm.__exit__(None, None, None)

    def _firmas_puertas_escape(self, partida) -> tuple[str, ...]:
        from Comun.escape_room import firma_puerta_escape

        return tuple(firma_puerta_escape(p) for p in partida.puertas_actuales)

    @patch("Comun.semillas.semilla_partida_aleatoria", return_value=_SEMILLA_FIJA)
    def test_escape_navegacion_semilla_fija_determinista(self, _mock_semilla) -> None:
        """Menú → especiales → escape → empezar: misma semilla, mismas puertas."""
        from Grafico.pantallas_escape import ConfigAjustesEscapeRoom, PartidaEscapeRoom
        from Grafico.pantallas_modos import ConfigModosEspeciales

        if not self.datos.perfil.modo_especial_disponible("escape_room"):
            self.skipTest("Escape room no disponible en este perfil de contenido")

        def _iniciar_partida() -> PartidaEscapeRoom:
            app = crear_app_grafica_pruebas(self.datos, nombre_jugador="NaveUI")
            nav = SecuenciaNavegacion(app)
            nav.pulsar_menu("especiales")
            nav.comprobar(ConfigModosEspeciales)
            nav.pulsar_modo_especial("escape_room")
            nav.comprobar(ConfigAjustesEscapeRoom)
            nav.pulsar_texto("Empezar")
            nav.comprobar(PartidaEscapeRoom)
            return nav.pantalla

        partida_a = _iniciar_partida()
        partida_b = _iniciar_partida()
        self.assertEqual(partida_a.semilla, _SEMILLA_FIJA)
        self.assertEqual(partida_b.semilla, _SEMILLA_FIJA)
        self.assertEqual(
            self._firmas_puertas_escape(partida_a),
            self._firmas_puertas_escape(partida_b),
        )

    def test_escape_ajustes_atras_vuelve_especiales(self) -> None:
        """Ajustes escape → Atrás conserva la lista de modos especiales."""
        from Grafico.pantallas_escape import ConfigAjustesEscapeRoom
        from Grafico.pantallas_modos import ConfigModosEspeciales

        if not self.datos.perfil.modo_especial_disponible("escape_room"):
            self.skipTest("Escape room no disponible en este perfil de contenido")

        self.nav.pulsar_menu("especiales")
        self.nav.comprobar(ConfigModosEspeciales)
        self.nav.pulsar_modo_especial("escape_room")
        self.nav.comprobar(ConfigAjustesEscapeRoom)
        self.nav.pulsar_texto("Atrás")
        self.nav.comprobar(ConfigModosEspeciales)
        self.assertGreaterEqual(len(self.nav.pantalla.botones_modo), 1)

    @patch("Comun.resistencia_motor.semilla_partida_aleatoria", return_value=_SEMILLA_FIJA)
    def test_resistencia_navegacion_semilla_fija(self, _mock_semilla) -> None:
        """Menú → especiales → resistencia: semilla de partida fijada al arrancar."""
        from Comun.resistencia_motor import rng_partida
        from Grafico.pantallas_modos import ConfigModosEspeciales
        from Grafico.pantallas_resistencia_partida import PartidaResistencia

        if not self.datos.perfil.modo_especial_disponible("resistencia"):
            self.skipTest("Resistencia no disponible en este perfil de contenido")

        self.nav.pulsar_menu("especiales")
        self.nav.comprobar(ConfigModosEspeciales)
        self.nav.pulsar_modo_especial("resistencia")
        self.nav.comprobar(PartidaResistencia)
        rng_partida(self.nav.pantalla.er)
        self.assertEqual(self.nav.pantalla.er.semilla_partida, _SEMILLA_FIJA)
        self.assertEqual(_mock_semilla.call_count, 1)

    @patch("Comun.resistencia_motor.semilla_partida_aleatoria", return_value=_SEMILLA_FIJA)
    def test_resistencia_misma_semilla_misma_primera_pregunta(self, _mock_semilla) -> None:
        """Dos arranques con la misma semilla muestran la misma primera pregunta."""
        from Grafico.pantallas_modos import ConfigModosEspeciales
        from Grafico.pantallas_resistencia_partida import PartidaResistencia

        if not self.datos.perfil.modo_especial_disponible("resistencia"):
            self.skipTest("Resistencia no disponible en este perfil de contenido")

        def _primera_pregunta() -> str:
            app = crear_app_grafica_pruebas(self.datos, nombre_jugador="NaveUI")
            nav = SecuenciaNavegacion(app)
            nav.pulsar_menu("especiales")
            nav.comprobar(ConfigModosEspeciales)
            nav.pulsar_modo_especial("resistencia")
            nav.comprobar(PartidaResistencia)
            partida = nav.pantalla
            idx = partida.pregunta_idx
            self.assertIsNotNone(idx)
            return partida.pool[idx].texto

        a = _primera_pregunta()
        b = _primera_pregunta()
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
