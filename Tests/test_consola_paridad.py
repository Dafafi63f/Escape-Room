#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrada de consola, robustez y paridad consola↔gráfico.

Secciones:
- test_robustez_entrada.py
- test_paridad_consola_grafico.py
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

# --- test_robustez_entrada.py ---

from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.support import ensure_juego_path

ensure_juego_path()

from Consola.consola import pedir_entero_en_rango, pedir_opcion
from Consola.entrada_menu import (
    TECLA_AYUDA,
    TECLA_FEEDBACK,
    TipoTecla,
    _EventoTecla,
    elegir_indice_menu,
)
from Consola.motor_partida import EstadoPartida, ResultadoRespuesta, preguntar_con_reglas
from Comun.modelos import Pregunta
from Comun.reglas_partida import preset_libre_arcade
from Consola.navegacion import (
    AccionPausa,
    SalirPrograma,
    VolverAtras,
    menu_ayuda_dinamico,
    menu_pausa,
)


def _pregunta_ejemplo(*, correcta: str = "B") -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia="Test",
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta=correcta,
    )


def _ev(tipo: TipoTecla, valor: str = "") -> _EventoTecla:
    return _EventoTecla(tipo, valor)


class TestEntradaConsola(unittest.TestCase):
    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_menu_opcion_1(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2", "3", "4"]), "1")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_opcion_cero_en_menu_0_3(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["0", "1", "2", "3"], default="0"), "0")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.DIGITO, "0"))
    def test_tecla_cero_valida_en_menu_0_3(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["0", "1", "2", "3"], default="0"), "0")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ENTER))
    def test_enter_pregunta_elige_a(self, _mock) -> None:
        """Enter sin pulsar tecla = respuesta A (defecto en pregunta)."""
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertFalse(r.acierto)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.IGNORAR), _ev(TipoTecla.DIGITO, "2")],
    )
    def test_tecla_invalida_ignorada(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2"]), "2")

    def test_eof_en_leer_linea_sale_programa(self) -> None:
        from Consola.navegacion import leer_linea

        with self.assertRaises(SalirPrograma):
            with patch("Consola.navegacion._input_seguro", side_effect=SalirPrograma):
                with patch.object(sys, "platform", "linux"):
                    leer_linea("x: ")
        with self.assertRaises(SalirPrograma):
            with patch(
                "Consola.entrada_menu._leer_tecla_texto_windows", side_effect=EOFError
            ):
                with patch.object(sys, "platform", "win32"):
                    leer_linea("x: ")

    @patch("Consola.navegacion.invocar_feedback_rapido")
    @patch("Consola.navegacion.feedback_rapido_disponible", return_value=True)
    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, TECLA_FEEDBACK), _ev(TipoTecla.ENTER)],
    )
    def test_tecla_f_abre_feedback(self, _mock_leer, _mock_disp, mock_invocar) -> None:
        self.assertEqual(elegir_indice_menu(2, prompt="m"), 1)
        mock_invocar.assert_called_once()

    def test_pedir_texto_vacio_usa_default(self) -> None:
        from Consola.consola import TEXTO_DEFAULT_VACIO, pedir_texto

        with patch("Consola.consola.leer_linea", return_value=""):
            self.assertEqual(pedir_texto("Nombre: "), TEXTO_DEFAULT_VACIO)
        with patch("Consola.consola.leer_linea", return_value="  "):
            self.assertEqual(pedir_texto("Nombre: ", default="Anonimo"), "Anonimo")

    def test_pedir_entero_rango_invertido_se_normaliza(self) -> None:
        with patch("Consola.consola.leer_linea", return_value=""):
            v = pedir_entero_en_rango("n", 5, 2, 99)
        self.assertEqual(v, 5)


