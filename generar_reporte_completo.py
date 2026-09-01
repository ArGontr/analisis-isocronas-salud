"""
Genera un reporte HTML completo que integra:
- Analisis de CLUES existentes (indispensabilidad, categorizacion)
- Analisis de casas de salud (estrategicas vs redundantees) v2: intersecciones reales
- Enfasis en las 653 casas de salud con CLUES asignada
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
from paleta_institucional import *

print("Cargando datos...")

# CLUES
clues = pd.read_csv('resultados_indispensabilidad/base_clues_normalizada.csv')
clues = clues[clues['institucion'] != 'DESCONOCIDA']

# Casas de salud (v2: intersecciones reales)
casas = pd.read_csv('resultados_casas_salud/casas_salud_clasificadas.csv')

# Cruzar con CLUES asignadas
cruce = pd.read_excel(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx')
casas_full = casas.merge(cruce[['ID_TEMP_SUS', 'CLUES_ASIGNADA', 'ENTIDAD', 'MUNICIPIO', 'NOMBRE']], 
                          left_on='ID_TEMP_SUS', right_on='ID_TEMP_SUS', how='left')

casas_full['estado'] = casas_full['ID_TEMP_SUS'].str.split('-').str[0]

print(f"CLUES: {len(clues)}")
print(f"Casas de salud: {len(casas_full)}")
print(f"Casas con CLUES asignada: {casas_full['CLUES_ASIGNADA'].notna().sum()}")

# ============================================================
# GRAFICOS
# ============================================================

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

print("\nGenerando graficos...")

# Grafico 1: CLUES por categoria
fig1, ax1 = plt.subplots(figsize=(8, 5))
clues_counts = clues['categoria'].value_counts()
ax1.bar(clues_counts.index, clues_counts.values, color=[EXITO, PRIMARIO, ALERTA])
ax1.set_title('CLUES por categoria', fontsize=14, fontweight='bold', color=TEXTO)
ax1.set_ylabel('Numero de CLUES', color=TEXTO)
ax1.tick_params(colors=TEXTO)
for i, v in enumerate(clues_counts.values):
    ax1.text(i, v + 50, f'{v:,}', ha='center', fontweight='bold')
img1 = fig_to_base64(fig1)

# Grafico 2: CLUES por institucion y categoria
fig2, ax2 = plt.subplots(figsize=(8, 5))
clues_inst = clues.groupby(['institucion', 'categoria']).size().unstack(fill_value=0)
clues_inst.plot(kind='bar', ax=ax2, color=[EXITO, PRIMARIO, ALERTA])
ax2.set_title('CLUES por institucion y categoria', fontsize=14, fontweight='bold', color=TEXTO)
ax2.set_ylabel('Numero de CLUES', color=TEXTO)
ax2.legend(title='Categoria')
ax2.tick_params(axis='x', rotation=0, colors=TEXTO)
img2 = fig_to_base64(fig2)

# Grafico 3: Casas de salud por tipo (v2)
fig3, ax3 = plt.subplots(figsize=(8, 5))
casas_counts = casas_full['tipo'].value_counts()
colores_tipo = [EXITO if t == 'estrategica' else (NEUTRO if t == 'redundante' else NARANJA) for t in casas_counts.index]
ax3.bar(casas_counts.index, casas_counts.values, color=colores_tipo)
ax3.set_title('Casas de salud por tipo (interseccion real)', fontsize=14, fontweight='bold', color=TEXTO)
ax3.set_ylabel('Numero de casas', color=TEXTO)
ax3.tick_params(colors=TEXTO)
for i, v in enumerate(casas_counts.values):
    ax3.text(i, v + 50, f'{v:,}', ha='center', fontweight='bold')
img3 = fig_to_base64(fig3)

# Grafico 4: Las 653 con CLUES asignada
con_clues = casas_full[casas_full['CLUES_ASIGNADA'].notna()]
fig4, ax4 = plt.subplots(figsize=(8, 5))
con_clues_counts = con_clues['tipo'].value_counts()
ax4.bar(con_clues_counts.index, con_clues_counts.values, color=[EXITO, NEUTRO])
ax4.set_title('Casas de salud con CLUES asignada (n=653)', fontsize=14, fontweight='bold', color=TEXTO)
ax4.set_ylabel('Numero de casas', color=TEXTO)
ax4.tick_params(colors=TEXTO)
for i, v in enumerate(con_clues_counts.values):
    ax4.text(i, v + 5, f'{v:,}', ha='center', fontweight='bold')
img4 = fig_to_base64(fig4)

# Grafico 5: Top estados con casas estrategicas con CLUES
fig5, ax5 = plt.subplots(figsize=(10, 6))
estrat_con_clues = con_clues[con_clues['tipo'] == 'estrategica']
top_estados = estrat_con_clues['estado'].value_counts().head(10)
ax5.barh(top_estados.index, top_estados.values, color=EXITO)
ax5.set_title('Top 10 estados con casas estrategicas con CLUES asignada', fontsize=14, fontweight='bold', color=TEXTO)
ax5.set_xlabel('Numero de casas', color=TEXTO)
ax5.tick_params(colors=TEXTO)
for i, v in enumerate(top_estados.values):
    ax5.text(v + 1, i, f'{v}', va='center', fontweight='bold')
img5 = fig_to_base64(fig5)

# Tabla: CLUES que tienen casas de salud asignadas estrategicas
clues_con_casas = estrat_con_clues.groupby('CLUES_ASIGNADA').agg(
    n_casas=('ID_TEMP_SUS', 'count'),
    estados=('estado', lambda x: ', '.join(x.unique())),
    pct_descubierta_prom=('pct_descubierta', 'mean'),
    pct_superpuesto_prom=('pct_superpuesto', 'mean')
).sort_values('n_casas', ascending=False).head(20)

# ============================================================
# HTML
# ============================================================
print("\nGenerando reporte HTML...")

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte: CLUES y Casas de Salud</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f6fa;
            color: {TEXTO};
        }}
        h1 {{
            color: {TEXTO};
            border-bottom: 3px solid {PRIMARIO};
            padding-bottom: 10px;
        }}
        h2 {{
            color: {TEXTO};
            margin-top: 40px;
            border-left: 4px solid {PRIMARIO};
            padding-left: 15px;
        }}
        h3 {{
            color: #4a5b6e;
            margin-top: 25px;
        }}
        .summary-box {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: {PRIMARIO};
        }}
        .card .label {{
            font-size: 0.9em;
            color: #4a5b6e;
            margin-top: 5px;
        }}
        .card.green .number {{ color: {EXITO}; }}
        .card.red .number {{ color: {ALERTA}; }}
        .card.gray .number {{ color: {NEUTRO}; }}
        .card.orange .number {{ color: {VULNERABLE}; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 15px 0;
        }}
        th {{
            background: {SECUNDARIO};
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .chart {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
        }}
        .highlight {{
            background: {CREMA_DORADA}33;
            border-left: 4px solid {AMARILLO_PRECAUCION};
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            text-align: center;
            color: {NEUTRO};
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>Reporte: CLUES y Casas de Salud</h1>
    <p>Analisis de indispensabilidad de CLUES y evaluacion de 3,560 casas de salud potenciales (intersecciones reales v2).</p>

    <!-- RESUMEN EJECUTIVO -->
    <h2>Resumen Ejecutivo</h2>
    <div class="summary-box">
        <div class="card">
            <div class="number">{len(clues):,}</div>
            <div class="label">CLUES totales</div>
        </div>
        <div class="card green">
            <div class="number">{(clues['categoria']=='clave').sum():,}</div>
            <div class="label">CLUES clave (indispensables)</div>
        </div>
        <div class="card red">
            <div class="number">{(clues['categoria']=='ideal_normativo').sum():,}</div>
            <div class="label">CLUES ideal normativo</div>
        </div>
        <div class="card orange">
            <div class="number">{(clues['categoria']=='complementaria').sum():,}</div>
            <div class="label">CLUES complementarias</div>
        </div>
        <div class="card">
            <div class="number">{len(casas_full):,}</div>
            <div class="label">Casas de salud</div>
        </div>
        <div class="card green">
            <div class="number">{(casas_full['tipo']=='estrategica').sum():,}</div>
            <div class="label">Casas estrategicas</div>
        </div>
        <div class="card gray">
            <div class="number">{(casas_full['tipo']=='redundante').sum():,}</div>
            <div class="label">Casas redundantes</div>
        </div>
        <div class="card">
            <div class="number">653</div>
            <div class="label">Casas con CLUES asignada (575 con coordenadas)</div>
        </div>
    </div>

    <!-- SECCION 1: CLUES -->
    <h2>1. Analisis de CLUES</h2>

    <div class="chart">
        <img src="data:image/png;base64,{img1}" alt="CLUES por categoria">
    </div>

    <div class="chart">
        <img src="data:image/png;base64,{img2}" alt="CLUES por institucion">
    </div>

    <h3>Tabla: CLUES por institucion y categoria</h3>
    <table>
        <tr><th>Institucion</th><th>Clave</th><th>Complementaria</th><th>Ideal Normativo</th><th>Total</th></tr>
"""

