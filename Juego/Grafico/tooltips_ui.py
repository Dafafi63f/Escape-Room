#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Textos de ayuda (hover) para botones del modo gráfico."""

from __future__ import annotations

from Comun.modelos import BancoPreguntas, ETIQUETA_BANCO

# Filas con ◀ valor ▶ en libre paso 1 sin tooltip en la caja central (solo números u obvias).
_OPCIONES_CICLO_SIN_TOOLTIP = frozenset({"vidas", "tiempo_pregunta", "tiempo_total"})

TOOLTIP_TIEMPO_MODO: dict[str, str] = {
    "ninguno": "Sin cronómetro en la partida.",
    "pregunta": "Cada pregunta tiene su propio límite en segundos.",
    "total": "Un único temporizador para toda la partida.",
}

TOOLTIP_SISTEMA: dict[str, str] = {
    "arcade": "Puntos por acierto; bonificaciones por racha y tiempo.",
    "nota": "Resultado en escala 0-10 según aciertos y penalizaciones.",
    "porcentaje": "Porcentaje de aciertos sobre preguntas respondidas.",
    "ninguno": "Sin puntuación numérica al final.",
}

TOOLTIP_N_PREGUNTAS_INFINITO = (
    "Partida sin tope: continúa hasta que termines, pierdas las vidas o abandones."
)

TOOLTIP_PAUSA = "Menú de pausa (Esc): continuar, ir al título o salir del juego."
TOOLTIP_BARRA_DURANTE_PARTIDA = (
    "No disponible durante la partida. Usa pausa (Esc) y luego D, H, F u O."
)
TOOLTIP_BARRA_DURANTE_PAUSA = (
    "No disponible con el menú de pausa abierto. Usa Continuar, F (feedback) o Esc (salir)."
)
TOOLTIP_BARRA_DURANTE_OPCIONES = (
    "No disponible con opciones abiertas. Usa Esc (pausa) u O para cerrar."
)
TOOLTIP_BARRA_BIENVENIDA = "Disponible después de introducir tu nombre y continuar."
TOOLTIP_DIARIOS = (
    "Examen del día y examen aleatorio (D). "
    "Semilla diaria o nueva cada vez."
)
TOOLTIP_OPCIONES = (
    "Opciones globales (O): nombre por defecto, ayudas al ratón, emojis y borrado de datos locales."
)

TOOLTIP_PAUSA_CONTINUAR = "Cierra el menú de pausa y vuelve a la pantalla actual."
TOOLTIP_PAUSA_CONTINUAR_PARTIDA = "Sigue jugando la partida en curso."
TOOLTIP_PAUSA_TITULO = "Abandona el flujo actual y vuelve al menú principal."
TOOLTIP_PAUSA_SALIR = "Cierra el programa por completo."

TOOLTIP_ATRAS = "Vuelve al paso o pantalla anterior sin perder lo configurado."
TOOLTIP_SIGUIENTE = "Avanza al siguiente paso de configuración."
TOOLTIP_EMPEZAR = "Inicia la partida con la configuración actual."
TOOLTIP_CONTINUAR = (
    "Continúa con el preset seleccionado (configuración extra si el reto lo permite)."
)

TOOLTIP_FEEDBACK = (
    "Formulario rápido de avisos al creador (F)."
)

TOOLTIP_MENU_PRINCIPAL: dict[str, str] = {
    "libre": (
        "Partida personalizada: eliges banco, vidas, tiempo, filtros y número de preguntas."
    ),
    "diarios": (
        "Examen del día (misma semilla hoy) y examen aleatorio (cambia cada vez)."
    ),
    "historia": (
        "Presets guiados: simulacros de examen, repasos y retos con datos históricos."
    ),
    "especiales": (
        "Modos aparte del carrusel historia: escape room y resistencia."
    ),
    "feedback": (
        "Envía avisos al creador (bugs, sugerencias) o consulta los contactos alternativos."
    ),
    "salir": "Cierra el juego.",
}

