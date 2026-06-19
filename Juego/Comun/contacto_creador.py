#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canales de contacto públicos del creador (sin credenciales SMTP ni tokens)."""

from __future__ import annotations

import json

from Comun.rutas import resolver_config_creador_privado

__all__ = [
    "canales_contacto_alternativo",
    "lineas_contacto_alternativo",
    "nota_contacto_jugador",
    "texto_bloque_contacto_alternativo",
]

_PLACEHOLDER_CORREOS = frozenset({"tu.correo@ejemplo.com"})
_PLACEHOLDER_GITHUB_USUARIO = frozenset({"tu_usuario"})
_PLACEHOLDER_GITHUB_REPO = frozenset({"nombre-del-repo"})
_NOTA_DEFECTO = (
    "Si prefieres otro canal, también puedes contactar al creador así:"
)


def _leer_privado() -> dict:
    path = resolver_config_creador_privado()
    if path is None:
        return {}
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _es_placeholder_correo(correo: str) -> bool:
    valor = correo.strip().lower()
    if not valor:
        return True
    if valor in _PLACEHOLDER_CORREOS:
        return True
    return "ejemplo.com" in valor


def _es_placeholder_github(texto: str) -> bool:
    valor = texto.strip().lower()
    if not valor:
        return True
    if valor in _PLACEHOLDER_GITHUB_USUARIO:
        return True
    if valor in _PLACEHOLDER_GITHUB_REPO:
        return True
    return "tu_usuario" in valor or "nombre-del-repo" in valor


def _url_github_issues(url_repo: str) -> str:
    url = url_repo.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    if "github.com" not in url.lower():
        return ""
    return f"{url}/issues"


def _correo_publico(privado: dict) -> str:
    creador = privado.get("creador")
    if not isinstance(creador, dict):
        return ""
    correo = str(creador.get("correo", "")).strip()
    if correo and not _es_placeholder_correo(correo):
        return correo
    return ""


def _github_issues_publico(privado: dict) -> str:
    github = privado.get("github")
    if not isinstance(github, dict):
        return ""
    url = str(github.get("url", "")).strip()
    if url and not _es_placeholder_github(url):
        issues = _url_github_issues(url)
        if issues:
            return issues
    usuario = str(github.get("usuario", "")).strip()
    repo = str(github.get("repositorio", "")).strip()
    if (
        usuario
        and repo
        and not _es_placeholder_github(usuario)
        and not _es_placeholder_github(repo)
    ):
        return f"https://github.com/{usuario}/{repo}/issues"
    return ""


def _resolver_autovalor(etiqueta: str, privado: dict) -> str:
    clave = etiqueta.lower()
    if any(p in clave for p in ("correo", "email", "mail")):
        return _correo_publico(privado)
    if "github" in clave:
        return _github_issues_publico(privado)
    return ""


def _es_canal_github(etiqueta: str, valor: str = "") -> bool:
    clave = etiqueta.lower()
    if "github" in clave:
        return True
    return "github.com" in valor.strip().lower()


def _canal_desde_item(item: dict, privado: dict) -> tuple[str, str] | None:
    etiqueta = str(item.get("etiqueta", "")).strip()
    if not etiqueta or _es_canal_github(etiqueta):
        return None
    valor = str(item.get("valor", "")).strip()
    if (
        not valor
        or _es_placeholder_correo(valor)
        or _es_placeholder_github(valor)
    ):
        valor = _resolver_autovalor(etiqueta, privado)
    if not valor or _es_canal_github(etiqueta, valor):
        return None
    return etiqueta, valor


def canales_contacto_alternativo() -> list[tuple[str, str]]:
    """Devuelve pares (etiqueta, valor) seguros para mostrar al jugador."""
    privado = _leer_privado()
    contacto = privado.get("contacto_jugador")
    canales_cfg = contacto.get("canales") if isinstance(contacto, dict) else None

    if isinstance(canales_cfg, list) and canales_cfg:
        resultado: list[tuple[str, str]] = []
        for item in canales_cfg:
            if not isinstance(item, dict):
                continue
            canal = _canal_desde_item(item, privado)
            if canal:
                resultado.append(canal)
        return resultado

    resultado = []
    correo = _correo_publico(privado)
    if correo:
        resultado.append(("Correo", correo))
    return resultado


def nota_contacto_jugador() -> str:
    privado = _leer_privado()
    contacto = privado.get("contacto_jugador")
    if isinstance(contacto, dict):
        nota = str(contacto.get("nota", "")).strip()
        if nota:
            return nota
    return _NOTA_DEFECTO


def lineas_contacto_alternativo() -> list[str]:
    canales = canales_contacto_alternativo()
    if not canales:
        return []
    lineas = [nota_contacto_jugador()]
    lineas.extend(f"  · {etiqueta}: {valor}" for etiqueta, valor in canales)
    return lineas


def texto_bloque_contacto_alternativo() -> str:
    return "\n".join(lineas_contacto_alternativo())
