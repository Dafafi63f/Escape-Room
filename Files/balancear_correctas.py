# -*- coding: utf-8 -*-
"""
Balancea la distribucion de respuestas correctas a 750 por opcion (A, B, C, D).
Estrategia: permutar el orden de las opciones (sin cambiar el contenido)
para que la respuesta correcta quede en distintas posiciones.
"""

import pandas as pd
import random

random.seed(42)

df = pd.read_csv("Data/Preguntas.csv", sep=";", encoding="utf-8")
conteos = df["Correcta"].value_counts()
print("Antes:")
for letra in ["A", "B", "C", "D"]:
    print(f"  {letra}: {conteos.get(letra, 0)}")

TARGET = 750  # 3000 / 4

# Objetivo: exactamente 750 de cada letra
objetivos = ["A"] * TARGET + ["B"] * TARGET + ["C"] * TARGET + ["D"] * TARGET
random.shuffle(objetivos)

# Para cada pregunta: permutar opciones para que la correcta quede en posicion objetivo
def permutar_opciones(row, objetivo):
    """Reordena A,B,C,D para que la respuesta correcta quede en posicion objetivo."""
    opciones = {"A": row["A"], "B": row["B"], "C": row["C"], "D": row["D"]}
    correcta_actual = row["Correcta"]
    valor_correcto = opciones[correcta_actual]
    
    # Nueva orden: poner valor_correcto en posicion objetivo
    letras = ["A", "B", "C", "D"]
    otras = [opciones[l] for l in letras if l != correcta_actual]
    random.shuffle(otras)
    
    nuevo = {}
    idx = 0
    for i, l in enumerate(letras):
        if l == objetivo:
            nuevo[l] = valor_correcto
        else:
            nuevo[l] = otras[idx]
            idx += 1
    
    return nuevo["A"], nuevo["B"], nuevo["C"], nuevo["D"], objetivo

# Aplicar permutacion
nuevas_A, nuevas_B, nuevas_C, nuevas_D, nuevas_Correcta = [], [], [], [], []
for i, (idx, row) in enumerate(df.iterrows()):
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

# Verificacion
conteos_final = df["Correcta"].value_counts()
print("\nDespues:")
for letra in ["A", "B", "C", "D"]:
    n = conteos_final.get(letra, 0)
    ok = "[OK]" if n == TARGET else f"(obj:{TARGET})"
    print(f"  {letra}: {n} {ok}")

df.to_csv("Data/Preguntas.csv", sep=";", index=False, encoding="utf-8")
print(f"\n[OK] Opciones permutadas para balancear respuestas correctas.")
