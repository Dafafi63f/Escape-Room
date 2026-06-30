#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import unittest

from Comun.config_historia import (
    ConfigPresetHistoria,
    ID_ESTRATEGIA_MATERIAS,
    ID_ESTRATEGIA_PRACTICA,
    opciones_config_historia,
    opcion_historia_soportada,
    sanitizar_estrategia_config,
    usar_analisis_historico_desde_config,
    usar_analisis_local_desde_config,
    usar_ponderacion_desde_config,
    valores_estrategia_historica,
    valores_estrategia_practica,
)
from Comun.perfil_contenido import PerfilContenido
from Comun.presets_historia import buscar_preset


class TestCapacidadesHistoria(unittest.TestCase):
    def test_sin_historico_pero_con_listado_permite_historia(self) -> None:
        perfil = PerfilContenido(
            analisis_historico_disponible=False,
            tiene_historico=False,
        )
        self.assertTrue(perfil.modo_historia_disponible)

    def test_estrategias_sin_historico_solo_practica(self) -> None:
        perfil = PerfilContenido(analisis_historico_disponible=False)
        vals = {v for v, _ in valores_estrategia_practica()}
        self.assertEqual(
            vals,
            {"sin_historico", "debilidades", "fortalezas", "equilibrado"},
        )

    def test_estrategias_historico_sin_plan_curricular(self) -> None:
        perfil = PerfilContenido(
            analisis_historico_disponible=True,
            tiene_metadatos_curriculares=False,
        )
        vals = {v for v, _ in valores_estrategia_historica(perfil)}
        self.assertNotIn("curricular", vals)
        self.assertEqual(
            vals,
            {"debilidades", "fortalezas", "equilibrado", "sin_historico"},
        )

    def test_opciones_historia_incluyen_ambos_filtros(self) -> None:
        perfil = PerfilContenido(analisis_historico_disponible=True)
        preset = buscar_preset("repaso")
        ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
        self.assertIn(ID_ESTRATEGIA_MATERIAS, ids)
        self.assertIn(ID_ESTRATEGIA_PRACTICA, ids)

    def test_opciones_sin_historico_solo_practica(self) -> None:
        perfil = PerfilContenido(analisis_historico_disponible=False)
        preset = buscar_preset("examen_fijo")
        ids = {o.id for o in opciones_config_historia(preset, perfil=perfil)}
        self.assertNotIn(ID_ESTRATEGIA_MATERIAS, ids)
        self.assertIn(ID_ESTRATEGIA_PRACTICA, ids)

    def test_etiquetas_estrategia_diferencian_historico_y_practica(self) -> None:
        from Comun.config_historia import (
            etiqueta_campo_estrategia_materias,
            etiqueta_campo_estrategia_practica,
            tooltip_valor_estrategia_historica,
            tooltip_valor_estrategia_practica,
        )

        perfil_hist = PerfilContenido(analisis_historico_disponible=True)
        hist = dict(valores_estrategia_historica(perfil_hist))
        pract = dict(valores_estrategia_practica())
        self.assertNotEqual(hist["equilibrado"], pract["equilibrado"])
        self.assertNotEqual(hist["sin_historico"], pract["sin_historico"])
        self.assertIn("MatCAD", etiqueta_campo_estrategia_materias(perfil_hist))
        self.assertIn("práctica", etiqueta_campo_estrategia_practica())
        self.assertIn("MatCAD", tooltip_valor_estrategia_historica("debilidades") or "")
        self.assertIn("práctica", tooltip_valor_estrategia_practica("debilidades") or "")

    def test_todos_los_presets_historia_tienen_prioridad(self) -> None:
        perfil = PerfilContenido(analisis_historico_disponible=False)
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

        perfil = PerfilContenido(
            analisis_historico_disponible=False,
            csv_minimal=True,
        )
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
        self.assertTrue(kwargs["usar_analisis_historico"])
        self.assertTrue(kwargs["seleccion_plana"])
        self.assertEqual(kwargs["perfil"], PerfilPedagogico.REFUERZO)

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
        cfg = ConfigPresetHistoria(valores={ID_ESTRATEGIA_PRACTICA: "debilidades"})
        sanitizar_estrategia_config(cfg, perfil)
        self.assertEqual(cfg.get_str(ID_ESTRATEGIA_PRACTICA), "debilidades")
        self.assertFalse(
            usar_analisis_historico_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertTrue(
            usar_analisis_local_desde_config(preset, cfg, perfil=perfil)
        )

    def test_filtros_independientes_con_historico(self) -> None:
        preset = buscar_preset("repaso")
        perfil = PerfilContenido(analisis_historico_disponible=True)
        cfg = ConfigPresetHistoria(
            valores={
                ID_ESTRATEGIA_MATERIAS: "sin_historico",
                ID_ESTRATEGIA_PRACTICA: "debilidades",
            }
        )
        self.assertFalse(
            usar_analisis_historico_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertTrue(
            usar_analisis_local_desde_config(preset, cfg, perfil=perfil)
        )
        self.assertTrue(
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
