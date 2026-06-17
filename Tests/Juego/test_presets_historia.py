#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del catálogo de presets del modo historia."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_orden_materias, cargar_preguntas  # noqa: E402
from Comun.presets_historia import (  # noqa: E402
    aplicar_preset,
    argumentos_generador,
    cargar_presets_historia,
    config_defecto,
    politica_desde_preset,
)
from Comun.config_historia import ConfigPresetHistoria, validar_config  # noqa: E402
from Comun.perfiles_historia import PerfilPedagogico  # noqa: E402
from Comun.rutas import resolver_dataset, resolver_listado_materias, resolver_presets_historia  # noqa: E402
from Consola.generador_examen_historia import cargar_estadisticas_historicas, generar_examen  # noqa: E402


class TestPresetsHistoria(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets = cargar_presets_historia(resolver_presets_historia())
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.orden = cargar_orden_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.stats = cargar_estadisticas_historicas(materias_validas=set(cls.materias_meta))

    def test_catalogo_ordenado_historico_primero(self) -> None:
        self.assertGreaterEqual(len(self.presets), 6)
        self.assertEqual(self.presets[0].id, "refuerzo_historico")
        self.assertTrue(self.presets[0].usa_analisis_historico)
        ids = [p.id for p in self.presets]
        self.assertNotEqual(ids[-1], "ranking_resistencia")

    def test_resistencia_destacada_tras_simulacro(self) -> None:
        ids = [p.id for p in self.presets]
        self.assertNotEqual(ids[-1], "ranking_resistencia")
        idx = ids.index("ranking_resistencia")
        self.assertEqual(ids[idx - 1], "simulacro_examen")
        self.assertEqual(ids[idx + 1], "sesion_pre_entrega")

        for preset in self.presets:
            if preset.id == "ranking_resistencia":
                self.assertFalse(preset.tiene_opciones())
                continue
            self.assertTrue(preset.tiene_opciones(), preset.id)

    def test_cada_preset_genera_examen_con_defectos(self) -> None:
        for preset in self.presets:
            if preset.id == "ranking_resistencia":
                continue
            with self.subTest(preset=preset.id):
                cfg = validar_config(
                    preset.opciones,
                    config_defecto(
                        preset,
                        materias_meta=self.materias_meta,
                        materias_orden=self.orden,
                    ),
                    materias_meta=self.materias_meta,
                )
                plan = generar_examen(
                    self.preguntas,
                    materias_orden=self.orden,
                    materias_meta=self.materias_meta,
                    stats=self.stats,
                    semilla=42,
                    **argumentos_generador(preset, cfg, materias_meta=self.materias_meta),
                )
                self.assertGreater(len(plan.preguntas), 0)
                self.assertGreater(len(plan.materias), 0)

    def test_simulacro_estrategia_debilidades_usa_refuerzo(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro_examen")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.REFUERZO)
        self.assertFalse(kwargs["seleccion_determinista"])

    def test_simulacro_estrategia_curricular_es_determinista(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro_examen")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        cfg.valores["estrategia_materias"] = "curricular"
        cfg = validar_config(preset.opciones, cfg, materias_meta=self.materias_meta)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.BALANCEADO)
        self.assertTrue(kwargs["seleccion_determinista"])

    def test_desafio_historico_perfil(self) -> None:
        preset = next(p for p in self.presets if p.id == "desafio_historico")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.DESAFIO)
        self.assertFalse(kwargs["seleccion_determinista"])

    def test_simulacro_examen_tiempo_configurable(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro_examen")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        cfg.valores["tiempo_total_min"] = 60
        reglas = aplicar_preset(preset, cfg)
        self.assertEqual(reglas.tiempo_total_seg, 3600)

    def test_repaso_curso_incluye_diez_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso_curso")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **argumentos_generador(preset, cfg, materias_meta=self.materias_meta),
        )
        self.assertEqual(len(plan.materias), 10)

    def test_simulacro_parcial_cubre_semestre(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro_examen")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["n_materias"], 5)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            **kwargs,
        )
        self.assertEqual(len(plan.materias), 5)

    def test_repaso_curso_orden_por_historico(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso_curso")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["orden_por_historico"], "desc")


if __name__ == "__main__":
    unittest.main()