class TestMenuAyuda(unittest.TestCase):
    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, TECLA_AYUDA), _ev(TipoTecla.ENTER)],
    )
    @patch("Consola.navegacion.menu_ayuda_dinamico")
    def test_tecla_h_abre_ayuda_y_luego_responde(self, mock_ayuda, _mock_tecla) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2"]), "1")
        mock_ayuda.assert_called_once_with(en_partida=False)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.SUPR)],
    )
    @patch("Consola.navegacion.limpiar_consola")
    @patch("Consola.navegacion._dibujar_menu_ayuda")
    def test_menu_ayuda_supr_cierra(self, _mock_dibujar, _mock_cls, _mock_tecla) -> None:
        menu_ayuda_dinamico()

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.DIGITO, "5"), _ev(TipoTecla.SUPR)],
    )
    @patch("Consola.navegacion.limpiar_consola")
    @patch("Consola.navegacion._dibujar_menu_ayuda")
    def test_menu_ayuda_otra_tecla_ignorada(self, mock_dibujar, _mock_cls, _mock_tecla) -> None:
        menu_ayuda_dinamico()
        self.assertEqual(mock_dibujar.call_count, 2)


class TestMenuPausa(unittest.TestCase):
    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=2)
    def test_pausa_opcion2_pantalla_titulo(self, _mock) -> None:
        self.assertEqual(menu_pausa(en_partida=False), AccionPausa.PANTALLA_TITULO)

    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=1)
    def test_pausa_opcion1_continuar(self, _mock) -> None:
        self.assertEqual(menu_pausa(en_partida=True), AccionPausa.CONTINUAR)

    @patch("Consola.entrada_menu.elegir_indice_menu", return_value=3)
    def test_opcion3_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            menu_pausa()

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.ESCAPE))
    def test_esc_en_pausa_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            elegir_indice_menu(3, defecto=1, en_pausa=True, prompt="")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_menu_principal_salir(self, _mock) -> None:
        with self.assertRaises(SalirPrograma):
            elegir_indice_menu(4, es_menu_principal=True, prompt="m")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_submenu_atras(self, _mock) -> None:
        with self.assertRaises(VolverAtras):
            elegir_indice_menu(3, permitir_atras=True, prompt="m")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.SUPR))
    def test_supr_en_pausa_continuar(self, _mock) -> None:
        self.assertEqual(elegir_indice_menu(3, en_pausa=True, prompt=""), 1)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.SUPR), _ev(TipoTecla.LETRA, "B")],
    )
    def test_supr_en_pregunta_ignorado(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)


class TestMotorPregunta(unittest.TestCase):
    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "A"), _ev(TipoTecla.DIGITO, "1")],
    )
    def test_letra_a_ignorada_en_menu_numerico(self, _mock) -> None:
        self.assertEqual(elegir_indice_menu(2, prompt="m"), 1)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "S"), _ev(TipoTecla.ENTER)],
    )
    def test_sn_ignorado_en_menu_numerico(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["1", "2"]), "1")

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.LETRA, "N"), _ev(TipoTecla.ENTER)],
    )
    def test_sn_funciona_en_menu_si_no(self, _mock) -> None:
        self.assertEqual(pedir_opcion("m", ["S", "N"], default="S"), "N")

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "A"))
    def test_letra_a_en_partida_elige_opcion(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertFalse(r.acierto)

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "B"))
    def test_respuesta_correcta(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)

    @patch(
        "Consola.entrada_menu.leer_tecla",
        side_effect=[_ev(TipoTecla.DIGITO, "2"), _ev(TipoTecla.LETRA, "B")],
    )
    def test_digitos_ignorados_en_pregunta(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(), estado)
        self.assertTrue(r.acierto)

    @patch("Consola.entrada_menu.leer_tecla", return_value=_ev(TipoTecla.LETRA, "A"))
    def test_pregunta_sin_correcta_valida_cuenta_fallo(self, _mock) -> None:
        estado = EstadoPartida("T", preset_libre_arcade(), vidas_restantes=3)
        r = preguntar_con_reglas(_pregunta_ejemplo(correcta="X"), estado)
        self.assertFalse(r.acierto)
        self.assertIsInstance(r, ResultadoRespuesta)

# --- test_paridad_consola_grafico.py ---

from typing import Callable, TypeVar

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.paridad_juegos import (
    BACKENDS,
    ConfigReglasLibre,
    crear_backend,
    tupla_opciones,
    tupla_reglas,
)

T = TypeVar("T")

try:
    crear_backend("grafico")
    _GRAFICO_DISPONIBLE = True
except Exception:
    _GRAFICO_DISPONIBLE = False


@unittest.skipUnless(_GRAFICO_DISPONIBLE, "Grafico no disponible")
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

if __name__ == "__main__":
    unittest.main()
