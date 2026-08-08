#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.config_historia import (
    ConfigPresetHistoria,
    ID_ESTRATEGIA_MATERIAS,
    ID_ESTRATEGIA_PRACTICA,
    opciones_config_historia,
    opcion_historia_soportada,
    sanitizar_estrategia_config,
    usar_analisis_local_desde_config,
    usar_ponderacion_desde_config,
    valores_estrategia_practica,
)
from Comun.perfil_contenido import PerfilContenido
from Comun.presets_historia import buscar_preset


class TestCapacidadesHistoria(unittest.TestCase):
    def test_con_listado_permite_historia(self) -> None:
        perfil = PerfilContenido()
        self.assertTrue(perfil.modo_historia_disponible)

    def test_estrategias_solo_practica(self) -> None:
        vals = {v for v, _ in valores_estrategia_practica()}
        self.assertEqual(
            vals,
            {"sin_historico", "debilidades", "fortalezas", "equilibrado"},
        )
        self.assertNotIn("curricular", vals)

    def test_opciones_historia_solo_practica(self) -> None:
        perfil = PerfilContenido()
        preset = buscar_preset("repaso")
        ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
        self.assertNotIn(ID_ESTRATEGIA_MATERIAS, ids)
        self.assertIn(ID_ESTRATEGIA_PRACTICA, ids)

    def test_opciones_examen_fijo_solo_practica(self) -> None:
        perfil = PerfilContenido()
        preset = buscar_preset("examen_fijo")
        ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
        self.assertNotIn(ID_ESTRATEGIA_MATERIAS, ids)
        self.assertIn(ID_ESTRATEGIA_PRACTICA, ids)

    def test_etiquetas_estrategia_practica(self) -> None:
        from Comun.config_historia import (
            etiqueta_campo_estrategia_practica,
            tooltip_valor_estrategia_practica,
        )

        pract = dict(valores_estrategia_practica())
        self.assertEqual(pract["equilibrado"], "Práctica suave")
        self.assertEqual(pract["sin_historico"], "Reparto uniforme")
        self.assertIn("práctica", etiqueta_campo_estrategia_practica())
        self.assertIn("práctica", tooltip_valor_estrategia_practica("debilidades") or "")

    def test_todos_los_presets_historia_tienen_prioridad(self) -> None:
        perfil = PerfilContenido()
        for preset_id in (
            "repaso",
            "repaso_area",
            "simulacro",
            "examen_asignatura",
            "examen_fijo",
        ):
            preset = buscar_preset(preset_id)
            ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
            self.assertIn(ID_ESTRATEGIA_PRACTICA, ids, preset_id)

    def test_examen_fijo_minimal_pondera_con_practica(self) -> None:
        from Comun.generador_examen_historia import PerfilPedagogico
        from Comun.presets_historia import argumentos_generador, config_defecto

        perfil = PerfilContenido(csv_minimal=True)
        preset = buscar_preset("examen_fijo")
        cfg = config_defecto(
            preset,
            materias_meta={},
            materias_orden=[],
            perfil=perfil,
        )
        cfg.valores[ID_ESTRATEGIA_PRACTICA] = "debilidades"
        kwargs = argumentos_generador(
            preset, cfg, materias_meta={}, perfil_datos=perfil
        )
        self.assertTrue(kwargs.usar_analisis_historico)
        self.assertTrue(kwargs.seleccion_plana)
        self.assertEqual(kwargs.perfil, PerfilPedagogico.REFUERZO)

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

    def test_sanitizar_migra_legacy_estrategia_materias(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido()
        cfg = ConfigPresetHistoria(
            valores={ID_ESTRATEGIA_MATERIAS: "debilidades"}
        )
        sanitizar_estrategia_config(cfg, perfil)
        self.assertIsNone(cfg.get_str(ID_ESTRATEGIA_MATERIAS))
        self.assertEqual(cfg.get_str(ID_ESTRATEGIA_PRACTICA), "debilidades")
        self.assertTrue(
            usar_analisis_local_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertTrue(
            usar_ponderacion_desde_config(preset, cfg, perfil=perfil)
        )

    def test_ponderacion_por_practica_local(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido()
        cfg = ConfigPresetHistoria(
            valores={ID_ESTRATEGIA_PRACTICA: "debilidades"}
        )
        self.assertTrue(
            usar_analisis_local_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertTrue(
            usar_ponderacion_desde_config(preset, cfg, perfil=perfil)
        )

    def test_sin_ponderacion_reparto_uniforme(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido()
        cfg = ConfigPresetHistoria(
            valores={ID_ESTRATEGIA_PRACTICA: "sin_historico"}
        )
        self.assertFalse(
            usar_analisis_local_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertFalse(
            usar_ponderacion_desde_config(preset, cfg, perfil=perfil)
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


if __name__ == "__main__":
    unittest.main()