TOOLTIP_MODOS_ESPECIALES: dict[str, str] = {
    "escape_room": (
        "30 salas, 3 puertas por sala. Descanso, tienda (puntos arcade) y botín. "
        "Partida distinta cada vez (semilla aleatoria). Objetos en la banda inferior. "
        "Fallar cuesta 1 vida pero avanzas."
    ),
    "resistencia": (
        "Banco completo, 3 vidas. Escalada, rachas y eventos aleatorios. "
        "Sin tope de preguntas."
    ),
}

TOOLTIP_DIFICULTAD_PROGRESIVA = (
    "Las preguntas empiezan en el nivel más bajo marcado y suben de complejidad "
    "a medida que avanzas en la partida."
)

TOOLTIP_FILTRO_PRINCIPAL: dict[str, str] = {
    "todas": "Usa todo el banco elegido, sin restringir por temática, semestre ni tipo.",
    "tematica": "Limita las preguntas a una o más temáticas del grado.",
    "semestre": "Limita las preguntas a uno o más semestres del plan de estudios.",
    "tipo": "Limita por tipo de pregunta (test, desarrollo, etc.).",
}

TOOLTIP_ABANDONAR_LIBRE = (
    "Termina la partida. Si ya respondiste alguna pregunta, verás el resumen "
    "y podrás guardar un informe .txt con lo jugado."
)

TOOLTIP_ABANDONAR_HISTORIA = (
    "Termina el examen o reto. Si ya respondiste preguntas, se genera un informe "
    "con la corrección de lo realizado hasta ahora."
)

TOOLTIP_ABANDONAR_RESISTENCIA = (
    "Termina la partida. Si ya respondiste preguntas, verás el resumen "
    "y podrás guardar un informe .txt con lo jugado."
)
TOOLTIP_APUESTA_SI = "Aceptar la apuesta arriesgada."
TOOLTIP_APUESTA_NO = "Rechazar la apuesta y jugar con las reglas normales."
TOOLTIP_EVENTO_SI_NO_SI = "Aceptar (gastas los puntos indicados, si los hay)."
TOOLTIP_EVENTO_SI_NO_SI_RIESGO = (
    "Aceptar: el riesgo o la recompensa aplican a esta pregunta."
)
TOOLTIP_EVENTO_SI_NO_NO = "Rechazar: no pasa nada y sigues a la pregunta."

def tooltip_guardar_informe() -> str:
    from Comun.rutas import etiqueta_dir_datos_jugador

    return (
        f"Guarda un archivo .txt en {etiqueta_dir_datos_jugador()}/ con tus respuestas, "
        "aciertos y corrección pregunta a pregunta."
    )

TOOLTIP_RANKING = (
    "Estadísticas locales, controles y contacto (H). "
    "Borrado local desde Opciones (O)."
)
TOOLTIP_VER_RANKING = TOOLTIP_RANKING

# Valores de opciones «eleccion» en presets historia (clave op → valor → texto).
_TOOLTIP_ELECCION_HISTORIA: dict[str, dict[str, str]] = {
    "estrategia_practica": {
        "debilidades": "Prioriza materias o conceptos con peor acierto en tu práctica.",
        "fortalezas": "Prioriza materias o conceptos con mejor acierto en tu práctica.",
        "equilibrado": "Ponderación suave según tus aciertos y fallos en este banco.",
        "sin_historico": "Reparto uniforme sin ponderar por tu práctica.",
    },
    "origen_semilla": {
        "diario": "Mismo contenido que el examen del día de hoy; el orden varía en cada partida.",
        "aleatorio": "Contenido nuevo en cada partida; orden fijo por dificultad (F→M→D).",
        "semilla": "Contenido reproducible con la semilla numérica indicada.",
    },
    "enfoque": {
        "mixto": "Mezcla preguntas de teoría y de cálculo.",
        "teoria": "Solo preguntas de tipo teoría.",
        "calculo": "Solo preguntas de tipo cálculo.",
    },
}

