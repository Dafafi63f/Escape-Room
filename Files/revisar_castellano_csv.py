#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correcciones puntuales de redacción en Data/Preguntas.csv (por Id).

No sustituye contenido de materia ya fijado por ``fix_final_materias.py``.
Evitar parches por Id en bloques revisados (31–130) salvo ortografía menor.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"

# Id -> campos a sustituir (solo los listados)
CORRECCIONES: dict[str, dict[str, str]] = {
    # Iniciació
    "31": {
        "Pregunta": "¿Qué es un condicional if?",
        "A": "Ejecuta código si la condición es verdadera",
    },
    "32": {
        "Pregunta": "¿Qué es un bucle while?",
        "A": "Itera mientras la condición sea verdadera",
        "B": "Itera un número fijo de veces",
        "C": "Itera solo sobre listas",
    },
    "33": {
        "Pregunta": "¿Qué es un bucle for?",
        "A": "Repite la ejecución sobre una secuencia o un rango",
    },
    "34": {
        "Pregunta": "¿Qué es un array (lista)?",
        "A": "Estructura que almacena elementos indexados",
    },
    "35": {
        "Pregunta": "¿Qué es el ámbito (scope) de una variable?",
        "A": "Zona del programa donde la variable es visible",
    },
    "39": {"Pregunta": "¿Cuál es len([1, 2, 3, 4, 5]) en Python?"},
    "40": {"Pregunta": "¿Qué hace el operador módulo (%)?"},
    # Tècniques (no parchear 42–50 Programari ni 91–100 POO; ver fix_final_materias.py)
    "133": {
        "D": "En cada paso elige la opción localmente óptima",
    },
    "134": {
        "A": "La solución óptima se compone de soluciones óptimas de subproblemas",
    },
    "135": {
        "A": "Almacenar resultados de subproblemas ya resueltos",
        "D": "Podar ramas del árbol de búsqueda",
    },
    "136": {"Pregunta": "¿Cuál es la complejidad media de quicksort?"},
    "137": {"Pregunta": "¿Cuál es la complejidad de la búsqueda binaria?"},
    "138": {
        "Pregunta": "¿Cuál es la complejidad temporal en el peor caso de merge sort sobre n elementos?",
    },
    "140": {
        "Pregunta": "¿Cuál es la complejidad de buscar en una lista no ordenada de n elementos?",
    },
    # Otros casos muy marcados
    "59": {
        "Pregunta": "¿Qué es un grafo euleriano?",
        "A": "Grafo con un circuito que recorre cada arista exactamente una vez",
    },
    "68": {
        "Pregunta": "Para x = r·cos(θ) e y = r·sin(θ), ¿cuál es el jacobiano |∂(x,y)/∂(r,θ)|?",
    },
    "69": {
        "Pregunta": "En coordenadas polares, ¿cuál es el jacobiano de la transformación (r, θ) → (x, y)?",
    },
    "174": {
        "Pregunta": "En un modelo de regresión con multicolinealidad severa, ¿qué problema afecta a los coeficientes estimados?",
    },
    "230": {
        "Pregunta": "En una EDP de segundo orden, si B²−4AC>0 en un punto, ¿cómo se clasifica la ecuación en ese punto?",
        "A": "Elíptica",
        "B": "Hiperbólica",
        "C": "Parabólica",
    },
    "255": {
        "Pregunta": "¿Qué ventaja ofrece NoSQL para datos no estructurados?",
    },
    "56": {"Pregunta": "¿Cuál es el grado de un vértice en el grafo completo K5?"},
    "116": {"Pregunta": "¿Cuál es el orden del método de Euler?"},
    "224": {"D": "Estático degenerado"},
    "283": {"C": "Solo rendimiento gráfico"},
}

