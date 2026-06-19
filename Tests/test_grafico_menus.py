#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Navegación de menús, pausa y hover en pygame.

Secciones:
- test_app_pausa_grafico.py
- test_botones_menus_grafico.py
- test_flujos_menus_grafico.py
- test_hover_tooltips_grafico.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from Tests.support import ensure_juego_path

ensure_juego_path()

# --- test_app_pausa_grafico.py ---

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

    def test_info_abre_desde_ranking_y_volver_restaura(self) -> None:
        from Grafico.pantalla_info import PantallaInfoHub
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        self.app.actual = ConfigOpcionesLibre(
            self.datos, self.app._ir_a, self.app._salir
        )
        self.app._abrir_info()
        self.assertIsInstance(self.app.actual, PantallaInfoHub)
        self.app.actual.volver()
        self.assertIsInstance(self.app.actual, ConfigOpcionesLibre)

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

    def test_pausa_bloquea_iconos_fijos(self) -> None:
        self.app._abrir_menu_pausa()
        self.assertTrue(self.app._barra_fija_bloqueada())
        pos_opciones = next(
            b.rect.center for b, tipo in self.app._botones_fijos if tipo == "opciones"
        )
        self.assertFalse(self.app._manejar_clic_fijos(pos_opciones, 1))
        self.assertFalse(self.app._menu_opciones_abierto)

    def test_opciones_overlay_bloquea_iconos_fijos(self) -> None:
        self.app._abrir_menu_opciones()
        self.assertTrue(self.app._barra_fija_bloqueada())
        pos_pausa = next(
            b.rect.center for b, tipo in self.app._botones_fijos if tipo == "pausa"
        )
        self.assertFalse(self.app._manejar_clic_fijos(pos_pausa, 1))
        self.assertFalse(self.app._menu_pausa_abierto)

    def test_bienvenida_bloquea_iconos_fijos(self) -> None:
        from Comun.preferencias_grafico import PreferenciasGrafico, guardar_preferencias_grafico
        from Grafico.app import AplicacionGrafica
        from Grafico.pantallas_bienvenida import PantallaBienvenida
        from Tests.helpers_navegacion_grafico import preferencias_grafico_aisladas

        with preferencias_grafico_aisladas():
            guardar_preferencias_grafico(
                PreferenciasGrafico(
                    nombre_jugador="",
                    mostrar_tooltips=True,
                    mostrar_emojis=True,
                    guardar_informes_txt=True,
                )
            )
            app = AplicacionGrafica(self.datos, saltar_bienvenida=False)
        self.assertIsInstance(app.actual, PantallaBienvenida)
        self.assertTrue(app._barra_fija_bloqueada())
        pos_opciones = next(
            b.rect.center for b, tipo in app._botones_fijos if tipo == "opciones"
        )
        self.assertFalse(app._manejar_clic_fijos(pos_opciones, 1))
        self.assertFalse(app._menu_opciones_abierto)

    def test_resistencia_aviso_bloquea_iconos_fijos(self) -> None:
        from Grafico.pantallas_historia import PartidaResistenciaHistoria

        partida = object.__new__(PartidaResistenciaHistoria)
        partida.fase = "aviso"
        self.app.actual = partida
        self.assertTrue(self.app._barra_fija_bloqueada())
        pos_pausa = next(
            b.rect.center for b, tipo in self.app._botones_fijos if tipo == "pausa"
        )
        self.assertFalse(self.app._manejar_clic_fijos(pos_pausa, 1))
        self.assertFalse(self.app._menu_pausa_abierto)

        partida.fase = "pregunta"
        self.assertFalse(partida.popup_bloqueante())

# --- test_botones_menus_grafico.py ---

