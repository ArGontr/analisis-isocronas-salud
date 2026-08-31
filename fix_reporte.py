import re

with open('generar_reporte_completo.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Reemplazar las lineas del HTML de la seccion 3
old_block = '''    <!-- SECCIÓN 3: CASAS CON CLUES ASIGNADA -->
    <h2>🔗 3. Casas de Salud con CLUES Asignada (n={len(con_clues)})</h2>

    <div class="highlight">
        <b>Hallazgo clave:</b> De las {len(con_clues)} casas de salud con CLUES asignada, 
        <b>{(con_clues['tipo']=='estrategica').sum()}</b> son estratégicas (aportan cobertura nueva) 
        y <b>{(con_clues['tipo']=='redundante').sum()}</b> son redundantes (caen en zonas ya redundantes).
    </div>'''

new_block = '''    <!-- SECCIÓN 3: CASAS CON CLUES ASIGNADA -->
    <h2>🔗 3. Casas de Salud con CLUES Asignada (n=653)</h2>

    <div class="highlight">
        <b>Hallazgo clave:</b> De las <b>653</b> casas de salud con CLUES asignada,
        <b>{(con_clues['tipo']=='estrategica').sum()}</b> tienen coordenadas y son estratégicas (aportan cobertura nueva)
        y <b>{(con_clues['tipo']=='redundante').sum()}</b> tienen coordenadas y son redundantes.
        <i>Nota: 78 casas del cruce no tienen coordenadas en el archivo de casas de salud.</i>
    </div>'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('Bloque 1 reemplazado.')
else:
    print('Bloque 1 NO encontrado.')

# 2. Reemplazar tarjeta de casas con CLUES asignada
old_card = '''        <div class="card">
            <div class="number">{casas_full[\'CLUES_ASIGNADA\'].notna().sum()}</div>
            <div class="label">Casas con CLUES asignada</div>
        </div>'''

new_card = '''        <div class="card">
            <div class="number">653</div>
            <div class="label">Casas con CLUES asignada (575 con coordenadas)</div>
        </div>'''

if old_card in content:
    content = content.replace(old_card, new_card)
    print('Bloque 2 reemplazado.')
else:
    print('Bloque 2 NO encontrado.')

with open('generar_reporte_completo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Archivo corregido.')
