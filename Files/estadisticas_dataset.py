import pandas as pd
from pathlib import Path
from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent

df = pd.read_csv(BASE / "Data" / "Preguntas.csv", sep=";", encoding="utf-8")
orden_materias, _ = cargar_orden_temas()
conteo_tema = df["Materia"].value_counts()

print("=" * 60)
print("INFORMACIÓN DEL DATASET DE PREGUNTAS")
print("=" * 60)

# Información básica
print(f"\nDimensiones: {df.shape[0]} filas, {df.shape[1]} columnas")
print(f"Columnas: {list(df.columns)}")

# Distribución por tema
print("\nPreguntas por TEMA:")
for tema in orden_materias:
    if tema in conteo_tema:
        print(f"{tema}: {conteo_tema[tema]}")

# Distribución por dificultad
print("\nPreguntas por DIFICULTAD:")
print(df["Dificultad"].value_counts().to_string())

# Distribución por tipo
print("\nPreguntas por TIPO (Teoria vs Calculo):")
print(df["Tipo"].value_counts().to_string())

# Distribución de respuestas correctas
print("\nDistribucion de respuestas CORRECTAS (A/B/C/D):")
print(df["Correcta"].value_counts().to_string())

# Resumen combinado (Tema + Dificultad)
print("\nPreguntas por TEMA y DIFICULTAD:")
tabla = df.groupby(["Materia", "Dificultad"]).size().unstack(fill_value=0)
tabla = tabla.reindex([t for t in orden_materias if t in tabla.index])
print(tabla.to_string())

print("\n" + "=" * 60)
