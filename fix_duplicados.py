with open('generar_reporte_completo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Eliminar lineas 21 y 22 (indices 20 y 21, ya que son 0-based)
# Linea 21: clues = clues[clues['institucion'] != 'DESCONOCIDA']  (duplicado)
# Linea 22: clues = pd.read_csv(...)  (sobreescribe)
del lines[20:22]

with open('generar_reporte_completo.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Lineas 21-22 eliminadas.')

# Verificar
for i, line in enumerate(lines[15:23], start=16):
    print(f'{i}: {line.rstrip()}')