from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parents[1]
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

    def test_menu_principal_sin_emojis(self) -> None:
        from unittest.mock import patch

        from Grafico.pantallas import MenuPrincipal

        with patch("Grafico.textos_grafico.emojis_habilitados", return_value=False):
            pantalla = MenuPrincipal(
                self.datos, self.ir_a, self.salir, self.app._abrir_feedback
            )
        etiquetas = [b.etiqueta for b in pantalla.botones]
        self.assertEqual(etiquetas[0], "Modo libre")
        self.assertNotIn("🎮", etiquetas[0])
        self.assertEqual(etiquetas[-1], "Salir")

    def test_pausa_y_barra_fija(self) -> None:
        self.app._crear_botones_pausa()
        self._assert_botones_validos("Pausa", self.app._botones_pausa)
        fijos = [b for b, _ in self.app._botones_fijos]
        tipos = [t for _, t in self.app._botones_fijos]
        self._assert_botones_validos("BarraFija", fijos)
        self.assertEqual(len(fijos), 5)
        self.assertEqual(tipos, ["pausa", "diarios", "ranking", "feedback", "opciones"])

    def test_info_hub(self) -> None:
        from Grafico.pantalla_info import PantallaInfoHub

        hub = PantallaInfoHub(
            lambda: None,
            navegar=lambda _p: None,
            abrir_ranking=lambda _v: None,
        )
        self._assert_botones_validos("InfoHub", hub._botones_ui())

    def test_feedback(self) -> None:
        from Grafico.pantallas import PantallaFeedback

        pantalla = PantallaFeedback(lambda: None)
        self._assert_botones_validos(
            "Feedback",
            [pantalla.boton_volver, pantalla.boton_enviar],
        )

    def test_modo_libre_paso1(self) -> None:
        from Grafico.pantallas_libre import ConfigOpcionesLibre

        pantalla = ConfigOpcionesLibre(self.datos, self.ir_a, self.salir)
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
        self._assert_botones_validos("Ranking", ranking._botones_ui())

    def test_manejar_evento_clic_navegacion_libre(self) -> None:
        import pygame

        from Grafico.pantallas_libre import ConfigOpcionesLibre

        pantalla = ConfigOpcionesLibre(self.datos, self.ir_a, self.salir)
        pulsado: list[bool] = []
        pantalla.boton_atras.al_pulsar = lambda: pulsado.append(True)
        pantalla.manejar_evento(_evento_clic(pantalla.boton_atras.rect.center))
        self.assertEqual(pulsado, [True])

        pantalla.manejar_evento(
            pygame.event.Event(pygame.MOUSEMOTION, {"pos": pantalla.boton_siguiente.rect.center})
        )
        self.assertTrue(pantalla.boton_siguiente.hover)

# --- test_flujos_menus_grafico.py ---

from Tests.helpers_navegacion_grafico import (
    SecuenciaNavegacion,
    configurar_pygame_tests,
    crear_app_grafica_pruebas,
    datos_prueba,
    preferencias_grafico_aisladas,
    pregunta_minima,
)


