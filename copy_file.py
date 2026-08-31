import shutil

src = r"C:\Users\armando.gonzalez\Downloads\equivalencia.xlsx"
dst = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\equivalencia.xlsx"

shutil.copy2(src, dst)
print(f"Archivo copiado a: {dst}")