_TOOLTIP_OPCION_HISTORIA_ID: dict[str, str] = {
    "curso": "Limita el ámbito del examen a un curso del grado (vacío = todo el grado).",
    "semestre": "Acota a un semestre concreto. Vacío: cualquier semestre del grado. Con curso: todo el curso o un semestre (5 asignaturas).",
    "periodo": "Semestre académico concreto del plan (p. ej. Semestre 3-2). Vacío: filtra por curso y semestre por separado.",
    "grupo": "Elige un bloque G1–G10: entran todas sus asignaturas (sin mezclar con curso ni semestre).",
    "materia": "Concentra el reto en una sola asignatura.",
    "estrategia_practica": "Ponderación según tus aciertos y fallos en este banco.",
    "n_materias": "Cuántas materias entran en el examen (mínimo 2 para alcanzar 5 preguntas).",
    "n_preguntas": "Cuántas preguntas incluir (mínimo 5; máximo según plantillas de la materia y el tipo de preguntas).",
    "enfoque": "Filtra si entran preguntas de teoría, de cálculo o ambas.",
    "origen_semilla": "Diario (semilla de hoy), aleatorio o semilla numérica fija.",
    "semilla": "Entero que fija el contenido del examen (por defecto, la semilla del día).",
    "tiempo_total_min": "Minutos para todo el examen; 0 significa sin límite de tiempo.",
}


TOOLTIP_MENU_PRINCIPAL_MINIMO: dict[str, str] = {
    "libre": (
        "Partida personalizada con el CSV cargado: vidas, tiempo y número de preguntas."
    ),
    "historia": (
        "No disponible en el paquete mínimo. Usa Examen fijo en la barra superior."
    ),
    "especiales": (
        "Resistencia y escape room (no disponible en el paquete mínimo)."
    ),
    "diarios": (
        "Examen fijo: del día, aleatorio o semilla numérica."
    ),
}

def tooltip_barra_diarios(perfil=None) -> str:
    if perfil is not None and perfil.examen_fijo_barra_completo:
        return (
            "Examen fijo: del día (semilla de hoy), aleatorio o semilla numérica."
        )
    return TOOLTIP_DIARIOS


def tooltip_menu_principal(opcion_id: str, perfil=None) -> str | None:
    if perfil is not None and perfil.modo_minimo:
        if opcion_id in TOOLTIP_MENU_PRINCIPAL_MINIMO:
            return TOOLTIP_MENU_PRINCIPAL_MINIMO[opcion_id]
    return TOOLTIP_MENU_PRINCIPAL.get(opcion_id)


def tooltip_modo_especial(preset_id: str, perfil=None) -> str | None:
    if perfil is not None and not perfil.modo_especial_disponible(preset_id):
        return perfil.motivo_modo_especial_no_disponible(preset_id)
    if perfil is not None and perfil.modo_minimo and preset_id == "resistencia":
        return (
            "Partida infinita con eventos aleatorios. Sin escalada por dificultad "
            "ni dataset UAB (Completo)."
        )
    return TOOLTIP_MODOS_ESPECIALES.get(preset_id)


def tooltip_filtro_principal(codigo: str) -> str | None:
    return TOOLTIP_FILTRO_PRINCIPAL.get(codigo)


def tooltips_menu_pausa(*, en_partida: bool) -> tuple[str, str, str]:
    """Textos para Continuar / Pantalla título / Salir."""
    return (
        TOOLTIP_PAUSA_CONTINUAR_PARTIDA if en_partida else TOOLTIP_PAUSA_CONTINUAR,
        TOOLTIP_PAUSA_TITULO,
        TOOLTIP_PAUSA_SALIR,
    )


