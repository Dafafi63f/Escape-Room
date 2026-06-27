#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informes al cerrar partida y envío de feedback.

Secciones:
- test_informe_examen.py
- test_feedback.py
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

# --- test_informe_examen.py ---

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.preferencias_grafico import NOMBRE_JUGADOR_DEFECTO
from Comun.informe_examen import (
    RegistroRespuesta,
    construir_nombre_archivo_informe,
    formatear_informe_examen,
    generar_id_sesion,
    publicar_informe_partida,
)
from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    ResultadoRespuesta,
    evaluar_respuesta,
    presentacion_opciones_pantalla,
    semilla_orden_opciones,
)
from Comun.reglas_partida import preset_historia_examen, preset_libre_arcade


def _pregunta_simple() -> Pregunta:
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
        correcta="B",
    )


class TestInformeExamen(unittest.TestCase):
    def test_informe_incluye_correccion_y_estadisticas(self) -> None:
        reglas = preset_historia_examen()
        estado = EstadoPartida("Ana", reglas, vidas_restantes=None)
        estado.aciertos = 1
        estado.respondidas = 2
        registros = [
            RegistroRespuesta(1, _pregunta_simple(), "B", True),
            RegistroRespuesta(2, _pregunta_simple(), "A", False),
        ]
        id_sesion = generar_id_sesion()
        nombre = construir_nombre_archivo_informe(
            prefijo="examen",
            nombre_jugador="Ana",
            id_sesion=id_sesion,
            meta={"modo": "Historia", "perfil": "simulacro"},
        )
        texto = formatear_informe_examen(
            estado,
            registros,
            titulo="FIN DEL EXAMEN (modo historia)",
            meta={
                "id_sesion": id_sesion,
                "nombre_archivo": nombre,
                "etiqueta_sesion": "Examen historia — simulacro",
                "modo": "Historia",
                "perfil": "simulacro",
                "n_preguntas": 2,
            },
            total_previsto=2,
            fallos_por_materia={"Test": 1},
        )
        self.assertIn("CORRECCIÓN DETALLADA", texto)
        self.assertIn("ESTADÍSTICAS POR MATERIA", texto)
        self.assertIn("Feedback:", texto)
        self.assertIn("MATERIAS A REFORZAR", texto)
        self.assertIn("Nota (0-10):", texto)
        self.assertIn(f"ID: {id_sesion}", texto)
        self.assertIn("Examen historia", texto)
        self.assertNotIn("Archivo:", texto)
        self.assertNotIn("Configuración elegida", texto)

    def test_nombres_archivo_distintos_por_id(self) -> None:
        id1 = generar_id_sesion()
        id2 = generar_id_sesion()
        meta = {"modo": "Libre"}
        n1 = construir_nombre_archivo_informe(
            prefijo="partida_libre", nombre_jugador="x", id_sesion=id1, meta=meta
        )
        n2 = construir_nombre_archivo_informe(
            prefijo="partida_libre", nombre_jugador="x", id_sesion=id2, meta=meta
        )
        self.assertNotEqual(n1, n2)

    def test_nombre_libre_sin_repetir_modo(self) -> None:
        nombre = construir_nombre_archivo_informe(
            prefijo="partida_libre",
            nombre_jugador=NOMBRE_JUGADOR_DEFECTO,
            id_sesion="MATCAD-20260617-182233-9ecf",
            meta={"modo": "libre", "tipo_actividad": "libre_infinito"},
        )
        self.assertRegex(
            nombre,
            r"^partida_libre_infinito_.+_\d{8}_\d{6}_9ecf\.txt$",
        )
        self.assertNotIn("_libre_libre_", nombre)

    def test_dos_actividades_misma_ejecucion_dos_archivos(self) -> None:
        """Cada cierre de partida genera su propio .txt (modo independiente)."""
        import tempfile
        from unittest.mock import patch

        reglas = preset_historia_examen()
        registros = [RegistroRespuesta(1, _pregunta_simple(), "B", True)]

        with tempfile.TemporaryDirectory() as tmp:
            dir_tmp = Path(tmp)
            with patch(
                "Comun.informe_examen.resolver_dir_informes",
                return_value=dir_tmp,
            ):
                estado_libre = EstadoPartida("Ana", preset_libre_arcade(), vidas_restantes=3)
                estado_libre.aciertos = 1
                estado_libre.respondidas = 1
                ruta1 = publicar_informe_partida(
                    estado_libre,
                    registros,
                    titulo="FIN DE PARTIDA (modo libre)",
                    total_previsto=10,
                    nombre_jugador="Ana",
                    meta={
                        "modo": "libre",
                        "tipo_actividad": "libre_finito",
                        "etiqueta_sesion": "Partida modo libre",
                    },
                    prefijo="partida_libre",
                    imprimir_aviso_terminal=False,
                )

                estado_hist = EstadoPartida("Ana", reglas, vidas_restantes=None)
                estado_hist.aciertos = 1
                estado_hist.respondidas = 1
                ruta2 = publicar_informe_partida(
                    estado_hist,
                    registros,
                    titulo="FIN DEL EXAMEN (modo historia)",
                    total_previsto=5,
                    nombre_jugador="Ana",
                    meta={
                        "modo": "historia",
                        "tipo_actividad": "historia",
                        "preset": "simulacro",
                        "perfil": "simulacro",
                        "etiqueta_sesion": "Historia — Simulacro",
                    },
                    prefijo="examen_historia",
                    imprimir_aviso_terminal=False,
                )

                self.assertIsNotNone(ruta1)
                self.assertIsNotNone(ruta2)
                self.assertNotEqual(ruta1, ruta2)
                self.assertEqual(len(list(dir_tmp.glob("*.txt"))), 2)

    def test_preset_historia_examen_correccion_al_final(self) -> None:
        reglas = preset_historia_examen()
        self.assertTrue(reglas.correccion_al_final)
        self.assertFalse(reglas.mostrar_solucion_tras_fallo)

    def test_examen_cerrado_sin_mensajes_inmediatos(self) -> None:
        reglas = preset_historia_examen()
        estado = EstadoPartida("T", reglas, vidas_restantes=None)
        p = _pregunta_simple()
        fb1 = evaluar_respuesta(p, estado, ResultadoRespuesta(acierto=False, respuesta="A"))
        fb2 = evaluar_respuesta(p, estado, ResultadoRespuesta(acierto=True, respuesta="B"))
        self.assertEqual(fb1.mensaje, "Respuesta registrada.")
        self.assertEqual(fb2.mensaje, "Respuesta registrada.")
        self.assertEqual(estado.aciertos, 1)
        self.assertEqual(estado.respondidas, 2)

    def test_orden_opciones_permutado_en_pantalla(self) -> None:
        p = _pregunta_simple()
        pres_a = presentacion_opciones_pantalla(p, semilla=11)
        pres_b = presentacion_opciones_pantalla(p, semilla=22)
        pres_rep = presentacion_opciones_pantalla(p, semilla=11)
        self.assertEqual(pres_a.filas, pres_rep.filas)
        etiquetas_a = tuple(etiq for etiq, _, _ in pres_a.filas)
        self.assertEqual(etiquetas_a, ("A", "B", "C", "D"))
        self.assertNotEqual(pres_a.filas, pres_b.filas)
        origen_correcta = next(
            origen for etiq, _, origen in pres_a.filas if etiq == "A"
        )
        self.assertEqual(pres_a.letra_dataset("A"), origen_correcta)
        self.assertIsNotNone(pres_a.etiqueta_visual(p.correcta))
        otra_vez = presentacion_opciones_pantalla(
            p,
            semilla=semilla_orden_opciones(
                semilla_base=99,
                numero_turno=0,
                indice_pregunta=0,
            ),
        )
        otra_vez_2 = presentacion_opciones_pantalla(
            p,
            semilla=semilla_orden_opciones(
                semilla_base=99,
                numero_turno=1,
                indice_pregunta=0,
            ),
        )
        self.assertNotEqual(otra_vez.filas, otra_vez_2.filas)

    def test_arcade_muestra_feedback_inmediato(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida("T", reglas, vidas_restantes=3)
        fb = evaluar_respuesta(
            _pregunta_simple(),
            estado,
            ResultadoRespuesta(acierto=True, respuesta="B"),
        )
        self.assertTrue(fb.mensaje.startswith("Correcto"))

# --- test_feedback.py ---

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.feedback import (
    CategoriaFeedback,
    ReporteFeedback,
    _cargar_config,
    _cuerpo_texto,
    enviar_feedback,
    guardar_reporte_local,
)


class TestFeedback(unittest.TestCase):
    def test_guardar_reporte_contiene_datos(self) -> None:
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.BUG,
            mensaje="El menu H muestra dos lineas",
            jugador="Tester",
            contacto="test@ejemplo.com",
            area="controles_interfaz",
            id_reporte="FB-TEST-001",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch("Comun.feedback.resolver_dir_feedback", return_value=Path(tmp)):
                path = guardar_reporte_local(reporte)
            texto = path.read_text(encoding="utf-8")
        self.assertIn("FB-TEST-001", texto)
        self.assertIn("bug", texto)
        self.assertIn("Tester", texto)
        self.assertIn("El menu H muestra dos lineas", texto)

    def test_cuerpo_texto_valores_por_defecto(self) -> None:
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.OTRO,
            mensaje="",
            jugador="",
            contacto="",
            area="",
            id_reporte="FB-DEF",
        )
        texto = _cuerpo_texto(reporte)
        self.assertIn("Anonimo", texto)
        self.assertIn("Sin contacto", texto)
        self.assertIn("(sin mensaje)", texto)

    def test_cuerpo_texto_multilinea(self) -> None:
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.SUGERENCIA,
            mensaje="Linea 1\nLinea 2",
            id_reporte="FB-X",
        )
        self.assertIn("Linea 2", _cuerpo_texto(reporte))

    def test_cargar_config_desde_creador_privado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            privado = Path(tmp) / "creador_privado.json"
            privado.write_text(
                '{"feedback_smtp": {"smtp_destino": "privado@ejemplo.com", "habilitar_smtp": true}}',
                encoding="utf-8",
            )
            with patch(
                "Comun.feedback.resolver_config_creador_privado",
                return_value=privado,
            ):
                config = _cargar_config()
        self.assertEqual(config.get("smtp_destino"), "privado@ejemplo.com")

    def test_cargar_config_vacio_sin_fichero(self) -> None:
        with patch(
            "Comun.feedback.resolver_config_creador_privado",
            return_value=None,
        ):
            self.assertEqual(_cargar_config(), {})

    @patch("Comun.feedback._cargar_config")
    def test_sin_envio_si_falta_password_smtp(self, mock_cfg) -> None:
        mock_cfg.return_value = {
            "habilitar_smtp": True,
            "smtp_servidor": "smtp.gmail.com",
            "smtp_usuario": "a@gmail.com",
            "smtp_password": "",
            "smtp_destino": "a@gmail.com",
        }
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.BUG,
            mensaje="Hola",
            id_reporte="FB-NOMAIL",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch("Comun.feedback.resolver_dir_feedback", return_value=Path(tmp)):
                resultado = enviar_feedback(reporte)
        self.assertFalse(resultado.smtp_enviado)
        self.assertIn("Faltan datos SMTP", resultado.smtp_error or "")

    @patch("Comun.feedback.smtplib.SMTP")
    @patch("Comun.feedback._cargar_config")
    def test_enviar_smtp_si_configurado(self, mock_cfg, mock_smtp_cls) -> None:
        mock_cfg.return_value = {
            "habilitar_smtp": True,
            "smtp_servidor": "smtp.gmail.com",
            "smtp_puerto": 587,
            "smtp_usuario": "remitente@gmail.com",
            "smtp_password": "app-pass",
            "smtp_destino": "destino@gmail.com",
            "correo_asunto": "Test",
        }
        smtp = mock_smtp_cls.return_value.__enter__.return_value
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.BUG,
            mensaje="Fallo en paso 5",
            id_reporte="FB-SMTP",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch("Comun.feedback.resolver_dir_feedback", return_value=Path(tmp)):
                resultado = enviar_feedback(reporte)
        self.assertTrue(resultado.smtp_enviado)
        self.assertEqual(resultado.smtp_destino, "destino@gmail.com")
        smtp.login.assert_called_once_with("remitente@gmail.com", "app-pass")
        smtp.sendmail.assert_called_once()


