# -*- coding: utf-8 -*-
"""Revision final del CSV de preguntas."""

from pathlib import Path

import pandas as pd

from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent

df = pd.read_csv(BASE / "Data" / "Preguntas.csv", sep=";", encoding="utf-8")
orden_materias, _ = cargar_orden_temas()

print("=" * 60)
print("REVISION FINAL - Data/Preguntas.csv")
print("=" * 60)

# 1. Estructura
print("\n1. ESTRUCTURA")
print(f"   Filas: {len(df)}, Columnas: {list(df.columns)}")

# 2. Valores nulos
print("\n2. VALORES NULOS")
nulos = df.isnull().sum()
for col in df.columns:
    if nulos[col] > 0:
        print(f"   {col}: {nulos[col]} nulos")

if nulos.sum() == 0:
    print("   Ninguno")

# 3. Columnas categoricas
print("\n3. VALORES EN COLUMNAS CATEGORICAS")
print("   Dificultad:", df["Dificultad"].unique().tolist())
print("   Tipo:", df["Tipo"].unique().tolist())
print("   Correcta:", sorted(df["Correcta"].unique().tolist()))

# 4. Consistencia Correcta
print("\n4. CONSISTENCIA Correcta")
invalidas = df[~df["Correcta"].isin(["A", "B", "C", "D"])]
print(f"   Correcta invalida (no A/B/C/D): {len(invalidas)}")

# Correcta debe apuntar a un valor no vacio
def check_correcta(row):
    corr = row["Correcta"]
    val = row.get(corr, None)
    return pd.isna(val) or str(val).strip() == ""

problemas = df[df.apply(check_correcta, axis=1)]
print(f"   Correcta apunta a valor vacio: {len(problemas)}")
if len(problemas) > 0:
    print("   Ejemplos:", problemas.head(3)[["Pregunta", "Correcta", "A", "B", "C", "D"]].to_string())

# 5. Opciones vacias
print("\n5. OPCIONES VACIAS (A,B,C,D)")
for col in ["A", "B", "C", "D"]:
    vacias = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
    print(f"   {col}: {len(vacias)} vacias")

# 6. Duplicados
print("\n6. DUPLICADOS")
dup_preg = df[df.duplicated(subset=["Pregunta"], keep=False)]
print(f"   Preguntas con texto duplicado: {len(dup_preg)}")
dup_ids = df[df.duplicated(subset=["Id"])]
print(f"   Ids duplicados: {len(dup_ids)}")

# 7. IDs
print("\n7. IDs")
print(f"   Unicos: {df['Id'].nunique()}, Total filas: {len(df)}")
print(f"   Rango: {df['Id'].min()} - {df['Id'].max()}")

# 8. Distribuciones (balance esperado: 40 temas con ~75 c/u)
print("\n8. DISTRIBUCIONES (balance esperado: 40 temas, ~75 c/u)")
n_temas = df["Materia"].nunique()
target_por_tema = len(df) // n_temas if n_temas > 0 else 0
conteo_temas = df["Materia"].value_counts()
for t in orden_materias:
    if t not in conteo_temas:
        continue
    n = conteo_temas[t]
    ok = "OK" if abs(n - target_por_tema) <= 1 else "!"
    print(f"      {t}: {n} {ok}")

print("   Por Dificultad:")
for d, n in df["Dificultad"].value_counts().items():
    print(f"      {d}: {n}")

print("   Por Tipo:")
for t, n in df["Tipo"].value_counts().items():
    print(f"      {t}: {n}")

print("   Por Correcta:")
for c, n in df["Correcta"].value_counts().items():
    print(f"      {c}: {n}")

# 9. Longitudes / caracteres raros
print("\n9. CALIDAD DE TEXTO")
preg_vacias = df[df["Pregunta"].str.strip() == ""]
print(f"   Preguntas vacias: {len(preg_vacias)}")
# Caracteres de reemplazo tipicos de encoding malo
raros = df[df["Pregunta"].str.contains("\ufffd", na=False, regex=False)]
print("   Preguntas con caracteres de encoding raro:", len(raros))

# 10. Opciones identicas (A=B=C=D seria sospechoso)
print("\n10. OPCIONES IDENTICAS EN UNA PREGUNTA")
def opciones_identicas(row):
    vals = [str(row["A"]).strip(), str(row["B"]).strip(), str(row["C"]).strip(), str(row["D"]).strip()]
    return len(set(vals)) < 4

identicas = df[df.apply(opciones_identicas, axis=1)]
print(f"   Preguntas con alguna opcion duplicada: {len(identicas)}")
if len(identicas) > 0 and len(identicas) <= 5:
    print("   Ejemplos:")
    for _, r in identicas.head(5).iterrows():
        print(f"      Id {r['Id']}: A={r['A'][:30]}... B={r['B'][:30]}...")

# 11. Resumen
print("\n" + "=" * 60)
problemas_totales = (
    len(invalidas) + len(problemas) + nulos.sum() + len(dup_ids) +
    sum(1 for col in ["A","B","C","D"] if len(df[df[col].isna() | (df[col].astype(str).str.strip() == "")]) > 0)
)
if problemas_totales == 0 and len(raros) == 0:
    print("RESUMEN: Dataset OK, sin inconsistencias criticas.")
else:
    print("RESUMEN: Revisar items marcados arriba.")
print("=" * 60)
