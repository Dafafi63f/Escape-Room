#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recogida y envio de feedback del jugador (archivo local + correo SMTP)."""

from __future__ import annotations

import json
import secrets
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path

from .config_creador import mensaje_crear_creador_privado
from Comun.contacto_creador import lineas_contacto_alternativo
from Comun.jugador import NOMBRE_JUGADOR_DEFECTO, nombre_jugador_efectivo
from Comun.rutas import (
    resolver_config_creador_privado,
    resolver_dir_feedback,
    ruta_feedback_para_usuario,
)


class CategoriaFeedback(str, Enum):
    BUG = "bug"
    SUGERENCIA = "sugerencia"
    PREGUNTA_INCORRECTA = "pregunta_incorrecta"
    CONTROLES_INTERFAZ = "controles_interfaz"
    OTRO = "otro"


@dataclass
class ReporteFeedback:
    categoria: CategoriaFeedback
    mensaje: str
    jugador: str = NOMBRE_JUGADOR_DEFECTO
    contacto: str = ""
    area: str = ""
    id_reporte: str = ""

    def __post_init__(self) -> None:
        if not self.id_reporte:
            ahora = datetime.now()
            self.id_reporte = f"FB-{ahora:%Y%m%d}-{ahora:%H%M%S}-{secrets.token_hex(2)}"


def _slug(texto: str, max_len: int = 24) -> str:
    limpio = "".join(c if c.isalnum() else "_" for c in (texto or "").strip())
    return (limpio.strip("_") or "sin")[:max_len]


def _cuerpo_texto(reporte: ReporteFeedback) -> str:
    jugador = nombre_jugador_efectivo(reporte.jugador or "")
    contacto = (reporte.contacto or "").strip() or "Sin contacto"
    mensaje = (reporte.mensaje or "").strip() or "(sin mensaje)"
    area = (reporte.area or "").strip() or "general"
    lineas = [
        "=== FEEDBACK MATCAD ===",
        f"ID: {reporte.id_reporte}",
        f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Jugador: {jugador}",
        f"Categoria: {reporte.categoria.value}",
        f"Area: {area}",
        f"Contacto: {contacto}",
        "",
        "Mensaje:",
        mensaje,
        "",
    ]
    return "\n".join(lineas)


def guardar_reporte_local(reporte: ReporteFeedback) -> Path:
    nombre = (
        f"feedback_{_slug(reporte.categoria.value)}_{_slug(reporte.jugador)}_"
        f"{datetime.now():%Y%m%d_%H%M%S}_{reporte.id_reporte.split('-')[-1]}.txt"
    )
    destino = resolver_dir_feedback() / nombre
    destino.write_text(_cuerpo_texto(reporte), encoding="utf-8")
    return destino


def _leer_json(path: Path) -> dict:
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _cargar_config() -> dict:
    """SMTP del feedback desde ``Data/Banco/creador_privado.json`` (seccion feedback_smtp)."""
    path_privado = resolver_config_creador_privado()
    if path_privado is None:
        return {}
    privado = _leer_json(path_privado)
    smtp = privado.get("feedback_smtp")
    if isinstance(smtp, dict) and smtp:
        return smtp
    return {}


def _correo_destino(config: dict) -> str:
    return (config.get("smtp_destino") or config.get("correo_destino") or "").strip()


def _correo_asunto(config: dict, reporte: ReporteFeedback) -> str:
    return (
        config.get("correo_asunto")
        or config.get("mailto_asunto")
        or f"MATCAD Feedback [{reporte.id_reporte}]"
    )


def _enviar_smtp(reporte: ReporteFeedback, config: dict) -> tuple[bool, str | None]:
    """Envia el feedback por SMTP si hay credenciales configuradas."""
    servidor = (config.get("smtp_servidor") or "").strip()
    usuario = (config.get("smtp_usuario") or "").strip()
    password = (config.get("smtp_password") or "").strip()
    destino = _correo_destino(config)
    if not all((servidor, usuario, password, destino)):
        return (
            False,
            "Faltan datos SMTP (servidor, usuario, password, destino) en "
            "Data/Banco/creador_privado.json (seccion feedback_smtp).",
        )
    puerto = int(config.get("smtp_puerto", 587))
    asunto = _correo_asunto(config, reporte)
    remitente = (config.get("smtp_remitente") or usuario).strip()
    mensaje = MIMEText(_cuerpo_texto(reporte), "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destino
    try:
        with smtplib.SMTP(servidor, puerto, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(usuario, password)
            smtp.sendmail(remitente, [destino], mensaje.as_string())
        return True, None
    except (OSError, smtplib.SMTPException) as exc:
        return False, str(exc)


def _faltan_credenciales_smtp(error: str | None) -> bool:
    return bool(error and "Faltan datos SMTP" in error)


@dataclass
class ResultadoEnvioFeedback:
    archivo: Path
    smtp_enviado: bool = False
    smtp_destino: str = ""
    smtp_error: str | None = None


def enviar_feedback(reporte: ReporteFeedback) -> ResultadoEnvioFeedback:
    """Guarda en disco y envia por correo SMTP al creador."""
    archivo = guardar_reporte_local(reporte)
    config = _cargar_config()
    resultado = ResultadoEnvioFeedback(archivo=archivo)
    if not config.get("habilitar_smtp", True):
        resultado.smtp_error = (
            "SMTP deshabilitado en Data/Banco/creador_privado.json (seccion feedback_smtp)."
        )
        return resultado
    ok, error = _enviar_smtp(reporte, config)
    resultado.smtp_enviado = ok
    resultado.smtp_error = error
    if ok:
        resultado.smtp_destino = _correo_destino(config)
    return resultado


def describir_resultado_envio(resultado: ResultadoEnvioFeedback) -> list[str]:
    lineas = [
        "Feedback registrado correctamente.",
        f"Copia local: {ruta_feedback_para_usuario(resultado.archivo)}",
    ]
    if resultado.smtp_enviado:
        lineas.append(f"Correo enviado automaticamente a {resultado.smtp_destino}.")
    elif _faltan_credenciales_smtp(resultado.smtp_error):
        lineas.append(
            "Envio automatico no configurado: falta smtp_password en "
            "Data/Banco/creador_privado.json (seccion feedback_smtp)."
        )
        lineas.append(mensaje_crear_creador_privado())
        lineas.append(
            "En Gmail: Seguridad > Verificacion en 2 pasos > Contraseñas de "
            "aplicaciones; pega la de 16 caracteres en smtp_password."
        )
    elif resultado.smtp_error:
        lineas.append(f"No se pudo enviar por correo: {resultado.smtp_error}")
    contacto = lineas_contacto_alternativo()
    if contacto:
        lineas.append("")
        lineas.extend(contacto)
    return lineas
