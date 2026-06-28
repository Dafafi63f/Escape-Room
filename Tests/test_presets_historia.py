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

from Comun.datos import (  # noqa: E402
    cargar_banco_todo,
    cargar_materias,
    cargar_orden_materias,
    cargar_plantillas_materia,
    cargar_preguntas,
)
from Comun.presets_historia import (  # noqa: E402
    aplicar_preset,
    argumentos_generador,
    buscar_preset,
    cargar_presets_especiales,
    cargar_presets_historia,
    config_defecto,
    contenido_examen_estable,
    NUM_MODOS_HISTORIA_CARRUSEL,
    politica_desde_preset,
    resolver_orden_preguntas,
    semilla_desde_preset,
    _cargar_presets_historia_archivo,
)
from Comun.config_historia import ConfigPresetHistoria, ID_ESTRATEGIA_MATERIAS, ORDEN_OPCIONES_HISTORIA, VALORES_PRIORIDAD_HISTORICA, limites_n_materias, opciones_config_historia, validar_config  # noqa: E402
from Comun.presets_historia import PresetHistoria  # noqa: E402
from Comun.generador_examen_historia import PerfilPedagogico  # noqa: E402
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_plantillas,
    resolver_presets,
    resolver_presets_historia,
)
from Comun.modos_diarios import config_atajo_aleatorio, config_atajo_diario, semilla_examen_dia  # noqa: E402
from Comun.generador_examen_historia import (  # noqa: E402
    calcular_pesos_materia,
    cargar_estadisticas_historicas,
    generar_examen,
    indices_dificultad_ambito,
)


