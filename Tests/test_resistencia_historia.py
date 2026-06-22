#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pool, escalada y ranking del modo resistencia.

Secciones:
- test_resistencia_historia.py
- test_ranking_resistencia.py
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

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.politica_reglas import ContextoPartida, validar_reglas  # noqa: E402
from Comun.presets_historia import aplicar_preset, cargar_presets_especiales, cargar_presets_historia  # noqa: E402
from Comun.ranking_resistencia import (  # noqa: E402
    invalidar_cache_ranking,
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
    construir_banco_resistencia,
    eventos_aleatorios_para_pregunta,
    indices_candidatos_resistencia,
    parametros_eventos_aleatorios,
)
from Comun.estado_resistencia import EstadoResistencia  # noqa: E402
from Comun.probabilidad_resistencia import PREGUNTAS_HASTA_EXTREMO_PROB  # noqa: E402
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_plantillas,
    resolver_presets_especiales,
    resolver_presets_historia,
)


def _reset_estado_ranking() -> None:
    import Comun.ranking_resistencia as rr

    rr.invalidar_cache_ranking()
    rr._modo_sesion_activo = False


class TestResistenciaHistoria(unittest.TestCase):
    def setUp(self) -> None:
        _reset_estado_ranking()

    @classmethod
    def setUpClass(cls) -> None:
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.banco = construir_banco_resistencia(
            cls.preguntas,
            cls.materias_meta,
            path_plantillas=resolver_plantillas(),
            path_preguntas_csv=resolver_dataset(),
        )
        cls.pool = cls.banco.pool_completo()
        cls.preset = next(
            p for p in cargar_presets_especiales(resolver_presets_especiales())
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
        er = EstadoResistencia()
        er.banco_resistencia = self.banco
        sel = crear_seleccion_resistencia(self.pool)
        for numero in (1, 16, 121, 501):
            escalada = escalada_para_pregunta(numero)
            idx = elegir_indice_resistencia(
                self.pool, sel, escalada, numero_pregunta=numero, er=er
            )
            self.assertIsNotNone(idx)

    def test_banco_dinamico_solo_revisado_al_inicio(self) -> None:
        if not self.banco.plantillas:
            self.skipTest("Sin plantillas beta fuera del dataset")
        er = EstadoResistencia()
        er.banco_resistencia = self.banco
        sel = crear_seleccion_resistencia(self.pool)
        escalada = escalada_para_pregunta(1)
        n_rev = self.banco.n_revisadas
        for _ in range(50):
            idx = elegir_indice_resistencia(
                self.pool, sel, escalada, numero_pregunta=1, er=er
            )
            self.assertIsNotNone(idx)
            self.assertLess(idx, n_rev)

    def test_banco_dinamico_desbloquea_plantillas(self) -> None:
        if not self.banco.plantillas:
            self.skipTest("Sin plantillas beta fuera del dataset")
        er = EstadoResistencia()
        er.banco_resistencia = self.banco
        sel = crear_seleccion_resistencia(self.pool)
        numero = PREGUNTAS_HASTA_EXTREMO_PROB + 5
        escalada = escalada_para_pregunta(numero)
        candidatas = indices_candidatos_resistencia(
            self.pool, sel, escalada, numero, solo_no_usadas=False, er=er
        )
        n_rev = self.banco.n_revisadas
        self.assertTrue(any(idx >= n_rev for idx in candidatas))

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
        from Comun.probabilidad_resistencia import probabilidad_evento_bueno_escalada

        self.assertEqual(parametros_eventos_aleatorios(4)[:2], (0.0, 0.0))
        prob_b, prob_m, max_malos, max_buenos, _ = parametros_eventos_aleatorios(10)
        self.assertGreater(prob_b, prob_m)
        self.assertGreater(prob_b, 0.7)
        self.assertLess(prob_m, 0.15)
        self.assertLess(probabilidad_evento_bueno_escalada(10), 0.25)
        self.assertEqual(max_malos, 1)
        self.assertEqual(max_buenos, 1)
        con_evento = [
            r
            for r in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 25)
            if eventos_aleatorios_para_pregunta(r)
        ]
        self.assertGreater(len(con_evento), 0)

    def test_curvas_buena_y_mala_opuestas(self) -> None:
        prob_b_ini, prob_m_ini, _, _, int_ini = parametros_eventos_aleatorios(8)
        prob_b_tar, prob_m_tar, _, _, int_tar = parametros_eventos_aleatorios(200)
        self.assertGreater(prob_b_ini, prob_b_tar)
        self.assertGreater(prob_m_tar, prob_m_ini)
        self.assertGreater(int_tar, int_ini)
        self.assertGreater(prob_b_ini, prob_m_ini)
        self.assertGreater(prob_m_tar, prob_b_tar)

    def test_punto_medio_probabilidades_equilibradas(self) -> None:
        from Comun.probabilidad_resistencia import (
            PREGUNTAS_HASTA_EXTREMO_PROB,
            probabilidad_buena_resistencia,
            probabilidad_mala_resistencia,
        )

        medio = PREGUNTA_MIN_EVENTOS_ALEATORIOS + PREGUNTAS_HASTA_EXTREMO_PROB // 2
        prob_b = probabilidad_buena_resistencia(medio)
        prob_m = probabilidad_mala_resistencia(medio)
        self.assertAlmostEqual(prob_b, prob_m, delta=0.05)
        self.assertAlmostEqual(prob_b, 0.465, delta=0.05)

    def test_relampago_mas_duro_con_pregunta_alta(self) -> None:
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

    def test_sin_sorpresa_dificil_en_eventos(self) -> None:
        for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 120):
            for ev in eventos_aleatorios_para_pregunta(n):
                self.assertIsNone(ev.min_max_complejidad)

    def test_eventos_malos_y_buenos_cupos_independientes(self) -> None:
        from unittest.mock import patch

        class _Rng:
            def __init__(self) -> None:
                self._i = 0
                self._vals = (0.0, 0.0)

            def random(self) -> float:
                v = self._vals[self._i % len(self._vals)]
                self._i += 1
                return v

            def shuffle(self, xs: list) -> None:
                xs.reverse()

        rng = _Rng()
        with (
            patch(
                "Comun.resistencia_historia.parametros_eventos_aleatorios",
                return_value=(1.0, 1.0, 1, 1, 0.8),
            ),
            patch("Comun.resistencia_historia.random.Random", return_value=rng),
        ):
            eventos = eventos_aleatorios_para_pregunta(50)
        self.assertEqual(len(eventos), 2)
        malos = sum(1 for e in eventos if e.tiempo_pregunta or e.opciones_ocultas or e.fraccion_enunciado)
        buenos = sum(1 for e in eventos if e.multiplicador_puntos)
        self.assertEqual(malos, 1)
        self.assertEqual(buenos, 1)

    def test_avisos_sin_tope_global_de_popups(self) -> None:
        from Comun.motor_resistencia_comun import avisos_pre_pregunta_resistencia

        extras = [f"Recompensa {i}" for i in range(4)]
        avisos = avisos_pre_pregunta_resistencia(
            self.pool[0],
            120,
            avisos_extra=extras,
            er=EstadoResistencia(semilla_partida=1),
        )
        self.assertGreaterEqual(len(avisos), len(extras))

