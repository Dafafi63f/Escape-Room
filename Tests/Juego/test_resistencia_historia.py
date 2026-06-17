#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del modo resistencia y ranking."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.politica_reglas import ContextoPartida, validar_reglas  # noqa: E402
from Comun.presets_historia import aplicar_preset, cargar_presets_historia  # noqa: E402
from Comun.ranking_resistencia import (  # noqa: E402
    registrar_partida,
    top_records,
)
from Comun.reglas_partida import preset_historia_resistencia  # noqa: E402
from Comun.resistencia_historia import (  # noqa: E402
    PREGUNTA_MIN_EVENTOS_ALEATORIOS,
    RACHA_MIN_EVENTOS_ALEATORIOS,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    escalada_para_racha,
    construir_pool_resistencia,
    eventos_aleatorios_para_pregunta,
    parametros_eventos_aleatorios,
)
from Comun.rutas import resolver_dataset, resolver_listado_materias, resolver_presets_historia  # noqa: E402


class TestResistenciaHistoria(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.pool = construir_pool_resistencia(cls.preguntas, cls.materias_meta)
        cls.preset = next(
            p for p in cargar_presets_historia(resolver_presets_historia())
            if p.id == "ranking_resistencia"
        )

    def test_preset_resistencia_en_catalogo(self) -> None:
        self.assertEqual(self.preset.contexto_reglas, ContextoPartida.HISTORIA_RESISTENCIA.value)

    def test_reglas_resistencia_tres_vidas(self) -> None:
        reglas = validar_reglas(
            preset_historia_resistencia(),
            ContextoPartida.HISTORIA_RESISTENCIA,
        )
        self.assertEqual(reglas.vidas, 3)
        self.assertIsNone(reglas.tiempo_por_pregunta_seg)

    def test_escalada_sin_tiempo_al_inicio(self) -> None:
        e1 = escalada_para_pregunta(1)
        self.assertIsNone(e1.tiempo_pregunta_seg)
        e56 = escalada_para_pregunta(56)
        self.assertEqual(e56.tiempo_pregunta_seg, 30)
        e702 = escalada_para_pregunta(702)
        self.assertEqual(e702.nivel, 7)
        self.assertEqual(e702.dificultades_permitidas, frozenset({"Dificil"}))
        if e702.tiempo_pregunta_seg is not None:
            self.assertLessEqual(e702.tiempo_pregunta_seg, 10)

    def test_pool_no_vacio(self) -> None:
        self.assertGreater(len(self.pool), 50)

    def test_elegir_preguntas_infinitas(self) -> None:
        sel = crear_seleccion_resistencia(self.pool)
        for numero in (1, 16, 121, 501):
            escalada = escalada_para_pregunta(numero)
            idx = elegir_indice_resistencia(self.pool, sel, escalada, numero_pregunta=numero)
            self.assertIsNotNone(idx)

    def test_ranking_guarda_y_ordena(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ranking.json"
            registrar_partida(path, nombre="Ana", racha=10, puntos=100, respondidas=50)
            registrar_partida(path, nombre="Bob", racha=25, puntos=400, respondidas=26)
            registrar_partida(path, nombre="Ana", racha=15, puntos=200, respondidas=16)
            top = top_records(path, limite=10)
            self.assertEqual(top[0].nombre, "Ana")
            self.assertEqual(top[0].respondidas, 50)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertLessEqual(len(data["records"]), 500)

    def test_aplicar_preset_resistencia(self) -> None:
        reglas = aplicar_preset(self.preset, None)
        self.assertEqual(reglas.sistema_puntuacion.value, "arcade")

    def test_eventos_aleatorios_antes_de_25(self) -> None:
        self.assertEqual(parametros_eventos_aleatorios(4)[0], 0.0)
        prob, max_ev, _ = parametros_eventos_aleatorios(10)
        self.assertGreater(prob, 0.0)
        self.assertEqual(max_ev, 1)
        con_evento = [
            r
            for r in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 25)
            if eventos_aleatorios_para_pregunta(r)
        ]
        self.assertGreater(len(con_evento), 0)

    def test_eventos_escalan_frecuencia_y_cantidad(self) -> None:
        prob_baja, max_bajo, _ = parametros_eventos_aleatorios(8)
        prob_alta, max_alto, intensidad_alta = parametros_eventos_aleatorios(160)
        self.assertGreater(prob_alta, prob_baja)
        self.assertGreater(max_alto, max_bajo)
        self.assertGreater(intensidad_alta, 0.8)
        largos = [len(eventos_aleatorios_para_pregunta(r)) for r in range(30, 200)]
        self.assertGreater(max(largos), 1)

    def test_relampago_mas_duro_con_racha_alta(self) -> None:
        eventos = eventos_aleatorios_para_pregunta(180)
        relampagos = [e for e in eventos if e.tiempo_pregunta is not None]
        if relampagos:
            self.assertLessEqual(relampagos[0].tiempo_pregunta, 5)

    def test_sin_eventos_redundantes_de_dificultad(self) -> None:
        etiquetas = set()
        for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 200):
            for ev in eventos_aleatorios_para_pregunta(n):
                etiquetas.add(ev.etiqueta)
        self.assertNotIn("Solo difíciles", etiquetas)
        self.assertNotIn("Sin preguntas fáciles", etiquetas)

    def test_sorpresa_dificil_solo_al_inicio(self) -> None:
        tempranas = set()
        for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 50):
            for ev in eventos_aleatorios_para_pregunta(n):
                if ev.min_max_complejidad is not None:
                    tempranas.add(ev.etiqueta)
        tardias = [
            ev
            for n in range(50, 120)
            for ev in eventos_aleatorios_para_pregunta(n)
            if ev.min_max_complejidad is not None
        ]
        self.assertGreater(len(tempranas), 0)
        self.assertEqual(tardias, [])

    def test_sorpresa_dificil_sube_techo_complejidad(self) -> None:
        from Comun.resistencia_historia import _construir_evento, _fusionar_evento_en_escalada

        evento = _construir_evento("sorpresa_dificil", 0.5)
        _, max_cx, permitidas, _, _, _ = _fusionar_evento_en_escalada(
            evento,
            tiempo=None,
            max_cx=2,
            permitidas=frozenset({"Facil", "Media"}),
            mult=1,
            opciones_ocultas=0,
            fraccion_enunciado=1.0,
            efectos=[],
        )
        self.assertEqual(max_cx, 3)
        self.assertIn("Dificil", permitidas)

        evento_extra = _construir_evento("sorpresa_dificil", 0.9)
        self.assertEqual(evento_extra.etiqueta, "Pregunta extra difícil")
        self.assertEqual(evento_extra.min_max_complejidad, 4)


if __name__ == "__main__":
    unittest.main()