class TestFlujosMenusGrafico(unittest.TestCase):
    def setUp(self) -> None:
        configurar_pygame_tests()
        self._prefs_cm = preferencias_grafico_aisladas()
        self._prefs_cm.__enter__()
        from Grafico.app import AplicacionGrafica

        self.datos = datos_prueba()
        self.app = crear_app_grafica_pruebas(self.datos)
        self.nav = SecuenciaNavegacion(self.app)

    def tearDown(self) -> None:
        self._prefs_cm.__exit__(None, None, None)

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

    def test_menu_especiales_lista_botones(self) -> None:
        """Modos especiales usa botones, no carrusel."""
        from Grafico.pantallas import MenuPrincipal
        from Grafico.pantallas_especiales import ConfigModosEspeciales

        self.nav.pulsar_menu("especiales")
        self.nav.comprobar(ConfigModosEspeciales)
        self.assertGreaterEqual(len(self.nav.pantalla.botones_modo), 2)
        self.assertFalse(hasattr(self.nav.pantalla, "rect_flecha_izq"))
        self.nav.pulsar_texto("Volver al menú")
        self.nav.comprobar(MenuPrincipal)

    def test_libre_paso1_paso2_y_volver(self) -> None:
        """Menú → Libre (paso 1) → Siguiente → paso 2 → Atrás → paso 1."""
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        self.nav.ejecutar(
            [
                ("Modo libre", lambda n: n.pulsar_menu("libre"), (ConfigOpcionesLibre,)),
                ("Siguiente", lambda n: n.pulsar_texto("Siguiente"), (ConfigFiltrosLibre,)),
                ("Atrás al paso 1", lambda n: n.pulsar_texto("Atrás"), (ConfigOpcionesLibre,)),
            ]
        )

    def test_libre_sin_nombre_usa_anonimo(self) -> None:
        """Sin nombre guardado, el modo libre usa el jugador anónimo por defecto."""
        from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
        from Comun.preferencias_grafico import PreferenciasGrafico, guardar_preferencias_grafico
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        guardar_preferencias_grafico(
            PreferenciasGrafico(
                nombre_jugador="",
                mostrar_tooltips=True,
                mostrar_emojis=True,
            )
        )
        self.nav.pulsar_menu("libre")
        self.nav.comprobar(ConfigOpcionesLibre)
        self.nav.pulsar_texto("Siguiente")
        self.nav.comprobar(ConfigFiltrosLibre)
        self.assertEqual(self.nav.pantalla.estado.nombre, NOMBRE_JUGADOR_DEFECTO)

    def test_libre_empezar_partida(self) -> None:
        """Menú → paso 1 → paso 2 → Empezar partida → partida."""
        from Grafico.pantallas import PartidaModoLibre
        from Grafico.pantallas_libre import ConfigFiltrosLibre, ConfigOpcionesLibre

        datos = datos_prueba(preguntas=[pregunta_minima()])
        self.app = crear_app_grafica_pruebas(datos, nombre_jugador="Bob")
        self.nav = SecuenciaNavegacion(self.app)

        self.nav.ejecutar(
            [
                ("Modo libre", lambda n: n.pulsar_menu("libre"), (ConfigOpcionesLibre,)),
                (
                    "Siguiente",
                    lambda n: n.pulsar_texto("Siguiente"),
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
        """En libre: feedback (barra) → Volver → misma pantalla de configuración."""
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
        """Carrusel historia: Continuar → opciones o partida (nombre desde preferencias)."""
        from Grafico.pantallas_historia import (
            ConfigModoHistoria,
            ConfigOpcionesHistoria,
            PartidaModoHistoria,
            PartidaResistenciaHistoria,
        )

        self.app = crear_app_grafica_pruebas(self.datos, nombre_jugador="Carlos")
        self.nav = SecuenciaNavegacion(self.app)
        self.nav.pulsar_menu("historia")
        self.nav.comprobar(ConfigModoHistoria)
        if not self.nav.pantalla.presets:
            self.skipTest("Sin presets de historia en el entorno de test")
        self.nav.pulsar_texto("Continuar")
        self.nav.comprobar(
            ConfigOpcionesHistoria,
            PartidaModoHistoria,
            PartidaResistenciaHistoria,
        )

    def test_historia_atras_conserva_carrusel(self) -> None:
        """Opciones → Atrás vuelve al mismo preset en el carrusel."""
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

        self.nav.pulsar_texto("Continuar")
        self.nav.comprobar(ConfigOpcionesHistoria)
        self.nav.pulsar_texto("Atrás")
        self.nav.comprobar(ConfigModoHistoria)
        self.assertEqual(self.nav.pantalla.indice, indice_objetivo)

    def test_salir_desde_menu(self) -> None:
        """Menú → Salir → la aplicación marca fin de ejecución."""
        self.nav.pulsar_menu("salir")
        self.assertFalse(self.app.ejecutando)

# --- test_hover_tooltips_grafico.py ---

from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parents[1]
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
        from Tests.helpers_navegacion_grafico import configurar_pygame_tests

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
        from Tests.helpers_navegacion_grafico import pregunta_minima

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

if __name__ == "__main__":
    unittest.main()
