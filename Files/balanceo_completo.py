# -*- coding: utf-8 -*-
"""
Ejecuta el balanceo completo del dataset de preguntas en bucle hasta que todo
esté balanceado (balancear una cosa puede desbalancear otra).

Objetivo final: 400 preguntas (TARGET_TOTAL_PREGUNTAS en objetivos_balanceo.py).
1. Temas: reparto equitativo por materia del listado
2. Tipo+Dificultad: reparto dentro de cada materia
3. Tipos: mitad Teoría, mitad Cálculo
4. Dificultad global: ~1/3 por nivel
5. Correctas: A/B/C/D lo más equilibrado posible
6. Tras converger: `reordenar_balance_por_materia.py` fija el orden canónico del CSV (listado, ladder TF..TD/CF..CD, Id, ciclo ABCD).

import csv
import os
import shutil
import subprocess
import sys
from collections import Counter

# Raíz del proyecto (carpeta padre de Files)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR) if os.path.basename(_SCRIPT_DIR) == "Files" else _SCRIPT_DIR
sys.path.insert(0, os.path.join(PROJECT_ROOT, "Files"))
from objetivos_balanceo import (
    TARGET_TOTAL_PREGUNTAS,
    objetivos_correcta_por_letra,
    objetivos_dificultad_por_totales,
    preguntas_por_materia,
    preguntas_por_tipo_global,
)
from utils_dataset_csv import materia_de_fila

PATH_CSV = os.path.join(PROJECT_ROOT, "Data", "Preguntas.csv")
MAX_ITERACIONES = 15

SCRIPT_DUPLICADOS = ("Files/eliminar_duplicados.py", "DUPLICADOS (reemplazar/eliminar)")
SCRIPTS = [
    ("Files/balancear_dataset.py", "TEMAS (reparto por materia)"),
    ("Files/balancear_tipo_y_dificultad.py", "TIPO+DIFICULTAD (por materia)"),
    ("Files/balancear_tipos.py", "TIPOS (200 Teoria, 200 Calculo)"),
    ("Files/balancear_dificultad_global.py", "DIFICULTAD (global ~1/3 cada una)"),
    ("Files/balancear_correctas.py", "CORRECTAS (A/B/C/D equilibradas)"),
]


def esta_balanceado():
    """Comprueba si el dataset cumple todos los criterios de balance."""
    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    n = len(rows)
    if n != TARGET_TOTAL_PREGUNTAS:
        return False, f"Total {n} != {TARGET_TOTAL_PREGUNTAS}"

    tgt_m = preguntas_por_materia()
    por_tema = Counter(materia_de_fila(r) for r in rows)
    if por_tema and (min(por_tema.values()) != tgt_m or max(por_tema.values()) != tgt_m):
        return False, f"Temas: min={min(por_tema.values())}, max={max(por_tema.values())} (obj. {tgt_m}/materia)"

    tgt_diff = objetivos_dificultad_por_totales(n)
    por_dificultad = Counter(r["Dificultad"] for r in rows)
    for d in ["Facil", "Media", "Dificil"]:
        if por_dificultad.get(d, 0) != tgt_diff[d]:
            return False, f"Dificultad {d}: {por_dificultad.get(d, 0)} (obj. {tgt_diff[d]})"

    tgt_tipo = preguntas_por_tipo_global()
    por_tipo = Counter(r["Tipo"] for r in rows)
    if por_tipo.get("Teoria", 0) != tgt_tipo or por_tipo.get("Calculo", 0) != tgt_tipo:
        return False, f"Tipos: Teoria={por_tipo.get('Teoria', 0)}, Calculo={por_tipo.get('Calculo', 0)} (obj. {tgt_tipo})"

    tgt_corr = objetivos_correcta_por_letra(n)
    por_correcta = Counter(r["Correcta"] for r in rows)
    for letra in ["A", "B", "C", "D"]:
        if por_correcta.get(letra, 0) != tgt_corr[letra]:
            return False, f"Correcta {letra}: {por_correcta.get(letra, 0)} (obj. {tgt_corr[letra]})"

    return True, "OK"


def ejecutar_balanceo():
    """Ejecuta una ronda completa de los 5 scripts."""
    for script, nombre in SCRIPTS:
        if not ejecutar_script(script, nombre):
            return False
    return True


def borrar_pycache():
    """Elimina carpetas __pycache__ creadas al importar módulos."""
    for root, dirs, _ in os.walk(PROJECT_ROOT, topdown=False):
        for d in dirs:
            if d == "__pycache__":
                path = os.path.join(root, d)
                try:
                    shutil.rmtree(path)
                except OSError:
                    pass


def ejecutar_script(script, nombre):
    """Ejecuta un script y devuelve True si tuvo éxito."""
    print(f"\n>>> {nombre}", flush=True)
    print("-" * 40, flush=True)
    script_path = os.path.join(PROJECT_ROOT, script)
    result = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
    return result.returncode == 0


def main():
    try:
        print("=" * 60, flush=True)
        print(f"BALANCEO COMPLETO (objetivo: {TARGET_TOTAL_PREGUNTAS} preguntas)", flush=True)
        print("=" * 60, flush=True)

        # Paso previo: eliminar duplicados (una sola vez)
        if not ejecutar_script(*SCRIPT_DUPLICADOS):
            print("\n[ERROR] eliminar_duplicados falló")
            sys.exit(1)

        for iteracion in range(1, MAX_ITERACIONES + 1):
            print(f"\n--- Iteración {iteracion}/{MAX_ITERACIONES} ---", flush=True)
            if not ejecutar_balanceo():
                print("\n[ERROR] Algún script falló")
                sys.exit(1)

            ok, msg = esta_balanceado()
            if ok:
                ejecutar_script(
                    "Files/reordenar_balance_por_materia.py",
                    "ORDEN CANONICO (listado, ladder TF..TD/CF..CD, F/M/D bloque, Id, ABCD)",
                )
                print("\n" + "=" * 60, flush=True)
                print(f"BALANCEO COMPLETO FINALIZADO (iteración {iteracion})", flush=True)
                print("=" * 60, flush=True)
                return

            print(f"\n[Iteración {iteracion}] Aún desbalanceado: {msg}", flush=True)

        print("\n[AVISO] Máximo de iteraciones alcanzado sin equilibrio completo.", flush=True)
        ok, msg = esta_balanceado()
        print(f"Estado final: {msg}", flush=True)
        sys.exit(1)
    finally:
        borrar_pycache()


if __name__ == "__main__":
    main()
