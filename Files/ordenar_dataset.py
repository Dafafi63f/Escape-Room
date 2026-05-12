"""
Script para ordenar el dataset de preguntas:
1. Por materia (Tema)
2. Dentro de cada materia: primero Teoría ordenada por dificultad
3. Luego Cálculo ordenada por dificultad
Orden de dificultad: Fácil -> Media -> Difícil
"""

import pandas as pd
from utils_orden_temas import cargar_orden_temas

# Cargar el dataset
df = pd.read_csv("Data/Preguntas.csv", sep=";")

# Definir orden de dificultad
orden_dificultad = {"Facil": 0, "Media": 1, "Dificil": 2}

# Definir orden de tipo (Teoria primero, Calculo después)
orden_tipo = {"Teoria": 0, "Calculo": 1}

# Definir orden de tema según Data/listado_materias.csv
_, orden_tema = cargar_orden_temas()
fallback_tema = len(orden_tema)

# Crear columnas auxiliares para ordenar
df["_orden_dificultad"] = df["Dificultad"].map(orden_dificultad)
df["_orden_tipo"] = df["Tipo"].map(orden_tipo)
df["_orden_tema"] = df["Tema"].map(orden_tema).fillna(fallback_tema)

# Ordenar: 1) Tema (según listado_materias), 2) Tipo, 3) Dificultad
df_ordenado = df.sort_values(
    by=["_orden_tema", "_orden_tipo", "_orden_dificultad"],
    ignore_index=True
)

# Eliminar columnas auxiliares
df_ordenado = df_ordenado.drop(columns=["_orden_tema", "_orden_dificultad", "_orden_tipo"])

# Renumerar los Id para que reflejen el orden (1, 2, 3...)
df_ordenado["Id"] = range(1, len(df_ordenado) + 1)

# Guardar el resultado (sobrescribe Preguntas.csv)
df_ordenado.to_csv("Data/Preguntas.csv", sep=";", index=False)

print("Dataset ordenado correctamente.")
print(f"\nResumen del orden:")
print(f"- Total de preguntas: {len(df_ordenado)}")
print(f"- Materias (Temas): {df_ordenado['Tema'].nunique()}")
print(f"\nEjemplo de las primeras filas por materia:")
for tema in df_ordenado["Tema"].unique()[:3]:
    subset = df_ordenado[df_ordenado["Tema"] == tema]
    print(f"\n  {tema}:")
    print(f"    Teoría: {subset[subset['Tipo']=='Teoria']['Dificultad'].tolist()}")
    print(f"    Cálculo: {subset[subset['Tipo']=='Calculo']['Dificultad'].tolist()}")
