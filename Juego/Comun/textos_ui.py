#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etiquetas de interfaz con emojis (consola: fondo oscuro; gráfico: botones claros)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = [
    "ContextoUi",
    "EmojiPar",
    "OpcionMenuPrincipal",
    "OPCIONES_MENU_PRINCIPAL",
    "BTN_ABANDONAR",
    "BTN_ATRAS",
    "BTN_CONTINUAR",
    "BTN_CONTINUAR_PARTIDA",
    "BTN_EMPEZAR",
    "BTN_GUARDAR_INFORME",
    "BTN_PANTALLA_TITULO",
    "BTN_SALIR_PROGRAMA",
    "BTN_SIGUIENTE",
    "BTN_VER_RANKING",
    "BTN_VOLVER",
    "BTN_VOLVER_MENU",
    "con_emoji",
    "emoji_icono",
    "etiqueta",
    "etiqueta_campo",
    "info_dataset",
    "mensaje_feedback",
    "nombre_paso",
    "posicion_emoji_navegacion",
    "resolver_emoji",
    "subtitulo",
    "titulo_flexible",
    "titulo_pantalla",
]

ContextoUi = Literal["grafico", "consola"]
PosicionEmoji = Literal["inicio", "fin", "simetrico"]


@dataclass(frozen=True)
class EmojiPar:
    """Par de emojis: gráfico (botones/fondos claros) y consola (fondo oscuro)."""

    grafico: str
    consola: str

    def elegir(self, contexto: ContextoUi) -> str:
        return self.consola if contexto == "consola" else self.grafico

    @staticmethod
    def igual(emoji: str) -> EmojiPar:
        return EmojiPar(emoji, emoji)


def _p(grafico: str, consola: str | None = None) -> EmojiPar:
    return EmojiPar(grafico, consola if consola is not None else grafico)


def resolver_emoji(emoji: str | EmojiPar, *, contexto: ContextoUi = "grafico") -> str:
    if isinstance(emoji, EmojiPar):
        return emoji.elegir(contexto)
    return emoji


# Iconos sueltos de la barra fija / atajos.
_EMOJI_ICONO: dict[str, EmojiPar] = {
    "feedback": _p("📣"),
    "pausa": _p("⏯", "⏸️"),
}

# Emojis por título de pantalla (clave = texto sin decorar).
_EMOJI_TITULO: dict[str, EmojiPar] = {
    "CUESTIONARIO MATCAD": _p("📝"),
    "MODO LIBRE": _p("🎮"),
    "MODO HISTORIA": _p("📖", "📕"),
    "MODO FEEDBACK": _p("📣"),
    "PAUSA": _p("⏯", "⏸️"),
    "FIN DE PARTIDA": _p("🏁"),
    "PARTIDA ABANDONADA": _p("⚠️"),
    "ABANDONO (modo libre)": _p("⚠️"),
    "FIN DE PARTIDA (modo libre)": _p("🏁"),
    "Ranking — resistencia": _p("🏆"),
    "PARTIDA (modo libre)": _p("🎮"),
    "PARTIDA (modo historia)": _p("📖", "📕"),
    "RANKING — RESISTENCIA INFINITA": _p("🏆"),
    "Banco de preguntas": _p("🗄️"),
    "Configuración modo libre": _p("⚙️"),
    "Modo historia": _p("📖", "📕"),
    "Modo libre — partida en curso": _p("🎮"),
    "Filtros de preguntas": _p("🔍"),
    "AYUDA — CONTROLES ACTUALES": _p("❓"),
    "Feedback": _p("📣"),
}

_EMOJI_TITULO_PREFIJO: tuple[tuple[str, EmojiPar], ...] = (
    ("FIN RACHA —", _p("🔥")),
    ("FIN —", _p("🏁")),
    ("FIN DE PARTIDA", _p("🏁")),
)

_EMOJI_FEEDBACK_PREFIJO: tuple[tuple[str, EmojiPar], ...] = (
    ("Correcto", _p("✅")),
    ("Incorrecto", _p("❌")),
    ("Tiempo agotado", _p("⏱️")),
    ("Respuesta registrada", _p("📝", "📋")),
)

