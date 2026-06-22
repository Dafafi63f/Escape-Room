#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor, mecánicas, pool exclusivo e iconos de resistencia.

Secciones:
- test_mecanicas_resistencia.py
- test_motor_resistencia_comun.py
- test_preguntas_exclusivas_resistencia.py
- test_iconos_resistencia.py
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

# --- test_mecanicas_resistencia.py ---

from datetime import date
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[1] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.estado_resistencia import EstadoResistencia  # noqa: E402
from Comun.mecanicas_resistencia import (  # noqa: E402
    texto_progreso_resistencia,
)
from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia, semilla_reto_dia  # noqa: E402
from Comun.resistencia_historia import (  # noqa: E402
    PREGUNTA_MIN_EVENTOS_ALEATORIOS,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    eventos_aleatorios_para_pregunta,
)


class TestMecanicasResistencia(unittest.TestCase):
    def test_semilla_reto_dia_estable(self) -> None:
        d = date(2026, 6, 18)
        self.assertEqual(semilla_reto_dia(d), 18_06_2026)
        self.assertIn("2026", etiqueta_fecha_reto_dia(d))

    def test_texto_progreso_resistencia(self) -> None:
        er = EstadoResistencia(racha=3)
        txt = texto_progreso_resistencia(er, 10)
        self.assertEqual(txt, "#10 · Racha 3")

    def test_bloque_grupo_usa_nombre_tematico(self) -> None:
        from Comun.mecanicas_resistencia import _descripcion_grupo_tematico
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
        from Comun.mecanicas_resistencia import BloqueFiltroActivo, consumir_bloque_filtro

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
        from Comun.mecanicas_resistencia import (
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
        from Comun.mecanicas_resistencia import (
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
        from Comun.mecanicas_resistencia import (
            aplicar_presion_racha_modificadores,
            preparar_presion_racha_turno,
        )
        from Comun.modelos import Pregunta
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import preset_historia_resistencia

        er = EstadoResistencia(semilla_partida=9, racha=50)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_historia_resistencia(),
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

    def test_racha_extrema_apila_eventos_hostiles(self) -> None:
        from Comun.resistencia_historia import eventos_aleatorios_para_pregunta

        eventos = eventos_aleatorios_para_pregunta(
            50, semilla_partida=3, racha=100
        )
        hostiles = [
            e
            for e in eventos
            if e.tiempo_pregunta
            or e.opciones_ocultas
            or e.fraccion_enunciado is not None
        ]
        self.assertGreater(len(hostiles), 2)
        self.assertFalse(any(e.multiplicador_puntos for e in eventos))

    def test_racha_extrema_aplica_maldiciones_presion(self) -> None:
        from Comun.mecanicas_resistencia import (
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
        self.assertTrue(er.sin_pistas_turno)
        self.assertLessEqual(er.fraccion_enunciado, 0.25)
        self.assertLessEqual(er.relampago_forzado_seg or 99, 5)

    def test_escalada_no_depende_de_racha_jugador(self) -> None:
        from Comun.resistencia_historia import escalada_para_pregunta

        e = escalada_para_pregunta(30, semilla_partida=123)
        self.assertEqual(e.nivel, 2)
        self.assertIsNone(
            escalada_para_pregunta(1, semilla_partida=123).tiempo_pregunta_seg
        )

    def test_recompensas_tras_acierto_no_quitan_vida_directa(self) -> None:
        from Comun.powerups_resistencia import _generar_recompensa_aleatoria
        import random

        rng = random.Random(42)
        for _ in range(80):
            ev = _generar_recompensa_aleatoria(rng, numero_pregunta=100)
            self.assertGreaterEqual(ev.delta_vidas, 0, ev.etiqueta)

    def test_doble_puntos_no_salta_casi_siempre_al_inicio(self) -> None:
        from Comun.resistencia_historia import eventos_aleatorios_para_pregunta

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
        from Comun.resistencia_historia import construir_banco_resistencia, crear_seleccion_resistencia
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

from Comun.estado_resistencia import EstadoResistencia  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta  # noqa: E402
from Comun.motor_resistencia_comun import (  # noqa: E402
    aplicar_bonificaciones_puntos_resistencia,
    bonificacion_puntos_racha,
    procesar_turno_resistencia,
    usar_powerup,
)
from Comun.powerups_resistencia import etiqueta_powerup, letras_ocultas_bomba, letras_ocultas_fifty_fifty  # noqa: E402
from Comun.reglas_partida import preset_historia_resistencia  # noqa: E402


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
            reglas=preset_historia_resistencia(),
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
        from Comun.mecanicas_resistencia import (
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
            reglas=preset_historia_resistencia(),
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
        from Comun.mecanicas_resistencia import (
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
            reglas=preset_historia_resistencia(),
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
            reglas=preset_historia_resistencia(),
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

    def test_recompensas_no_dependen_de_racha_ni_pregunta(self) -> None:
        from Comun.powerups_resistencia import tirar_recompensas_tras_acierto

        er_alta = EstadoResistencia(semilla_partida=12345, racha=40)
        er_baja = EstadoResistencia(semilla_partida=12345, racha=1)
        self.assertEqual(
            tirar_recompensas_tras_acierto(er_alta, numero_pregunta=20),
            tirar_recompensas_tras_acierto(er_baja, numero_pregunta=20),
        )

    def test_recompensa_buena_decae_y_mala_crece(self) -> None:
        from Comun.probabilidad_resistencia import (
            probabilidad_buena_resistencia,
            probabilidad_mala_resistencia,
        )

        self.assertGreater(probabilidad_buena_resistencia(10), probabilidad_buena_resistencia(200))
        self.assertGreater(probabilidad_mala_resistencia(200), probabilidad_mala_resistencia(10))

    def test_hasta_dos_recompensas_por_acierto(self) -> None:
        from unittest.mock import patch

        from Comun.powerups_resistencia import (
            MAX_TIRADAS_RECOMPENSA_ACIERTO,
            tirar_recompensas_tras_acierto,
        )

        er = EstadoResistencia(semilla_partida=7)
        with (
            patch("Comun.probabilidad_resistencia.probabilidad_buena_resistencia", return_value=1.0),
            patch("Comun.powerups_resistencia.FACTOR_TIRADA_RECOMPENSA", 1.0),
        ):
            recs = tirar_recompensas_tras_acierto(er, numero_pregunta=10)
        self.assertEqual(len(recs), MAX_TIRADAS_RECOMPENSA_ACIERTO)

        er2 = EstadoResistencia(semilla_partida=7)
        with patch("Comun.probabilidad_resistencia.probabilidad_buena_resistencia", return_value=0.0):
            self.assertEqual(tirar_recompensas_tras_acierto(er2, numero_pregunta=10), [])

    def test_acierto_propaga_avisos_recompensa(self) -> None:
        from unittest.mock import patch

        er = EstadoResistencia(semilla_partida=3)
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_historia_resistencia(),
            vidas_restantes=3,
        )
        with (
            patch("Comun.probabilidad_resistencia.probabilidad_buena_resistencia", return_value=1.0),
            patch("Comun.powerups_resistencia.FACTOR_TIRADA_RECOMPENSA", 1.0),
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
        from Comun.motor_resistencia_comun import avisos_pre_pregunta_resistencia, formatear_aviso_evento

        p = _pregunta()
        avisos = avisos_pre_pregunta_resistencia(
            p,
            12,
            avisos_extra=[formatear_aviso_evento("Doble puntos")],
        )
        self.assertTrue(any("Doble" in a for a in avisos))

    def test_texto_pregunta_visible_trunca(self) -> None:
        from Comun.powerups_resistencia import texto_pregunta_visible

        texto = "¿Cuál es la capital de Francia en el siglo XXI?"
        truncado = texto_pregunta_visible(texto, 0.5)
        self.assertIn("▓", truncado)
        self.assertLess(len(truncado.split("▓")[0]), len(texto))

    def test_escalada_con_niebla_opciones(self) -> None:
        from Comun.resistencia_historia import eventos_aleatorios_para_pregunta

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
            reglas=preset_historia_resistencia(),
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
from Comun.estado_resistencia import EstadoResistencia  # noqa: E402
from Comun.preguntas_resistencia import (  # noqa: E402
    cargar_preguntas_exclusivas_resistencia,
    construir_banco_resistencia,
    construir_pool_resistencia,
)
from Comun.resistencia_historia import (  # noqa: E402
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

from Comun.iconos_resistencia import (  # noqa: E402
    emoji_evento_etiqueta,
    emoji_powerup,
    emoji_recompensa_etiqueta,
    prefijar_emoji,
    separar_emoji_mensaje,
)
from Comun.motor_resistencia_comun import formatear_aviso_evento, formatear_aviso_recompensa  # noqa: E402


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

if __name__ == "__main__":
    unittest.main()
