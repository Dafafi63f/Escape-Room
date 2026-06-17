#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paridad entre ``juego_consola.py`` y ``juego_grafico.py``.

Cada test ejecuta la misma operación por ambas rutas de arranque y falla si
la respuesta no coincide.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Callable, TypeVar

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.Juego.paridad_juegos import (
    BACKENDS,
    ConfigReglasLibre,
    crear_backend,
    tupla_opciones,
    tupla_reglas,
)

T = TypeVar("T")


class TestParidadConsolaGrafico(unittest.TestCase):
    """Compara resultados de consola y gráfico en las mismas operaciones."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._backends = {nombre: crear_backend(nombre) for nombre in BACKENDS}

    def _comparar(
        self,
        ejecutar: Callable[..., T],
        *args: object,
        **kwargs: object,
    ) -> T:
        resultados: dict[str, T] = {}
        for nombre in BACKENDS:
            with self.subTest(backend=nombre):
                resultados[nombre] = ejecutar(self._backends[nombre], *args, **kwargs)
        self.assertEqual(
            resultados["consola"],
            resultados["grafico"],
            msg=(
                "consola y gráfico difieren:\n"
                f"  consola = {resultados['consola']!r}\n"
                f"  grafico = {resultados['grafico']!r}"
            ),
        )
        return resultados["consola"]

    def test_carga_datos_inicial(self) -> None:
        self._comparar(lambda b: b.cargar_datos())

    def test_contexto_libre_finito_normal(self) -> None:
        self._comparar(
            lambda b: b.contexto_libre(modo_infinito=False, n_preguntas=10),
        )

    def test_contexto_libre_infinito(self) -> None:
        self._comparar(
            lambda b: b.contexto_libre(modo_infinito=True, n_preguntas=10),
        )

    def test_contexto_libre_una_pregunta(self) -> None:
        self._comparar(
            lambda b: b.contexto_libre(modo_infinito=False, n_preguntas=1),
        )

    def test_reglas_arcade_sin_vidas_bloque_10(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=None,
            sistema=SistemaPuntuacion.ARCADE,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_reglas_arcade_con_vidas(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=3,
            sistema=SistemaPuntuacion.ARCADE,
            dificultad_progresiva=True,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_reglas_nota_sin_vidas_bloque_largo(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=None,
            sistema=SistemaPuntuacion.NOTA,
            mostrar_aciertos_en_curso=False,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_reglas_nota_con_vidas_fuerza_arcade(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=10,
            vidas=2,
            sistema=SistemaPuntuacion.NOTA,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_reglas_infinito_solo_arcade(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=True,
            n_preguntas=10,
            vidas=3,
            sistema=SistemaPuntuacion.PORCENTAJE,
            tiempo_por_pregunta_seg=90,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_reglas_pocas_preguntas_sin_nota(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        cfg = ConfigReglasLibre(
            modo_infinito=False,
            n_preguntas=3,
            vidas=None,
            sistema=SistemaPuntuacion.NOTA,
        )
        self._comparar(lambda b: tupla_reglas(b.reglas_libre(cfg)))

    def test_opciones_con_vidas_bloquean_nota(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        self._comparar(
            lambda b: tupla_opciones(
                b.opciones_libre(
                    modo_infinito=False,
                    n_preguntas=10,
                    sin_vidas=False,
                    sistema=SistemaPuntuacion.ARCADE,
                )
            ),
        )

    def test_opciones_nota_bloquean_vidas(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        self._comparar(
            lambda b: tupla_opciones(
                b.opciones_libre(
                    modo_infinito=False,
                    n_preguntas=10,
                    sin_vidas=True,
                    sistema=SistemaPuntuacion.NOTA,
                )
            ),
        )

    def test_evaluar_acierto_arcade(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        def _evaluar(b):
            reglas = b.reglas_libre(
                ConfigReglasLibre(
                    modo_infinito=False,
                    n_preguntas=5,
                    vidas=None,
                    sistema=SistemaPuntuacion.ARCADE,
                )
            )
            return b.evaluar_respuesta(
                reglas=reglas,
                pregunta=b.pregunta_ejemplo(),
                acierto=True,
                letra="B",
            )

        self._comparar(_evaluar)

    def test_evaluar_fallo_con_vidas(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        def _evaluar(b):
            reglas = b.reglas_libre(
                ConfigReglasLibre(
                    modo_infinito=False,
                    n_preguntas=5,
                    vidas=3,
                    sistema=SistemaPuntuacion.ARCADE,
                )
            )
            return b.evaluar_respuesta(
                reglas=reglas,
                pregunta=b.pregunta_ejemplo(),
                acierto=False,
                letra="A",
            )

        self._comparar(_evaluar)

    def test_evaluar_tiempo_agotado(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        def _evaluar(b):
            reglas = b.reglas_libre(
                ConfigReglasLibre(
                    modo_infinito=False,
                    n_preguntas=5,
                    vidas=2,
                    sistema=SistemaPuntuacion.ARCADE,
                    tiempo_por_pregunta_seg=30,
                )
            )
            return b.evaluar_respuesta(
                reglas=reglas,
                pregunta=b.pregunta_ejemplo(),
                acierto=False,
                letra="",
                tiempo_agotado=True,
            )

        self._comparar(_evaluar)

    def test_linea_estado_arcade_infinito(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        def _linea(b):
            reglas = b.reglas_libre(
                ConfigReglasLibre(
                    modo_infinito=True,
                    n_preguntas=10,
                    vidas=3,
                    sistema=SistemaPuntuacion.ARCADE,
                )
            )
            return b.linea_estado_partida(
                reglas=reglas,
                progreso="Pregunta 1/inf",
                puntos=0,
                vidas=3,
                segundos_pregunta=45,
            )

        self._comparar(_linea)

    def test_linea_estado_nota_en_curso(self) -> None:
        from Comun.reglas_partida import SistemaPuntuacion

        def _linea(b):
            reglas = b.reglas_libre(
                ConfigReglasLibre(
                    modo_infinito=False,
                    n_preguntas=10,
                    vidas=None,
                    sistema=SistemaPuntuacion.NOTA,
                )
            )
            return b.linea_estado_partida(
                reglas=reglas,
                progreso="Pregunta 3/10",
                aciertos=2,
                respondidas=3,
            )

        self._comparar(_linea)

    def test_nombre_jugador_defecto(self) -> None:
        self._comparar(lambda b: b.nombre_jugador_defecto())

    def test_catalogo_historia_ids(self) -> None:
        self._comparar(lambda b: b.catalogo_historia_ids())

    def test_reglas_historia_simulacro(self) -> None:
        self._comparar(lambda b: b.reglas_historia_preset("simulacro_examen"))

    def test_reglas_historia_resistencia(self) -> None:
        self._comparar(lambda b: b.reglas_historia_preset("ranking_resistencia"))


if __name__ == "__main__":
    unittest.main()
