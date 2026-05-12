# -*- coding: utf-8 -*-
"""
Ejecuta el balanceo completo del dataset de preguntas en bucle hasta que todo
esté balanceado (balancear una cosa puede desbalancear otra).
1. Temas: 75 preguntas por tema (40 temas, 3000 total)
2. Tipo+Dificultad: ~12 por cada combinación (Tema, Tipo, Dificultad)
3. Tipos: 1500 Teoría, 1500 Cálculo
4. Dificultad global: 1000 Fácil, 1000 Media, 1000 Difícil (después de Tipos para corregir el desbalance que introduce)
5. Correctas: 750 respuestas correctas en A, B, C y D
"""

import csv
import os
import shutil
import subprocess
import sys
from collections import Counter

# Raíz del proyecto (carpeta padre de Files)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR) if os.path.basename(_SCRIPT_DIR) == "Files" else _SCRIPT_DIR
PATH_CSV = os.path.join(PROJECT_ROOT, "Data", "Preguntas.csv")
MAX_ITERACIONES = 15

SCRIPT_DUPLICADOS = ("Files/eliminar_duplicados.py", "DUPLICADOS (reemplazar/eliminar)")
SCRIPTS = [
    ("Files/balancear_dataset.py", "TEMAS (75 por tema)"),
    ("Files/balancear_tipo_y_dificultad.py", "TIPO+DIFICULTAD (~12 por Tema×Tipo×Dificultad)"),
    ("Files/balancear_tipos.py", "TIPOS (1500 Teoría, 1500 Cálculo)"),
    ("Files/balancear_dificultad_global.py", "DIFICULTAD (1000/1000/1000)"),
    ("Files/balancear_correctas.py", "CORRECTAS (750 A/B/C/D)"),
]


def esta_balanceado():
    """Comprueba si el dataset cumple todos los criterios de balance."""
    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    if len(rows) != 3000:
        return False, f"Total {len(rows)} != 3000"

    por_tema = Counter(r["Tema"] for r in rows)
    if min(por_tema.values()) != 75 or max(por_tema.values()) != 75:
        return False, f"Temas: min={min(por_tema.values())}, max={max(por_tema.values())}"

    por_dificultad = Counter(r["Dificultad"] for r in rows)
    for d in ["Facil", "Media", "Dificil"]:
        if por_dificultad.get(d, 0) != 1000:
            return False, f"Dificultad {d}: {por_dificultad.get(d, 0)}"

    por_tipo = Counter(r["Tipo"] for r in rows)
    if por_tipo.get("Teoria", 0) != 1500 or por_tipo.get("Calculo", 0) != 1500:
        return False, f"Tipos: Teoria={por_tipo.get('Teoria', 0)}, Calculo={por_tipo.get('Calculo', 0)}"

    por_correcta = Counter(r["Correcta"] for r in rows)
    for letra in ["A", "B", "C", "D"]:
        if por_correcta.get(letra, 0) != 750:
            return False, f"Correcta {letra}: {por_correcta.get(letra, 0)}"

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
        print("BALANCEO COMPLETO DEL DATASET (bucle hasta equilibrio)", flush=True)
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
                ejecutar_script("Files/ordenar_dataset.py", "ORDENAR (Tema, Tipo, Dificultad)")
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
