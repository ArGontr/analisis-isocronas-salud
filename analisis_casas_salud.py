"""
"""
"""
Análisis de casas de salud: identificar redundantes vs estratégicas.

Usa buffers de 10 km como pseudo-isocronas y las cruza con el grid
existente para ver qué tipo de celdas cubren.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box, Point
import matplotlib.pyplot as plt
import os
import time

# ------------------------------------------------------------------
# 1. Cargar datos
# ------------------------------------------------------------------
print("[1/6] Cargando datos...")

# Isocronas existentes
gdf_iso = gpd.read_file('iso_upn_unido_15km.gpkg')
print(f"  Isocronas existentes: {len(gdf_iso)}")

# Casas de salud
casas = pd.read_excel('casas_de_salud.xlsx')
print(f"  Casas de salud: {len(casas)}")

# Cruzar con CLUES asignadas (653 registros)
if os.path.exists(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx'):
    cruce = pd.read_excel(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx')
    casas = casas.merge(cruce[['ID_TEMP_SUS', 'CLUES_ASIGNADA']], on='ID_TEMP_SUS', how='left')
    print(f"  Casas con CLUES asignada: {casas['CLUES_ASIGNADA'].notna().sum()}")

# ------------------------------------------------------------------
# 2. Crear geometrías de casas de salud (buffer 10 km)
# ------------------------------------------------------------------
print("\n[2/6] Creando buffers de 10 km para casas de salud...")

# Crear GeoDataFrame de puntos en WGS84, luego reproyectar a EPSG:8858
casas_gdf = gpd.GeoDataFrame(
    casas,
    geometry=[Point(lon, lat) for lat, lon in zip(casas['LAT'], casas['LON'])],
    crs='EPSG:4326'
).to_crs('EPSG:8858')

# Buffer de 10 km
casas_gdf['geometry'] = casas_gdf.geometry.buffer(10000)
casas_gdf['area_km2'] = casas_gdf.geometry.area / 1e6
print(f"  Área promedio por buffer: {casas_gdf['area_km2'].mean():.0f} km²")

# ------------------------------------------------------------------
# 3. Recrear fishnet y contar isocronas por celda
# ------------------------------------------------------------------
print("\n[3/6] Creando grid y contando isocronas por celda...")

cell_size_m = 10000.0
bounds = gdf_iso.total_bounds
xmin, ymin, xmax, ymax = bounds
xmin = np.floor(xmin / cell_size_m) * cell_size_m
ymin = np.floor(ymin / cell_size_m) * cell_size_m
xmax = np.ceil(xmax / cell_size_m) * cell_size_m
ymax = np.ceil(ymax / cell_size_m) * cell_size_m
cols = int(np.ceil((xmax - xmin) / cell_size_m))
rows = int(np.ceil((ymax - ymin) / cell_size_m))
print(f"  Grid: {cols} x {rows} = {cols*rows} celdas")

polygons = []
ids = []
for i in range(cols):
    for j in range(rows):
        x0 = xmin + i * cell_size_m
        y0 = ymin + j * cell_size_m
        polygons.append(box(x0, y0, x0 + cell_size_m, y0 + cell_size_m))
        ids.append(f"{i}_{j}")

fishnet = gpd.GeoDataFrame({'cell_id': ids, 'geometry': polygons}, crs='EPSG:8858')

# Spatial join: isocronas -> celdas
t0 = time.time()
joined_iso = gpd.sjoin(
    gdf_iso[['clues', 'geometry']],
    fishnet[['cell_id', 'geometry']],
    how='inner', predicate='intersects'
)
print(f"  Pares isocrona-celda: {len(joined_iso)}. Tiempo: {time.time()-t0:.1f}s")

# Contar isocronas por celda
cell_counts = joined_iso.groupby('cell_id').size().reset_index(name='n_isocronas')
fishnet = fishnet.merge(cell_counts, on='cell_id', how='left')
fishnet['n_isocronas'] = fishnet['n_isocronas'].fillna(0).astype(int)

print(f"  Celdas con 0 isocronas: {(fishnet['n_isocronas']==0).sum()}")
print(f"  Celdas con 1 isocrona (vulnerables): {(fishnet['n_isocronas']==1).sum()}")
print(f"  Celdas con ≥2 isocronas (redundantes): {(fishnet['n_isocronas']>=2).sum()}")

# ------------------------------------------------------------------
# 4. Spatial join: casas de salud -> celdas
# ------------------------------------------------------------------
print("\n[4/6] Cruzando casas de salud con grid...")

t0 = time.time()
joined_casas = gpd.sjoin(
    casas_gdf[['ID_TEMP_SUS', 'CLUES_ASIGNADA', 'NUM_CONSULTORIOS', 'geometry']],
    fishnet[['cell_id', 'n_isocronas', 'geometry']],
    how='inner', predicate='intersects'
)
print(f"  Pares casa-celda: {len(joined_casas)}. Tiempo: {time.time()-t0:.1f}s")

# ------------------------------------------------------------------
# 5. Clasificar cada casa de salud
# ------------------------------------------------------------------
print("\n[5/6] Clasificando casas de salud...")

stats = joined_casas.groupby('ID_TEMP_SUS').agg(
    total_celdas=('cell_id', 'nunique'),
    celdas_descubiertas=('n_isocronas', lambda x: int((x == 0).sum())),
    celdas_vulnerables=('n_isocronas', lambda x: int((x == 1).sum())),
    celdas_redundantes=('n_isocronas', lambda x: int((x >= 2).sum())),
    clues_asignada=('CLUES_ASIGNADA', 'first'),
    consultorios=('NUM_CONSULTORIOS', 'first')
).reset_index()

# Cálculo de porcentajes
stats['pct_descubierta'] = (stats['celdas_descubiertas'] / stats['total_celdas'] * 100).round(1)
stats['pct_vulnerable'] = (stats['celdas_vulnerables'] / stats['total_celdas'] * 100).round(1)
stats['pct_redundante'] = (stats['celdas_redundantes'] / stats['total_celdas'] * 100).round(1)

# Clasificación
def clasificar(row):
    if row['celdas_descubiertas'] > 0 or row['celdas_vulnerables'] > 0:
        return 'estrategica'
    elif row['pct_redundante'] >= 90:
        return 'redundante'
    else:
        return 'intermedia'

stats['tipo'] = stats.apply(clasificar, axis=1)

print(f"\n  Estratégicas: {(stats['tipo']=='estrategica').sum()}")
print(f"  Redundantes: {(stats['tipo']=='redundante').sum()}")
print(f"  Intermedias: {(stats['tipo']=='intermedia').sum()}")

# ------------------------------------------------------------------
# 6. Guardar resultados
# ------------------------------------------------------------------
print("\n[6/6] Guardando resultados...")

os.makedirs('resultados_casas_salud', exist_ok=True)

# CSV principal
stats.to_csv('resultados_casas_salud/casas_salud_clasificadas.csv', index=False)
print("  Guardado: resultados_casas_salud/casas_salud_clasificadas.csv")

# Resumen por tipo
resumen = stats.groupby('tipo').agg(
    n=('ID_TEMP_SUS', 'count'),
    celdas_total=('total_celdas', 'sum'),
    celdas_estrategicas=('celdas_vulnerables', 'sum'),
    celdas_nuevas=('celdas_descubiertas', 'sum'),
    consultorios=('consultorios', 'sum')
).reset_index()
resumen.to_csv('resultados_casas_salud/resumen_por_tipo.csv', index=False)
print("  Guardado: resultados_casas_salud/resumen_por_tipo.csv")

# Casas estratégicas con CLUES asignada
if 'clues_asignada' in stats.columns:
    estrat_con_clues = stats[(stats['tipo'] == 'estrategica') & (stats['clues_asignada'].notna())]
    print(f"\n  Casas estratégicas con CLUES asignada: {len(estrat_con_clues)}")
    if len(estrat_con_clues) > 0:
        estrat_con_clues.to_csv('resultados_casas_salud/estrategicas_con_clues.csv', index=False)
        print("  Guardado: resultados_casas_salud/estrategicas_con_clues.csv")

print("\n✅ Análisis de casas de salud completado.")
