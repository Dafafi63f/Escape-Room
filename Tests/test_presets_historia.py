#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogos de presets (historia y modos especiales).

Secciones:
- test_presets_historia.py
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

# --- test_presets_historia.py ---

from Comun.datos import cargar_materias, cargar_orden_materias, cargar_preguntas  # noqa: E402
from Comun.presets_historia import (  # noqa: E402
    aplicar_preset,
    argumentos_generador,
    cargar_presets_especiales,
    cargar_presets_historia,
    config_defecto,
    politica_desde_preset,
    semilla_desde_preset,
)
from Comun.config_historia import ConfigPresetHistoria, validar_config  # noqa: E402
from Comun.perfiles_historia import PerfilPedagogico  # noqa: E402
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_presets_especiales,
    resolver_presets_historia,
)
from Comun.examen_dia_historia import semilla_examen_dia  # noqa: E402
from Comun.generador_examen_historia import cargar_estadisticas_historicas, generar_examen  # noqa: E402


class TestPresetsHistoria(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets = cargar_presets_historia(resolver_presets_historia())
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.orden = cargar_orden_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.stats = cargar_estadisticas_historicas(materias_validas=set(cls.materias_meta))

    def test_catalogo_ordenado_historico_primero(self) -> None:
        self.assertGreaterEqual(len(self.presets), 10)
        self.assertEqual(len(self.presets), 10)
        self.assertEqual(self.presets[0].id, "examen_dia_historia")
        self.assertEqual(
            [p.id for p in self.presets],
            [
                "examen_dia_historia",
                "refuerzo_historico",
                "desafio_historico",
                "sesion_pre_entrega",
                "repaso_semestre",
                "repaso_curso",
                "simulacro_examen",
                "simulacro_solo_teoria",
                "parcial_materia",
                "parcial_grupo",
            ],
        )
        self.assertTrue(self.presets[1].usa_analisis_historico)
        ids = [p.id for p in self.presets]
        self.assertNotIn("ranking_resistencia", ids)
        self.assertNotIn("reto_dia_resistencia", ids)
        for nuevo in (
            "repaso_semestre",
            "simulacro_solo_teoria",
            "examen_dia_historia",
        ):
            self.assertIn(nuevo, ids)
        self.assertNotIn("simulacro_solo_calculo", ids)

    def test_historia_sin_modos_resistencia(self) -> None:
        for preset in self.presets:
            self.assertNotEqual(preset.contexto_reglas, "historia_resistencia")

    def test_cada_preset_genera_examen_con_defectos(self) -> None:
        for preset in self.presets:
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
                    semilla=semilla_desde_preset(preset) or 42,
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

    def test_repaso_semestre_cinco_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso_semestre")
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
        self.assertEqual(len(plan.materias), 5)

    def test_simulacro_solo_teoria_sin_calculo(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro_solo_teoria")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertTrue(all(t == "Teoria" for t, _ in kwargs["slots"]))
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            **kwargs,
        )
        self.assertTrue(all(p.tipo == "Teoria" for p in plan.preguntas))

    def test_examen_dia_misma_semilla_mismo_plan(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_dia_historia")
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden),
            materias_meta=self.materias_meta,
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        semilla = semilla_examen_dia(date(2026, 6, 18))
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla,
            **kwargs,
        )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla,
            **kwargs,
        )
        self.assertEqual(plan_a.materias, plan_b.materias)
        self.assertEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_b.preguntas],
        )


class TestPresetsEspeciales(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets = cargar_presets_especiales(resolver_presets_especiales())

    def test_catalogo_resistencia(self) -> None:
        ids = [p.id for p in self.presets]
        self.assertEqual(ids, ["reto_dia_resistencia", "ranking_resistencia"])
        for preset in self.presets:
            self.assertEqual(preset.contexto_reglas, "historia_resistencia")
            self.assertFalse(preset.tiene_opciones())

if __name__ == "__main__":
    unittest.main()
