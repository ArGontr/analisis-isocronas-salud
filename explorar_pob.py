import pandas as pd

file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad\datos_pob_y_prod.xlsx"

# Leer todas las hojas
xl = pd.ExcelFile(file_path)
print("Hojas:", xl.sheet_names)

# Leer la primera hoja
df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0])
print(f"\nFilas: {len(df)}, Columnas: {list(df.columns)}")
print(f"\nDtypes:\n{df.dtypes}")
print(f"\nHead:\n{df.head(10)}")
print(f"\nValores nulos:\n{df.isnull().sum()}")
