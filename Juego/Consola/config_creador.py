#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plantilla y utilidades para ``Data/creador_privado.json`` (no versionado)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from Comun.rutas import PATH_PREGUNTAS, resolver_config_creador_privado

FICHERO_CREADOR_PRIVADO = "creador_privado.json"

PLANTILLA_CREADOR_PRIVADO: dict = {
    "creador": {
        "nombre": "Tu nombre completo",
        "correo": "tu.correo@ejemplo.com",
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
        "correo_destino": "tu.correo@ejemplo.com",
        "correo_asunto": "MATCAD — feedback del juego",
        "habilitar_smtp": True,
        "smtp_servidor": "smtp.gmail.com",
        "smtp_puerto": 587,
        "smtp_usuario": "tu.cuenta@gmail.com",
        "smtp_password": "",
        "smtp_remitente": "tu.cuenta@gmail.com",
        "smtp_destino": "tu.correo@ejemplo.com",
    },
}


def plantilla_creador_privado() -> dict:
    """Copia de la plantilla por defecto (evita mutar la constante del modulo)."""
    return deepcopy(PLANTILLA_CREADOR_PRIVADO)


def ruta_creador_privado() -> Path:
    """Ruta a ``Data/creador_privado.json`` (existe o no)."""
    existente = resolver_config_creador_privado()
    if existente is not None:
        return existente
    return PATH_PREGUNTAS.parent / FICHERO_CREADOR_PRIVADO


def texto_plantilla_creador_privado() -> str:
    return json.dumps(plantilla_creador_privado(), indent=2, ensure_ascii=False) + "\n"


def escribir_plantilla_creador_privado(
    destino: Path | None = None,
    *,
    sobrescribir: bool = False,
) -> Path:
    """Escribe la plantilla en ``Data/creador_privado.json`` si aun no existe."""
    ruta = destino or ruta_creador_privado()
    if ruta.exists() and not sobrescribir:
        raise FileExistsError(f"Ya existe {ruta}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto_plantilla_creador_privado(), encoding="utf-8")
    return ruta


def mensaje_crear_creador_privado() -> str:
    return (
        "Crea Data/creador_privado.json con la plantilla del modulo "
        "(python -m Consola.config_creador desde Juego/)."
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Genera Data/creador_privado.json desde la plantilla embebida",
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
