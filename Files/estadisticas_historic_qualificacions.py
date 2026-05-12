import pandas as pd

# Leer el CSV completo (todas las hojas combinadas)
df_completo = pd.read_csv("Data/Historic_qualificacions_MatCAD_completo.csv", sep=";", encoding="utf-8")

# Columnas del CSV
col_any = "Any"
col_assignatura = "Assignatura"
col_qual_num = "Qualificació"
col_qual_text = df_completo.columns[18]  # Unnamed: 17 (qualificació texto)
col_convocatoria = "Convocatòria"
col_periode = "Periode"

print("=" * 60)
print("INFORMACIÓN DEL DATASET HISTÒRIC QUALIFICACIONS MATCAD")
print("=" * 60)
print(f"\nFuente: Data/Historic_qualificacions_MatCAD_completo.csv")
print(f"Años encontrados: {sorted(df_completo[col_any].dropna().unique())}")


def mostrar_estadisticas(df, titulo, cols):
    """Muestra estadísticas para un dataframe."""
    col_any, col_assignatura, col_qual_num, col_qual_text, col_convocatoria, col_periode = cols
    print(f"\n--- {titulo} ---")
    print(f"Registros: {len(df)}")
    print("\nPor ASSIGNATURA:")
    print(df[col_assignatura].value_counts().to_string())
    print("\nPor QUALIFICACIÓ (texto):")
    print(df[col_qual_text].value_counts().to_string())
    print("\nPor CONVOCATÒRIA:")
    print(df[col_convocatoria].value_counts().to_string())
    print("\nPor PERIODE:")
    print(df[col_periode].value_counts().to_string())
    print("\nEstadísticas NOTA NUMÉRICA:")
    print(df[col_qual_num].describe().to_string())
    print("\nASSIGNATURA x QUALIFICACIÓ:")
    print(df.groupby([col_assignatura, col_qual_text]).size().unstack(fill_value=0).to_string())


cols = (col_any, col_assignatura, col_qual_num, col_qual_text, col_convocatoria, col_periode)

# Estadísticas por cada año
for any_ in sorted(df_completo[col_any].dropna().unique()):
    df_any = df_completo[df_completo[col_any] == any_]
    mostrar_estadisticas(df_any, f"ANY {any_}", cols)

# Resumen combinado (todos los años)
print("\n" + "=" * 60)
print("RESUMEN COMBINADO (TODOS LOS AÑOS)")
print("=" * 60)
print(f"\nTotal registros: {len(df_completo)}")
print("\nRegistros por AÑO:")
print(df_completo[col_any].value_counts().to_string())
mostrar_estadisticas(df_completo, "TODOS LOS AÑOS", cols)

print("\n" + "=" * 60)