_EMOJI_ETIQUETA: dict[str, EmojiPar] = {
    "nombre": _p("👤"),
    "nombre_teclado": _p("⌨️"),
    "tipo_partida": _p("🎯"),
    "filtro_principal": _p("🔍"),
    "valor_filtro": _p("🏷️"),
    "opciones_juego": _p("⚙️"),
    "nivel_inicial": _p("📈"),
    "nivel_minimo": _p("📉"),
    "nivel_maximo": _p("📈"),
    "niveles_complejidad": _p("📊"),
    "banco": _p("🗄️"),
    "n_preguntas": _p("🔢", "📝"),
    "vidas": _p("❤️"),
    "tiempo_modo": _p("⏱️"),
    "tiempo_pregunta": _p("⏳"),
    "tiempo_total": _p("🕐"),
    "sistema": _p("⭐"),
    "haz_clic": _p("👆"),
    "estas_en": _p("📍"),
    "ayuda_pausa": _p("🖱️"),
    "placeholder_nombre": _p("✍️", "✏️"),
    "datos_historicos": _p("📊"),
    "sin_registros": _p("📭"),
    "jugador": _p("👤"),
    "racha": _p("🔥"),
    "ranking_pos": _p("🏆"),
    "ayuda": _p("❓"),
    "banco_seguro": _p("🛡️"),
    "banco_beta": _p("🧪"),
}

_EMOJI_PASO: dict[str, EmojiPar] = {
    "Nombre": _p("👤"),
    "Tipo de partida": _p("🎯"),
    "Tamaño de partida": _p("🔢", "📝"),
    "Reglas": _p("⚙️"),
    "Filtros": _p("🔍"),
    "Dificultad inicial": _p("📈"),
    "Opciones del tipo": _p("⚙️"),
    "Histórico (opcional)": _p("📊"),
    "Categoría": _p("🏷️"),
    "Área": _p("🎯"),
    "Mensaje": _p("✍️", "✏️"),
    "Confirmación": _p("✅"),
}


def emoji_icono(clave: str, *, contexto: ContextoUi = "grafico") -> str:
    par = _EMOJI_ICONO.get(clave)
    if par is None:
        return ""
    return par.elegir(contexto)


def con_emoji(
    texto: str,
    emoji: str | EmojiPar,
    *,
    usar_emojis: bool = True,
    simetrico: bool = True,
    posicion: PosicionEmoji | None = None,
    contexto: ContextoUi = "grafico",
) -> str:
    """Formato con emoji; por defecto simétrico «emoji texto emoji»."""
    texto = texto.strip()
    simbolo = resolver_emoji(emoji, contexto=contexto)
    if not usar_emojis or not simbolo:
        return texto
    if posicion is None:
        posicion = "simetrico" if simetrico else "inicio"
    if posicion == "simetrico":
        return f"{simbolo} {texto} {simbolo}"
    if posicion == "inicio":
        return f"{simbolo} {texto}"
    return f"{texto} {simbolo}"


def etiqueta(
    texto: str,
    emoji: str | EmojiPar,
    *,
    usar_emojis: bool = True,
    simetrico: bool = True,
    posicion: PosicionEmoji | None = None,
    contexto: ContextoUi = "grafico",
) -> str:
    """Alias de ``con_emoji`` para botones y líneas de menú."""
    return con_emoji(
        texto,
        emoji,
        usar_emojis=usar_emojis,
        simetrico=simetrico,
        posicion=posicion,
        contexto=contexto,
    )


