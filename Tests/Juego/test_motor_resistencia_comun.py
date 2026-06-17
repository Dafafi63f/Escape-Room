#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del motor compartido de resistencia."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.estado_resistencia import EstadoResistencia  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta  # noqa: E402
from Comun.motor_resistencia_comun import (  # noqa: E402
    aplicar_bonificaciones_puntos_resistencia,
    bonificacion_puntos_racha,
    procesar_turno_resistencia,
    usar_powerup,
)
from Comun.powerups_resistencia import etiqueta_powerup, letras_ocultas_bomba, letras_ocultas_fifty_fifty  # noqa: E402
from Comun.reglas_partida import preset_historia_resistencia  # noqa: E402


def _pregunta() -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia="MAT",
        tematica="",
        dificultad="Facil",
        tipo="test",
        grupo="",
        nivel="",
        curso="1",
        semestre="1",
        correcta="B",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
    )


class TestMotorResistenciaComun(unittest.TestCase):
    def test_racha_se_corta_al_fallar(self) -> None:
        er = EstadoResistencia()
        er.racha = 5
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_historia_resistencia(),
            vidas_restantes=3,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=1,
        )
        self.assertEqual(er.racha, 0)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertFalse(turno.feedback.sin_vidas)

    def test_escudo_evita_perder_vida_y_racha(self) -> None:
        er = EstadoResistencia()
        er.racha = 7
        er.escudo_activo = True
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_historia_resistencia(),
            vidas_restantes=2,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=2,
        )
        self.assertTrue(turno.reintentar_pregunta)
        self.assertEqual(er.racha, 7)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertFalse(er.escudo_activo)

    def test_fifty_fifty_oculta_dos_incorrectas(self) -> None:
        p = _pregunta()
        ocultas = letras_ocultas_fifty_fifty(p)
        self.assertEqual(len(ocultas), 2)
        self.assertNotIn("B", ocultas)

    def test_bomba_oculta_una_incorrecta(self) -> None:
        p = _pregunta()
        ocultas = letras_ocultas_bomba(p)
        self.assertEqual(len(ocultas), 1)
        self.assertNotIn("B", ocultas)

    def test_etiqueta_bomba(self) -> None:
        self.assertEqual(etiqueta_powerup("bomba"), "Bomba")

    def test_usar_powerup_consumo(self) -> None:
        er = EstadoResistencia()
        er.agregar_powerup("skip", 2)
        p = _pregunta()
        self.assertIsNone(usar_powerup("skip", er, p))
        self.assertEqual(er.cantidad("skip"), 1)

    def test_avisos_pre_pregunta_incluyen_recompensa_y_evento(self) -> None:
        from Comun.motor_resistencia_comun import avisos_pre_pregunta_resistencia

        p = _pregunta()
        avisos = avisos_pre_pregunta_resistencia(
            p,
            180,
            recompensa_etiqueta="Objeto: Escudo",
        )
        self.assertTrue(any("Escudo" in a for a in avisos))

    def test_texto_pregunta_visible_trunca(self) -> None:
        from Comun.powerups_resistencia import texto_pregunta_visible

        texto = "¿Cuál es la capital de Francia en el siglo XXI?"
        truncado = texto_pregunta_visible(texto, 0.5)
        self.assertIn("▓", truncado)
        self.assertLess(len(truncado.split("▓")[0]), len(texto))

    def test_escalada_con_niebla_opciones(self) -> None:
        from Comun.resistencia_historia import eventos_aleatorios_para_pregunta

        eventos = [
            e for e in eventos_aleatorios_para_pregunta(120)
            if e.opciones_ocultas
        ]
        if eventos:
            self.assertGreater(eventos[0].opciones_ocultas or 0, 0)
            self.assertNotIn("Ceguera", eventos[0].etiqueta)

    def test_bonificacion_racha_solo_puntos(self) -> None:
        self.assertEqual(bonificacion_puntos_racha(1), 1.0)
        self.assertGreater(bonificacion_puntos_racha(10), 1.4)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_historia_resistencia(),
            vidas_restantes=3,
        )
        estado.puntos_arcade = 20
        aplicar_bonificaciones_puntos_resistencia(
            estado,
            puntos_prev=10,
            racha=10,
            mult_escalada=1,
            exclusiva=False,
            acierto=True,
            tiempo_agotado=False,
        )
        self.assertGreater(estado.puntos_arcade, 20)


if __name__ == "__main__":
    unittest.main()
