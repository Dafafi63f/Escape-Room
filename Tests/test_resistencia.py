#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo resistencia: partida, ranking, motor, exclusivas e iconos."""

from __future__ import annotations

import json
import random
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta  # noqa: E402
from Comun.politica_reglas import ContextoPartida, validar_reglas  # noqa: E402
from Comun.preguntas_resistencia import (  # noqa: E402
    cargar_preguntas_exclusivas_resistencia,
    construir_banco_resistencia,
)
from Comun.presets_historia import aplicar_preset, cargar_presets_especiales  # noqa: E402
from Comun.preferencias_ranking import ModoRetencionRanking, PreferenciasRanking  # noqa: E402
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
from Comun.reglas_partida import preset_resistencia  # noqa: E402
from Comun.resistencia_motor import EstadoResistencia, PREGUNTAS_HASTA_EXTREMO_PROB  # noqa: E402
from Comun.resistencia_motor import texto_progreso_resistencia  # noqa: E402
from Comun.resistencia_partida import (  # noqa: E402
    PREGUNTA_MIN_EVENTOS_ALEATORIOS,
    avisos_pre_pregunta_resistencia,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    eventos_aleatorios_para_pregunta,
    indices_candidatos_resistencia,
    parametros_eventos_aleatorios,
    probabilidad_pregunta_exclusiva,
)
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_plantillas,
    resolver_presets,
    resolver_preguntas_resistencia,
)


