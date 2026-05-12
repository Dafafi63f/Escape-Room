"""
Script para validar la integridad del CSV de preguntas.
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "Files"))
from utils_dataset_csv import complejidad_global_valor, mapa_metadatos_por_materia  # noqa: E402
from reordenar_balance_por_materia import comprobar_orden_canonico_df  # noqa: E402

# Evitar UnicodeEncodeError en Windows al imprimir caracteres especiales
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

df = pd.read_csv(BASE / "Data" / "Preguntas.csv", sep=";", encoding="utf-8")

print("=" * 60)
print("VALIDACIÓN DEL CSV DE PREGUNTAS")
print("=" * 60)

# 1. Estructura básica
print(f"\n1. Filas cargadas: {len(df)}")
print(f"   Columnas: {list(df.columns)}")

# 2. IDs únicos y consecutivos
ids = df["Id"].dropna().astype(int)
ids_duplicados = ids[ids.duplicated()]
if len(ids_duplicados) > 0:
    print(f"\n2. IDs duplicados: {ids_duplicados.tolist()}")
else:
    print(f"\n2. IDs: OK (sin duplicados)")

# 3. Columna Correcta: debe ser A, B, C o D
correcta_valores = df["Correcta"].dropna().astype(str).str.strip().str.upper()
validos = correcta_valores.isin(["A", "B", "C", "D"])
invalidos = df[~validos & df["Correcta"].notna()]
if len(invalidos) > 0:
    print(f"\n3. Valores incorrectos en 'Correcta': {len(invalidos)} filas")
    print(invalidos[["Id", "Correcta"]].head(10))
else:
    print(f"\n3. Columna 'Correcta': OK (solo A, B, C, D)")

# 4. Coherencia: la respuesta correcta debe coincidir con el contenido de A/B/C/D
errores_coherencia = []
for idx, row in df.iterrows():
    correcta = str(row["Correcta"]).strip().upper()
    if correcta not in ["A", "B", "C", "D"]:
        continue
    col_respuesta = correcta
    respuesta_esperada = str(row[col_respuesta]).strip() if pd.notna(row[col_respuesta]) else ""
    # Verificar que la columna Correcta apunta a una opción que existe
    if pd.isna(row[col_respuesta]) or str(row[col_respuesta]).strip() == "":
        errores_coherencia.append((row["Id"], f"Correcta={correcta} pero opción {correcta} está vacía"))
    elif respuesta_esperada == "nan":
        errores_coherencia.append((row["Id"], f"Correcta={correcta} pero opción {correcta} es NaN"))

if errores_coherencia:
    print(f"\n4. Errores de coherencia: {len(errores_coherencia)}")
    for eid, msg in errores_coherencia[:10]:
        print(f"   - Id {eid}: {msg}")
else:
    print(f"\n4. Coherencia Correcta <-> opciones: OK")

# 5. Campos obligatorios no vacíos (solo columnas del CSV; metadatos vienen del listado)
campos_obligatorios = [
    "Pregunta",
    "Materia",
    "Dificultad",
    "Tipo",
    "A",
    "B",
    "C",
    "D",
]
vacios = {}
for col in campos_obligatorios:
    if col in df.columns:
        n_vacios = df[col].isna() | (df[col].astype(str).str.strip() == "")
        vacios[col] = n_vacios.sum()
    else:
        vacios[col] = len(df)
if any(v > 0 for v in vacios.values()):
    print(f"\n5. Campos vacíos o ausentes:")
    for col, n in vacios.items():
        if n > 0:
            print(f"   - {col}: {n} vacíos")
else:
    print(f"\n5. Campos obligatorios: OK (ninguno vacío)")

# 5b. Complejidad global (derivada): Nivel del listado + Dificultad de la fila (misma formula que el juego)
mapa = mapa_metadatos_por_materia(BASE / "Data" / "listado_materias.csv")
incoherentes = []
materias_desconocidas = []
if "Dificultad" in df.columns and "Materia" in df.columns:
    for _, row in df.iterrows():
        mat = str(row.get("Materia", "") or "").strip()
        meta = mapa.get(mat)
        if not meta:
            materias_desconocidas.append(row.get("Id"))
            continue
        try:
            esperado = complejidad_global_valor(
                str(meta.get("Nivel", "")), str(row.get("Dificultad", ""))
            )
        except (TypeError, ValueError):
            incoherentes.append(row.get("Id"))
            continue
        if "ComplejidadGlobal" in df.columns and str(row.get("ComplejidadGlobal", "")).strip() != "":
            try:
                actual = int(float(str(row.get("ComplejidadGlobal", "")).strip() or "0"))
                if esperado != actual:
                    incoherentes.append(row.get("Id"))
            except ValueError:
                incoherentes.append(row.get("Id"))
if materias_desconocidas:
    print(
        f"\n5b. Materia sin entrada en listado_materias.csv: {len(materias_desconocidas)} filas "
        f"(muestra Id): {materias_desconocidas[:8]}"
    )
if incoherentes:
    print(f"\n5b. ComplejidadGlobal en CSV no coincide con derivada (muestra Id): {incoherentes[:8]}")
if not materias_desconocidas and not incoherentes:
    print("\n5b. Materias reconocibles en listado y complejidad derivada: OK")

# 6. Valores esperados en Dificultad y Tipo
dificultades_validas = ["Facil", "Media", "Dificil"]
tipos_validos = ["Teoria", "Calculo"]
diff_inv = df[~df["Dificultad"].isin(dificultades_validas)]
tipo_inv = df[~df["Tipo"].isin(tipos_validos)]
if len(diff_inv) > 0:
    print(f"\n6. Dificultad inválida: {len(diff_inv)} filas")
    print(diff_inv[["Id", "Dificultad"]].head(5))
if len(tipo_inv) > 0:
    print(f"\n6. Tipo inválido: {len(tipo_inv)} filas")
    print(tipo_inv[["Id", "Tipo"]].head(5))
if len(diff_inv) == 0 and len(tipo_inv) == 0:
    print(f"\n6. Dificultad y Tipo: OK")

# 7. Orden canónico del banco (listado, ladder TF..TD / CF..CD, bloques F/M/D, ciclo ABCD)
errores_orden = comprobar_orden_canonico_df(df)
if errores_orden:
    print(f"\n7. Orden canónico: {len(errores_orden)} incidencias")
    for msg in errores_orden[:25]:
        print(f"   - {msg}")
else:
    print("\n7. Orden canónico (reordenar_balance_por_materia): OK")

# 8. Filas que antes eran problemáticas (spot-check)
ids_problematicos = [38, 41, 44, 265, 326, 336, 347, 575, 576, 577, 622, 628, 651, 670, 1032]
filas_check = df[df["Id"].isin(ids_problematicos)]
print(f"\n8. Revisión de filas antes problemáticas (muestra):")
for _, row in filas_check.head(5).iterrows():
    preg = str(row["Pregunta"])[:60] + "..." if len(str(row["Pregunta"])) > 60 else row["Pregunta"]
    print(f"   Id {row['Id']}: {preg} | Correcta={row['Correcta']}")

print("\n" + "=" * 60)
print("VALIDACIÓN COMPLETADA")
print("=" * 60)