# (patrón, sustitución) solo si la pregunta no empieza ya por ¿
_REGLAS_PREGUNTA: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^Integral de ", re.I), "¿Cuál es la integral de "),
    (re.compile(r"^Traza de ", re.I), "¿Cuál es la traza de "),
    (re.compile(r"^Módulo del ", re.I), "¿Cuál es el módulo del "),
    (re.compile(r"^Derivada de ", re.I), "¿Cuál es la derivada de "),
    (re.compile(r"^Gradiente de ", re.I), "¿Cuál es el gradiente de "),
    (re.compile(r"^Hessiano de ", re.I), "¿Cuál es el hessiano de "),
    (re.compile(r"^Determinante de ", re.I), "¿Cuál es el determinante de "),
    (re.compile(r"^Residuo de ", re.I), "¿Cuál es el residuo de "),
    (re.compile(r"^Conjugado de ", re.I), "¿Cuál es el conjugado de "),
    (re.compile(r"^Varianza de ", re.I), "¿Cuál es la varianza de "),
    (re.compile(r"^Solución de ", re.I), "¿Cuál es la solución de "),
    (re.compile(r"^Solución general de ", re.I), "¿Cuál es la solución general de "),
    (re.compile(r"^Producto escalar ", re.I), "¿Cuál es el producto escalar "),
    (re.compile(r"^Softmax de ", re.I), "¿Cuál es el softmax de "),
    (re.compile(r"^Sigmoid\(", re.I), "¿Cuánto vale sigmoid("),
    (re.compile(r"^Salida ReLU", re.I), "¿Cuál es la salida de ReLU"),
    (re.compile(r"^Pooling ", re.I), "¿Qué tamaño tiene la salida del pooling "),
    (re.compile(r"^2\+2 en ", re.I), "¿Cuánto es 2+2 en "),
    (re.compile(r"^Fibonacci F\(", re.I), "¿Cuánto vale Fibonacci F("),
    (re.compile(r"^len\(", re.I), "¿Cuál es len("),
    (re.compile(r"^Grado de vértice en ", re.I), "¿Cuál es el grado de un vértice en el "),
    (re.compile(r"^Orden del método de ", re.I), "¿Cuál es el orden del método de "),
    (re.compile(r"^Poisson ", re.I), "Si X~Poisson, "),
    (re.compile(r"^pH=", re.I), "Si pH = "),
]

# Ortografía: tildes y erratas (orden: cadenas largas primero)
_SUSTITUCIONES: list[tuple[str, str]] = [
    ("en  en", "en "),
    ("método  de", "método de"),
    ("Estatico", "Estático"),
    ("Eliptica", "Elíptica"),
    ("rendimiento grafico", "rendimiento gráfico"),
    ("  ", " "),
]


def _aplicar_sustituciones(texto: str) -> str:
    t = texto or ""
    for viejo, nuevo in _SUSTITUCIONES:
        t = t.replace(viejo, nuevo)
    return t.strip() if t != (texto or "") else t


def _pulir_pregunta(texto: str) -> str:
    t = (texto or "").strip()
    if not t or t.startswith("¿"):
        return t
    for pat, repl in _REGLAS_PREGUNTA:
        if pat.search(t):
            return pat.sub(repl, t, count=1)
    return t


def main() -> None:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
        fieldnames = rows[0].keys() if rows else []

    cambios = 0
    for r in rows:
        cid = str(r["Id"]).strip()
        if cid in CORRECCIONES:
            for k, v in CORRECCIONES[cid].items():
                if r.get(k) != v:
                    r[k] = v
                    cambios += 1
        for col in ("Pregunta", "A", "B", "C", "D"):
            nt = _aplicar_sustituciones(r.get(col, ""))
            if nt != r.get(col):
                r[col] = nt
                cambios += 1
        np = _pulir_pregunta(r.get("Pregunta", ""))
        if np != r.get("Pregunta"):
            r["Pregunta"] = np
            cambios += 1

    with PATH_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"OK: {cambios} campos actualizados en {PATH_CSV.name}")

    sync = BASE / "Files" / "sync_plantillas_materias.py"
    if sync.exists():
        subprocess.run([sys.executable, str(sync)], cwd=BASE, check=True)


if __name__ == "__main__":
    main()
