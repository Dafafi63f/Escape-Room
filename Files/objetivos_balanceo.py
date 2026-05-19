# -*- coding: utf-8 -*-
"""
Objetivos compartidos del pipeline de balanceo de `Data/Preguntas.csv`.

El orden de filas canónico del CSV (materias según listado, ladder TF…TM…TD y
CF…CM…CD, reparto global de dificultad y ciclo de `Correcta`) lo aplica
`Files/balance.py reordenar`, invocado al cerrar `balance.py agresivo` o `balance.py conservador`.
"""
from __future__ import annotations

from utils_orden_temas import cargar_orden_temas

# Total de filas que deben quedar tras el balanceo completo.
TARGET_TOTAL_PREGUNTAS = 400

# El banco de plantillas debe ser más amplio que el CSV publicado (reserva para
# sustituciones sin repetir enunciados del dataset activo).
MIN_PLANTILLAS_POR_MATERIA_FACTOR = 2


def num_materias_listado() -> int:
    temas, _ = cargar_orden_temas()
    return len(temas)


def preguntas_por_materia() -> int:
    """Preguntas por cada materia del listado (TARGET_TOTAL / N materias)."""
    n = num_materias_listado()
    if n == 0:
        return TARGET_TOTAL_PREGUNTAS
    return TARGET_TOTAL_PREGUNTAS // n


def plantillas_minimas_por_materia() -> int:
    """Mínimo de entradas en plantillas.json por materia ( > preguntas en el CSV )."""
    return preguntas_por_materia() * MIN_PLANTILLAS_POR_MATERIA_FACTOR


def preguntas_por_tipo_global() -> int:
    """Teoria y Calculo a la mitad del total."""
    return TARGET_TOTAL_PREGUNTAS // 2


def objetivos_dificultad_por_totales(n: int) -> dict[str, int]:
    """Reparto equilibrado Facil/Media/Dificil que suma n."""
    if n <= 0:
        return {"Facil": 0, "Media": 0, "Dificil": 0}
    b = n // 3
    r = n % 3
    facil = b + (1 if r >= 1 else 0)
    media = b + (1 if r >= 2 else 0)
    dificil = n - facil - media
    return {"Facil": facil, "Media": media, "Dificil": dificil}


def objetivos_dificultad_globales() -> dict[str, int]:
    """Objetivos de dificultad para el tamaño canónico del dataset."""
    return objetivos_dificultad_por_totales(TARGET_TOTAL_PREGUNTAS)


def objetivos_correcta_por_letra(n_total: int | None = None) -> dict[str, int]:
    """Cuenta objetivo por letra A..D (reparto equitativo del resto)."""
    n = n_total if n_total is not None else TARGET_TOTAL_PREGUNTAS
    base = n // 4
    rem = n % 4
    letras = ["A", "B", "C", "D"]
    return {letras[i]: base + (1 if i < rem else 0) for i in range(4)}


def lista_objetivos_correcta(n_total: int | None = None) -> list[str]:
    """Lista de longitud n_total para permutar Correcta (balancear_correctas)."""
    n = n_total if n_total is not None else TARGET_TOTAL_PREGUNTAS
    obj = objetivos_correcta_por_letra(n)
    out: list[str] = []
    for letra in ["A", "B", "C", "D"]:
        out.extend([letra] * obj[letra])
    return out
