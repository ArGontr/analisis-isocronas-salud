with open('generar_reporte_completo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y mostrar las lineas problematicas
for i, line in enumerate(lines[15:25], start=16):
    print(f'{i}: {line.rstrip()}')
