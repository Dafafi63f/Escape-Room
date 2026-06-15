# -*- coding: utf-8 -*-
"""
Validación y estadísticas de ``Data/Preguntas.csv`` (solo lectura).

  python Files/Scripts/mantenimiento.py revision          # revisión amplia
  python Files/Scripts/mantenimiento.py estadisticas      # tablas de distribución
  python Files/Scripts/mantenimiento.py dataset           # checks adicionales (hash, complejidad, …)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent
from balance_lib import comprobar_orden_canonico_df  # noqa: E402
from utils_dataset_csv import complejidad_global_valor, mapa_metadatos_por_materia  # noqa: E402
from utils_orden_temas import cargar_orden_temas  # noqa: E402

MATERIA_CRIPTO = "Informació i Seguretat"
_PATRON_HASH = re.compile(r"\bhash(?:ing|es|ed)?\b", re.IGNORECASE)
PATH_CSV = BASE / "Data" / "Preguntas.csv"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _cargar_df() -> pd.DataFrame:
    return pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")


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

    print("\n12. TABLA TEMA x DIFICULTAD")
    tabla = df.groupby(["Materia", "Dificultad"]).size().unstack(fill_value=0)
    tabla = tabla.reindex([t for t in orden_materias if t in tabla.index])
    print(tabla.to_string())

    print("\n" + "=" * 60)
    problemas_totales = (
        len(invalidas) + len(problemas) + nulos.sum() + len(dup_ids) + len(errores_orden)
    )
    if problemas_totales == 0 and len(raros) == 0:
        print("RESUMEN: Dataset OK, sin inconsistencias criticas.")
    else:
        print("RESUMEN: Revisar items marcados arriba.")
    print("=" * 60)


def validacion_extendida(df: pd.DataFrame, *, con_variedad: bool) -> int:
    print("=" * 60)
    print("VALIDACIÓN EXTENDIDA DEL CSV")
    print("=" * 60)

    ids = df["Id"].dropna().astype(int)
    if ids.duplicated().any():
        print(f"\nIDs duplicados: {ids[ids.duplicated()].tolist()[:10]}")
    else:
        print(f"\nIDs: OK ({len(ids)} filas)")

    campos = ["Pregunta", "Materia", "Dificultad", "Tipo", "A", "B", "C", "D"]
    vacios = {
        col: (df[col].isna() | (df[col].astype(str).str.strip() == "")).sum()
        for col in campos
        if col in df.columns
    }
    if any(v > 0 for v in vacios.values()):
        print("Campos vacíos:", {k: v for k, v in vacios.items() if v})
    else:
        print("Campos obligatorios: OK")

    mapa = mapa_metadatos_por_materia(BASE / "Data" / "listado_materias.csv")
    incoherentes: list = []
    desconocidas: list = []
    for _, row in df.iterrows():
        mat = str(row.get("Materia", "") or "").strip()
        meta = mapa.get(mat)
        if not meta:
            desconocidas.append(row.get("Id"))
            continue
        try:
            esperado = complejidad_global_valor(
                str(meta.get("Nivel", "")), str(row.get("Dificultad", ""))
            )
        except (TypeError, ValueError):
            incoherentes.append(row.get("Id"))
            continue
        if "ComplejidadGlobal" in df.columns and str(row.get("ComplejidadGlobal", "")).strip():
            try:
                actual = int(float(str(row.get("ComplejidadGlobal", "")).strip() or "0"))
                if esperado != actual:
                    incoherentes.append(row.get("Id"))
            except ValueError:
                incoherentes.append(row.get("Id"))
    if desconocidas:
        print(f"Materias sin listado: {len(desconocidas)} (muestra {desconocidas[:6]})")
    if incoherentes:
        print(f"ComplejidadGlobal incoherente: {len(incoherentes)} (muestra {incoherentes[:6]})")
    elif not desconocidas:
        print("Complejidad derivada / listado: OK")

    diff_inv = df[~df["Dificultad"].isin(["Facil", "Media", "Dificil"])]
    tipo_inv = df[~df["Tipo"].isin(["Teoria", "Calculo"])]
    if len(diff_inv) or len(tipo_inv):
        print(f"Dificultad/Tipo inválidos: {len(diff_inv)} / {len(tipo_inv)}")
    else:
        print("Dificultad y Tipo: OK")

    hash_fuera = []
    for _, row in df.iterrows():
        texto = " ".join(str(row.get(c, "") or "") for c in ("Pregunta", "A", "B", "C", "D"))
        if _PATRON_HASH.search(texto) and str(row.get("Materia", "")).strip() != MATERIA_CRIPTO:
            hash_fuera.append(int(row["Id"]))
    if hash_fuera:
        print(f"«hash» fuera de {MATERIA_CRIPTO}: {hash_fuera[:12]}")
    else:
        print(f"«hash» solo en {MATERIA_CRIPTO}: OK")

    errores_orden = comprobar_orden_canonico_df(df)
    if errores_orden:
        print(f"Orden canónico: {len(errores_orden)} incidencias (muestra)")
        for msg in errores_orden[:12]:
            print(f"  - {msg}")
    else:
        print("Orden canónico: OK")

    rc = 0
    if con_variedad:
        try:
            sys.path.insert(0, str(FILES / "Archivo"))
            from utils_variedad import UMBRAL_VALIDACION, alertas_variedad_csv  # noqa: E402

            alertas = alertas_variedad_csv(df.to_dict("records"), umbral=UMBRAL_VALIDACION)
            if alertas:
                print(f"Variedad temática: {len(alertas)} pares similares (≥{UMBRAL_VALIDACION})")
                for mat, a, b, sim in alertas[:10]:
                    print(f"  - {mat}: Id {a} vs {b} (sim={sim})")
                rc = 1
            else:
                print("Variedad temática: OK")
        except ImportError:
            print("Variedad temática: omitida (utils_variedad en Files/Archivo)")

    print("=" * 60)
    return rc or (1 if hash_fuera or errores_orden or desconocidas else 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validación del dataset cerrado")
    parser.add_argument(
        "--estadisticas",
        action="store_true",
        help="Solo tablas de distribución",
    )
    parser.add_argument(
        "--extendida",
        action="store_true",
        help="Checks de validar_csv (hash, complejidad, variedad opcional)",
    )
    parser.add_argument("--variedad", action="store_true", help="Incluir alertas de variedad temática")
    args = parser.parse_args(argv)

    df = _cargar_df()
    orden_materias, _ = cargar_orden_temas()

    if args.estadisticas:
        imprimir_estadisticas(df, orden_materias)
        return 0
    if args.extendida:
        return validacion_extendida(df, con_variedad=args.variedad)
    revision_completa(df, orden_materias)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
