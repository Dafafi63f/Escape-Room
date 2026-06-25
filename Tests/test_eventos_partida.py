#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo compartido de eventos."""

from __future__ import annotations

import unittest

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.eventos_partida import (  # noqa: E402
    AlcanceEvento,
    EventoContenidoInstanciado,
    catalogo_eventos,
    combinar_modificadores_puerta,
    evento_por_id,
    evento_resistencia_aleatorio,
    eventos_para_escape,
    eventos_para_resistencia,
    iconos_efecto_puerta,
    instanciar_evento_contenido,
    texto_evento_contenido,
)
from Comun.escape_room import PuertaEscape  # noqa: E402


class TestEventosPartida(unittest.TestCase):
    def test_catalogo_no_vacio(self) -> None:
        self.assertGreaterEqual(len(catalogo_eventos()), 10)

    def test_escape_catalogo_por_rol(self) -> None:
        from Comun.eventos_partida import (
            RolEscape,
            eventos_contenido_escape_para_sala,
            eventos_para_escape,
            eventos_puerta_escape_para_sala,
        )

        self.assertGreater(len(eventos_para_escape()), 10)
        self.assertIn("descanso", {e.id for e in eventos_puerta_escape_para_sala(1)})
        self.assertIn("respiro", {e.id for e in eventos_puerta_escape_para_sala(1)})
        self.assertIn("botin", {e.id for e in eventos_puerta_escape_para_sala(6)})
        ids_escape_puerta = {e.id for e in eventos_puerta_escape_para_sala(30)}
        self.assertNotIn("sin_pistas", ids_escape_puerta)
        self.assertNotIn("examen_cerrado", ids_escape_puerta)
        self.assertNotIn("relampago", ids_escape_puerta)
        self.assertIn("cronometro_pregunta", ids_escape_puerta)
        self.assertIn("cronometro_bloque", ids_escape_puerta)
        self.assertIn("cronometro_doble", {e.id for e in eventos_puerta_escape_para_sala(30)})
        from Comun.eventos_partida import RASGOS_TIEMPO_PUERTA_ESCAPE

        self.assertLessEqual(
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            ids_escape_puerta,
        )
        self.assertNotIn("sin_pistas", {e.id for e in catalogo_eventos()})
        self.assertNotIn("examen_cerrado", {e.id for e in catalogo_eventos()})
        self.assertIn("solo_facil", {e.id for e in eventos_contenido_escape_para_sala(1)})
        for ev in eventos_para_escape():
            self.assertIn(ev.rol_escape, {RolEscape.PUERTA, RolEscape.CONTENIDO})
        self.assertIn("triple_puntos", {e.id for e in eventos_puerta_escape_para_sala(30)})
        self.assertNotIn("triple_puntos", {e.id for e in eventos_contenido_escape_para_sala(30)})
        self.assertIn("triple_puntos", {e.id for e in eventos_para_resistencia()})

    def test_resistencia_incluye_compartidos(self) -> None:
        ids_res = {e.id for e in eventos_para_resistencia()}
        self.assertIn("relampago", ids_res)
        self.assertIn("triple_puntos", ids_res)
        self.assertNotIn("descanso", ids_res)

    def test_texto_contenido_incluye_materia(self) -> None:
        ev = instanciar_evento_contenido(
            evento_por_id("pregunta_unica"),
            materias_pool=("Àlgebra Lineal",),
            grupos_pool=(),
            semilla=0,
            indice_puerta=0,
        )
        texto = texto_evento_contenido(ev)
        self.assertIn("Àlgebra Lineal", texto)
        self.assertIn("Balanceado", texto)

    def test_texto_contenido_incluye_nombre_grupo_completo(self) -> None:
        ev = EventoContenidoInstanciado(
            definicion=evento_por_id("bloque_grupo"),
            grupo="3",
        )
        texto = texto_evento_contenido(ev)
        self.assertIn("G3 — Sistemas y seguridad", texto)
        self.assertNotIn("Grupo: G3", texto)

    def test_alias_resistencia_relampago(self) -> None:
        ev = evento_resistencia_aleatorio("relampago", 0.5)
        self.assertIn("Relámpago", ev.etiqueta)
        self.assertIsNotNone(ev.tiempo_pregunta)

    def test_alcances_validos(self) -> None:
        for ev in catalogo_eventos():
            self.assertIsInstance(ev.alcance, AlcanceEvento)

    def test_iconos_descanso_sin_contenido(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia="Probabilitat",
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=combinar_modificadores_puerta((evento_por_id("descanso"),)),
            evento=evento,
        )
        iconos = iconos_efecto_puerta(
            evento=puerta.evento,
            modificadores=puerta.modificadores,
            n_preguntas=puerta.n_preguntas,
        )
        self.assertEqual(len(iconos), 1)
        self.assertEqual(iconos[0].emoji, "💤")


if __name__ == "__main__":
    unittest.main()
