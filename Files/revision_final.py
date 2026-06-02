# -*- coding: utf-8 -*-
"""
Revisión amplia del CSV y estadísticas del banco.

  python Files/revision_final.py              # revisión completa
  python Files/revision_final.py --estadisticas  # solo tablas de distribución
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "Files"))
from balance_lib import comprobar_orden_canonico_df  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def imprimir_estadisticas(df: pd.DataFrame, orden_materias: list[str]) -> None:
    conteo_tema = df["Materia"].value_counts()
    print("=" * 60)
    print("ESTADÍSTICAS DEL DATASET DE PREGUNTAS")
    print("=" * 60)
    print(f"\nDimensiones: {df.shape[0]} filas, {df.shape[1]} columnas")
    print(f"Columnas: {list(df.columns)}")
    print("\nPreguntas por TEMA:")
    for tema in orden_materias:
        if tema in conteo_tema:
            print(f"{tema}: {conteo_tema[tema]}")
    print("\nPreguntas por DIFICULTAD:")
    print(df["Dificultad"].value_counts().to_string())
    print("\nPreguntas por TIPO (Teoria vs Calculo):")
    print(df["Tipo"].value_counts().to_string())
    print("\nDistribución de respuestas CORRECTAS (A/B/C/D):")
    print(df["Correcta"].value_counts().to_string())
    print("\nPreguntas por TEMA y DIFICULTAD:")
    tabla = df.groupby(["Materia", "Dificultad"]).size().unstack(fill_value=0)
    tabla = tabla.reindex([t for t in orden_materias if t in tabla.index])
    print(tabla.to_string())
    print("\n" + "=" * 60)


def revision_completa(df: pd.DataFrame, orden_materias: list[str]) -> None:
    print("=" * 60)
    print("REVISION FINAL - Data/Preguntas.csv")
    print("=" * 60)

    print("\n1. ESTRUCTURA")
    print(f"   Filas: {len(df)}, Columnas: {list(df.columns)}")

    print("\n2. VALORES NULOS")
    nulos = df.isnull().sum()
    for col in df.columns:
        if nulos[col] > 0:
            print(f"   {col}: {nulos[col]} nulos")
    if nulos.sum() == 0:
        print("   Ninguno")

    print("\n3. VALORES EN COLUMNAS CATEGORICAS")
    print("   Dificultad:", df["Dificultad"].unique().tolist())
    print("   Tipo:", df["Tipo"].unique().tolist())
    print("   Correcta:", sorted(df["Correcta"].unique().tolist()))

    print("\n4. CONSISTENCIA Correcta")
    invalidas = df[~df["Correcta"].isin(["A", "B", "C", "D"])]
    print(f"   Correcta invalida (no A/B/C/D): {len(invalidas)}")

    def check_correcta(row):
        corr = row["Correcta"]
        val = row.get(corr, None)
        return pd.isna(val) or str(val).strip() == ""

    problemas = df[df.apply(check_correcta, axis=1)]
    print(f"   Correcta apunta a valor vacio: {len(problemas)}")
    if len(problemas) > 0:
        print("   Ejemplos:", problemas.head(3)[["Pregunta", "Correcta", "A", "B", "C", "D"]].to_string())

    print("\n5. OPCIONES VACIAS (A,B,C,D)")
    for col in ["A", "B", "C", "D"]:
        vacias = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
        print(f"   {col}: {len(vacias)} vacias")

    print("\n6. DUPLICADOS")
    dup_preg = df[df.duplicated(subset=["Pregunta"], keep=False)]
    print(f"   Preguntas con texto duplicado: {len(dup_preg)}")
    dup_ids = df[df.duplicated(subset=["Id"])]
    print(f"   Ids duplicados: {len(dup_ids)}")

    print("\n7. IDs")
    print(f"   Unicos: {df['Id'].nunique()}, Total filas: {len(df)}")
    print(f"   Rango: {df['Id'].min()} - {df['Id'].max()}")

    print("\n8. DISTRIBUCIONES (balance esperado: 40 materias, 12 preguntas c/u)")
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

    print("\n9. ORDEN CANONICO (listado + ladder TF..TD / CF..CD + ciclo ABCD)")
    errores_orden = comprobar_orden_canonico_df(df)
    if errores_orden:
        print(f"   Incidencias: {len(errores_orden)}")
        for msg in errores_orden[:15]:
            print(f"   - {msg}")
    else:
        print("   OK")

    print("\n10. CALIDAD DE TEXTO")
    preg_vacias = df[df["Pregunta"].str.strip() == ""]
    print(f"   Preguntas vacias: {len(preg_vacias)}")
    raros = df[df["Pregunta"].str.contains("\ufffd", na=False, regex=False)]
    print("   Preguntas con caracteres de encoding raro:", len(raros))

    print("\n11. OPCIONES IDENTICAS EN UNA PREGUNTA")

    def opciones_identicas(row):
        vals = [str(row["A"]).strip(), str(row["B"]).strip(), str(row["C"]).strip(), str(row["D"]).strip()]
        return len(set(vals)) < 4

    identicas = df[df.apply(opciones_identicas, axis=1)]
    print(f"   Preguntas con alguna opcion duplicada: {len(identicas)}")
    if 0 < len(identicas) <= 5:
        print("   Ejemplos:")
        for _, r in identicas.head(5).iterrows():
            print(f"      Id {r['Id']}: A={r['A'][:30]}... B={r['B'][:30]}...")

    print("\n12. TABLA TEMA x DIFICULTAD")
    tabla = df.groupby(["Materia", "Dificultad"]).size().unstack(fill_value=0)
    tabla = tabla.reindex([t for t in orden_materias if t in tabla.index])
    print(tabla.to_string())

    print("\n" + "=" * 60)
    problemas_totales = (
        len(invalidas) + len(problemas) + nulos.sum() + len(dup_ids)
        + sum(
            1
            for col in ["A", "B", "C", "D"]
            if len(df[df[col].isna() | (df[col].astype(str).str.strip() == "")]) > 0
        )
        + len(errores_orden)
    )
    if problemas_totales == 0 and len(raros) == 0:
        print("RESUMEN: Dataset OK, sin inconsistencias criticas.")
    else:
        print("RESUMEN: Revisar items marcados arriba.")
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisión y estadísticas del dataset")
    parser.add_argument(
        "--estadisticas",
        action="store_true",
        help="Solo imprime distribuciones (antes en estadisticas_dataset.py)",
    )
    args = parser.parse_args()

    df = pd.read_csv(BASE / "Data" / "Preguntas.csv", sep=";", encoding="utf-8")
    orden_materias, _ = cargar_orden_temas()

    if args.estadisticas:
        imprimir_estadisticas(df, orden_materias)
    else:
        revision_completa(df, orden_materias)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
