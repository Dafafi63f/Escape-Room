# -*- coding: utf-8 -*-
"""
Balancea la distribución de respuestas correctas (A/B/C/D) repartiendo lo más igual posible.
Estrategia: permutar el orden de las opciones (sin cambiar el contenido)
para que la respuesta correcta quede en distintas posiciones.
"""

import random

import pandas as pd
from pathlib import Path

from objetivos_balanceo import lista_objetivos_correcta, objetivos_correcta_por_letra
from utils_dataset_csv import COLUMNAS_PREGUNTAS

BASE = Path(__file__).resolve().parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"


def permutar_opciones(row, objetivo):
    """Reordena A,B,C,D para que la respuesta correcta quede en posicion objetivo."""
    opciones = {"A": row["A"], "B": row["B"], "C": row["C"], "D": row["D"]}
    correcta_actual = row["Correcta"]
    valor_correcto = opciones[correcta_actual]

    letras = ["A", "B", "C", "D"]
    otras = [opciones[l] for l in letras if l != correcta_actual]
    random.shuffle(otras)

    nuevo = {}
    idx = 0
    for _, l in enumerate(letras):
        if l == objetivo:
            nuevo[l] = valor_correcto
        else:
            nuevo[l] = otras[idx]
            idx += 1

    return nuevo["A"], nuevo["B"], nuevo["C"], nuevo["D"], objetivo


def main() -> None:
    random.seed(42)

    df = pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")
    n = len(df)
    objetivos_por_letra = objetivos_correcta_por_letra(n)

    conteos = df["Correcta"].value_counts()
    print("Antes:")
    for letra in ["A", "B", "C", "D"]:
        print(f"  {letra}: {conteos.get(letra, 0)}")

    objetivos = lista_objetivos_correcta(n)
    random.shuffle(objetivos)

    nuevas_A, nuevas_B, nuevas_C, nuevas_D, nuevas_Correcta = [], [], [], [], []
    for i, (_, row) in enumerate(df.iterrows()):
        obj = objetivos[i]
        a, b, c, d, corr = permutar_opciones(row, obj)
        nuevas_A.append(a)
        nuevas_B.append(b)
        nuevas_C.append(c)
        nuevas_D.append(d)
        nuevas_Correcta.append(corr)

    df["A"] = nuevas_A
    df["B"] = nuevas_B
    df["C"] = nuevas_C
    df["D"] = nuevas_D
    df["Correcta"] = nuevas_Correcta

    conteos_final = df["Correcta"].value_counts()
    print("\nDespues:")
    for letra in ["A", "B", "C", "D"]:
        n_fin = conteos_final.get(letra, 0)
        obj = objetivos_por_letra[letra]
        ok = "[OK]" if n_fin == obj else f"(obj:{obj})"
        print(f"  {letra}: {n_fin} {ok}")

    df = df[[c for c in COLUMNAS_PREGUNTAS if c in df.columns]]
    df.to_csv(PATH_CSV, sep=";", index=False, encoding="utf-8")
    print(f"\n[OK] Opciones permutadas para balancear respuestas correctas ({n} filas).")


if __name__ == "__main__":
    main()
