import pandas as pd

# Leer el archivo Excel
file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\equivalencia.xlsx"
df = pd.read_excel(file_path)

print("=== INFORMACIÓN GENERAL ===")
print(f"Filas: {len(df)}")
print(f"Columnas: {list(df.columns)}")
print(f"\n=== PRIMERAS 30 FILAS ===")
print(df.head(30).to_string())
print(f"\n=== ÚLTIMAS 10 FILAS ===")
print(df.tail(10).to_string())