class TestResistenciaPartida(unittest.TestCase):
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
            p for p in cargar_presets_especiales(resolver_presets())
            if p.id == "ranking_resistencia"
        )

    def test_preset_en_catalogo_especiales(self) -> None:
        self.assertEqual(self.preset.contexto_reglas, ContextoPartida.RESISTENCIA.value)

    def test_reglas_tres_vidas(self) -> None:
        reglas = validar_reglas(
            preset_resistencia(),
            ContextoPartida.RESISTENCIA,
        )
        self.assertEqual(reglas.vidas, 3)
        self.assertIsNone(reglas.tiempo_por_pregunta_seg)

    def test_aplicar_preset(self) -> None:
        reglas = aplicar_preset(self.preset, None)
        self.assertEqual(reglas.sistema_puntuacion.value, "arcade")

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

    def test_elegir_preguntas_en_escalada(self) -> None:
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

    def test_eventos_aleatorios_antes_de_25(self) -> None:
        from Comun.resistencia_motor import probabilidad_evento_bueno_escalada

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
        from Comun.resistencia_motor import (
            probabilidad_buena_resistencia,
            probabilidad_mala_resistencia,
        )

        medio = PREGUNTA_MIN_EVENTOS_ALEATORIOS + PREGUNTAS_HASTA_EXTREMO_PROB // 2
        prob_b = probabilidad_buena_resistencia(medio)
        prob_m = probabilidad_mala_resistencia(medio)
        self.assertAlmostEqual(prob_b, prob_m, delta=0.05)
        self.assertAlmostEqual(prob_b, 0.465, delta=0.05)

    def test_relampago_solo_sin_tiempo_base(self) -> None:
        from Comun.eventos_partida import malos_resistencia_vigentes

        self.assertIn(
            "relampago",
            malos_resistencia_vigentes(
                15,
                tiempo_baseline=None,
                fraccion_baseline=1.0,
                opciones_baseline=0,
            ),
        )
        self.assertNotIn(
            "relampago",
            malos_resistencia_vigentes(
                56,
                tiempo_baseline=30,
                fraccion_baseline=0.72,
                opciones_baseline=0,
            ),
        )

    def test_relampago_aleatorio_solo_antes_de_tiempo_base(self) -> None:
        relampagos = [
            e
            for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 25)
            for e in eventos_aleatorios_para_pregunta(n, semilla_partida=11)
            if e.tiempo_pregunta is not None
        ]
        self.assertGreater(len(relampagos), 0)
        tardios = [
            e
            for n in range(120, 200)
            for e in eventos_aleatorios_para_pregunta(n, semilla_partida=11)
            if e.tiempo_pregunta is not None
        ]
        self.assertEqual(tardios, [])

    def test_escalada_incluye_niebla_base_en_fases_altas(self) -> None:
        from Comun.resistencia_partida import baseline_escalada_resistencia

        b26 = baseline_escalada_resistencia(26)
        self.assertLess(b26.fraccion_enunciado, 1.0)
        self.assertIsNotNone(b26.tiempo_pregunta_seg)
        b151 = baseline_escalada_resistencia(151)
        self.assertLessEqual(b151.fraccion_enunciado, 0.55)
        b351 = baseline_escalada_resistencia(351)
        self.assertGreaterEqual(b351.opciones_ocultas, 1)

    def test_malos_exclusivos_un_tiempo_y_una_niebla(self) -> None:
        from Comun.eventos_partida import (
            elegir_malos_resistencia_exclusivos,
            familia_malo_resistencia,
        )
        import random

        rng = random.Random(0)
        kinds = (
            "relampago",
            "opciones_ocultas",
            "enunciado_oculto",
            "niebla_ambos",
        )
        elegidos = elegir_malos_resistencia_exclusivos(kinds, 3, rng)
        familias = [
            familia_malo_resistencia(k) for k in elegidos if familia_malo_resistencia(k)
        ]
        self.assertEqual(len(familias), len(set(familias)))
        self.assertLessEqual(len(elegidos), 2)

    def test_desafio_bloque_completa_y_limpia_estado(self) -> None:
        from Comun.resistencia_motor import (
            DesafioBloqueTiempoResistencia,
            procesar_post_turno_resistencia,
        )

        er = EstadoResistencia()
        er.desafio_bloque = DesafioBloqueTiempoResistencia(
            aciertos_objetivo=2,
            tiempo_limite_seg=60,
        )
        avisos = procesar_post_turno_resistencia(er, acierto=True, numero_pregunta=150)
        self.assertEqual(er.desafio_bloque.aciertos_logrados, 1)
        self.assertEqual(avisos, [])
        avisos = procesar_post_turno_resistencia(er, acierto=True, numero_pregunta=151)
        self.assertIsNone(er.desafio_bloque)
        self.assertTrue(any("superado" in a for a in avisos))

    def test_desafio_bloque_expirado_finaliza_partida(self) -> None:
        import time
        from Comun.resistencia_motor import (
            DesafioBloqueTiempoResistencia,
            desafio_bloque_expirado,
            finalizar_partida_por_desafio_bloque,
        )

        er = EstadoResistencia()
        estado = EstadoPartida(nombre="T", reglas=preset_resistencia(), vidas_restantes=3)
        er.desafio_bloque = DesafioBloqueTiempoResistencia(
            aciertos_objetivo=3,
            tiempo_limite_seg=1,
            inicio_monotonic=time.monotonic() - 5,
        )
        self.assertTrue(desafio_bloque_expirado(er))
        msg = finalizar_partida_por_desafio_bloque(estado, er)
        self.assertIn("tiempo agotado", msg.lower())
        self.assertEqual(estado.vidas_restantes, 0)
        self.assertIsNone(er.desafio_bloque)

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

    def test_sin_niebla_en_eventos_malos_tempranos(self) -> None:
        from Comun.eventos_partida import (
            PREGUNTA_MIN_NIEBLA_RESISTENCIA,
            ids_eventos_malos_resistencia_para,
        )

        self.assertEqual(ids_eventos_malos_resistencia_para(10), ("relampago",))
        self.assertIn(
            "opciones_ocultas",
            ids_eventos_malos_resistencia_para(PREGUNTA_MIN_NIEBLA_RESISTENCIA),
        )

    def test_pity_resistencia_incrementa_y_resetea(self) -> None:
        from Comun.eventos_partida import evento_resistencia_aleatorio
        from Comun.resistencia_partida import (
            actualizar_pity_eventos_resistencia,
            kind_de_evento_resistencia,
            PityEventosResistencia,
        )

        pity = PityEventosResistencia()
        relampago = evento_resistencia_aleatorio("relampago", 0.8, numero_pregunta=50)
        self.assertEqual(kind_de_evento_resistencia(relampago), "relampago")
        actualizar_pity_eventos_resistencia(
            pity,
            (relampago,),
            numero_pregunta=10,
            kinds_vigentes=("relampago", "opciones_ocultas"),
        )
        self.assertEqual(pity.preguntas_sin_malo, 0)
        self.assertEqual(pity.preguntas_sin_bueno, 1)
        self.assertEqual(pity.preguntas_sin_por_kind["relampago"], 0)
        self.assertEqual(pity.preguntas_sin_por_kind["opciones_ocultas"], 1)

    def test_pity_resistencia_alto_favorece_tipo_ausente(self) -> None:
        from Comun.eventos_partida import elegir_malos_resistencia_exclusivos
        from Comun.resistencia_partida import PityEventosResistencia
        import random

        kinds = ("relampago", "opciones_ocultas", "enunciado_oculto")
        pity = PityEventosResistencia(
            preguntas_sin_por_kind={
                "relampago": 12,
                "opciones_ocultas": 0,
                "enunciado_oculto": 0,
                "niebla_ambos": 0,
                "doble": 0,
            }
        )
        pesos = {k: 1.0 + pity.preguntas_sin_por_kind.get(k, 0) * 0.22 for k in kinds}
        vistos: set[str] = set()
        for semilla in range(40):
            rng = random.Random(semilla)
            elegidos = elegir_malos_resistencia_exclusivos(
                kinds, 1, rng, pesos=pesos
            )
            vistos.update(elegidos)
        self.assertIn("relampago", vistos)

    def test_pity_resistencia_cache_coherente_escalada_y_avisos(self) -> None:
        from Comun.resistencia_partida import PityEventosResistencia

        er = EstadoResistencia(semilla_partida=99)
        escalada_para_pregunta(20, semilla_partida=99, pity=er.pity_eventos)
        avisos = avisos_pre_pregunta_resistencia(
            self.pool[0], 20, er=er
        )
        eventos = er.pity_eventos._cache_eventos
        self.assertEqual(er.pity_eventos._cache_pregunta, 20)
        if eventos:
            self.assertGreaterEqual(len(avisos), len(eventos))

    def test_eventos_malos_y_buenos_cupos_independientes(self) -> None:
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
                "Comun.resistencia_partida.parametros_eventos_aleatorios",
                return_value=(1.0, 1.0, 1, 1, 0.8),
            ),
            patch("Comun.resistencia_partida.random.Random", return_value=rng),
        ):
            eventos = eventos_aleatorios_para_pregunta(50)
        self.assertEqual(len(eventos), 2)
        malos = sum(
            1 for e in eventos if e.tiempo_pregunta or e.opciones_ocultas or e.fraccion_enunciado
        )
        buenos = sum(1 for e in eventos if e.multiplicador_puntos)
        self.assertEqual(malos, 1)
        self.assertEqual(buenos, 1)

    def test_avisos_sin_tope_global_de_popups(self) -> None:
        extras = [f"Recompensa {i}" for i in range(4)]
        avisos = avisos_pre_pregunta_resistencia(
            self.pool[0],
            120,
            avisos_extra=extras,
            er=EstadoResistencia(semilla_partida=1),
        )
        self.assertGreaterEqual(len(avisos), len(extras))