def titulo_pantalla(
    texto: str,
    *,
    usar_emojis: bool = True,
    simetrico: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    """Título de cabecera; usa emoji registrado o el texto tal cual."""
    base = texto.strip()
    par = _EMOJI_TITULO.get(base)
    if par:
        return con_emoji(
            base,
            par,
            usar_emojis=usar_emojis,
            simetrico=simetrico,
            contexto=contexto,
        )
    return base


def titulo_flexible(
    texto: str,
    *,
    usar_emojis: bool = True,
    simetrico: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    """Título exacto o por prefijo (p. ej. «FIN — Simulacro»)."""
    base = texto.strip()
    exacto = titulo_pantalla(
        base, usar_emojis=usar_emojis, simetrico=simetrico, contexto=contexto
    )
    if exacto != base:
        return exacto
    if usar_emojis:
        for prefijo, par in _EMOJI_TITULO_PREFIJO:
            if base.startswith(prefijo):
                return con_emoji(
                    base,
                    par,
                    usar_emojis=usar_emojis,
                    simetrico=simetrico,
                    contexto=contexto,
                )
    return base


def nombre_paso(
    nombre: str,
    *,
    usar_emojis: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    par = _EMOJI_PASO.get(nombre.strip())
    if par:
        return con_emoji(nombre.strip(), par, usar_emojis=usar_emojis, contexto=contexto)
    return nombre.strip()


def subtitulo(
    texto: str,
    emoji: str | EmojiPar = "📋",
    *,
    usar_emojis: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    """Subtítulo de paso o sección."""
    return con_emoji(
        texto.strip(), emoji, usar_emojis=usar_emojis, contexto=contexto
    )


def etiqueta_campo(
    clave: str,
    texto: str,
    *,
    usar_emojis: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    """Etiqueta de formulario con emoji coherente."""
    par = _EMOJI_ETIQUETA.get(clave)
    if par:
        return con_emoji(texto, par, usar_emojis=usar_emojis, contexto=contexto)
    return texto


def info_dataset(
    num_preguntas: int,
    num_materias: int,
    *,
    usar_emojis: bool = True,
    simetrico: bool = True,
    contexto: ContextoUi = "grafico",
) -> str:
    cuerpo = f"{num_preguntas} preguntas · {num_materias} materias"
    return con_emoji(
        cuerpo,
        _p("📚", "📕"),
        usar_emojis=usar_emojis,
        simetrico=simetrico,
        contexto=contexto,
    )


def mensaje_feedback(mensaje: str, *, usar_emojis: bool = True) -> str:
    for prefijo, par in _EMOJI_FEEDBACK_PREFIJO:
        if mensaje.startswith(prefijo):
            return con_emoji(mensaje, par, usar_emojis=usar_emojis)
    return mensaje


@dataclass(frozen=True)
class OpcionMenuPrincipal:
    id: str
    texto: str
    emoji: EmojiPar

    def etiqueta(
        self,
        *,
        usar_emojis: bool = True,
        contexto: ContextoUi = "grafico",
        simetrico: bool = True,
    ) -> str:
        return etiqueta(
            self.texto,
            self.emoji,
            usar_emojis=usar_emojis,
            simetrico=simetrico,
            contexto=contexto,
        )


OPCIONES_MENU_PRINCIPAL: tuple[OpcionMenuPrincipal, ...] = (
    OpcionMenuPrincipal("libre", "Modo libre", _p("🎮")),
    OpcionMenuPrincipal("historia", "Modo historia", _p("📖", "📕")),
    OpcionMenuPrincipal("feedback", "Modo feedback", _p("📣")),
    OpcionMenuPrincipal("salir", "Salir", _p("🚪")),
)

# Navegación: mismo emoji por dirección (atrás / adelante).
_EMOJI_ATRAS = _p("◀️")
_EMOJI_ADELANTE = _p("▶️")

BTN_VOLVER = ("Volver", _EMOJI_ATRAS)
BTN_VOLVER_MENU = ("Volver al menú", _EMOJI_ATRAS)
BTN_ATRAS = ("Atrás", _EMOJI_ATRAS)
BTN_SIGUIENTE = ("Siguiente", _EMOJI_ADELANTE)
BTN_EMPEZAR = ("Empezar partida", _EMOJI_ADELANTE)
BTN_CONTINUAR = ("Continuar", _EMOJI_ADELANTE)
BTN_CONTINUAR_PARTIDA = ("Continuar la partida", _EMOJI_ADELANTE)
BTN_ABANDONAR = ("Abandonar", _p("🛑"))
BTN_VER_RANKING = ("Ver ranking", _p("🏆"))
BTN_GUARDAR_INFORME = ("Guardar informe y volver", _p("💾"))
BTN_PANTALLA_TITULO = ("Pantalla de título", _p("🏠", "📋"))
BTN_SALIR_PROGRAMA = ("Salir del programa", _p("🚪"))


def posicion_emoji_navegacion(
    emoji: str | EmojiPar,
    *,
    contexto: ContextoUi = "grafico",
) -> PosicionEmoji:
    """Atrás → inicio; adelante → fin; resto → fin (un emoji tras el texto)."""
    simbolo = resolver_emoji(emoji, contexto=contexto)
    if simbolo == _EMOJI_ATRAS.elegir(contexto):
        return "inicio"
    if simbolo == _EMOJI_ADELANTE.elegir(contexto):
        return "fin"
    return "fin"
