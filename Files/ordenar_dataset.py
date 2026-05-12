"""
Script para ordenar el dataset de preguntas:
1. Por materia (columna Materia, orden según Data/listado_materias.csv)
2. Dentro de cada materia: primero Teoría ordenada por dificultad
3. Luego Cálculo ordenada por dificultad
Orden de dificultad: Fácil -> Media -> Difícil
"""

from pathlib import Path

import pandas as pd

from utils_dataset_csv import COLUMNAS_PREGUNTAS
from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"

df = pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")

orden_dificultad = {"Facil": 0, "Media": 1, "Dificil": 2}
orden_tipo = {"Teoria": 0, "Calculo": 1}

_, orden_materia = cargar_orden_temas()
fallback_materia = len(orden_materia)

col_materia = "Materia" if "Materia" in df.columns else "Tema"
if col_materia == "Tema" and "Materia" not in df.columns:
    df = df.rename(columns={"Tema": "Materia"})

df["_orden_dificultad"] = df["Dificultad"].map(orden_dificultad)
df["_orden_tipo"] = df["Tipo"].map(orden_tipo)
df["_orden_materia"] = df["Materia"].map(orden_materia).fillna(fallback_materia)

df_ordenado = df.sort_values(
    by=["_orden_materia", "_orden_tipo", "_orden_dificultad"],
    ignore_index=True,
)

df_ordenado = df_ordenado.drop(
    columns=["_orden_materia", "_orden_dificultad", "_orden_tipo"]
)

df_ordenado["Id"] = range(1, len(df_ordenado) + 1)

df_out = df_ordenado[[c for c in COLUMNAS_PREGUNTAS if c in df_ordenado.columns]]
df_out.to_csv(PATH_CSV, sep=";", index=False, encoding="utf-8")

print("Dataset ordenado correctamente.")
print(f"\nResumen del orden:")
print(f"- Total de preguntas: {len(df_out)}")
print(f"- Materias distintas: {df_out['Materia'].nunique()}")
print(f"\nEjemplo de las primeras filas por materia:")
for materia in df_out["Materia"].unique()[:3]:
    subset = df_out[df_out["Materia"] == materia]
    print(f"\n  {materia}:")
    print(f"    Teoría: {subset[subset['Tipo']=='Teoria']['Dificultad'].tolist()}")
    print(f"    Cálculo: {subset[subset['Tipo']=='Calculo']['Dificultad'].tolist()}")