def _reset_estado_ranking() -> None:
    import Comun.ranking_resistencia as rr

    rr.invalidar_cache_ranking()
    rr._modo_sesion_activo = False


class TestRankingResistencia(unittest.TestCase):
    def setUp(self) -> None:
        _reset_estado_ranking()

    def tearDown(self) -> None:
        _reset_estado_ranking()

    def test_guarda_y_ordena(self) -> None:
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

    def test_registro_en_variante_resistencia(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_ranking = Path(tmp) / "ranking_resistencia.json"

            with patch(
                "Comun.ranking_resistencia.path_ranking_para_preset",
                return_value=path_ranking,
            ):
                registrar_partida(
                    path_ranking,
                    nombre="Ana",
                    racha=3,
                    puntos=50,
                    respondidas=5,
                    preset_id="ranking_resistencia",
                )
                self.assertEqual(len(top_records(path_ranking)), 1)

    def test_modo_sesion_no_persiste_al_salir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_ranking = Path(tmp) / "ranking_resistencia.json"
            path_ranking.write_text('{"version": 1, "records": []}', encoding="utf-8")

            with (
                patch("Comun.ranking_resistencia._path_ranking", return_value=path_ranking),
                patch(
                    "Comun.datos_locales_juego.inicializar_datos_locales_juego",
                    lambda: None,
                ),
                patch(
                    "Comun.ranking_resistencia.cargar_preferencias",
                    lambda: PreferenciasRanking(modo=ModoRetencionRanking.SESION),
                ),
            ):
                inicializar_ranking_sesion()
                registrar_partida(
                    path_ranking,
                    nombre="Ana",
                    racha=3,
                    puntos=50,
                    respondidas=5,
                )
                finalizar_ranking_al_salir()
                invalidar_cache_ranking()
                self.assertEqual(json.loads(path_ranking.read_text())["records"], [])

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
        self.assertEqual(variante_desde_preset("ranking_resistencia"), "resistencia")
        self.assertEqual(variante_desde_preset("otro"), "resistencia")


class TestMecanicasResistencia(unittest.TestCase):
    def test_texto_progreso_resistencia(self) -> None:
        er = EstadoResistencia(racha=3)
        txt = texto_progreso_resistencia(er, 10)
        self.assertEqual(txt, "#10 · Racha 3")

    def test_bloque_grupo_usa_nombre_tematico(self) -> None:
        from Comun.resistencia_motor import _descripcion_grupo_tematico
        from Comun.modelos import Pregunta

        pool = [
            Pregunta(
                texto="Q",
                materia="Física",
                tematica="",
                dificultad="Facil",
                tipo="Teoria",
                grupo="10",
                nivel="",
                curso="2",
                semestre="4",
                correcta="A",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            )
        ]
        desc = _descripcion_grupo_tematico("10", pool)
        self.assertIn("Modelización física", desc)
        self.assertNotIn("grupo 10", desc)

    def test_bloque_filtro_restaura_al_expirar(self) -> None:
        from Comun.resistencia_motor import BloqueFiltroActivo, consumir_bloque_filtro

        er = EstadoResistencia()
        er.bloque_filtro = BloqueFiltroActivo(
            etiqueta="Bloque: 2 preguntas de Teoría",
            preguntas_restantes=2,
            tipo="Teoria",
        )
        consumir_bloque_filtro(er)
        self.assertIsNotNone(er.bloque_filtro)
        self.assertEqual(er.bloque_filtro.preguntas_restantes, 1)
        consumir_bloque_filtro(er)
        self.assertIsNone(er.bloque_filtro)

    def test_apuestas_variedad_riesgo_recompensa(self) -> None:
        from Comun.resistencia_motor import (
            APUESTAS_DISPONIBLES,
            ApuestaRiesgo,
            CosteApuesta,
            RecompensaApuesta,
            _elegir_apuesta,
            formatear_aviso_apuesta,
            oferta_apuesta_para_pregunta,
            rng_partida,
        )

        tipos_recompensa = {
            (
                a.recompensa.mult_puntos > 1,
                a.recompensa.delta_vidas > 0,
                bool(a.recompensa.powerup_id or a.recompensa.powerup_aleatorio),
            )
            for a in APUESTAS_DISPONIBLES
        }
        self.assertGreaterEqual(len(tipos_recompensa), 3)
        tipos_coste = {
            (
                a.coste.vidas_fallo > 1,
                a.coste.puntos_perdidos > 0,
                a.coste.pierde_powerup_aleatorio or a.coste.pierde_todos_objetos,
                a.coste.fin_partida,
            )
            for a in APUESTAS_DISPONIBLES
        }
        self.assertTrue(any(t[3] for t in tipos_coste))
        self.assertTrue(any(t[2] for t in tipos_coste))
        self.assertGreaterEqual(len(APUESTAS_DISPONIBLES), 8)

        er = EstadoResistencia(semilla_partida=42)
        vistos: set[str] = set()
        for n in range(8, 120):
            rng = rng_partida(er, n * 53 + 4049)
            if rng.random() > 0.5:
                continue
            ap = _elegir_apuesta(rng, n)
            vistos.add(ap.etiqueta)
        self.assertGreaterEqual(len(vistos), 3)

        suave = formatear_aviso_apuesta(
            ApuestaRiesgo(
                "Prueba",
                RecompensaApuesta(mult_puntos=2),
                CosteApuesta(vidas_fallo=1),
            )
        )
        self.assertIn("como de costumbre", suave)
        mortal = formatear_aviso_apuesta(
            ApuestaRiesgo(
                "Última carta",
                RecompensaApuesta(mult_puntos=4),
                CosteApuesta(fin_partida=True),
            )
        )
        self.assertIn("termina al instante", mortal)
        botin = formatear_aviso_apuesta(
            ApuestaRiesgo(
                "Botín",
                RecompensaApuesta(powerup_aleatorio=True),
                CosteApuesta(puntos_perdidos=30),
            )
        )
        self.assertIn("objeto al azar", botin)
        self.assertIn("−30 puntos", botin)

        er2 = EstadoResistencia(semilla_partida=99)
        oferta = None
        for n in range(8, 80):
            candidata = oferta_apuesta_para_pregunta(n, er2)
            if candidata is not None:
                oferta = candidata
                break
        self.assertIsNotNone(oferta)
        self.assertIn(oferta, APUESTAS_DISPONIBLES)

    def test_presion_racha_sin_efecto_bajo_umbral(self) -> None:
        from Comun.resistencia_motor import (
            intensidad_presion_racha,
            preparar_presion_racha_turno,
            presion_racha_umbral,
        )

        self.assertEqual(presion_racha_umbral(), 25)
        self.assertEqual(intensidad_presion_racha(24), 0.0)
        er = EstadoResistencia(semilla_partida=1, racha=20)
        self.assertIsNone(preparar_presion_racha_turno(er, numero_pregunta=30))
        self.assertEqual(er.presion_racha_intensidad, 0.0)
        self.assertEqual(er.racha, 20)

    def test_presion_racha_endurece_pregunta_sin_quitar_vida(self) -> None:
        from Comun.resistencia_motor import (
            aplicar_presion_racha_modificadores,
            preparar_presion_racha_turno,
        )
        from Comun.modelos import Pregunta
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import preset_resistencia

        er = EstadoResistencia(semilla_partida=9, racha=50)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        aviso = preparar_presion_racha_turno(er, numero_pregunta=50)
        self.assertIsNotNone(aviso)
        self.assertGreater(er.presion_racha_intensidad, 0.5)
        self.assertLess(er.presion_racha_intensidad, 1.0)
        p = Pregunta(
            texto="¿2+2?",
            materia="MAT",
            tematica="",
            dificultad="Facil",
            tipo="test",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            correcta="B",
            opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        )
        aplicar_presion_racha_modificadores(er, p, numero_pregunta=50)
        self.assertEqual(er.racha, 50)
        self.assertEqual(estado.vidas_restantes, 3)
        self.assertLess(er.fraccion_enunciado, 1.0)
        self.assertTrue(er.letras_ocultas)

    def test_racha_extrema_un_tiempo_y_una_niebla_como_maximo(self) -> None:
        from Comun.resistencia_partida import eventos_aleatorios_para_pregunta

        eventos = eventos_aleatorios_para_pregunta(
            50, semilla_partida=3, racha=100
        )
        n_tiempo = sum(1 for e in eventos if e.tiempo_pregunta is not None)
        n_niebla = sum(
            1
            for e in eventos
            if (e.opciones_ocultas or 0) > 0 or e.fraccion_enunciado is not None
        )
        self.assertLessEqual(n_tiempo, 1)
        self.assertLessEqual(n_niebla, 1)
        self.assertGreater(n_tiempo + n_niebla, 0)
        self.assertFalse(any(e.multiplicador_puntos for e in eventos))

    def test_racha_extrema_aplica_maldiciones_presion(self) -> None:
        from Comun.resistencia_motor import (
            aplicar_presion_racha_modificadores,
            preparar_presion_racha_turno,
        )
        from Comun.modelos import Pregunta

        er = EstadoResistencia(semilla_partida=2, racha=100)
        preparar_presion_racha_turno(er, numero_pregunta=60)
        self.assertGreater(er.presion_racha_intensidad, 1.0)
        p = Pregunta(
            texto="¿2+2?",
            materia="MAT",
            tematica="",
            dificultad="Facil",
            tipo="test",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            correcta="B",
            opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        )
        aplicar_presion_racha_modificadores(er, p, numero_pregunta=60)
        self.assertTrue(er.objetos_bloqueados)
        self.assertLessEqual(er.fraccion_enunciado, 0.25)
        self.assertLessEqual(er.relampago_forzado_seg or 99, 5)

    def test_presion_racha_temprana_sin_niebla(self) -> None:
        from Comun.resistencia_motor import (
            aplicar_presion_racha_modificadores,
            preparar_presion_racha_turno,
        )
        from Comun.modelos import Pregunta

        er = EstadoResistencia(semilla_partida=2, racha=100)
        preparar_presion_racha_turno(er, numero_pregunta=10)
        p = Pregunta(
            texto="¿2+2?",
            materia="MAT",
            tematica="",
            dificultad="Facil",
            tipo="test",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            correcta="B",
            opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        )
        er.fraccion_enunciado = 1.0
        er.letras_ocultas = set()
        aplicar_presion_racha_modificadores(er, p, numero_pregunta=10)
        self.assertEqual(er.fraccion_enunciado, 1.0)
        self.assertEqual(er.letras_ocultas, set())
        self.assertIsNotNone(er.relampago_forzado_seg)

    def test_escalada_no_depende_de_racha_jugador(self) -> None:
        from Comun.resistencia_partida import escalada_para_pregunta

        e = escalada_para_pregunta(30, semilla_partida=123)
        self.assertEqual(e.nivel, 2)
        self.assertIsNone(
            escalada_para_pregunta(1, semilla_partida=123).tiempo_pregunta_seg
        )

    def test_recompensas_tras_acierto_no_quitan_vida_directa(self) -> None:
        from Comun.resistencia_motor import _generar_recompensa_aleatoria
        import random

        rng = random.Random(42)
        for _ in range(80):
            ev = _generar_recompensa_aleatoria(rng, numero_pregunta=100)
            self.assertGreaterEqual(ev.delta_vidas, 0, ev.etiqueta)

    def test_doble_puntos_no_salta_casi_siempre_al_inicio(self) -> None:
        from Comun.resistencia_partida import eventos_aleatorios_para_pregunta

        con_doble = sum(
            1
            for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 45)
            if any(
                e.multiplicador_puntos
                for e in eventos_aleatorios_para_pregunta(n, semilla_partida=7)
            )
        )
        self.assertLess(con_doble, 18)

    def test_eventos_aleatorios_no_vacios_en_rango(self) -> None:
        con_evento = [
            n
            for n in range(PREGUNTA_MIN_EVENTOS_ALEATORIOS, 50)
            if eventos_aleatorios_para_pregunta(n)
        ]
        self.assertGreater(len(con_evento), 0)

    def test_escalada_y_elegir_coherentes(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.resistencia_partida import construir_banco_resistencia, crear_seleccion_resistencia
        from Comun.rutas import resolver_dataset, resolver_listado_materias, resolver_plantillas

        materias = cargar_materias(resolver_listado_materias())
        preguntas = cargar_preguntas(resolver_dataset(), materias)
        banco = construir_banco_resistencia(
            preguntas,
            materias,
            path_plantillas=resolver_plantillas(),
            path_preguntas_csv=resolver_dataset(),
        )
        pool = banco.pool_completo()
        er = EstadoResistencia()
        er.banco_resistencia = banco
        sel = crear_seleccion_resistencia(pool)
        esc = escalada_para_pregunta(5)
        idx = elegir_indice_resistencia(pool, sel, esc, numero_pregunta=5, er=er)
        self.assertIsNotNone(idx)

# --- test_motor_resistencia_comun.py ---

from Comun.resistencia_motor import EstadoResistencia  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta  # noqa: E402
from Comun.resistencia_motor import (  # noqa: E402
    aplicar_bonificaciones_puntos_resistencia,
    bonificacion_puntos_racha,
    procesar_turno_resistencia,
    usar_powerup,
)
from Comun.resistencia_motor import etiqueta_powerup, letras_ocultas_bomba, letras_ocultas_fifty_fifty  # noqa: E402
from Comun.reglas_partida import preset_resistencia  # noqa: E402


def _pregunta() -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia="MAT",
        tematica="",
        dificultad="Facil",
        tipo="test",
        grupo="",
        nivel="",
        curso="1",
        semestre="1",
        correcta="B",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
    )