class TestPresetsHistoria(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets = cargar_presets_historia(resolver_presets())
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.orden = cargar_orden_materias(resolver_listado_materias())
        cls.preguntas = cargar_banco_todo(
            resolver_dataset(),
            resolver_plantillas(),
            cls.materias_meta,
        )
        cls.stats = cargar_estadisticas_historicas(materias_validas=set(cls.materias_meta))

    def _kwargs_generador(
        self,
        preset: PresetHistoria,
        cfg: ConfigPresetHistoria,
    ) -> dict:
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        if kwargs.get("usar_plantillas_materia") and kwargs.get("materia_fija"):
            kwargs["plantillas_materia"] = cargar_plantillas_materia(
                resolver_plantillas(),
                kwargs["materia_fija"],
            )
        return kwargs

    def _config_defecto(self, preset: PresetHistoria) -> ConfigPresetHistoria:
        cfg = config_defecto(
            preset,
            materias_meta=self.materias_meta,
            materias_orden=self.orden,
        )
        return cfg

    def _validar(self, preset: PresetHistoria, cfg: ConfigPresetHistoria) -> ConfigPresetHistoria:
        plantillas_materia = None
        if any(o.id == "n_preguntas" for o in opciones_config_historia(preset)):
            materia = cfg.get_str("materia") or cfg.valores.get("materia")
            if materia:
                plantillas_materia = cargar_plantillas_materia(
                    resolver_plantillas(),
                    str(materia),
                )
        return validar_config(
            opciones_config_historia(preset),
            cfg,
            materias_meta=self.materias_meta,
            preset_id=preset.id,
            plantillas_materia=plantillas_materia,
        )

    def _examen_fijo(
        self,
        origen: str = "diario",
    ) -> tuple[PresetHistoria, ConfigPresetHistoria]:
        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(valores={"origen_semilla": origen}),
        )
        return preset, cfg

    def test_catalogo_ordenado_historico_primero(self) -> None:
        self.assertEqual(NUM_MODOS_HISTORIA_CARRUSEL, 5)
        self.assertEqual(len(self.presets), NUM_MODOS_HISTORIA_CARRUSEL)
        self.assertEqual(self.presets[0].id, "repaso")
        self.assertNotIn("examen_dia_historia", [p.id for p in self.presets])
        self.assertNotIn("examen_aleatorio_historia", [p.id for p in self.presets])
        self.assertNotIn("repaso_express", [p.id for p in self.presets])
        self.assertEqual(
            [p.id for p in self.presets],
            [
                "repaso",
                "repaso_area",
                "simulacro",
                "examen_asignatura",
                "examen_fijo",
            ],
        )
        ids = [p.id for p in self.presets]
        self.assertNotIn("ranking_resistencia", ids)
        self.assertNotIn("reto_dia_resistencia", ids)
        self.assertNotIn("examen_dia_historia", ids)
        self.assertNotIn("examen_aleatorio_historia", ids)

    def test_catalogo_activo_sin_presets_obsoletos(self) -> None:
        from Comun.presets_historia import PRESETS_HISTORIA_RETIRADOS, _es_preset_historia

        todos = [
            p
            for p in _cargar_presets_historia_archivo(resolver_presets())
            if _es_preset_historia(p)
        ]
        ids = {p.id for p in todos}
        self.assertEqual(len(todos), NUM_MODOS_HISTORIA_CARRUSEL)
        for retirado in PRESETS_HISTORIA_RETIRADOS:
            self.assertNotIn(retirado, ids)
        with self.assertRaises(KeyError):
            buscar_preset("examen_dia_historia")

    def test_historia_sin_modos_resistencia(self) -> None:
        for preset in self.presets:
            self.assertNotEqual(preset.contexto_reglas, "resistencia")

    def test_cada_preset_genera_examen_con_defectos(self) -> None:
        for preset in self.presets:
            with self.subTest(preset=preset.id):
                cfg = self._validar(
                    preset,
                    self._config_defecto(preset),
                )
                plan = generar_examen(
                    self.preguntas,
                    materias_orden=self.orden,
                    materias_meta=self.materias_meta,
                    stats=self.stats,
                    semilla=semilla_desde_preset(preset) or 42,
                    **self._kwargs_generador(preset, cfg),
                )
                self.assertGreater(len(plan.preguntas), 0)
                self.assertGreater(len(plan.materias), 0)

    def test_simulacro_estrategia_debilidades_usa_refuerzo(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = self._validar(preset, self._config_defecto(preset))
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.REFUERZO)
        self.assertFalse(kwargs["seleccion_determinista"])

    def test_simulacro_estrategia_curricular_es_determinista(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        cfg.valores["estrategia_materias"] = "curricular"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.BALANCEADO)
        self.assertTrue(kwargs["seleccion_determinista"])

    def test_repaso_estrategia_fortalezas(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        cfg.valores["estrategia_materias"] = "fortalezas"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.DESAFIO)
        self.assertFalse(kwargs["seleccion_determinista"])

    def test_repasos_sin_opcion_tiempo(self) -> None:
        repasos = {"repaso", "repaso_area"}
        for preset in self.presets:
            if preset.id in repasos:
                with self.subTest(preset=preset.id):
                    self.assertFalse(
                        any(o.id == "tiempo_total_min" for o in preset.opciones),
                    )

    def test_simulacros_con_opcion_tiempo(self) -> None:
        simulacros = {"simulacro", "examen_asignatura"}
        for preset in self.presets:
            if preset.id in simulacros:
                with self.subTest(preset=preset.id):
                    op = next(o for o in preset.opciones if o.id == "tiempo_total_min")
                    self.assertEqual(op.tipo, "entero")
                    self.assertGreaterEqual(op.min or 0, 0)

    def test_simulacro_tiempo_configurable(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = self._validar(preset, self._config_defecto(preset))
        cfg.valores["tiempo_total_min"] = 60
        reglas = aplicar_preset(preset, cfg)
        self.assertEqual(reglas.tiempo_total_seg, 3600)

    def test_repaso_curso_diez_materias_con_n_maximo(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"curso": "1", "n_materias": 10, "estrategia_materias": "debilidades"},
            ),
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

    def test_simulacro_semestre_cinco_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = self._validar(preset, self._config_defecto(preset))
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

    def test_simulacro_sin_filtro_permite_cuarenta_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        op = next(o for o in preset.opciones if o.id == "n_materias")
        min_v, max_v = limites_n_materias(
            op, {}, materias_meta=self.materias_meta, preset_id="simulacro"
        )
        self.assertEqual((min_v, max_v), (2, 40))
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"n_materias": 40, "estrategia_materias": "debilidades"},
            ),
        )
        self.assertEqual(cfg.get_int("n_materias"), 40)

    def test_simulacro_limites_n_materias_por_ambito(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        op = next(o for o in preset.opciones if o.id == "n_materias")
        casos = (
            ({}, 40),
            ({"semestre": "1"}, 20),
            ({"curso": "1"}, 10),
            ({"periodo": "1-1"}, 5),
            ({"curso": "1", "semestre": "1"}, 5),
        )
        for valores, esperado in casos:
            with self.subTest(valores=valores):
                min_v, max_v = limites_n_materias(
                    op,
                    valores,
                    materias_meta=self.materias_meta,
                    preset_id="simulacro",
                )
                self.assertEqual((min_v, max_v), (2, esperado))

    def test_simulacro_ordenan_preguntas_por_materia(self) -> None:
        for ambito, valores_extra in (
            ("semestre", {"periodo": "1-1"}),
            ("curso", {"curso": "1", "n_materias": 10}),
        ):
            with self.subTest(ambito=ambito):
                preset = next(p for p in self.presets if p.id == "simulacro")
                cfg = self._validar(
                    preset,
                    ConfigPresetHistoria(
                        valores={
                            "estrategia_materias": "debilidades",
                            **valores_extra,
                        }
                    ),
                )
                kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
                self.assertEqual(kwargs["orden_preguntas"], "materia")
                plan = generar_examen(
                    self.preguntas,
                    materias_orden=self.orden,
                    materias_meta=self.materias_meta,
                    stats=self.stats,
                    semilla=11,
                    **kwargs,
                )
                materias_en_preg: list[str] = []
                for p in plan.preguntas:
                    if not materias_en_preg or materias_en_preg[-1] != p.materia:
                        materias_en_preg.append(p.materia)
                self.assertEqual(materias_en_preg, plan.materias)

    def test_repaso_periodo_reproducible_con_n_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={
                    "periodo": "1-1",
                    "n_materias": 5,
                    "estrategia_materias": "debilidades",
                },
            ),
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **kwargs,
        )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **kwargs,
        )
        self.assertEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_b.preguntas],
        )
        plan_otra = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=99,
            **kwargs,
        )
        self.assertNotEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_otra.preguntas],
        )

    def test_repaso_periodo_cinco_materias_con_n_maximo(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={
                    "periodo": "1-1",
                    "n_materias": 5,
                    "estrategia_materias": "debilidades",
                },
            ),
        )
        self.assertEqual(cfg.get_str("periodo"), "1-1")
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **argumentos_generador(preset, cfg, materias_meta=self.materias_meta),
        )
        self.assertEqual(len(plan.materias), 5)

    def test_refuerzo_reparto_ponderado_puede_ser_desigual(self) -> None:
        from collections import Counter

        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={
                    "curso": "1",
                    "semestre": "1",
                    "n_materias": 5,
                    "estrategia_materias": "debilidades",
                },
            ),
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        desigual = False
        for semilla in range(64):
            plan = generar_examen(
                self.preguntas,
                materias_orden=self.orden,
                materias_meta=self.materias_meta,
                stats=self.stats,
                semilla=semilla,
                **kwargs,
            )
            conteos = Counter(p.materia for p in plan.preguntas)
            if conteos and max(conteos.values()) != min(conteos.values()):
                desigual = True
                break
        self.assertTrue(desigual)

    def test_repaso_semestre_veinte_materias_con_n_maximo(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"semestre": "1", "n_materias": 20, "estrategia_materias": "debilidades"},
            ),
        )
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **argumentos_generador(preset, cfg, materias_meta=self.materias_meta),
        )
        self.assertEqual(len(plan.materias), 20)

    def test_exclusion_periodo_curso_semestre(self) -> None:
        from Comun.config_historia import (
            aplicar_exclusion_al_cambiar_ambito,
            filtro_ambito_bloqueado,
            tiene_exclusion_periodo_curso_semestre,
        )

        preset = next(p for p in self.presets if p.id == "repaso")
        self.assertTrue(tiene_exclusion_periodo_curso_semestre(preset.opciones))
        valores: dict[str, str] = {"periodo": "3-2"}
        self.assertTrue(
            filtro_ambito_bloqueado("curso", valores, preset.opciones, preset_id="repaso")
        )
        self.assertTrue(
            filtro_ambito_bloqueado("semestre", valores, preset.opciones, preset_id="repaso")
        )
        self.assertFalse(
            filtro_ambito_bloqueado("periodo", valores, preset.opciones, preset_id="repaso")
        )
        valores = {"curso": "2", "semestre": "1"}
        self.assertTrue(
            filtro_ambito_bloqueado("periodo", valores, preset.opciones, preset_id="repaso")
        )
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"periodo": "1-1", "curso": "1"},
            ),
        )
        self.assertEqual(cfg.get_str("periodo"), "1-1")
        self.assertNotIn("curso", cfg.valores)
        valores_mut = {"periodo": "2-1", "curso": "2", "semestre": "1"}
        aplicar_exclusion_al_cambiar_ambito(valores_mut, "curso")
        self.assertNotIn("periodo", valores_mut)

    def test_simulacro_ambito_curso_diez_materias(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"curso": "1", "n_materias": 10},
            ),
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

    def test_examen_asignatura_n_preguntas_defecto(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_asignatura")
        self.assertFalse(preset.usa_analisis_historico)
        self.assertTrue(preset.usar_plantillas_materia)
        cfg = self._validar(preset, self._config_defecto(preset))
        kwargs = self._kwargs_generador(preset, cfg)
        self.assertFalse(kwargs["usar_analisis_historico"])
        self.assertEqual(kwargs["n_preguntas"], 12)
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=1,
            **kwargs,
        )
        self.assertEqual(len(plan_a.preguntas), 12)
        tipos = [p.tipo for p in plan_a.preguntas]
        n_teoria = sum(1 for t in tipos if t == "Teoria")
        if n_teoria and n_teoria < len(tipos):
            self.assertEqual(tipos[:n_teoria], ["Teoria"] * n_teoria)

    def test_examen_asignatura_n_preguntas_dinamico(self) -> None:
        from Comun.config_historia import contar_plantillas_elegibles, limites_n_preguntas

        preset = next(p for p in self.presets if p.id == "examen_asignatura")
        materia = self.orden[0]
        plantillas = cargar_plantillas_materia(resolver_plantillas(), materia)
        op = next(o for o in opciones_config_historia(preset) if o.id == "n_preguntas")

        for enfoque in ("mixto", "teoria", "calculo"):
            with self.subTest(enfoque=enfoque):
                cfg = self._validar(
                    preset,
                    ConfigPresetHistoria(
                        valores={
                            "materia": materia,
                            "enfoque": enfoque,
                            "n_preguntas": 5,
                        }
                    ),
                )
                min_v, max_v = limites_n_preguntas(
                    op,
                    cfg.valores,
                    plantillas_materia=plantillas,
                )
                self.assertGreater(max_v, 0)
                self.assertLessEqual(5, max_v)
                tope = contar_plantillas_elegibles(plantillas, enfoque)
                self.assertEqual(max_v, min(op.max or 9999, tope))
                cfg_max = self._validar(
                    preset,
                    ConfigPresetHistoria(
                        valores={
                            "materia": materia,
                            "enfoque": enfoque,
                            "n_preguntas": max_v,
                        }
                    ),
                )
                kwargs = self._kwargs_generador(preset, cfg_max)
                plan = generar_examen(
                    self.preguntas,
                    materias_orden=self.orden,
                    materias_meta=self.materias_meta,
                    stats=self.stats,
                    semilla=3,
                    **kwargs,
                )
                self.assertEqual(len(plan.preguntas), max_v)

    def test_historia_rechaza_examenes_demasiado_pequenos(self) -> None:
        from Comun.reglas_partida import MIN_PREGUNTAS_PARTIDA

        repaso = next(p for p in self.presets if p.id == "repaso")
        with self.assertRaises(ValueError):
            self._validar(
                repaso,
                ConfigPresetHistoria(valores={"n_materias": 1}),
            )
        examen = next(p for p in self.presets if p.id == "examen_asignatura")
        with self.assertRaises(ValueError):
            self._validar(
                examen,
                ConfigPresetHistoria(
                    valores={
                        "materia": self.orden[0],
                        "n_preguntas": MIN_PREGUNTAS_PARTIDA - 1,
                    }
                ),
            )

    def test_examen_asignatura_enfoque_teoria(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_asignatura")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={
                    "materia": self.orden[0],
                    "enfoque": "teoria",
                }
            ),
        )
        kwargs = self._kwargs_generador(preset, cfg)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            **kwargs,
        )
        self.assertGreater(len(plan.preguntas), 0)
        self.assertTrue(all(p.tipo == "Teoria" for p in plan.preguntas))

    def test_repaso_muestra_ocho_materias_por_defecto(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"n_materias": 8, "estrategia_materias": "debilidades"},
            ),
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["n_materias"], 8)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **kwargs,
        )
        self.assertEqual(len(plan.materias), 8)

    def test_repaso_muestra_estrategia_historica(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.REFUERZO)
        cfg.valores["estrategia_materias"] = "equilibrado"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.BALANCEADO)
        cfg.valores["estrategia_materias"] = "fortalezas"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.DESAFIO)

    def test_periodos_academicos_ocho_en_el_grado(self) -> None:
        from Comun.config_historia import parse_periodo, periodos_academicos

        periodos = periodos_academicos(self.materias_meta)
        self.assertEqual(len(periodos), 8)
        self.assertEqual(periodos[0][0], "1-1")
        self.assertEqual(periodos[-1][0], "4-2")
        self.assertEqual(parse_periodo("3-2"), ("3", "2"))

    def test_etiquetas_periodo_academico_unificadas(self) -> None:
        from Comun.config_historia import (
            clave_periodo_academico,
            descripcion_ambito_curso_semestre,
            etiqueta_curso_academico,
            etiqueta_periodo_academico,
            etiqueta_periodo_desde_clave,
        )

        self.assertEqual(clave_periodo_academico("3", "2"), "3-2")
        self.assertEqual(etiqueta_periodo_academico("3", "2"), "Semestre 3-2")
        self.assertEqual(etiqueta_periodo_desde_clave("3-2"), "Semestre 3-2")
        self.assertEqual(etiqueta_curso_academico("3"), "Curso 3")
        self.assertEqual(
            descripcion_ambito_curso_semestre("3", "2"),
            "del semestre 3-2",
        )
        self.assertEqual(
            descripcion_ambito_curso_semestre("3", None),
            "del curso 3",
        )

    def test_indices_ambito_relativizan_dentro_del_semestre(self) -> None:
        from Comun.config_historia import cursos_disponibles, semestres_para_curso

        encontrado = False
        for curso in cursos_disponibles(self.materias_meta):
            for semestre in semestres_para_curso(self.materias_meta, curso):
                candidatas = [
                    m
                    for m in self.orden
                    if self.materias_meta[m].get("curso") == curso
                    and self.materias_meta[m].get("semestre") == semestre
                ]
                if len(candidatas) < 2:
                    continue
                brutos = [
                    self.stats[m].indice_dificultad if m in self.stats else 0.5
                    for m in candidatas
                ]
                if max(brutos) - min(brutos) < 1e-6:
                    continue
                indices = indices_dificultad_ambito(candidatas, self.stats)
                self.assertEqual(set(indices), set(candidatas))
                self.assertAlmostEqual(min(indices.values()), 0.0, places=5)
                self.assertAlmostEqual(max(indices.values()), 1.0, places=5)
                encontrado = True
        self.assertTrue(encontrado, "Se esperaba al menos un semestre con dispersión histórica")

    def test_todos_los_presets_con_opciones_generan_en_cada_curso(self) -> None:
        from Comun.config_historia import (
            cursos_disponibles,
            semestres_para_curso,
            tiene_exclusion_periodo_curso_semestre,
            _PRESETS_AMBITO_SEMESTRE_ESTRICTO,
        )

        for preset in self.presets:
            if not preset.opciones:
                continue
            if not any(o.id == "curso" for o in preset.opciones):
                continue
            base = self._config_defecto(preset)
            for curso in cursos_disponibles(self.materias_meta):
                valores = dict(base.valores)
                if tiene_exclusion_periodo_curso_semestre(preset.opciones):
                    valores.pop("periodo", None)
                valores["curso"] = curso
                if preset.id in _PRESETS_AMBITO_SEMESTRE_ESTRICTO or any(
                    o.id == "semestre" and o.obligatorio for o in preset.opciones
                ):
                    valores["semestre"] = semestres_para_curso(self.materias_meta, curso)[0]
                with self.subTest(preset=preset.id, curso=curso):
                    cfg = self._validar(preset, ConfigPresetHistoria(valores=valores))
                    plan = generar_examen(
                        self.preguntas,
                        materias_orden=self.orden,
                        materias_meta=self.materias_meta,
                        stats=self.stats,
                        semilla=99,
                        **argumentos_generador(preset, cfg, materias_meta=self.materias_meta),
                    )
                    self.assertGreater(len(plan.preguntas), 0)

    def test_simulacro_enfoque_teoria_sin_calculo(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        cfg.valores["enfoque"] = "teoria"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["tipos_permitidos"], frozenset({"Teoria"}))
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            **kwargs,
        )
        self.assertTrue(all(p.tipo == "Teoria" for p in plan.preguntas))

    def test_simulacro_enfoque_calculo_sin_teoria(self) -> None:
        preset = next(p for p in self.presets if p.id == "simulacro")
        cfg = config_defecto(preset, materias_meta=self.materias_meta, materias_orden=self.orden)
        cfg.valores["enfoque"] = "calculo"
        cfg = self._validar(preset, cfg)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["tipos_permitidos"], frozenset({"Calculo"}))
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            **kwargs,
        )
        self.assertTrue(all(p.tipo == "Calculo" for p in plan.preguntas))

    def test_pasos_ciclo_entero_historia(self) -> None:
        from Comun.config_historia import (
            paso_entero_opcion_historia,
            siguiente_entero_ciclo,
        )

        self.assertEqual(paso_entero_opcion_historia("n_materias"), 5)
        self.assertEqual(paso_entero_opcion_historia("n_preguntas"), 5)
        self.assertEqual(paso_entero_opcion_historia("tiempo_total_min"), 15)
        self.assertEqual(paso_entero_opcion_historia("semilla"), 1)
        self.assertEqual(
            siguiente_entero_ciclo(12, 1, min_v=5, max_v=40, paso=5),
            17,
        )
        self.assertEqual(
            siguiente_entero_ciclo(7, -1, min_v=2, max_v=40, paso=5),
            2,
        )
        self.assertEqual(
            siguiente_entero_ciclo(90, 1, min_v=0, max_v=240, paso=15),
            105,
        )
        self.assertEqual(
            siguiente_entero_ciclo(240, 1, min_v=0, max_v=240, paso=15),
            240,
        )

    def test_carrusel_historia_tiene_seis_modos(self) -> None:
        self.assertEqual(NUM_MODOS_HISTORIA_CARRUSEL, 5)
        self.assertEqual(len(self.presets), NUM_MODOS_HISTORIA_CARRUSEL)

    def test_repaso_area_incluye_todas_las_materias_del_grupo(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso_area")
        cfg = self._validar(preset, self._config_defecto(preset))
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertTrue(kwargs["usar_todas_materias_ambito"])
        self.assertTrue(kwargs["seleccion_determinista"])
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **kwargs,
        )
        grupo = cfg.get_str("grupo")
        esperadas = [
            m
            for m in self.orden
            if self.materias_meta[m].get("grupo") == grupo
        ]
        self.assertEqual(set(plan.materias), set(esperadas))
        self.assertGreater(len(plan.materias), 0)

    def test_limites_n_materias_segun_ambito(self) -> None:
        repaso = next(p for p in self.presets if p.id == "repaso")
        op = next(o for o in repaso.opciones if o.id == "n_materias")
        total = len(self.materias_meta)
        self.assertEqual(total, 40)
        min_v, max_v = limites_n_materias(op, {}, materias_meta=self.materias_meta, preset_id="repaso")
        self.assertEqual((min_v, max_v), (2, 40))
        min_v, max_v = limites_n_materias(
            op, {"curso": "1"}, materias_meta=self.materias_meta
        )
        self.assertEqual((min_v, max_v), (2, 10))
        min_v, max_v = limites_n_materias(
            op, {"curso": "1", "semestre": "1"}, materias_meta=self.materias_meta
        )
        self.assertEqual((min_v, max_v), (2, 5))
        min_v, max_v = limites_n_materias(
            op, {"semestre": "1"}, materias_meta=self.materias_meta
        )
        self.assertEqual((min_v, max_v), (2, 20))
        cfg = self._validar(
            repaso,
            ConfigPresetHistoria(
                valores={"semestre": "1", "n_materias": 20, "estrategia_materias": "debilidades"},
            ),
        )
        self.assertEqual(cfg.get_int("n_materias"), 20)
        cfg = self._validar(
            repaso,
            ConfigPresetHistoria(
                valores={"n_materias": 40, "estrategia_materias": "equilibrado"},
            ),
        )
        self.assertEqual(cfg.get_int("n_materias"), 40)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            **argumentos_generador(repaso, cfg, materias_meta=self.materias_meta),
        )
        self.assertEqual(len(plan.materias), 40)

    def test_opciones_config_respetan_orden_global(self) -> None:
        casos = {
            "repaso": [
                "periodo",
                "curso",
                "semestre",
                ID_ESTRATEGIA_MATERIAS,
                "n_materias",
            ],
            "repaso_area": ["grupo", ID_ESTRATEGIA_MATERIAS],
            "simulacro": [
                "periodo",
                "curso",
                "semestre",
                ID_ESTRATEGIA_MATERIAS,
                "n_materias",
                "enfoque",
                "tiempo_total_min",
            ],
            "examen_asignatura": ["materia", "enfoque", "n_preguntas", "tiempo_total_min"],
            "examen_fijo": [
                "origen_semilla",
                "semilla",
            ],
        }
        for preset in self.presets:
            ids = [o.id for o in opciones_config_historia(preset)]
            with self.subTest(preset=preset.id):
                self.assertEqual(ids, casos[preset.id])
                orden_global = [i for i in ORDEN_OPCIONES_HISTORIA if i in ids]
                self.assertEqual(ids, orden_global)

    def test_todos_los_modos_tienen_misma_prioridad_historica(self) -> None:
        esperada = VALORES_PRIORIDAD_HISTORICA
        for preset in self.presets:
            if not preset.usa_analisis_historico:
                continue
            ops = opciones_config_historia(preset)
            prioridad = next(o for o in ops if o.id == ID_ESTRATEGIA_MATERIAS)
            with self.subTest(preset=preset.id):
                self.assertEqual(prioridad.etiqueta, "Prioridad histórica")
                self.assertEqual(prioridad.valores, esperada)

    def test_todos_los_modos_historia_usan_analisis_historico_por_defecto(self) -> None:
        from Comun.presets_historia import _es_preset_historia

        todos = [
            p
            for p in _cargar_presets_historia_archivo(resolver_presets())
            if _es_preset_historia(p)
        ]
        self.assertEqual(len(todos), NUM_MODOS_HISTORIA_CARRUSEL)
        for preset in todos:
            if preset.id in ("examen_asignatura", "examen_fijo"):
                self.assertFalse(preset.usa_analisis_historico)
                continue
            self.assertTrue(preset.usa_analisis_historico, preset.id)
        for preset in self.presets:
            cfg = self._validar(preset, self._config_defecto(preset))
            kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
            if preset.id in ("examen_asignatura", "examen_fijo"):
                self.assertFalse(kwargs["usar_analisis_historico"])
            else:
                self.assertTrue(kwargs["usar_analisis_historico"], preset.id)

    def test_prioridad_sin_historico_desactiva_analisis(self) -> None:
        preset = next(p for p in self.presets if p.id == "repaso")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"estrategia_materias": "sin_historico", "n_materias": 5},
            ),
        )
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertFalse(kwargs["usar_analisis_historico"])
        self.assertEqual(cfg.get_str("estrategia_materias"), "sin_historico")

    def test_pesos_historicos_no_excluyen_materias(self) -> None:
        muestra = self.orden[:8]
        pesos_ref = calcular_pesos_materia(
            muestra,
            self.stats,
            PerfilPedagogico.REFUERZO,
            usar_analisis_historico=True,
        )
        pesos_off = calcular_pesos_materia(
            muestra,
            self.stats,
            PerfilPedagogico.REFUERZO,
            usar_analisis_historico=False,
        )
        self.assertTrue(all(w > 0 for w in pesos_ref.values()))
        self.assertTrue(all(w == 1.0 for w in pesos_off.values()))

    def test_refuerzo_y_desafio_inclinan_pesos_en_sentidos_opuestos(self) -> None:
        difíciles = sorted(
            self.stats.values(),
            key=lambda s: s.indice_dificultad,
            reverse=True,
        )[:2]
        fáciles = sorted(self.stats.values(), key=lambda s: s.indice_dificultad)[:2]
        self.assertGreaterEqual(len(difíciles), 1)
        self.assertGreaterEqual(len(fáciles), 1)
        d = difíciles[0].materia
        f = fáciles[0].materia
        pesos_ref = calcular_pesos_materia(
            [d, f],
            self.stats,
            PerfilPedagogico.REFUERZO,
            usar_analisis_historico=True,
        )
        pesos_des = calcular_pesos_materia(
            [d, f],
            self.stats,
            PerfilPedagogico.DESAFIO,
            usar_analisis_historico=True,
        )
        self.assertGreater(pesos_ref[d], pesos_ref[f])
        self.assertGreater(pesos_des[f], pesos_des[d])

    def test_semilla_diaria_formato_ddmmaaaa(self) -> None:
        from Comun.modos_diarios import formatear_semilla_diaria, semilla_diaria

        self.assertEqual(semilla_diaria(date(2026, 6, 22)), 22_06_2026)
        self.assertEqual(semilla_diaria(date(2026, 6, 18)), 18_06_2026)
        self.assertEqual(semilla_diaria(date(2026, 1, 1)), 1_01_2026)
        self.assertEqual(formatear_semilla_diaria(1_01_2026), "01012026")
        self.assertEqual(formatear_semilla_diaria(22_06_2026), "22062026")
        self.assertEqual(semilla_examen_dia(date(2026, 6, 18)), semilla_diaria(date(2026, 6, 18)))

    def test_examen_fijo_sin_analisis_historico(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        self.assertFalse(preset.usa_analisis_historico)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertFalse(kwargs["usar_analisis_historico"])
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.BALANCEADO)
        self.assertFalse(kwargs["seleccion_determinista"])

    def test_examen_fijo_diario_misma_semilla_mismo_plan(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        self.assertTrue(preset.exigir_balance_completo)
        self.assertEqual(preset.n_materias, 4)
        self.assertEqual(preset.preguntas_por_materia, 6)
        self.assertEqual(resolver_orden_preguntas(preset, cfg), "variar")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        semilla_contenido = semilla_examen_dia(date(2026, 6, 18))
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=42,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        self.assertEqual(plan_a.materias, plan_b.materias)
        self.assertEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_b.preguntas],
        )
        self.assertEqual(len(plan_a.preguntas), 24)

    def test_examen_fijo_diario_orden_distinto_por_partida(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        semilla_contenido = semilla_examen_dia(date(2026, 6, 18))
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=1,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=99,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        self.assertEqual(
            sorted(p.texto for p in plan_a.preguntas),
            sorted(p.texto for p in plan_b.preguntas),
        )
        self.assertNotEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_b.preguntas],
        )

    def test_examen_fijo_balance_por_materia(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla_examen_dia(date(2026, 6, 18)),
            **kwargs,
        )
        n_materias = len(plan.materias)
        ppm = plan.preguntas_por_materia
        self.assertEqual(ppm, 6)
        self.assertEqual(len(plan.preguntas), n_materias * ppm)
        from collections import Counter

        por_materia = Counter(p.materia for p in plan.preguntas)
        self.assertTrue(all(c == ppm for c in por_materia.values()))
        por_tipo = Counter(p.tipo for p in plan.preguntas)
        self.assertIn("Teoria", por_tipo)
        self.assertIn("Calculo", por_tipo)

    def test_examen_fijo_puede_mezclar_cursos_y_semestres(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla_examen_dia(date(2026, 1, 1)),
            **kwargs,
        )
        cursos = {self.materias_meta[m].get("curso") for m in plan.materias}
        semestres = {self.materias_meta[m].get("semestre") for m in plan.materias}
        self.assertGreater(len(cursos), 1)
        self.assertGreater(len(semestres), 1)

    def test_examen_fijo_no_usa_primeras_materias_del_catalogo(self) -> None:
        preset, cfg = self._examen_fijo("diario")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla_examen_dia(date(2026, 6, 18)),
            **kwargs,
        )
        self.assertNotEqual(plan.materias, self.orden[: preset.n_materias])

    def test_examen_aleatorio_semilla_nueva_cada_vez(self) -> None:
        from Comun.modos_diarios import semilla_aleatoria_examen

        semillas = {semilla_aleatoria_examen() for _ in range(32)}
        self.assertGreater(len(semillas), 1)

    def test_examen_fijo_aleatorio_misma_semilla_mismo_plan(self) -> None:
        preset, cfg = self._examen_fijo("aleatorio")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        semilla = 424242
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

    def test_examen_fijo_orden_por_origen_semilla(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg_dia = self._validar(preset, config_atajo_diario())
        cfg_alea = self._validar(preset, config_atajo_aleatorio())
        self.assertEqual(resolver_orden_preguntas(preset, cfg_dia), "variar")
        self.assertEqual(resolver_orden_preguntas(preset, cfg_alea), "dificultad")

    def test_examen_fijo_aleatorio_orden_por_dificultad(self) -> None:
        preset, cfg = self._examen_fijo("aleatorio")
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["orden_preguntas"], "dificultad")
        semilla = 424242
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla,
            **kwargs,
        )
        dificultades = [p.dificultad for p in plan.preguntas]
        orden_dif = {"Facil": 0, "Media": 1, "Dificil": 2}
        for i in range(len(dificultades) - 1):
            self.assertLessEqual(
                orden_dif[dificultades[i]],
                orden_dif[dificultades[i + 1]],
            )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=semilla,
            **kwargs,
        )
        self.assertEqual(
            [p.texto for p in plan.preguntas],
            [p.texto for p in plan_b.preguntas],
        )

    def test_examen_fijo_diario_usa_semilla_del_dia_y_orden_variar(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg = self._validar(preset, self._config_defecto(preset))
        self.assertEqual(cfg.get_str("origen_semilla"), "diario")
        self.assertEqual(resolver_orden_preguntas(preset, cfg), "variar")
        self.assertTrue(contenido_examen_estable(preset, cfg=cfg))
        semilla_contenido = semilla_examen_dia(date(2026, 6, 18))
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["orden_preguntas"], "variar")
        plan_a = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        plan_b = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=7,
            semilla_contenido=semilla_contenido,
            **kwargs,
        )
        self.assertEqual(len(plan_a.preguntas), 24)
        self.assertEqual(
            [p.texto for p in plan_a.preguntas],
            [p.texto for p in plan_b.preguntas],
        )

    def test_examen_fijo_aleatorio_orden_dificultad_y_contenido_variable(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(valores={"origen_semilla": "aleatorio"}),
        )
        self.assertEqual(resolver_orden_preguntas(preset, cfg), "dificultad")
        self.assertFalse(contenido_examen_estable(preset, cfg=cfg))
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        self.assertEqual(kwargs["orden_preguntas"], "dificultad")
        with patch(
            "Comun.semillas.semilla_partida_aleatoria",
            side_effect=[111, 222],
        ):
            sem_a = semilla_desde_preset(preset, cfg)
            sem_b = semilla_desde_preset(preset, cfg)
        self.assertNotEqual(sem_a, sem_b)

    def test_examen_fijo_semilla_personalizada(self) -> None:
        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg = self._validar(
            preset,
            ConfigPresetHistoria(
                valores={"origen_semilla": "semilla", "semilla": 424242},
            ),
        )
        self.assertEqual(resolver_orden_preguntas(preset, cfg), "dificultad")
        self.assertTrue(contenido_examen_estable(preset, cfg=cfg))
        self.assertEqual(semilla_desde_preset(preset, cfg), 424242)
        kwargs = argumentos_generador(preset, cfg, materias_meta=self.materias_meta)
        plan = generar_examen(
            self.preguntas,
            materias_orden=self.orden,
            materias_meta=self.materias_meta,
            stats=self.stats,
            semilla=424242,
            **kwargs,
        )
        self.assertEqual(len(plan.preguntas), 24)

    def test_examen_fijo_semilla_bloqueada_si_no_es_modo_semilla(self) -> None:
        from Comun.config_historia import (
            aplicar_exclusion_al_cambiar_ambito,
            filtro_ambito_bloqueado,
        )

        preset = next(p for p in self.presets if p.id == "examen_fijo")
        cfg = self._config_defecto(preset)
        self.assertTrue(
            filtro_ambito_bloqueado(
                "semilla", cfg.valores, preset.opciones, preset_id="examen_fijo"
            )
        )
        cfg.valores["origen_semilla"] = "semilla"
        aplicar_exclusion_al_cambiar_ambito(cfg.valores, "origen_semilla")
        self.assertFalse(
            filtro_ambito_bloqueado(
                "semilla", cfg.valores, preset.opciones, preset_id="examen_fijo"
            )
        )
        self.assertEqual(cfg.get_int("semilla"), semilla_examen_dia())


class TestPresetsEspeciales(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets = cargar_presets_especiales(resolver_presets())

    def test_catalogo_especiales(self) -> None:
        ids = [p.id for p in self.presets]
        self.assertEqual(
            ids,
            ["escape_room", "ranking_resistencia"],
        )
        escape = next(p for p in self.presets if p.id == "escape_room")
        self.assertEqual(escape.contexto_reglas, "escape")
        for preset in self.presets:
            if preset.id == "escape_room":
                continue
            self.assertEqual(preset.contexto_reglas, "resistencia")
            self.assertFalse(preset.tiene_opciones())
        self.assertFalse(escape.tiene_opciones())

if __name__ == "__main__":
    unittest.main()
