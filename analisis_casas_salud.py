"""
Análisis de casas de salud: identificar redundantes vs estratégicas.

CORRECCIÓN CRÍTICA v2:
- Ya NO se usa grid/fishnet para determinar cobertura.
- Se calculan intersecciones REALES entre el buffer de cada casa de salud
  y las isocronas existentes.
- Optimizado: simplificación previa de isocronas para velocidad.

Requiere: geopandas, shapely, pandas, numpy
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.strtree import STRtree
import os
import time

# ------------------------------------------------------------------
# 1. Cargar datos
# ------------------------------------------------------------------
print("[1/5] Cargando datos...")

gdf_iso = gpd.read_file('iso_upn_unido_15km.gpkg')
print(f"  Isocronas existentes: {len(gdf_iso)}")

casas = pd.read_excel('casas_de_salud.xlsx')
print(f"  Casas de salud: {len(casas)}")

if os.path.exists(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx'):
    cruce = pd.read_excel(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx')
    casas = casas.merge(cruce[['ID_TEMP_SUS', 'CLUES_ASIGNADA']], on='ID_TEMP_SUS', how='left')
    print(f"  Casas con CLUES asignada: {casas['CLUES_ASIGNADA'].notna().sum()}")

# ------------------------------------------------------------------
# 2. Crear buffers de casas de salud y simplificar isocronas
# ------------------------------------------------------------------
print("\n[2/5] Preparando geometrías...")

casas_gdf = gpd.GeoDataFrame(
    casas,
    geometry=[Point(lon, lat) for lat, lon in zip(casas['LAT'], casas['LON'])],
    crs='EPSG:4326'
).to_crs('EPSG:8858')

casas_gdf['geometry'] = casas_gdf.geometry.buffer(10000)
casas_gdf['area_km2'] = casas_gdf.geometry.area / 1e6
print(f"  Área promedio por buffer: {casas_gdf['area_km2'].mean():.0f} km²")

# Simplificar isocronas AGRESIVAMENTE para acelerar intersecciones
# 1000m de tolerancia es razonable para buffers de 10km
t0 = time.time()
gdf_iso['geometry'] = gdf_iso.geometry.simplify(tolerance=1000, preserve_topology=False)
print(f"  Isocronas simplificadas en {time.time()-t0:.1f}s")

# ------------------------------------------------------------------
# 3. Encontrar vecinos reales con STRtree (muy rápido)
# ------------------------------------------------------------------
print("\n[3/5] Encontrando vecinos reales con STRtree...")

t0 = time.time()
tree = STRtree(gdf_iso.geometry.values)

resultados = []
total = len(casas_gdf)

for i, row in casas_gdf.iterrows():
    geom = row.geometry
    area_total = geom.area
    
    # Encontrar isocronas que REALMENTE se intersectan con este buffer
    idx_vecinos = tree.query(geom, predicate='intersects')
    
    if len(idx_vecinos) == 0:
        area_superpuesta = 0
    else:
        # Unir SOLO los vecinos reales (no todas las isocronas)
        geoms_vecinos = gdf_iso.iloc[idx_vecinos].geometry
        union_vecinos = geoms_vecinos.union_all()
        interseccion = geom.intersection(union_vecinos)
        area_superpuesta = interseccion.area
    
    pct_superpuesto = (area_superpuesta / area_total * 100.0) if area_total > 0 else 0
    pct_descubierta = 100.0 - pct_superpuesto
    
    resultados.append({
        'ID_TEMP_SUS': row['ID_TEMP_SUS'],
        'area_total_m2': area_total,
        'area_superpuesta_m2': area_superpuesta,
        'area_descubierta_m2': area_total - area_superpuesta,
        'pct_superpuesto': round(pct_superpuesto, 1),
        'pct_descubierta': round(pct_descubierta, 1),
        'clues_asignada': row.get('CLUES_ASIGNADA', None),
        'consultorios': row.get('NUM_CONSULTORIOS', None)
    })
    
    if (i + 1) % 500 == 0 or i == total - 1:
        print(f"    Procesadas {i+1}/{total} casas... (t={time.time()-t0:.0f}s)")

print(f"  Tiempo total: {time.time()-t0:.1f}s")

stats = pd.DataFrame(resultados)

# ------------------------------------------------------------------
# 4. Clasificar
# ------------------------------------------------------------------
print("\n[4/5] Clasificando casas de salud...")

def clasificar(row):
    if row['pct_descubierta'] >= 10:
        return 'estrategica'
    elif row['pct_superpuesto'] >= 90:
        return 'redundante'
    else:
        return 'intermedia'

stats['tipo'] = stats.apply(clasificar, axis=1)

print(f"\n  Estratégicas: {(stats['tipo']=='estrategica').sum()}")
print(f"  Redundantes: {(stats['tipo']=='redundante').sum()}")
print(f"  Intermedias: {(stats['tipo']=='intermedia').sum()}")

# ------------------------------------------------------------------
# 5. Guardar
# ------------------------------------------------------------------
print("\n[5/5] Guardando resultados...")

os.makedirs('resultados_casas_salud', exist_ok=True)

stats.to_csv('resultados_casas_salud/casas_salud_clasificadas.csv', index=False)
print("  Guardado: resultados_casas_salud/casas_salud_clasificadas.csv")

resumen = stats.groupby('tipo').agg(
    n=('ID_TEMP_SUS', 'count'),
    area_total_km2=('area_total_m2', lambda x: x.sum() / 1e6),
    area_descubierta_km2=('area_descubierta_m2', lambda x: x.sum() / 1e6),
    area_superpuesta_km2=('area_superpuesta_m2', lambda x: x.sum() / 1e6),
    consultorios=('consultorios', 'sum')
).reset_index()
resumen.to_csv('resultados_casas_salud/resumen_por_tipo.csv', index=False)
print("  Guardado: resultados_casas_salud/resumen_por_tipo.csv")

if 'clues_asignada' in stats.columns:
    estrat_con_clues = stats[(stats['tipo'] == 'estrategica') & (stats['clues_asignada'].notna())]
    print(f"\n  Casas estratégicas con CLUES asignada: {len(estrat_con_clues)}")
    if len(estrat_con_clues) > 0:
        estrat_con_clues.to_csv('resultados_casas_salud/estrategicas_con_clues.csv', index=False)
        print("  Guardado: resultados_casas_salud/estrategicas_con_clues.csv")

print("\n✅ Análisis de casas de salud completado (con intersecciones reales).")
