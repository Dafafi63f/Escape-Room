#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capacidades del modo historia según datos disponibles."""

from __future__ import annotations

import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.config_historia import (  # noqa: E402
    ConfigPresetHistoria,
    opcion_historia_soportada,
    opciones_config_historia,
    sanitizar_estrategia_config,
    usar_analisis_historico_desde_config,
    valores_estrategia_materias,
)
from Comun.perfil_contenido import PerfilContenido  # noqa: E402
from Comun.presets_historia import buscar_preset  # noqa: E402


class TestCapacidadesHistoria(unittest.TestCase):
    def test_sin_historico_pero_con_listado_permite_historia(self) -> None:
        perfil = PerfilContenido(
            analisis_historico_disponible=False,
            tiene_historico=False,
        )
        self.assertTrue(perfil.modo_historia_disponible)

    def test_estrategias_sin_historico(self) -> None:
        perfil = PerfilContenido(analisis_historico_disponible=False)
        vals = {v for v, _ in valores_estrategia_materias(perfil)}
        self.assertEqual(vals, {"curricular", "sin_historico"})
        self.assertNotIn("debilidades", vals)

    def test_repaso_sin_metadatos_curriculares_oculta_filtros(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido(tiene_metadatos_curriculares=False)
        ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
        self.assertIn("n_materias", ids)
        self.assertNotIn("periodo", ids)
        self.assertNotIn("curso", ids)
        self.assertNotIn("semestre", ids)

    def test_repaso_area_no_viable_sin_grupos(self) -> None:
        preset = buscar_preset("repaso_area")
        perfil = PerfilContenido(tiene_grupos_tematicos=False)
        viable, motivo = perfil.preset_historia_viable(preset)
        self.assertFalse(viable)
        self.assertIn("grupo", motivo.lower())

    def test_usar_analisis_desactivado_sin_historico(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido(analisis_historico_disponible=False)
        cfg = ConfigPresetHistoria(valores={"estrategia_materias": "debilidades"})
        sanitizar_estrategia_config(cfg, perfil)
        self.assertEqual(cfg.get_str("estrategia_materias"), "curricular")
        self.assertFalse(
            usar_analisis_historico_desde_config(preset, cfg, perfil=perfil)
        )

    def test_enfoque_requiere_tipos(self) -> None:
        from Comun.config_historia import OpcionPreset

        op = OpcionPreset(id="enfoque", tipo="eleccion", etiqueta="Tipo")
        perfil = PerfilContenido(tiene_tipos_pregunta=False)
        self.assertFalse(opcion_historia_soportada(op, perfil))

    def test_portable_examen_fijo_barra_sin_carrusel(self) -> None:
        from Comun.presets_historia import PRESETS_HISTORIA_PORTABLE

        perfil = PerfilContenido(solo_csv=True, csv_minimal=True, modo_minimo=True, tiene_presets=True)
        self.assertFalse(perfil.modo_historia_disponible)
        self.assertTrue(perfil.examen_fijo_barra_completo)
        self.assertTrue(perfil.modos_diarios_disponibles)
        self.assertEqual(PRESETS_HISTORIA_PORTABLE, frozenset())
        preset_ef = buscar_preset("examen_fijo")
        viable, motivo = perfil.preset_historia_viable(preset_ef)
        self.assertFalse(viable)
        self.assertIn("paquete mínimo", motivo.lower())
        preset_repaso = buscar_preset("repaso")
        viable, motivo = perfil.preset_historia_viable(preset_repaso)
        self.assertFalse(viable)
        self.assertIn("paquete mínimo", motivo.lower())
        preset_area = buscar_preset("repaso_area")
        viable, motivo = perfil.preset_historia_viable(preset_area)
        self.assertFalse(viable)
        self.assertIn("paquete mínimo", motivo.lower())


if __name__ == "__main__":
    unittest.main()
