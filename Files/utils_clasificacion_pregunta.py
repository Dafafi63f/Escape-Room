# -*- coding: utf-8 -*-
"""
Clasificación de una pregunta a partir solo de su contenido (enunciado + opciones + correcta).

Dada una pregunta «correcta» (texto coherente), infiere la mejor combinación
Materia + Tipo + Dificultad. Sirve para revisar metadatos sin reetiquetar a ciegas.

Uso:
    from utils_clasificacion_pregunta import clasificar_pregunta, comparar_con_asignacion

    cl = clasificar_pregunta("¿Qué es un espacio vectorial?", "...", "...", "...", "...", "A")
    cmp = comparar_con_asignacion(fila_csv)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from utils_puntuacion_materia import (
    MATERIAS,
    mejor_materia_por_texto,
    puntuar_texto_completo,
    score_fila_para_materia,
)

TIPOS_VALIDOS = ("Teoria", "Calculo")
DIFICULTADES_VALIDAS = ("Facil", "Media", "Dificil")


@dataclass
class ClasificacionPregunta:
    """Mejor combinación inferida solo del texto."""

    pregunta: str
    materia: str | None
    tipo: str
    dificultad: str
    correcta: str
    scores_materia: dict[str, float] = field(default_factory=dict)
    scores_tipo: dict[str, float] = field(default_factory=dict)
    scores_dificultad: dict[str, float] = field(default_factory=dict)

    def top_materias(self, n: int = 4) -> list[tuple[str, float]]:
        return sorted(self.scores_materia.items(), key=lambda x: (-x[1], x[0]))[:n]

    def resumen(self) -> str:
        return (
            f"Materia={self.materia!r} | Tipo={self.tipo} | Dificultad={self.dificultad}"
        )


@dataclass
class ComparacionAsignacion:
    """Metadatos del CSV frente a la clasificación inferida."""

    asignado: dict[str, str]
    inferido: ClasificacionPregunta
    campos_incoherentes: list[str] = field(default_factory=list)
    detalle: dict[str, Any] = field(default_factory=dict)

    @property
    def debe_sustituir(self) -> bool:
        return bool(self.campos_incoherentes)


def puntuar_como_calculo(
    pregunta: str,
    a: str = "",
    b: str = "",
    c: str = "",
    d: str = "",
) -> float:
    """Mayor puntuación ⇒ más parecida a Cálculo."""
    texto = f"{pregunta} {a} {b} {c} {d}"
    score = 0.0
    if re.search(r"\d+", texto):
        score += 2.0
    if re.search(r"[=+\-*/^∫∑∏√πλΣ]", texto):
        score += 2.0
    if re.search(
        r"\b(media|varianza|integral|derivada|limite|límite|determinante|rango|"
        r"matriz|vector|probabilidad|esperanza|gradiente|jacobiano)\b",
        texto.lower(),
    ):
        score += 2.0
    if re.search(
        r"\b(cuánto|cuántos|cuál es el valor|valor de|calcular|resuelve|hallar)\b",
        texto.lower(),
    ):
        score += 1.0
    if re.search(r"\b(suma|resta|producto|cociente)\b.*\d", texto.lower()):
        score += 0.5
    return score


def puntuar_tipo(
    pregunta: str,
    a: str = "",
    b: str = "",
    c: str = "",
    d: str = "",
    correcta: str = "",
) -> dict[str, float]:
    """Puntuación por tipo (Teoria / Calculo)."""
    _ = correcta  # reservado (p. ej. longitud de la opción correcta)
    p_low = (pregunta or "").lower()
    teoria = 0.0
    if re.search(
        r"¿qué es |¿qué son |¿cuál es la defin|define |definici|concepto de |"
        r"¿en qué consiste",
        p_low,
    ):
        teoria += 3.0
    if re.search(r"\b(teorema|propiedad|axioma|demostración|lema|corolario)\b", p_low):
        teoria += 2.0
    if not re.search(r"\d", pregunta or ""):
        teoria += 1.0
    if re.search(r"¿verdadero|¿falso|verdadera o falsa", p_low):
        teoria += 1.5
    calculo = puntuar_como_calculo(pregunta, a, b, c, d)
    return {"Teoria": teoria, "Calculo": calculo}


def puntuar_dificultad(
    pregunta: str,
    a: str = "",
    b: str = "",
    c: str = "",
    d: str = "",
    correcta: str = "",
) -> dict[str, float]:
    """Puntuación por dificultad (Facil / Media / Dificil)."""
    texto = f"{pregunta} {a} {b} {c} {d}"
    p_low = (pregunta or "").lower()
    facil = 0.0
    media = 1.0
    dificil = 0.0

    if re.search(r"¿qué es |¿qué son |definici|concepto de ", p_low):
        facil += 3.0
    if re.search(r"\b(básic|elemental|sencill|introducci)\b", p_low):
        facil += 2.0
    plen = len(pregunta or "")
    if plen < 45:
        facil += 1.5
    elif plen > 100:
        dificil += 1.5
    elif plen > 70:
        media += 0.5

    nums = len(re.findall(r"\d+", texto))
    syms = len(re.findall(r"[=+\-*/^∫∑∏√πλΣ]", texto))
    if nums >= 2:
        dificil += 1.0
        media += 0.5
    if syms >= 2:
        dificil += 2.0
    if re.search(r"\b(demuestra|demostr|probar que|teorema de)\b", p_low):
        dificil += 2.5
    if re.search(
        r"\b(cuánto|cuántos|calcular|integral|derivada|determinante|autovalor)\b",
        p_low,
    ):
        media += 1.5
        if nums >= 1:
            dificil += 0.5

    opciones = [x for x in (a, b, c, d) if x]
    if opciones:
        lens = [len(x) for x in opciones]
        if max(lens) - min(lens) > 45:
            dificil += 0.5
        if all(len(x) < 25 for x in opciones):
            facil += 0.5

    if correcta and correcta in "ABCD":
        opt = {"A": a, "B": b, "C": c, "D": d}.get(correcta, "")
        if opt and len(opt) > 60:
            dificil += 0.5

    return {"Facil": facil, "Media": media, "Dificil": dificil}


def _mejor_clave(scores: dict[str, float], orden: tuple[str, ...]) -> str:
    return max(orden, key=lambda k: (scores.get(k, 0.0), -orden.index(k)))


def clasificar_pregunta(
    pregunta: str,
    a: str = "",
    b: str = "",
    c: str = "",
    d: str = "",
    correcta: str = "A",
) -> ClasificacionPregunta:
    """
    Infiere Materia, Tipo y Dificultad óptimos para el texto dado.
    No usa metadatos previos (solo contenido + letra correcta).
    """
    correcta = (correcta or "A").strip().upper()[:1] or "A"
    mid, scores_id = mejor_materia_por_texto(pregunta, a, b, c, d)
    scores_materia = {MATERIAS[i]: s for i, s in scores_id.items()}
    materia = MATERIAS.get(mid) if mid else None

    st = puntuar_tipo(pregunta, a, b, c, d, correcta)
    sd = puntuar_dificultad(pregunta, a, b, c, d, correcta)

    return ClasificacionPregunta(
        pregunta=pregunta,
        materia=materia,
        tipo=_mejor_clave(st, TIPOS_VALIDOS),
        dificultad=_mejor_clave(sd, DIFICULTADES_VALIDAS),
        correcta=correcta,
        scores_materia=scores_materia,
        scores_tipo=st,
        scores_dificultad=sd,
    )


def clasificar_fila(fila: dict) -> ClasificacionPregunta:
    """Clasifica una fila del dataset o un dict compatible con plantillas."""
    return clasificar_pregunta(
        fila.get("Pregunta") or fila.get("pregunta", ""),
        fila.get("A", ""),
        fila.get("B", ""),
        fila.get("C", ""),
        fila.get("D", ""),
        fila.get("Correcta", "A"),
    )


def _margen(scores: dict[str, float], mejor: str, segundo: str | None = None) -> float:
    if not scores or mejor not in scores:
        return 0.0
    otros = [v for k, v in scores.items() if k != mejor]
    if not otros:
        return scores[mejor]
    segundo_val = max(otros) if segundo is None else scores.get(segundo, max(otros))
    return scores[mejor] - segundo_val


def comparar_con_asignacion(
    fila: dict,
    *,
    min_score_materia: float = 2.0,
    margen_materia: float = 2.0,
    margen_tipo: float = 1.5,
    margen_dificultad: float = 1.0,
    estricto: bool = False,
) -> ComparacionAsignacion:
    """
    Compara metadatos asignados en `fila` con la clasificación inferida del texto.
    `campos_incoherentes` lista qué columnas conviene corregir (sustitución, no reetiqueta).
    """
    inferido = clasificar_fila(fila)
    materia_asig = (fila.get("Materia") or "").strip()
    tipo_asig = (fila.get("Tipo") or "").strip()
    diff_asig = (fila.get("Dificultad") or "").strip()

    asignado = {
        "Materia": materia_asig,
        "Tipo": tipo_asig,
        "Dificultad": diff_asig,
        "Correcta": (fila.get("Correcta") or "A").strip(),
    }

    incoherentes: list[str] = []
    sc_actual = score_fila_para_materia(fila, materia_asig) if materia_asig else 0.0
    sc_mejor = (
        inferido.scores_materia.get(inferido.materia or "", 0.0)
        if inferido.materia
        else 0.0
    )

    if inferido.materia and materia_asig and inferido.materia != materia_asig:
        if sc_mejor >= min_score_materia and (
            sc_actual == 0 or sc_mejor >= sc_actual + margen_materia
        ):
            incoherentes.append("Materia")

    if tipo_asig in TIPOS_VALIDOS and inferido.tipo != tipo_asig:
        if _margen(inferido.scores_tipo, inferido.tipo) >= margen_tipo:
            incoherentes.append("Tipo")

    if diff_asig in DIFICULTADES_VALIDAS and inferido.dificultad != diff_asig:
        margen_d = _margen(inferido.scores_dificultad, inferido.dificultad)
        if estricto:
            if margen_d >= margen_dificultad:
                incoherentes.append("Dificultad")
        else:
            # Informe: solo contrastes fuertes (Facil vs Dificil); la escalera del bloque puede diferir.
            orden = {"Facil": 0, "Media": 1, "Dificil": 2}
            salto = abs(orden.get(diff_asig, 1) - orden.get(inferido.dificultad, 1))
            if salto >= 2 and margen_d >= margen_dificultad + 1.0:
                incoherentes.append("Dificultad")

    return ComparacionAsignacion(
        asignado=asignado,
        inferido=inferido,
        campos_incoherentes=incoherentes,
        detalle={
            "score_materia_actual": sc_actual,
            "score_materia_inferida": sc_mejor,
            "top_materias": inferido.top_materias(4),
        },
    )


def metadatos_optimos(fila: dict) -> dict[str, str]:
    """Mejor tripleta Materia/Tipo/Dificultad inferida del contenido."""
    inf = clasificar_fila(fila)
    return {
        "Materia": inf.materia or (fila.get("Materia") or "").strip(),
        "Tipo": inf.tipo,
        "Dificultad": inf.dificultad,
    }


def prioridad_eliminacion(fila: dict, materia: str | None = None) -> float:
    """
    Menor valor ⇒ peor encaje en `materia` (candidata a borrar en balanceo).
    Combina score de materia y penalización por tipo/dificultad incoherentes.
    """
    mat = materia or fila.get("Materia", "")
    base = score_fila_para_materia(fila, mat)
    cmp = comparar_con_asignacion(fila)
    penal = 0.0
    if "Tipo" in cmp.campos_incoherentes:
        penal += 2.0
    if "Dificultad" in cmp.campos_incoherentes:
        penal += 1.5
    if "Materia" in cmp.campos_incoherentes:
        penal += 3.0
    return base - penal