class TestMotorResistenciaComun(unittest.TestCase):
    def test_racha_se_corta_al_fallar(self) -> None:
        er = EstadoResistencia()
        er.racha = 5
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=1,
        )
        self.assertEqual(er.racha, 0)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertFalse(turno.feedback.sin_vidas)

    def test_apuesta_fin_partida_al_fallar(self) -> None:
        from Comun.resistencia_motor import (
            ApuestaRiesgo,
            CosteApuesta,
            RecompensaApuesta,
        )

        er = EstadoResistencia(semilla_partida=1)
        er.apuesta_activa = ApuestaRiesgo(
            "Última carta",
            RecompensaApuesta(mult_puntos=4),
            CosteApuesta(fin_partida=True),
        )
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=10,
        )
        self.assertEqual(estado.vidas_restantes, 0)
        self.assertTrue(turno.feedback.sin_vidas)
        self.assertTrue(
            any("fin de partida" in a.lower() for a in turno.avisos_extra)
        )

    def test_apuesta_objeto_al_acertar_y_puntos_al_fallar(self) -> None:
        from Comun.resistencia_motor import (
            ApuestaRiesgo,
            CosteApuesta,
            RecompensaApuesta,
        )

        er = EstadoResistencia(semilla_partida=2)
        er.apuesta_activa = ApuestaRiesgo(
            "Vida de la suerte",
            RecompensaApuesta(delta_vidas=1),
            CosteApuesta(puntos_perdidos=35),
        )
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=2,
            puntos_arcade=100,
        )
        turno_ok = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=True, respuesta="B"),
            indice_pregunta=11,
        )
        self.assertEqual(estado.vidas_restantes, 3)
        self.assertTrue(any("Apuesta: +1 vida" in a for a in turno_ok.avisos_extra))

        er.apuesta_activa = ApuestaRiesgo(
            "Vida de la suerte",
            RecompensaApuesta(delta_vidas=1),
            CosteApuesta(puntos_perdidos=35),
        )
        estado.puntos_arcade = 80
        turno_ko = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=12,
        )
        self.assertLess(estado.puntos_arcade, 80)
        self.assertTrue(
            any("−35 puntos" in a for a in turno_ko.avisos_extra)
        )

    def test_escudo_evita_perder_vida_y_racha(self) -> None:
        er = EstadoResistencia()
        er.racha = 7
        er.escudo_activo = True
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=2,
        )
        turno = procesar_turno_resistencia(
            estado,
            er,
            _pregunta(),
            ResultadoRespuesta(acierto=False, respuesta="A"),
            indice_pregunta=2,
        )
        self.assertTrue(turno.reintentar_pregunta)
        self.assertEqual(er.racha, 7)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertFalse(er.escudo_activo)

    def test_fifty_fifty_oculta_dos_incorrectas(self) -> None:
        p = _pregunta()
        ocultas = letras_ocultas_fifty_fifty(p)
        self.assertEqual(len(ocultas), 2)
        self.assertNotIn("B", ocultas)

    def test_bomba_oculta_una_incorrecta(self) -> None:
        p = _pregunta()
        ocultas = letras_ocultas_bomba(p)
        self.assertEqual(len(ocultas), 1)
        self.assertNotIn("B", ocultas)

    def test_etiqueta_bomba(self) -> None:
        self.assertEqual(etiqueta_powerup("bomba"), "Bomba")

    def test_usar_powerup_consumo(self) -> None:
        er = EstadoResistencia()
        er.agregar_powerup("skip", 2)
        p = _pregunta()
        self.assertIsNone(usar_powerup("skip", er, p))
        self.assertEqual(er.cantidad("skip"), 1)
        self.assertIn("skip", er.powerups_usados_en_pregunta)

    def test_bomba_y_fifty_incompatibles_misma_pregunta(self) -> None:
        er = EstadoResistencia()
        er.agregar_powerup("bomba", 1)
        er.agregar_powerup("fifty_fifty", 1)
        p = _pregunta()
        self.assertIsNone(usar_powerup("bomba", er, p))
        self.assertIsNotNone(usar_powerup("fifty_fifty", er, p))
        er.reiniciar_slot_pregunta()
        self.assertIsNone(usar_powerup("fifty_fifty", er, p))

    def test_bomba_y_tiempo_extra_compatibles(self) -> None:
        er = EstadoResistencia()
        er.agregar_powerup("bomba", 1)
        er.agregar_powerup("tiempo_extra", 1)
        p = _pregunta()
        self.assertIsNone(usar_powerup("bomba", er, p))
        self.assertIsNone(usar_powerup("tiempo_extra", er, p))
        self.assertEqual(er.tiempo_extra_seg, 20)

    def test_recompensas_no_dependen_de_racha_ni_pregunta(self) -> None:
        from Comun.resistencia_motor import tirar_recompensas_tras_acierto

        er_alta = EstadoResistencia(semilla_partida=12345, racha=40)
        er_baja = EstadoResistencia(semilla_partida=12345, racha=1)
        self.assertEqual(
            tirar_recompensas_tras_acierto(er_alta, numero_pregunta=20),
            tirar_recompensas_tras_acierto(er_baja, numero_pregunta=20),
        )

    def test_recompensa_buena_decae_y_mala_crece(self) -> None:
        from Comun.resistencia_motor import (
            probabilidad_buena_resistencia,
            probabilidad_mala_resistencia,
        )

        self.assertGreater(probabilidad_buena_resistencia(10), probabilidad_buena_resistencia(200))
        self.assertGreater(probabilidad_mala_resistencia(200), probabilidad_mala_resistencia(10))

    def test_hasta_dos_recompensas_por_acierto(self) -> None:
        from unittest.mock import patch

        from Comun.resistencia_motor import (
            MAX_TIRADAS_RECOMPENSA_ACIERTO,
            tirar_recompensas_tras_acierto,
        )

        er = EstadoResistencia(semilla_partida=7)
        with (
            patch("Comun.resistencia_motor.probabilidad_buena_resistencia", return_value=1.0),
            patch("Comun.resistencia_motor.FACTOR_TIRADA_RECOMPENSA", 1.0),
        ):
            recs = tirar_recompensas_tras_acierto(er, numero_pregunta=10)
        self.assertEqual(len(recs), MAX_TIRADAS_RECOMPENSA_ACIERTO)

        er2 = EstadoResistencia(semilla_partida=7)
        with patch("Comun.resistencia_motor.probabilidad_buena_resistencia", return_value=0.0):
            self.assertEqual(tirar_recompensas_tras_acierto(er2, numero_pregunta=10), [])

    def test_acierto_propaga_avisos_recompensa(self) -> None:
        from unittest.mock import patch

        er = EstadoResistencia(semilla_partida=3)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        with (
            patch("Comun.resistencia_motor.probabilidad_buena_resistencia", return_value=1.0),
            patch("Comun.resistencia_motor.FACTOR_TIRADA_RECOMPENSA", 1.0),
        ):
            turno = procesar_turno_resistencia(
                estado,
                er,
                _pregunta(),
                ResultadoRespuesta(acierto=True, respuesta="B"),
                indice_pregunta=200,
            )
        self.assertGreaterEqual(len(turno.avisos_extra), 1)
        self.assertTrue(
            any("Obtuviste" in aviso or "Vida" in aviso for aviso in turno.avisos_extra)
        )

    def test_avisos_pre_pregunta_propagan_extras(self) -> None:
        from Comun.resistencia_partida import avisos_pre_pregunta_resistencia
        from Comun.resistencia_motor import formatear_aviso_evento

        p = _pregunta()
        avisos = avisos_pre_pregunta_resistencia(
            p,
            12,
            avisos_extra=[formatear_aviso_evento("Doble puntos")],
        )
        self.assertTrue(any("Doble" in a for a in avisos))

    def test_texto_pregunta_visible_trunca(self) -> None:
        from Comun.resistencia_motor import texto_pregunta_visible

        texto = "¿Cuál es la capital de Francia en el siglo XXI?"
        truncado = texto_pregunta_visible(texto, 0.5)
        self.assertIn("▓", truncado)
        self.assertLess(len(truncado.split("▓")[0]), len(texto))

    def test_escalada_con_niebla_opciones(self) -> None:
        from Comun.resistencia_partida import eventos_aleatorios_para_pregunta

        eventos = [
            e for e in eventos_aleatorios_para_pregunta(120)
            if e.opciones_ocultas
        ]
        if eventos:
            self.assertGreater(eventos[0].opciones_ocultas or 0, 0)
            self.assertNotIn("Ceguera", eventos[0].etiqueta)

    def test_bonificacion_racha_solo_puntos(self) -> None:
        self.assertEqual(bonificacion_puntos_racha(1), 1.0)
        self.assertGreater(bonificacion_puntos_racha(10), 1.4)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
        )
        estado.puntos_arcade = 20
        aplicar_bonificaciones_puntos_resistencia(
            estado,
            puntos_prev=10,
            racha=10,
            mult_escalada=1,
            exclusiva=False,
            acierto=True,
            tiempo_agotado=False,
        )
        self.assertGreater(estado.puntos_arcade, 20)

