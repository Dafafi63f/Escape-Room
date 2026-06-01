#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reubica entradas en plantillas.json según las mismas reglas de contenido que
fix_final_materias.py (Python / shell / algoritmos / hardware).

Uso:
  python Files/sync_plantillas_materias.py
  python Files/sync_plantillas_materias.py --inyectar   # además inyecta Preguntas.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATH_PL = BASE / "Data" / "plantillas.json"
PATH_CSV = BASE / "Data" / "Preguntas.csv"

INI = "Iniciació a la Programació"
POO = "Programació Orientada als Objectes"
DEST = "Tècniques de Disseny d'Algoritmes"
FON = "Fonaments de Computadors"
PROG = "Programari de Sistema"
HPC = "Computació i Simulació d'Altes Prestacions"


def norm_pregunta(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


_SUSTITUCIONES_ORTOGRAFIA: list[tuple[str, str]] = [
    ("en  en", "en "),
    ("método  de", "método de"),
    ("Estatico", "Estático"),
    ("Eliptica", "Elíptica"),
    ("rendimiento grafico", "rendimiento gráfico"),
]


def _corregir_ortografia(texto: str) -> str:
    t = texto or ""
    for viejo, nuevo in _SUSTITUCIONES_ORTOGRAFIA:
        t = t.replace(viejo, nuevo)
    return re.sub(r"  +", " ", t)


def es_paralelismo(pregunta: str) -> bool:
    p = (pregunta or "").lower()
    if any(k in p for k in ("semáforo", "semaforo", "mutex")):
        return True
    if "pipeline" in p and "paraleliz" not in p:
        return False
    if ("hilo" in p or " thread" in p or "thread)" in p) and (
        "proceso" in p or "ejecución" in p or "ejecucion" in p
    ):
        return True
    if any(
        x in p
        for x in (
            "paralelepípedo",
            "paralelos al eje",
            "no son paralelos",
            "paralelismo cuántico",
            "paralelismo cuantico",
            "clustering",
            "k-means",
        )
    ):
        return False
    if "escalabilidad" in p and "iot" in p:
        return False
    claves = (
        "speedup",
        "amdahl",
        " mpi ",
        "allreduce",
        "computación paralela",
        "computacion paralela",
        "paralelizable",
        "paraleliz",
        "escalabilidad fuerte",
        "escalabilidad débil",
        "escalabilidad debil",
        "memoria compartida",
        "openmp",
        "paralelizar",
        "4 cpus",
    )
    if any(k in p for k in claves):
        return True
    if "mpi" in p and any(x in p for x in ("broadcast", "allreduce", "scatter", "gather")):
        return True
    return False


def destino_por_contenido(pregunta: str) -> str | None:
    p = (pregunta or "").lower()
    if es_paralelismo(pregunta):
        return HPC
    if "memoización" in p or "memoizacion" in p:
        return DEST
    if "tflops" in p:
        return FON
    if "operador combina condiciones" in p:
        return INI
    if "banquero" in p:
        return PROG
    if any(
        x in p
        for x in (
            "redirecci",
            "shell",
            "terminal",
            "touch",
            "cd ..",
            "comando sube",
            "comando crea un archivo",
            "comando lista archivos",
            "stdout",
            "stderr",
            "stdin",
            "git commit",
            "git add",
            "git status",
            "compilador",
            "gcc ",
            "chmod",
            "#!/bin/bash",
        )
    ):
        return PROG
    if "pipe" in p and "pipeline" not in p:
        return PROG
    if "lifo" in p:
        return DEST
    if "1 bit" in p or "representar 1 bit" in p:
        return FON
    return None


def destino_desde_materia_actual(materia: str, pregunta: str) -> str | None:
    p = (pregunta or "").lower()
    dest = destino_por_contenido(pregunta)
    if dest and dest != materia:
        return dest

    if materia == POO:
        if "condicional if" in p:
            return INI
        if any(
            k in p
            for k in (
                "complejidad",
                "lista no ordenada",
                "fibonacci recursivo",
                "backtracking",
                "branch and bound",
            )
        ):
            return DEST
        if "fibonacci f(" in p:
            return DEST

    if materia == INI:
        if p.startswith("¿qué es un algoritmo") or (
            "algoritmo" in p and "voraz" not in p and "banquero" not in p
        ):
            return DEST
        if "complejidad" in p and "árbol binario" in p:
            return DEST

    if materia == DEST:
        if "1111 en binario" in p:
            return INI

    if materia == FON and "banquero" in p:
        return PROG

    if materia != HPC and es_paralelismo(pregunta):
        return HPC

    return None


def _tiene_pregunta(items: list[dict], pregunta: str) -> bool:
    n = norm_pregunta(pregunta)
    return any(norm_pregunta(t.get("pregunta", "")) == n for t in items)


def reclasificar(plantillas: dict[str, list]) -> tuple[int, int]:
    """Devuelve (movidas, eliminadas_duplicado_en_origen)."""
    movidas = 0
    todas_materias = list(plantillas.keys())

    for materia in todas_materias:
        nuevas: list[dict] = []
        for t in plantillas.get(materia, []):
            pregunta = t.get("pregunta", "")
            dest = destino_desde_materia_actual(materia, pregunta)
            if not dest:
                nuevas.append(t)
                continue

            if dest not in plantillas:
                plantillas[dest] = []

            if _tiene_pregunta(plantillas[dest], pregunta):
                movidas += 1
                continue

            plantillas[dest].append(t)
            movidas += 1

        plantillas[materia] = nuevas

    return movidas, 0


def _fila_csv_para_plantilla(materia: str, pregunta: str, por_np: dict) -> dict | None:
    np = norm_pregunta(pregunta)
    candidatos = por_np.get(np, [])
    if not candidatos:
        return None
    if len(candidatos) == 1:
        return candidatos[0]
    for r in candidatos:
        if r["Materia"] == materia:
            return r
    return None


def actualizar_metadatos_desde_csv(plantillas: dict[str, list]) -> int:
    """Alinea texto y metadatos con Preguntas.csv cuando el enunciado coincide."""
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))
    por_np: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        por_np[norm_pregunta(r["Pregunta"])].append(r)

    cambios = 0
    for materia, items in plantillas.items():
        for t in items:
            for k in ("pregunta", "A", "B", "C", "D"):
                if k in t:
                    t[k] = _corregir_ortografia(t[k])
            r = _fila_csv_para_plantilla(materia, t.get("pregunta", ""), por_np)
            if not r:
                continue
            campos = {
                "pregunta": r["Pregunta"],
                "A": r["A"],
                "B": r["B"],
                "C": r["C"],
                "D": r["D"],
                "correcta": r["Correcta"],
                "dificultad": r["Dificultad"],
                "tipo": r["Tipo"],
            }
            for k, v in campos.items():
                if t.get(k) != v:
                    t[k] = v
                    cambios += 1
    return cambios


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inyectar",
        action="store_true",
        help="Tras reclasificar, ejecuta inyectar_dataset_en_plantillas.py",
    )
    args = parser.parse_args()

    with PATH_PL.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    movidas, _ = reclasificar(plantillas)
    meta = actualizar_metadatos_desde_csv(plantillas)

    with PATH_PL.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"plantillas.json: {movidas} entradas reubicadas, {meta} metadatos actualizados")

    for m in (INI, PROG, POO, DEST, FON):
        n = len(plantillas.get(m, []))
        print(f"  {m}: {n} plantillas")

    if args.inyectar:
        subprocess.run(
            [sys.executable, str(BASE / "Files" / "inyectar_dataset_en_plantillas.py")],
            cwd=BASE,
            check=True,
        )


if __name__ == "__main__":
    main()
