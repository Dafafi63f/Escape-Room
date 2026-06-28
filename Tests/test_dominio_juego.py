#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dominio del juego gráfico: datos, reglas libre/historia y evaluación."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Tests.Fixtures.adaptador_juego import (
    ConfigReglasLibre,
    crear_backend,
    tupla_opciones,
    tupla_reglas,
)

try:
    crear_backend("grafico")
    _GRAFICO_DISPONIBLE = True
except Exception:
    _GRAFICO_DISPONIBLE = False


@unittest.skipUnless(_GRAFICO_DISPONIBLE, "Grafico no disponible")
class TestDominioJuego(unittest.TestCase):
    """Comprueba el dominio expuesto por el lanzador gráfico."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._backend = crear_backend("grafico")

    def test_carga_datos_inicial(self) -> None:
        datos = self._backend.cargar_datos()
        self.assertGreater(datos.num_preguntas, 0)
        self.assertGreater(datos.num_materias, 0)
        self.assertTrue(datos.muestra_texto)
        self.assertTrue(datos.muestra_materia)

    def test_contexto_libre_finito_normal(self) -> None:
        self._backend.contexto_libre(modo_infinito=False, n_preguntas=10)

    def test_contexto_libre_infinito(self) -> None:
        self._backend.contexto_libre(modo_infinito=True, n_preguntas=10)

    def test_contexto_libre_minimo_cinco_preguntas(self) -> None:
        self._backend.contexto_libre(modo_infinito=False, n_preguntas=5)
        with self.assertRaises(ValueError):
            self._backend.contexto_libre(modo_infinito=False, n_preguntas=4)

    def test_reglas_arcade_sin_vidas_bloque_10(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=None,
            sistema=SistemaPuntuacion.ARCADE,
        )
        tupla_reglas(self._backend.reglas_libre(cfg))

    def test_reglas_arcade_con_vidas(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=3,
            sistema=SistemaPuntuacion.ARCADE,
            dificultad_progresiva=True,
        )
        tupla_reglas(self._backend.reglas_libre(cfg))

    def test_reglas_nota_sin_vidas_bloque_largo(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=None,
            sistema=SistemaPuntuacion.NOTA,
            mostrar_aciertos_en_curso=False,
        )
        tupla_reglas(self._backend.reglas_libre(cfg))

    def test_reglas_nota_con_vidas_fuerza_arcade(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=2,
            sistema=SistemaPuntuacion.NOTA,
        )
        reglas = self._backend.reglas_libre(cfg)
        self.assertEqual(reglas.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_reglas_infinito_solo_arcade(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=True,
            n_preguntas=10,
            vidas=3,
            sistema=SistemaPuntuacion.PORCENTAJE,
            tiempo_por_pregunta_seg=90,
        )
        reglas = self._backend.reglas_libre(cfg)
        self.assertEqual(reglas.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_reglas_pocas_preguntas_rechaza_partida_corta(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=4,
            vidas=None,
            sistema=SistemaPuntuacion.NOTA,
        )
        with self.assertRaises(ValueError):
            self._backend.reglas_libre(cfg)

    def test_opciones_con_vidas_bloquean_nota(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        opts = self._backend.opciones_libre(
            modo_infinito=False,
            n_preguntas=10,
            sin_vidas=False,
            sistema=SistemaPuntuacion.ARCADE,
        )
        tupla_opciones(opts)

    def test_opciones_nota_bloquean_vidas(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        opts = self._backend.opciones_libre(
            modo_infinito=False,
            n_preguntas=10,
            sin_vidas=True,
            sistema=SistemaPuntuacion.NOTA,
        )
        self.assertFalse(opts.permitir_con_vidas)

    def test_evaluar_acierto_arcade(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=False,
                n_preguntas=5,
                vidas=None,
                sistema=SistemaPuntuacion.ARCADE,
            )
        )
        resultado = self._backend.evaluar_respuesta(
            reglas=reglas,
            pregunta=self._backend.pregunta_ejemplo(),
            acierto=True,
            letra="B",
        )
        self.assertEqual(resultado.aciertos, 1)
        self.assertGreater(resultado.puntos_arcade, 0)
        self.assertIn("Correcto", resultado.mensaje)

    def test_evaluar_fallo_con_vidas(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=False,
                n_preguntas=5,
                vidas=3,
                sistema=SistemaPuntuacion.ARCADE,
            )
        )
        resultado = self._backend.evaluar_respuesta(
            reglas=reglas,
            pregunta=self._backend.pregunta_ejemplo(),
            acierto=False,
            letra="A",
        )
        self.assertEqual(resultado.vidas_restantes, 2)

    def test_fallo_arcade_no_deja_puntos_negativos(self) -> None:
        from Comun.reglas import SistemaPuntuacion, sumar_puntos_arcade

        self.assertEqual(sumar_puntos_arcade(0, -10), (0, 0))
        self.assertEqual(sumar_puntos_arcade(3, -10), (0, -3))

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=False,
                n_preguntas=5,
                vidas=3,
                sistema=SistemaPuntuacion.ARCADE,
            )
        )
        from Comun.motor_nucleo import EstadoPartida, ResultadoRespuesta, evaluar_respuesta

        estado = EstadoPartida(
            nombre="Test",
            reglas=reglas,
            vidas_restantes=reglas.vidas,
            puntos_arcade=0,
        )
        fb = evaluar_respuesta(
            self._backend.pregunta_ejemplo(),
            estado,
            ResultadoRespuesta(acierto=False, respuesta="A"),
        )
        self.assertEqual(estado.puntos_arcade, 0)
        self.assertIn("(0 puntos)", fb.mensaje)

    def test_evaluar_tiempo_agotado(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=False,
                n_preguntas=5,
                vidas=2,
                sistema=SistemaPuntuacion.ARCADE,
                tiempo_por_pregunta_seg=30,
            )
        )
        resultado = self._backend.evaluar_respuesta(
            reglas=reglas,
            pregunta=self._backend.pregunta_ejemplo(),
            acierto=False,
            letra="",
            tiempo_agotado=True,
        )
        self.assertEqual(resultado.vidas_restantes, 1)

    def test_linea_estado_arcade_infinito(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=True,
                n_preguntas=10,
                vidas=3,
                sistema=SistemaPuntuacion.ARCADE,
            )
        )
        texto = self._backend.linea_estado_partida(
            reglas=reglas,
            progreso="Pregunta 1/inf",
            puntos=0,
            vidas=3,
            segundos_pregunta=45,
        )
        self.assertIn("Pregunta", texto)

    def test_linea_estado_nota_en_curso(self) -> None:
        from Comun.reglas import SistemaPuntuacion

        reglas = self._backend.reglas_libre(
            ConfigReglasLibre(
                modo_infinito=False,
                n_preguntas=10,
                vidas=None,
                sistema=SistemaPuntuacion.NOTA,
            )
        )
        texto = self._backend.linea_estado_partida(
            reglas=reglas,
            progreso="Pregunta 3/10",
            aciertos=2,
            respondidas=3,
        )
        self.assertIn("3/10", texto)

    def test_nombre_jugador_defecto(self) -> None:
        from Comun.preferencias_grafico import NOMBRE_JUGADOR_DEFECTO

        self.assertEqual(self._backend.nombre_jugador_defecto(), NOMBRE_JUGADOR_DEFECTO)

    def test_catalogo_historia_ids(self) -> None:
        ids = self._backend.catalogo_historia_ids()
        self.assertIn("simulacro", ids)

    def test_reglas_historia_simulacro(self) -> None:
        t = self._backend.reglas_historia_preset("simulacro")
        self.assertIsNone(t[0])  # examen sin vidas
        self.assertTrue(t[6])  # correccion_al_final

    def test_reglas_historia_resistencia(self) -> None:
        t = self._backend.reglas_historia_preset("resistencia")
        self.assertEqual(t[0], 3)


if __name__ == "__main__":
    unittest.main()