# --- test_preguntas_exclusivas_resistencia.py ---

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.resistencia_motor import EstadoResistencia  # noqa: E402
from Comun.preguntas_resistencia import (  # noqa: E402
    cargar_preguntas_exclusivas_resistencia,
    construir_banco_resistencia,
    construir_pool_resistencia,
)
from Comun.resistencia_partida import (  # noqa: E402
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    probabilidad_pregunta_exclusiva,
)
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_plantillas,
    resolver_preguntas_resistencia,
)


class TestPreguntasExclusivasResistencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.exclusivas = cargar_preguntas_exclusivas_resistencia(cls.materias_meta)
        cls.banco = construir_banco_resistencia(
            cls.preguntas,
            cls.materias_meta,
            path_plantillas=resolver_plantillas(),
            path_preguntas_csv=resolver_dataset(),
        )
        cls.pool = cls.banco.pool_completo()

    def test_archivo_exclusivas_cargado(self) -> None:
        self.assertTrue(resolver_preguntas_resistencia().exists())
        self.assertGreaterEqual(len(self.exclusivas), 20)
        for p in self.exclusivas:
            self.assertTrue(p.exclusiva_resistencia)
            self.assertGreaterEqual(p.racha_minima_resistencia, 100)

    def test_pool_incluye_exclusivas(self) -> None:
        n_exc = sum(1 for p in self.pool if p.exclusiva_resistencia)
        self.assertEqual(n_exc, len(self.exclusivas))

    def test_exclusivas_no_en_modo_normal(self) -> None:
        """El dataset principal no marca preguntas como exclusivas."""
        for p in self.preguntas:
            self.assertFalse(p.exclusiva_resistencia)

    def test_no_salen_con_pregunta_baja(self) -> None:
        er = EstadoResistencia()
        er.banco_resistencia = self.banco
        sel = crear_seleccion_resistencia(self.pool)
        numero = 51
        escalada = escalada_para_pregunta(numero)
        for _ in range(30):
            idx = elegir_indice_resistencia(
                self.pool, sel, escalada, numero_pregunta=numero, er=er
            )
            self.assertIsNotNone(idx)
            self.assertFalse(self.pool[idx].exclusiva_resistencia)

    def test_pueden_salir_con_pregunta_alta(self) -> None:
        er = EstadoResistencia()
        er.banco_resistencia = self.banco
        sel = crear_seleccion_resistencia(self.pool)
        numero = 601
        escalada = escalada_para_pregunta(numero)
        visto_exclusiva = False
        for _ in range(80):
            idx = elegir_indice_resistencia(
                self.pool, sel, escalada, numero_pregunta=numero, er=er
            )
            self.assertIsNotNone(idx)
            if self.pool[idx].exclusiva_resistencia:
                visto_exclusiva = True
                break
        self.assertTrue(visto_exclusiva)

    def test_probabilidad_exclusiva_crece(self) -> None:
        self.assertEqual(probabilidad_pregunta_exclusiva(50), 0.0)
        self.assertLess(
            probabilidad_pregunta_exclusiva(150),
            probabilidad_pregunta_exclusiva(800),
        )

    def test_tiers_desbloqueo(self) -> None:
        t4 = min(p.racha_minima_resistencia for p in self.exclusivas if p.tier_resistencia == 4)
        self.assertGreaterEqual(t4, 750)