def _tooltip_historia_eleccion(
    op_id: str,
    clave: str,
    etiqueta_opcion: str,
    *,
    perfil=None,
) -> str | None:
    if op_id in {"estrategia_practica", "estrategia_materias"} and perfil is not None:
        from Comun.config_historia import tooltip_valor_estrategia_practica

        tip = tooltip_valor_estrategia_practica(clave)
        if tip:
            return tip
    por_op = _TOOLTIP_ELECCION_HISTORIA.get(op_id, {})
    if clave in por_op:
        return por_op[clave]
    return etiqueta_opcion or None


def _tooltip_historia_entero(
    op_id: str,
    clave: str,
    etiqueta_opcion: str,
) -> str | None:
    base = _TOOLTIP_OPCION_HISTORIA_ID.get(op_id)
    if op_id == "tiempo_total_min" and clave in ("", "0"):
        return "Sin límite de tiempo para completar el examen."
    if base:
        return base
    return etiqueta_opcion or None


def tooltip_opcion_ciclo_historia(
    op_id: str,
    tipo: str,
    clave: str,
    *,
    etiqueta_opcion: str = "",
    curso_actual: str | None = None,
    perfil=None,
) -> str | None:
    """Ayuda en la caja central ◀ valor ▶ del configurador de preset historia."""
    from Comun.config_historia import (
        descripcion_campo_estrategia_practica,
        etiqueta_periodo_academico,
        etiqueta_periodo_desde_clave,
    )

    if op_id in {"estrategia_practica", "estrategia_materias"} and tipo == "eleccion":
        if not clave:
            return descripcion_campo_estrategia_practica()

    if tipo == "eleccion":
        return _tooltip_historia_eleccion(
            op_id, clave, etiqueta_opcion, perfil=perfil
        )
    if tipo == "curso":
        if not clave:
            return "Sin filtro de curso: el preset puede abarcar todo el grado."
        return f"Limita el reto al curso {clave}."
    if tipo == "semestre":
        if not clave:
            return "Sin filtro de semestre: se usa el curso completo elegido."
        if curso_actual:
            return f"Acota al {etiqueta_periodo_academico(str(curso_actual), clave).lower()}."
        return f"Acota al semestre {clave}."
    if tipo == "periodo" and clave:
        return f"Limita al {etiqueta_periodo_desde_clave(clave).lower()}."
    if tipo in ("curso", "semestre", "periodo") and not clave:
        return _TOOLTIP_OPCION_HISTORIA_ID.get(tipo)
    if tipo == "grupo" and clave:
        return _TOOLTIP_OPCION_HISTORIA_ID.get("grupo")
    if tipo == "materia" and clave:
        return f"Preguntas centradas en {clave}."
    if tipo == "entero":
        return _tooltip_historia_entero(op_id, clave, etiqueta_opcion)
    return _TOOLTIP_OPCION_HISTORIA_ID.get(op_id) or (etiqueta_opcion or None)


def tooltip_opcion_ciclo_libre(
    op_id: str,
    clave: str,
    *,
    perfil=None,
) -> str | None:
    """Ayuda en la caja central ◀ valor ▶ del paso 1 libre; None si es autoexplicativo."""
    del perfil
    if op_id in _OPCIONES_CICLO_SIN_TOOLTIP:
        return None
    if op_id == "banco":
        try:
            return ETIQUETA_BANCO[BancoPreguntas(clave)][1]
        except (ValueError, KeyError):
            return None
    if op_id == "n_preguntas":
        if clave == "infinito":
            return TOOLTIP_N_PREGUNTAS_INFINITO
        return None
    if op_id == "tiempo_modo":
        return TOOLTIP_TIEMPO_MODO.get(clave)
    if op_id == "sistema":
        return TOOLTIP_SISTEMA.get(clave)
    if op_id == "estrategia_practica":
        from Comun.config_historia import tooltip_valor_estrategia_practica

        return tooltip_valor_estrategia_practica(clave)
    return None
