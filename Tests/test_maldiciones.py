#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests del catálogo unificado de maldiciones."""

from __future__ import annotations

import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta
from Comun.reglas import preset_resistencia


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


class TestMaldicionesPartida(unittest.TestCase):
    def test_plantillas_filtran_por_progreso(self) -> None:
        from Comun.maldiciones_partida import (
            PREGUNTA_MIN_MALDICION_RESISTENCIA,
            plantillas_maldicion_resistencia,
        )

        tempranas = plantillas_maldicion_resistencia(
            PREGUNTA_MIN_MALDICION_RESISTENCIA - 1,
        )
        self.assertEqual(tempranas, [])

        disponibles = plantillas_maldicion_resistencia(
            PREGUNTA_MIN_MALDICION_RESISTENCIA,
        )
        ids_tempranas = {p.id for p in disponibles}
        self.assertIn("sin_objetos", ids_tempranas)
        self.assertNotIn("relampago", ids_tempranas)
        self.assertNotIn("niebla", ids_tempranas)
        self.assertNotIn("puntos_mitad", ids_tempranas)
        self.assertNotIn("fatal", ids_tempranas)

        tardias = plantillas_maldicion_resistencia(40)
        ids_tardias = {p.id for p in tardias}
        self.assertIn("puntos_mitad", ids_tardias)
        self.assertIn("fatal", ids_tardias)

    def test_no_maldicion_antes_de_pregunta_min(self) -> None:
        from Comun.maldiciones_partida import (
            PREGUNTA_MIN_MALDICION_RESISTENCIA,
            probabilidad_activar_maldicion_fallo_resistencia,
        )
        from Comun.maldiciones_partida import PityMaldicionesResistencia
        from Comun.resistencia_motor import EstadoResistencia, _activar_maldicion

        pity = PityMaldicionesResistencia(preguntas_sin_maldicion=99)
        self.assertEqual(
            probabilidad_activar_maldicion_fallo_resistencia(
                PREGUNTA_MIN_MALDICION_RESISTENCIA - 1,
                pity,
                prob_base=0.9,
            ),
            0.0,
        )
        er = EstadoResistencia(semilla_partida=1)
        er.ventana_resultados = [False, False, False]
        self.assertIsNone(_activar_maldicion(er, 3))

    def test_pity_fuerza_maldicion_y_variedad(self) -> None:
        from Comun.maldiciones_partida import (
            PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA,
            PityMaldicionesResistencia,
            actualizar_pity_maldiciones_resistencia,
            debe_forzar_maldicion_resistencia,
            elegir_plantilla_maldicion_resistencia,
            plantillas_maldicion_resistencia,
        )

        pity = PityMaldicionesResistencia(
            preguntas_sin_maldicion=PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA,
        )
        self.assertTrue(debe_forzar_maldicion_resistencia(pity, 30))
        candidatas = plantillas_maldicion_resistencia(30)
        rng = __import__("random").Random(7)
        elegidas = {
            elegir_plantilla_maldicion_resistencia(candidatas, pity, rng).id
            for _ in range(12)
        }
        self.assertGreater(len(elegidas), 1)
        actualizar_pity_maldiciones_resistencia(
            pity, numero_pregunta=30, maldicion_id_activada="sin_objetos"
        )
        self.assertEqual(pity.preguntas_sin_maldicion, 0)
        self.assertEqual(pity.preguntas_sin_por_id.get("sin_objetos"), 0)

    def test_sin_objetos_bloquea_tras_reset_pregunta(self) -> None:
        from Comun.maldiciones_partida import (
            ModoFinMaldicion,
            objetos_bloqueados_efectivo_resistencia,
            reaplicar_efectos_maldicion_persistente,
        )
        from Comun.resistencia_motor import EstadoResistencia, MaldicionActiva, usar_powerup

        er = EstadoResistencia()
        er.maldicion = MaldicionActiva(
            id="sin_objetos",
            etiqueta="Maldición: no puedes usar objetos",
            modo_fin=ModoFinMaldicion.DURACION,
            preguntas_restantes=2,
        )
        er.agregar_powerup("bomba")
        er.reset_pregunta()
        self.assertTrue(objetos_bloqueados_efectivo_resistencia(er))
        self.assertEqual(
            usar_powerup("bomba", er, _pregunta()),
            "Maldición activa: no puedes usar objetos.",
        )
        reaplicar_efectos_maldicion_persistente(er)
        self.assertTrue(er.objetos_bloqueados)

    def test_puntos_mitad_reduce_arcade(self) -> None:
        from Comun.maldiciones_partida import multiplicador_puntos_maldicion
        from Comun.resistencia_motor import (
            MaldicionActiva,
            aplicar_bonificaciones_puntos_resistencia,
        )

        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=100,
        )
        maldicion = MaldicionActiva(
            id="puntos_mitad",
            etiqueta="Maldición: puntos al 50 %",
            preguntas_restantes=2,
            multiplicador_puntos=0.5,
        )
        self.assertEqual(multiplicador_puntos_maldicion(maldicion), 0.5)
        estado.puntos_arcade = 120
        aplicar_bonificaciones_puntos_resistencia(
            estado,
            puntos_prev=100,
            racha=0,
            mult_escalada=1,
            exclusiva=False,
            acierto=True,
            tiempo_agotado=False,
            mult_maldicion=0.5,
        )
        self.assertEqual(estado.puntos_arcade, 110)

    def test_maldicion_desafio_tiempo_en_slot_unico(self) -> None:
        from Comun.maldiciones_partida import (
            ModoFinMaldicion,
            instanciar_maldicion_desafio_tiempo,
            maldicion_tiene_desafio_tiempo,
        )

        maldicion = instanciar_maldicion_desafio_tiempo(130)
        self.assertEqual(maldicion.modo_fin, ModoFinMaldicion.DESAFIO)
        self.assertTrue(maldicion_tiene_desafio_tiempo(maldicion))
        assert maldicion.desafio is not None
        self.assertEqual(maldicion.desafio.aciertos_objetivo, 3)
        self.assertEqual(maldicion.desafio.tiempo_limite_seg, 90)

    def test_resistencia_solo_una_maldicion_activa(self) -> None:
        from Comun.maldiciones_partida import ModoFinMaldicion
        from Comun.resistencia_motor import (
            EstadoResistencia,
            MaldicionActiva,
            _activar_maldicion,
        )

        er = EstadoResistencia(semilla_partida=99)
        er.maldicion = MaldicionActiva(
            id="sin_objetos",
            etiqueta="Maldición: no puedes usar objetos",
            preguntas_restantes=2,
        )
        er.ventana_resultados = [False, False, False]
        self.assertIsNone(_activar_maldicion(er, 30))

        er.maldicion = MaldicionActiva(
            id="desafio_tiempo",
            etiqueta="Maldición: desafío de tiempo",
            modo_fin=ModoFinMaldicion.DESAFIO,
            preguntas_restantes=0,
        )
        self.assertIsNone(_activar_maldicion(er, 130))

    def test_maldicion_no_fatal_solo_pierde_vida(self) -> None:
        from Comun.resistencia_motor import (
            EstadoResistencia,
            MaldicionActiva,
            procesar_turno_resistencia,
        )

        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        er = EstadoResistencia()
        er.maldicion = MaldicionActiva(
            id="sin_objetos",
            etiqueta="Maldición: no puedes usar objetos",
            preguntas_restantes=2,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=10,
        )
        self.assertFalse(turno.feedback.sin_vidas)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertIsNotNone(er.maldicion)
        self.assertEqual(er.maldicion.preguntas_restantes, 1)

    def test_maldicion_fatal_fin_partida(self) -> None:
        from Comun.resistencia_motor import (
            EstadoResistencia,
            MaldicionActiva,
            procesar_turno_resistencia,
        )

        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        er = EstadoResistencia()
        er.maldicion = MaldicionActiva(
            id="fatal",
            etiqueta="Maldición mortal",
            preguntas_restantes=2,
            fin_partida_si_fallo=True,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=40,
        )
        self.assertTrue(turno.feedback.sin_vidas)
        self.assertIn("mortal", turno.feedback.mensaje.lower())
        self.assertEqual(estado.vidas_restantes, 0)


if __name__ == "__main__":
    unittest.main()
