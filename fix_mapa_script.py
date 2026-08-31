with open('generar_mapa_casas_salud.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazos
content = content.replace('print(f"Inútiles: {(casas_gdf[\'tipo\']==\'redundante\').sum()}")', 
                          'print(f"Redundantes: {(casas_gdf[\'tipo\']==\'redundante\').sum()}")')
content = content.replace('Tipo: <b>Inútil</b>', 'Tipo: <b>Redundante</b>')
content = content.replace('<b>Inútiles:</b>', '<b>Redundantes:</b>')
content = content.replace('Inútil (redundante)', 'Redundante')
content = content.replace('Casas de Salud: Estratégicas vs Inútiles', 
                          'Casas de Salud: Estratégicas vs Redundantes')

with open('generar_mapa_casas_salud.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Correcciones aplicadas.')

# Verificar
for line_num, line in enumerate(content.split('\n'), 1):
    if 'Inútil' in line or 'Inútiles' in line:
        print(f'Linea {line_num}: {line}')
