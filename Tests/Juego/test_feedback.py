#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.support import ensure_juego_path

ensure_juego_path()

from Consola.envio_feedback import (
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
            with patch("Consola.envio_feedback.resolver_dir_feedback", return_value=Path(tmp)):
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
                "Consola.envio_feedback.resolver_config_creador_privado",
                return_value=privado,
            ):
                config = _cargar_config()
        self.assertEqual(config.get("smtp_destino"), "privado@ejemplo.com")

    def test_cargar_config_vacio_sin_fichero(self) -> None:
        with patch(
            "Consola.envio_feedback.resolver_config_creador_privado",
            return_value=None,
        ):
            self.assertEqual(_cargar_config(), {})

    @patch("Consola.envio_feedback._cargar_config")
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
            with patch("Consola.envio_feedback.resolver_dir_feedback", return_value=Path(tmp)):
                resultado = enviar_feedback(reporte)
        self.assertFalse(resultado.smtp_enviado)
        self.assertIn("Faltan datos SMTP", resultado.smtp_error or "")

    @patch("Consola.envio_feedback.smtplib.SMTP")
    @patch("Consola.envio_feedback._cargar_config")
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
            with patch("Consola.envio_feedback.resolver_dir_feedback", return_value=Path(tmp)):
                resultado = enviar_feedback(reporte)
        self.assertTrue(resultado.smtp_enviado)
        self.assertEqual(resultado.smtp_destino, "destino@gmail.com")
        smtp.login.assert_called_once_with("remitente@gmail.com", "app-pass")
        smtp.sendmail.assert_called_once()


if __name__ == "__main__":
    unittest.main()
