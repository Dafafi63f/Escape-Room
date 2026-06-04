#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de entradas adversas (troll / vacías / EOF) sin romper el juego."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Consola.consola import pedir_entero_en_rango, pedir_opcion
from Consola.entrada_menu import TipoTecla, _EventoTecla, elegir_indice_menu
from Consola.motor_partida import ResultadoRespuesta, preguntar_con_reglas
from Consola.modelos import Pregunta
from Consola.motor_partida import EstadoPartida
from Consola.reglas_partida import preset_libre_arcade
from Consola.navegacion import (
    AccionPausa,
    SalirPrograma,
    VolverAtras,
    menu_pausa,
)


def _pregunta_ejemplo(*, correcta: str = "B") -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia="Test",
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta=correcta,
    )


def _ev(tipo: TipoTecla, valor: str = "") -> _EventoTecla:
    return _EventoTecla(tipo, valor)


class TestEntradaConsola(unittest.TestCase):
    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_menu_opcion_1(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2", "3", "4"]), "1")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_opcion_cero_en_menu_0_3(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["0", "1", "2", "3"], default="0"), "0")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.DIGITO, "0"))
    def test_tecla_cero_valida_en_menu_0_3(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["0", "1", "2", "3"], default="0"), "0")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_pregunta_elige_a(self, _mock) -> None:
        """Enter sin pulsar tecla = respuesta A (defecto en pregunta)."""
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertFalse(r.acierto)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.IGNORAR), _ev(TipoTecla.DIGITO, "2")],
    )
    def test_tecla_invalida_ignorada(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2"]), "2")

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_en_leer_linea_sale_programa(self, _mock) -> None:
        from Consola.navegacion import leer_linea

        with self.assertRaises(SalirPrograma):
            leer_linea("x: ")

    def test_pedir_entero_rango_invertido_se_normaliza(self) -> None:
        with patch("Consola.navegacion._input_seguro", return_value=""):
            v = pedir_entero_en_rango("n", 5, 2, 99)
        self.assertEqual(v, 5)


class TestMenuPausa(unittest.TestCase):
    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=2)
    def test_pausa_opcion2_pantalla_titulo(self, _mock) -> None:
        self.assertEqual(menu_pausa(en_partida=False), AccionPausa.PANTALLA_TITULO)

    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=1)
    def test_pausa_opcion1_continuar(self, _mock) -> None:
        self.assertEqual(menu_pausa(en_partida=True), AccionPausa.CONTINUAR)

    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=3)
    def test_opcion3_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            menu_pausa()

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.CTRL_C))
    def test_ctrl_c_en_pausa_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            elegir_indice_menu(3, defecto=1, en_pausa=True, prompt="")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_menu_principal_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            elegir_indice_menu(4, es_menu_principal=True, prompt="m")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_submenu_atras(self, _mock) -> None:
        with self.assertRaises(VolverAtras):
            elegir_indice_menu(3, permitir_atras=True, prompt="m")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_en_pausa_continuar(self, _mock) -> None:
        self.assertEqual(elegir_indice_menu(3, en_pausa=True, prompt=""), 1)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.SUPR), _ev(TipoTecla.LETRA, "B")],
    )
    def test_supr_en_pregunta_ignorado(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)


class TestMotorPregunta(unittest.TestCase):
    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "A"), _ev(TipoTecla.DIGITO, "1")],
    )
    def test_letra_a_ignorada_en_menu_numerico(self, _mock) -> None:
        self.assertEqual(elegir_indice_menu(2, prompt="m"), 1)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "S"), _ev(TipoTecla.ENTER)],
    )
    def test_sn_ignorado_en_menu_numerico(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2"]), "1")

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "N"), _ev(TipoTecla.ENTER)],
    )
    def test_sn_funciona_en_menu_si_no(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["S", "N"], default="S"), "N")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "A"))
    def test_letra_a_en_partida_elige_opcion(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertFalse(r.acierto)

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "B"))
    def test_respuesta_correcta(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.DIGITO, "2"), _ev(TipoTecla.LETRA, "B")],
    )
    def test_digitos_ignorados_en_pregunta(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "A"))
    def test_pregunta_sin_correcta_valida_cuenta_fallo(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(correcta="X"), estado)
        self.assertFalse(r.acierto)
        self.assertIsInstance(r, ResultadoRespuesta)


if __name__ == "__main__":
    unittest.main()