# --- test_ranking_resistencia.py ---

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_JUEGO = Path(__file__).resolve().parents[1] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.preferencias_ranking import (  # noqa: E402
    ModoRetencionRanking,
    PreferenciasRanking,
)
from Comun.ranking_resistencia import (  # noqa: E402
    RecordResistencia,
    aplicar_retencion,
    finalizar_ranking_al_salir,
    inicializar_ranking_sesion,
    invalidar_cache_ranking,
    registrar_partida,
    top_records,
    variante_desde_preset,
)
from Comun.reto_dia_resistencia import ID_PRESET_RETO_DIA  # noqa: E402


class TestRankingResistencia(unittest.TestCase):
    def setUp(self) -> None:
        _reset_estado_ranking()

    def tearDown(self) -> None:
        _reset_estado_ranking()

    def test_variantes_separadas_por_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_inf = Path(tmp) / "ranking_resistencia_infinita.json"
            path_dia = Path(tmp) / "ranking_reto_dia.json"

            def _path(preset_id: str) -> Path:
                return path_dia if preset_id == ID_PRESET_RETO_DIA else path_inf

            with patch("Comun.ranking_resistencia.path_ranking_para_preset", _path):
                registrar_partida(
                    path_inf,
                    nombre="Ana",
                    racha=3,
                    puntos=50,
                    respondidas=5,
                    preset_id="ranking_resistencia",
                )
                registrar_partida(
                    path_dia,
                    nombre="Bob",
                    racha=2,
                    puntos=40,
                    respondidas=4,
                    preset_id=ID_PRESET_RETO_DIA,
                )
                self.assertEqual(len(top_records(path_inf)), 1)
                self.assertEqual(len(top_records(path_dia)), 1)

    def test_reto_dia_se_reinicia_si_cambia_fecha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ranking_reto_dia.json"
            ayer = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
            path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "fecha_reto": ayer,
                        "records": [
                            {
                                "id": "x",
                                "nombre": "Ana",
                                "racha": 1,
                                "puntos": 10,
                                "respondidas": 3,
                                "fecha_iso": datetime.now(timezone.utc).isoformat(),
                                "preset_id": ID_PRESET_RETO_DIA,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            invalidar_cache_ranking()
            self.assertEqual(top_records(path), [])

    def test_modo_sesion_no_persiste_al_salir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_inf = Path(tmp) / "ranking_resistencia_infinita.json"
            path_dia = Path(tmp) / "ranking_reto_dia.json"
            path_inf.write_text('{"version": 1, "records": []}', encoding="utf-8")
            hoy = datetime.now(timezone.utc).date().isoformat()
            path_dia.write_text(
                json.dumps({"version": 2, "fecha_reto": hoy, "records": []}),
                encoding="utf-8",
            )

            def _paths() -> list[Path]:
                return [path_inf, path_dia]

            with (
                patch("Comun.ranking_resistencia._paths_ranking", _paths),
                patch(
                    "Comun.ranking_resistencia.cargar_preferencias",
                    lambda: PreferenciasRanking(modo=ModoRetencionRanking.SESION),
                ),
            ):
                inicializar_ranking_sesion()
                registrar_partida(
                    path_inf,
                    nombre="Ana",
                    racha=3,
                    puntos=50,
                    respondidas=5,
                )
                finalizar_ranking_al_salir()
                invalidar_cache_ranking()
                self.assertEqual(json.loads(path_inf.read_text())["records"], [])

    def test_retencion_7_dias_podas_antiguos(self) -> None:
        viejo = RecordResistencia(
            id="a",
            nombre="Ana",
            racha=1,
            puntos=10,
            respondidas=2,
            fecha_iso=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        )
        reciente = RecordResistencia(
            id="b",
            nombre="Bob",
            racha=2,
            puntos=20,
            respondidas=4,
            fecha_iso=datetime.now(timezone.utc).isoformat(),
        )
        filtrados = aplicar_retencion(
            [viejo, reciente],
            ModoRetencionRanking.DIAS_7,
        )
        self.assertEqual(len(filtrados), 1)

    def test_variante_desde_preset(self) -> None:
        self.assertEqual(variante_desde_preset("ranking_resistencia"), "infinita")
        self.assertEqual(variante_desde_preset(ID_PRESET_RETO_DIA), "reto_dia")

if __name__ == "__main__":
    unittest.main()
