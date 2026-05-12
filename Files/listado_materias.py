import os
import pandas as pd

# Rutas: Excel y CSV en Data/ (raíz = carpeta padre de Files)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, "Data")
os.chdir(project_root)

# Leer todas las hojas del Excel
xl = pd.ExcelFile(os.path.join(data_dir, "Històric_qualificacions_MatCAD.xlsx"))
materias = {}  # codigo -> nombre (para evitar duplicados y quedarnos con el nombre)

for sheet in xl.sheet_names:
    df = pd.read_excel(os.path.join(data_dir, "Històric_qualificacions_MatCAD.xlsx"), sheet_name=sheet)
    if len(df) > 0 and df.iloc[0].isna().sum() > 10:
        df = df.drop(0)
    for _, row in df.iterrows():
        cod = row.iloc[8]
        nom = row.iloc[9] if len(df.columns) > 9 else ""
        if pd.notna(cod) and cod not in materias:
            materias[cod] = nom if pd.notna(nom) else ""

# Ordenar por código
print("LISTADO DE MATERIAS (Històric Qualificacions MatCAD)")
print("=" * 50)
for cod, nom in sorted(materias.items(), key=lambda x: x[0]):
    print(f"{int(cod)}\t{nom}")

# Guardar a CSV con encoding UTF-8 en Data/
path_csv = os.path.join(data_dir, "listado_materias.csv")
with open(path_csv, "w", encoding="utf-8") as f:
    f.write("Codi;Materia\n")
    for cod, nom in sorted(materias.items(), key=lambda x: x[0]):
        f.write(f"{int(cod)};{nom}\n")
print(f"\nListado guardado en: {path_csv}")
