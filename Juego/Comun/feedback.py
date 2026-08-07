#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feedback del jugador, contacto público y plantilla creador_privado."""

from __future__ import annotations

import argparse
import json
import secrets
import smtplib
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path

from Comun.preferencias_grafico import NOMBRE_JUGADOR_DEFECTO, nombre_jugador_efectivo
from Comun.rutas import (
    resolver_config_creador_privado,
    resolver_dir_feedback,
    resolver_ruta_creador_privado_defecto,
    ruta_feedback_para_usuario,
)

# --- Categorías y áreas del formulario ---

CATEGORIAS_FEEDBACK: list[tuple[str, str]] = [
    ("bug", "Error o fallo del juego"),
    ("sugerencia", "Sugerencia de mejora"),
    ("pregunta_incorrecta", "Pregunta con error o respuesta dudosa"),
    ("controles_interfaz", "Controles, menús o interfaz"),
    ("otro", "Otro tema"),
]

AREAS_FEEDBACK: list[tuple[str, str]] = [
    ("menu", "Menús y navegación"),
    ("partida", "Durante una partida o pregunta"),
    ("datos", "Preguntas, materias o banco de datos"),
    ("informes", "Informes o resultados"),
    ("rendimiento", "Rendimiento o carga"),
    ("general", "General / no sé"),
]


def etiqueta_categoria(cat_id: str) -> str:
    for cid, desc in CATEGORIAS_FEEDBACK:
        if cid == cat_id:
            return desc
    return cat_id


def etiqueta_area(area_id: str) -> str:
    for aid, desc in AREAS_FEEDBACK:
        if aid == area_id:
            return desc
    return area_id


def indice_area_defecto() -> int:
    for i, (aid, _) in enumerate(AREAS_FEEDBACK):
        if aid == "general":
            return i
    return len(AREAS_FEEDBACK) - 1


# --- Plantilla creador_privado.json ---

FICHERO_CREADOR_PRIVADO = "creador_privado.json"
_CORREO_EJEMPLO = "tu.correo@ejemplo.com"

PLANTILLA_CREADOR_PRIVADO: dict = {
    "creador": {
        "nombre": "Tu nombre completo",
        "correo": _CORREO_EJEMPLO,
        "universidad": "UAB",
        "titulacion": "Grau en Enginyeria Informàtica",
        "tutor": "Nombre del tutor/a",
        "notas": "Apuntes personales solo para ti (no se suben a git).",
    },
    "github": {
        "usuario": "tu_usuario",
        "repositorio": "nombre-del-repo",
        "url": "https://github.com/tu_usuario/nombre-del-repo.git",
        "personal_access_token": "",
    },
    "feedback_smtp": {
        "correo_destino": _CORREO_EJEMPLO,
        "correo_asunto": "MATCAD — feedback del juego",
        "habilitar_smtp": True,
        "smtp_servidor": "smtp.gmail.com",
        "smtp_puerto": 587,
        "smtp_usuario": "tu.cuenta@gmail.com",
        "smtp_password": "",
        "smtp_remitente": "tu.cuenta@gmail.com",
        "smtp_destino": _CORREO_EJEMPLO,
    },
    "contacto_jugador": {
        "nota": "Si prefieres no usar el formulario del juego, también puedes escribirme por:",
        "canales": [
            {"etiqueta": "Correo", "valor": ""}
        ],
    },
}


def plantilla_creador_privado() -> dict:
    return deepcopy(PLANTILLA_CREADOR_PRIVADO)


def ruta_creador_privado() -> Path:
    return resolver_ruta_creador_privado_defecto()


def texto_plantilla_creador_privado() -> str:
    return json.dumps(plantilla_creador_privado(), indent=2, ensure_ascii=False) + "\n"


def escribir_plantilla_creador_privado(
    destino: Path | None = None,
    *,
    sobrescribir: bool = False,
) -> Path:
    ruta = destino or ruta_creador_privado()
    if ruta.exists() and not sobrescribir:
        raise FileExistsError(f"Ya existe {ruta}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto_plantilla_creador_privado(), encoding="utf-8")
    return ruta


def mensaje_crear_creador_privado() -> str:
    return (
        "Crea Data/Privado/creador_privado.json con la plantilla del modulo "
        "(python -m Comun.feedback desde Juego/)."
    )


# --- Contacto público del creador (estático; pantalla Info ℹ️) ---

CORREO_CONTACTO_CREADOR = "dafafi63@gmail.com"

NOTA_CONTACTO_JUGADOR = "Puedes contactar al creador por correo:"

CANALES_CONTACTO_JUGADOR: tuple[tuple[str, str], ...] = (
    ("Correo", CORREO_CONTACTO_CREADOR),
)


def canales_contacto_alternativo() -> list[tuple[str, str]]:
    return list(CANALES_CONTACTO_JUGADOR)


def nota_contacto_jugador() -> str:
    return NOTA_CONTACTO_JUGADOR


def lineas_contacto_alternativo() -> list[str]:
    canales = canales_contacto_alternativo()
    if not canales:
        return []
    lineas = [nota_contacto_jugador()]
    lineas.extend(f"  · {etiqueta}: {valor}" for etiqueta, valor in canales)
    return lineas


def texto_bloque_contacto_alternativo() -> str:
    return "\n".join(lineas_contacto_alternativo())


# --- Envío y guardado de feedback ---

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
    servidor = (config.get("smtp_servidor") or "").strip()
    usuario = (config.get("smtp_usuario") or "").strip()
    password = (config.get("smtp_password") or "").strip()
    destino = _correo_destino(config)
    if not all((servidor, usuario, password, destino)):
        return (
            False,
            "Faltan datos SMTP (servidor, usuario, password, destino) en "
            "Data/Privado/creador_privado.json (seccion feedback_smtp).",
        )
    puerto = int(config.get("smtp_puerto", 587))
    asunto = _correo_asunto(config, reporte)
    remitente = (config.get("smtp_remitente") or usuario).strip()
    mensaje = MIMEText(_cuerpo_texto(reporte), "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destino
    try:
        with smtplib.SMTP(servidor, puerto, timeout=8) as smtp:
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
    archivo = guardar_reporte_local(reporte)
    config = _cargar_config()
    resultado = ResultadoEnvioFeedback(archivo=archivo)
    if not config.get("habilitar_smtp", True):
        resultado.smtp_error = (
            "SMTP deshabilitado en Data/Privado/creador_privado.json (seccion feedback_smtp)."
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
            "Data/Privado/creador_privado.json (seccion feedback_smtp)."
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera Data/Privado/creador_privado.json desde la plantilla embebida",
    )
    parser.add_argument(
        "--sobrescribir",
        action="store_true",
        help="Sobrescribe el fichero si ya existe",
    )
    args = parser.parse_args()
    try:
        ruta = escribir_plantilla_creador_privado(sobrescribir=args.sobrescribir)
    except FileExistsError as exc:
        print(str(exc))
        return 1
    print(f"Plantilla escrita en: {ruta}")
    print("Rellena tus datos reales (correo, token GitHub, smtp_password, etc.).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
