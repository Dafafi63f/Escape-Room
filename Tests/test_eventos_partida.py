#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo compartido de eventos."""

from __future__ import annotations

import random
import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.eventos_partida import (  # noqa: E402
    AlcanceEvento,
    EventoContenidoInstanciado,
    RASGOS_BOTIN_ESCAPE,
    catalogo_eventos,
    combinar_modificadores_puerta,
    evento_por_id,
    evento_resistencia_aleatorio,
    eventos_para_escape,
    eventos_para_resistencia,
    iconos_efecto_puerta,
    instanciar_evento_contenido,
    lineas_botin_puerta,
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
        self.assertIn("botin", {e.id for e in eventos_puerta_escape_para_sala(6)})
        self.assertIn(
            "botin_corazon_max",
            {e.id for e in eventos_puerta_escape_para_sala(12)},
        )
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
        self.assertIn("puerta_materia", {e.id for e in eventos_contenido_escape_para_sala(1)})
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
            rng=random.Random(0),
            indice_puerta=0,
        )
        texto = texto_evento_contenido(ev)
        self.assertIn("Àlgebra Lineal", texto)
        self.assertIn("Puerta de materia", texto)

    def test_texto_contenido_incluye_nombre_grupo_completo(self) -> None:
        ev = EventoContenidoInstanciado(
            definicion=evento_por_id("bloque_grupo"),
            grupo="3",
        )
        texto = texto_evento_contenido(ev)
        self.assertIn("G3 — Sistemas y seguridad", texto)
        self.assertNotIn("Grupo: G3", texto)

    def test_tooltip_subtipo_bloque_generico_y_foco_en_texto(self) -> None:
        from Comun.config_historia import etiqueta_curso_academico, etiqueta_periodo_academico
        from Comun.eventos_partida import (
            TOOLTIP_PUERTA_CURSO,
            TOOLTIP_PUERTA_GRUPO,
            TOOLTIP_PUERTA_PERIODO,
            TOOLTIP_PUERTA_SEMESTRE,
            iconos_contenido_puerta,
            linea_foco_contenido_puerta,
        )

        curso_ev = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_curso"),
            curso="2",
        )
        self.assertEqual(iconos_contenido_puerta(curso_ev)[0].tooltip, TOOLTIP_PUERTA_CURSO)
        self.assertEqual(linea_foco_contenido_puerta(curso_ev), etiqueta_curso_academico("2"))
        self.assertIn(etiqueta_curso_academico("2"), texto_evento_contenido(curso_ev))

        sem_ev = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_semestre"),
            semestre="1",
        )
        self.assertEqual(iconos_contenido_puerta(sem_ev)[0].tooltip, TOOLTIP_PUERTA_SEMESTRE)
        self.assertEqual(linea_foco_contenido_puerta(sem_ev), "Semestre 1")

        per_ev = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_periodo"),
            curso="3",
            semestre="2",
        )
        self.assertEqual(iconos_contenido_puerta(per_ev)[0].tooltip, TOOLTIP_PUERTA_PERIODO)
        etiqueta = etiqueta_periodo_academico("3", "2")
        self.assertEqual(linea_foco_contenido_puerta(per_ev), etiqueta)

        grupo_ev = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_grupo"),
            grupo="5",
        )
        self.assertEqual(iconos_contenido_puerta(grupo_ev)[0].tooltip, TOOLTIP_PUERTA_GRUPO)
        self.assertNotIn("G5", iconos_contenido_puerta(grupo_ev)[0].tooltip)

    def test_alias_resistencia_relampago(self) -> None:
        ev = evento_resistencia_aleatorio("relampago", 0.5)
        self.assertIn("Relámpago", ev.etiqueta)
        self.assertIsNotNone(ev.tiempo_pregunta)

    def test_alcances_validos(self) -> None:
        for ev in catalogo_eventos():
            self.assertIsInstance(ev.alcance, AlcanceEvento)

    def test_catalogo_escape_emojis_y_capas(self) -> None:
        from Comun.emojis_escape import (
            CAPA_EVENTO_ESCAPE,
            EMOJI_EVENTO_ESCAPE,
            capa_evento_escape,
        )

        for eid, emoji in EMOJI_EVENTO_ESCAPE.items():
            ev = evento_por_id(eid)
            self.assertEqual(ev.emoji, emoji, msg=eid)
            self.assertEqual(capa_evento_escape(eid), CAPA_EVENTO_ESCAPE[eid])

    def test_iconos_descanso_sin_contenido(self) -> None:
        from Comun.emojis_escape import EMOJI_DESCANSO
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
            rng=random.Random(0),
        )
        self.assertEqual(len(iconos), 1)
        self.assertEqual(iconos[0].emoji, EMOJI_DESCANSO)

    def test_icono_botin_unico_con_varios_premios(self) -> None:
        from Comun.emojis_escape import EMOJI_BOTIN_ESCAPE, TOOLTIP_BOTIN

        mods = combinar_modificadores_puerta(
            (evento_por_id("botin"), evento_por_id("botin_bomba")),
            numero_sala=8,
        )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_materia"),
            materia="Àlgebra Lineal",
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=3,
            rng=random.Random(0),
        )
        botines = [ic for ic in iconos if ic.emoji == EMOJI_BOTIN_ESCAPE]
        self.assertEqual(len(botines), 1)
        self.assertEqual(iconos[-1].emoji, EMOJI_BOTIN_ESCAPE)
        self.assertEqual(iconos[-1].tooltip, TOOLTIP_BOTIN)
        self.assertEqual(len(lineas_botin_puerta(mods)), 2)

    def test_icono_botin_al_final_y_pie_con_premio_concreto(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape, EMOJI_BOTIN_ESCAPE, TOOLTIP_BOTIN

        mods = combinar_modificadores_puerta(
            (evento_por_id("botin_fifty_fifty"),),
            numero_sala=2,
        )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia="Càlcul en una Variable",
            perfil_id="facil",
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=3,
            rng=random.Random(0),
        )
        self.assertEqual(iconos[-1].capa, CapaIconoEscape.BOTIN)
        self.assertEqual(iconos[-1].emoji, EMOJI_BOTIN_ESCAPE)
        self.assertEqual(iconos[-1].tooltip, TOOLTIP_BOTIN)
        self.assertNotIn("incorrecta", iconos[-1].tooltip.lower())
        lineas = lineas_botin_puerta(mods)
        self.assertEqual(len(lineas), 1)
        self.assertIn("al superar", lineas[0].lower())

    def test_botin_comodin_en_catalogo_y_icono_unico_al_final(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape, EMOJI_BOTIN_ESCAPE, TOOLTIP_BOTIN

        self.assertIn("botin_comodin", RASGOS_BOTIN_ESCAPE)
        mods = combinar_modificadores_puerta(
            (evento_por_id("botin_comodin"),),
            numero_sala=8,
        )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia="Àlgebra Lineal",
            perfil_id="facil",
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=3,
            rng=random.Random(0),
        )
        botines = [ic for ic in iconos if ic.emoji == EMOJI_BOTIN_ESCAPE]
        self.assertEqual(len(botines), 1)
        self.assertEqual(iconos[-1].capa, CapaIconoEscape.BOTIN)
        self.assertEqual(iconos[-1].tooltip, TOOLTIP_BOTIN)
        self.assertEqual(len(lineas_botin_puerta(mods)), 1)


if __name__ == "__main__":
    unittest.main()