# --- test_iconos_resistencia.py ---

from Comun.resistencia_motor import (  # noqa: E402
    emoji_evento_etiqueta,
    emoji_powerup,
    emoji_recompensa_etiqueta,
    prefijar_emoji,
    separar_emoji_mensaje,
)
from Comun.resistencia_motor import formatear_aviso_evento, formatear_aviso_recompensa  # noqa: E402


class TestIconosResistencia(unittest.TestCase):
    def test_emoji_powerups(self) -> None:
        self.assertEqual(emoji_powerup("bomba"), "💣")
        self.assertEqual(emoji_powerup("escudo"), "🛡️")
        self.assertEqual(emoji_powerup("skip"), "⏭️")

    def test_prefijar_y_separar(self) -> None:
        mensaje = prefijar_emoji("Bomba", "💣")
        self.assertEqual(mensaje, "💣  Bomba")
        emoji, resto = separar_emoji_mensaje(mensaje)
        self.assertEqual(emoji, "💣")
        self.assertEqual(resto, "Bomba")

    def test_emoji_eventos(self) -> None:
        self.assertEqual(emoji_evento_etiqueta("Relámpago: 8 s por pregunta"), "⚡")
        self.assertEqual(emoji_evento_etiqueta("Pregunta extra difícil"), "☠️")

    def test_avisos_con_emoji(self) -> None:
        aviso = formatear_aviso_evento("Doble puntos")
        self.assertTrue(aviso.startswith("✨"))
        rec = formatear_aviso_recompensa("Objeto: Bomba")
        self.assertIn("💣", rec)
        self.assertIn("Bomba", rec)

    def test_emoji_recompensa_vida(self) -> None:
        self.assertEqual(emoji_recompensa_etiqueta("¡Vida extra!"), "❤️")


if __name__ == "__main__":
    unittest.main()