for _, row in clues.groupby('institucion')['categoria'].value_counts().unstack(fill_value=0).iterrows():
    clave = row.get('clave', 0)
    comp = row.get('complementaria', 0)
    ideal = row.get('ideal_normativo', 0)
    total = clave + comp + ideal
    html += f"        <tr><td><b>{_}</b></td><td>{clave}</td><td>{comp}</td><td>{ideal}</td><td><b>{total}</b></td></tr>\n"

html += """    </table>

    <!-- SECCION 2: CASAS DE SALUD -->
    <h2>2. Analisis de Casas de Salud (Interseccion Real v2)</h2>

    <div class="chart">
        <img src="data:image/png;base64,{img3}" alt="Casas de salud por tipo">
    </div>

    <h3>Tabla: Resumen por tipo</h3>
    <table>
        <tr><th>Tipo</th><th>Cantidad</th><th>%</th><th>Area total (km2)</th><th>Area descubierta (km2)</th><th>Area superpuesta (km2)</th></tr>
""".format(img3=img3)

for tipo in ['estrategica', 'redundante', 'intermedia']:
    subset = casas_full[casas_full['tipo'] == tipo]
    if len(subset) == 0:
        continue
    n = len(subset)
    pct = n / len(casas_full) * 100
    area_total = subset['area_total_m2'].sum() / 1e6
    area_desc = subset['area_descubierta_m2'].sum() / 1e6
    area_sup = subset['area_superpuesta_m2'].sum() / 1e6
    html += f"        <tr><td><b>{tipo}</b></td><td>{n:,}</td><td>{pct:.1f}%</td><td>{area_total:,.0f}</td><td>{area_desc:,.0f}</td><td>{area_sup:,.0f}</td></tr>\n"