class TestContactoCreador(unittest.TestCase):
    def test_canales_solo_correo_por_defecto(self) -> None:
        import json
        from Comun.feedback import canales_contacto_alternativo

        privado = {
            "creador": {"correo": "autor@uab.cat"},
            "github": {
                "usuario": "miusuario",
                "repositorio": "mi-repo",
                "url": "https://github.com/miusuario/mi-repo.git",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "creador_privado.json"
            path.write_text(json.dumps(privado), encoding="utf-8")
            with patch(
                "Comun.feedback.resolver_config_creador_privado",
                return_value=path,
            ):
                canales = canales_contacto_alternativo()
        self.assertEqual(canales, [("Correo", "autor@uab.cat")])

    def test_canales_configurados_explicitamente(self) -> None:
        import json
        from Comun.feedback import canales_contacto_alternativo, nota_contacto_jugador

        privado = {
            "contacto_jugador": {
                "nota": "Escríbeme por:",
                "canales": [
                    {"etiqueta": "LinkedIn", "valor": "https://linkedin.com/in/ejemplo"},
                    {"etiqueta": "Correo", "valor": ""},
                ],
            },
            "creador": {"correo": "autor@uab.cat"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "creador_privado.json"
            path.write_text(json.dumps(privado), encoding="utf-8")
            with patch(
                "Comun.feedback.resolver_config_creador_privado",
                return_value=path,
            ):
                self.assertEqual(nota_contacto_jugador(), "Escríbeme por:")
                canales = canales_contacto_alternativo()
        self.assertEqual(
            canales,
            [
                ("LinkedIn", "https://linkedin.com/in/ejemplo"),
                ("Correo", "autor@uab.cat"),
            ],
        )

    def test_describir_resultado_incluye_contacto(self) -> None:
        import json
        from Comun.feedback import ResultadoEnvioFeedback, describir_resultado_envio

        privado = {"creador": {"correo": "autor@uab.cat"}}
        with tempfile.TemporaryDirectory() as tmp:
            path_priv = Path(tmp) / "creador_privado.json"
            path_priv.write_text(json.dumps(privado), encoding="utf-8")
            archivo = Path(tmp) / "feedback.txt"
            archivo.write_text("ok", encoding="utf-8")
            with patch(
                "Comun.feedback.resolver_config_creador_privado",
                return_value=path_priv,
            ):
                lineas = describir_resultado_envio(
                    ResultadoEnvioFeedback(archivo=archivo, smtp_enviado=True, smtp_destino="x@y.z")
                )
        self.assertTrue(any("autor@uab.cat" in linea for linea in lineas))


if __name__ == "__main__":
    unittest.main()
