#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza Data/criterios_clasificacion_materia.csv con aliases oficiales
de guias docentes UAB (denominaciones en espanol).

Objetivo:
- Reforzar la identificacion de materia anadiendo nombres oficiales de guia
  como keywords adicionales (sin borrar las existentes).
- Recalcular N_palabras_clave.

Uso:
  python Files/actualizar_criterios_desde_guias.py --dry-run
  python Files/actualizar_criterios_desde_guias.py --inplace
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils_puntuacion_materia import normalizar

PATH_CRIT = BASE / "Data" / "criterios_clasificacion_materia.csv"

# Materia (CSV interno) -> alias oficial en guias UAB (es)
ALIASES_GUIAS_ES: dict[str, list[str]] = {
    "Àlgebra Lineal": ["álgebra lineal"],
    "Càlcul en una Variable": ["cálculo en una variable"],
    "Fonaments de Computadors": ["fundamentos de computadores"],
    "Iniciació a la Programació": ["iniciación a la programación"],
    "Programari de Sistema": ["software de sistema"],
    "Algorítmia i Combinatòria en Grafs. Mètodes Heurístics": [
        "algoritmia y combinatoria en grafos",
        "métodos heurísticos",
    ],
    "Càlcul en Diverses Variables": ["cálculo en varias variables"],
    "Càlcul Numèric": ["cálculo numérico"],
    "Probabilitat": ["probabilidad"],
    "Programació Orientada als Objectes": ["programación orientada a los objetos"],
    "Bases de Dades Relacionals": ["bases de datos relacionales"],
    "Equacions Diferencials Ordinàries": ["ecuaciones diferenciales ordinarias"],
    "Modelització i Inferència": ["modelización e inferencia"],
    "Tècniques de Disseny d'Algoritmes": ["técnicas de diseño de algoritmos"],
    "Visualització 3D": ["visualización 3d"],
    "Anàlisi Complexa i de Fourier": ["análisis complejo y de fourier"],
    "Anàlisi de Dades Complexes": ["análisis de datos complejos"],
    "Intel·ligència Artificial": ["inteligencia artificial"],
    "Mètodes Numèrics i Probabilístics": ["métodos numéricos y probabilísticos"],
    "Optimització": ["optimización"],
    "Aprenentatge Computacional": ["aprendizaje computacional"],
    "Computació i Simulació d'Altes Prestacions": ["computación de altas prestaciones"],
    "Equacions en Derivades Parcials": ["ecuaciones en derivadas parciales"],
    "Física, Abstracció i Computació": ["física, abstracción y computación"],
    "Teoria de la Informació": ["teoría de la información"],
    "Bases de Dades No Relacionals": ["bases de datos no relacionales"],
    "Informació Quàntica": ["información cuántica"],
    "Modelització i Simulació": ["modelización y simulación"],
    "Sistemes Distribuïts i el Núvol": ["sistemas distribuidos y la nube"],
    "Xarxes Neuronals i Aprenentatge Profund": [
        "redes neuronales y aprendizaje profundo",
    ],
    "Anàlisi de Dades Financeres": ["análisis de datos financieros"],
    "Anàlisi de Dades Temporals": ["análisis de datos temporales"],
    "Anàlisi Topològica de Dades": ["análisis topológico de datos"],
    "Internet de les Coses": ["internet de las cosas"],
    "Mètodes d Anàlisi en Ciències de la Salut": [
        "métodos de análisis en ciencias de la salud",
    ],
    "Anàlisi de Dades en Astrofísica": ["análisis de datos en astrofísica"],
    "Bioinformàtica": ["bioinformática"],
    "Informació i Seguretat": ["información y seguridad"],
    "Teoria de Jocs": ["teoría de juegos"],
    "Visió per Computador": ["visión por computador"],
}


def _parse_keywords(celda: str) -> list[str]:
    return [p.strip() for p in (celda or "").split("|") if p.strip()]


def _join_keywords(kws: list[str]) -> str:
    return " | ".join(kws)


def run(inplace: bool, dry_run: bool) -> int:
    with PATH_CRIT.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    total_add = 0
    detalle: list[str] = []
    by_materia = {r["Materia"]: r for r in rows}

    for materia, aliases in ALIASES_GUIAS_ES.items():
        row = by_materia.get(materia)
        if not row:
            continue
        kws = _parse_keywords(row.get("Palabras_clave", ""))
        norm_set = {normalizar(k) for k in kws}
        add_here = 0
        for a in aliases:
            if normalizar(a) not in norm_set:
                kws.append(a)
                norm_set.add(normalizar(a))
                add_here += 1
        if add_here:
            row["Palabras_clave"] = _join_keywords(kws)
            row["N_palabras_clave"] = str(len(kws))
            total_add += add_here
            detalle.append(f"  - {materia}: +{add_here}")

    print(f"Aliases nuevos anadidos: {total_add}")
    if detalle:
        print("Detalle por materia:")
        for d in detalle:
            print(d)
    else:
        print("Sin cambios: los aliases ya estaban incluidos.")

    if dry_run or not inplace:
        print("\nDry-run: no se ha escrito el CSV.")
        return 0

    with PATH_CRIT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nGuardado: {PATH_CRIT}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        args.dry_run = True
    return run(inplace=args.inplace, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
