"""
Genera mapa interactivo de casas de salud coloreadas por tipo.
Usa paleta institucional.
"""

import geopandas as gpd
import pandas as pd
import folium
import os
from paleta_institucional import *

print("Cargando datos...")

# Casas de salud con coordenadas originales
casas_raw = pd.read_excel('casas_de_salud.xlsx')

# Resultados del análisis
stats = pd.read_csv('resultados_casas_salud/casas_salud_clasificadas.csv')

# Cruzar para tener coords + clasificación
casas = casas_raw.merge(stats[['ID_TEMP_SUS', 'tipo', 'pct_descubierta', 'pct_vulnerable', 'pct_redundante', 'clues_asignada']], on='ID_TEMP_SUS', how='left')

# Crear GeoDataFrame de puntos (WGS84)
casas_gdf = gpd.GeoDataFrame(
    casas,
    geometry=gpd.points_from_xy(casas['LON'], casas['LAT']),
    crs='EPSG:4326'
)

print(f"Total casas: {len(casas_gdf)}")
print(f"Estratégicas: {(casas_gdf['tipo']=='estrategica').sum()}")
print(f"Redundantes: {(casas_gdf['tipo']=='redundante').sum()}")

# Crear mapa
center = [casas_gdf.geometry.y.mean(), casas_gdf.geometry.x.mean()]
m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')

# Agregar casas estratégicas (puntos más grandes)
estrategicas = casas_gdf[casas_gdf['tipo'] == 'estrategica'].copy()
if not estrategicas.empty:
    print(f"Agregando {len(estrategicas)} casas estratégicas...")
    for _, row in estrategicas.iterrows():
        # Color según % descubierta usando paleta institucional
        if row['pct_descubierta'] >= 50:
            color = VERDE_CONSOLIDADO
        elif row['pct_descubierta'] > 0:
            color = AMARILLO_PRECAUCION
        elif row['pct_vulnerable'] > 0:
            color = NARANJA
        else:
            color = VERDE_OSCURO
        
        popup_text = f"""
        <b>{row['ID_TEMP_SUS']}</b><br>
        Tipo: <b>Estratégica</b><br>
        Descubierta: {row['pct_descubierta']}%<br>
        Vulnerable: {row['pct_vulnerable']}%<br>
        Redundante: {row['pct_redundante']}%<br>
        CLUES: {row['clues_asignada'] if pd.notna(row['clues_asignada']) else 'N/A'}
        """
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color=color,
            fill=True,
            fillOpacity=0.8,
            popup=folium.Popup(popup_text, max_width=250)
        ).add_to(m)

# Agregar casas redundantes (puntos pequeños, gris, semi-transparentes)
redundantees = casas_gdf[casas_gdf['tipo'] == 'redundante'].copy()
if not redundantees.empty:
    print(f"Agregando {len(redundantees)} casas redundantes...")
    # Samplear para no saturar el mapa (mostrar max 500)
    if len(redundantees) > 500:
        redundantees_muestra = redundantees.sample(500, random_state=42)
        print(f"  (muestra de 500 para visualización)")
    else:
        redundantees_muestra = redundantees
    
    for _, row in redundantees_muestra.iterrows():
        popup_text = f"""
        <b>{row['ID_TEMP_SUS']}</b><br>
        Tipo: <b>Redundante</b><br>
        Redundante: {row['pct_redundante']}%<br>
        CLUES: {row['clues_asignada'] if pd.notna(row['clues_asignada']) else 'N/A'}
        """
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,
            color=GRIS,
            fill=True,
            fillOpacity=0.4,
            popup=folium.Popup(popup_text, max_width=250)
        ).add_to(m)

# Leyenda con paleta institucional
legend_html = f'''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 280px;
            background-color: white; border: 2px solid {NEGRO};
            border-radius: 8px; padding: 12px; font-size: 13px;
            box-shadow: 3px 3px 10px rgba(0,0,0,0.3);
            z-index: 9999;">
    <h4 style="margin-top:0; color:{NEGRO};">🏥 Casas de Salud</h4>
    <b>Total:</b> 3,560<br>
    <b>Estratégicas:</b> <span style="color:{VERDE_CONSOLIDADO};">858</span><br>
    <b>Redundantes:</b> <span style="color:{GRIS};">2,702</span><br>
    <hr style="margin:8px 0;">
    <b>Estratégicas:</b><br>
    <span style="display:inline-block;width:10px;height:10px;background:{VERDE_CONSOLIDADO};"></span> &gt;50% descubierta<br>
    <span style="display:inline-block;width:10px;height:10px;background:{AMARILLO_PRECAUCION};"></span> Algo descubierta<br>
    <span style="display:inline-block;width:10px;height:10px;background:{NARANJA};"></span> Cubre vulnerable<br>
    <span style="display:inline-block;width:10px;height:10px;background:{VERDE_OSCURO};"></span> Otra estratégica<br>
    <span style="display:inline-block;width:10px;height:10px;background:{GRIS};"></span> Redundante
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

title_html = f'''
<div style="position: fixed; 
            top: 10px; left: 50%; transform: translateX(-50%);
            background-color: rgba(255,255,255,0.9);
            border: 2px solid {NEGRO}; border-radius: 8px;
            padding: 10px 20px; font-size: 16px; font-weight: bold;
            z-index: 9999; color: {NEGRO};">
    Casas de Salud: Estratégicas vs Redundantes
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Guardar
os.makedirs('resultados_casas_salud', exist_ok=True)
out_path = 'resultados_casas_salud/mapa_casas_salud.html'
m.save(out_path)
print(f"\n✅ Mapa guardado en: {out_path}")