html += f"""    </table>

    <!-- SECCION 3: CASAS CON CLUES ASIGNADA -->
    <h2>3. Casas de Salud con CLUES Asignada (n=653)</h2>

    <div class="highlight">
        <b>Hallazgo clave:</b> De las <b>653</b> casas de salud con CLUES asignada,
        <b>{(con_clues['tipo']=='estrategica').sum()}</b> tienen coordenadas y son estrategicas (aportan cobertura nueva)
        y <b>{(con_clues['tipo']=='redundante').sum()}</b> tienen coordenadas y son redundantes.
        <i>Nota: 78 casas del cruce no tienen coordenadas en el archivo de casas de salud.</i>
    </div>

    <div class="chart">
        <img src="data:image/png;base64,{img4}" alt="Casas con CLUES asignada">
    </div>

    <div class="chart">
        <img src="data:image/png;base64,{img5}" alt="Top estados">
    </div>

    <h3>Tabla: Top 20 CLUES con mas casas de salud estrategicas asignadas</h3>
    <table>
        <tr><th>CLUES Asignada</th><th>N Casas</th><th>Estados</th><th>% Descubierta promedio</th><th>% Superpuesto promedio</th></tr>
"""

for clues_id, row in clues_con_casas.iterrows():
    html += f"        <tr><td><b>{clues_id}</b></td><td>{int(row['n_casas'])}</td><td>{row['estados']}</td><td>{row['pct_descubierta_prom']:.1f}%</td><td>{row['pct_superpuesto_prom']:.1f}%</td></tr>\n"

html += f"""    </table>

    <h3>Tabla completa: Casas estrategicas con CLUES asignada</h3>
    <table>
        <tr><th>ID Casa</th><th>CLUES Asignada</th><th>Estado</th><th>Municipio</th><th>% Descubierta</th><th>% Superpuesto</th></tr>
"""

for _, row in estrat_con_clues.head(50).iterrows():
    html += f"        <tr><td>{row['ID_TEMP_SUS']}</td><td><b>{row['CLUES_ASIGNADA']}</b></td><td>{row['estado']}</td><td>{row['MUNICIPIO']}</td><td>{row['pct_descubierta']:.1f}%</td><td>{row['pct_superpuesto']:.1f}%</td></tr>\n"

html += """    </table>

    <!-- MAPAS -->
    <h2>4. Mapas Interactivos</h2>
    <p>Los mapas interactivos estan disponibles en los siguientes archivos locales:</p>
    <ul>
        <li><b>Mapa de CLUES (indispensabilidad):</b> <code>resultados_indispensabilidad/reporte_indispensabilidad.html</code></li>
        <li><b>Mapa de casas de salud:</b> <code>resultados_casas_salud/mapa_casas_salud.html</code></li>
    </ul>

    <div class="footer">
        <p>Reporte generado el 2026-08-31 | Analisis reproducible en <a href="https://github.com/ArGontr/analisis-isocronas-salud">GitHub</a></p>
    </div>
</body>
</html>
"""

# Guardar
os.makedirs('resultados_reporte', exist_ok=True)
out_path = 'resultados_reporte/reporte_completo.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nReporte completo guardado en: {out_path}")
print(f"Tamano: {os.path.getsize(out_path) / 1024:.0f} KB")
