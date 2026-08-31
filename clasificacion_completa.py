"""
Clasificación completa de CLUES con emparejamiento por zona compartida.

Flujo:
1. Cargar isocronas, población e indispensabilidad.
2. Crear grid y spatial join para identificar CLUES que comparten celdas.
3. Clasificar: clave / descartar (redundante + pob>=3000) / complementaria (redundante + pob<3000).
4. Para cada complementaria, encontrar la CLUES de MAYOR población que comparta celda.
5. Generar base final y conteo por institución.

Requiere: geopandas, pandas, numpy, shapely
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box
import json
import os
import time

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
POB_PATH = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad\datos_pob_y_prod.xlsx"
INDISP_PATH = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad\indispensabilidad.csv"
GPKG_PATH = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km.gpkg"
OUT_DIR = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad"

CELL_SIZE_M = 10000.0
SIMPLIFY_M = 200.0
POB_UMBRAL = 3000

# ─── 1. CARGAR DATOS ─────────────────────────────────────────────────────────
print("[1/6] Cargando datos...")
t0 = time.time()

# Población
df_pob = pd.read_excel(POB_PATH)
df_pob = df_pob.dropna(subset=['clues'])
df_pob['clues'] = df_pob['clues'].astype(str).str.strip()

# Indispensabilidad
df_ind = pd.read_csv(INDISP_PATH)
df_ind['clues'] = df_ind['clues'].astype(str).str.strip()

# Isocronas (solo geometría y clues)
print("  Leyendo isocronas (solo clues + geom)...")
gdf_iso = gpd.read_file(GPKG_PATH, columns=['clues'])
gdf_iso['clues'] = gdf_iso['clues'].astype(str).str.strip()

# Simplificar para velocidad
print(f"  Simplificando geometrías ({SIMPLIFY_M}m)...")
gdf_iso['geometry'] = gdf_iso.geometry.simplify(tolerance=SIMPLIFY_M, preserve_topology=False)

print(f"  Datos cargados en {time.time()-t0:.1f}s")
print(f"    Población: {len(df_pob)} | Indispensabilidad: {len(df_ind)} | Isocronas: {len(gdf_iso)}")

# ─── 2. CRUZAR POBLACIÓN + INDISPENSABILIDAD ─────────────────────────────────
print("\n[2/6] Cruzando población con indispensabilidad...")
df = df_ind.merge(df_pob, on='clues', how='left')

# Llenar nulos
df['poblacion_total_2026'] = df['poblacion_total_2026'].fillna(0).astype(int)
df['poblacion_sin_derechohabiencia_2026'] = df['poblacion_sin_derechohabiencia_2026'].fillna(0).astype(int)
df['poblacion_con_derechohabiencia_2026'] = df['poblacion_con_derechohabiencia_2026'].fillna(0).astype(int)
df['consultas_generales'] = df['consultas_generales'].fillna(0)
df['institucion'] = df['institucion'].fillna('DESCONOCIDA')

# ─── 3. CLASIFICAR ───────────────────────────────────────────────────────────
print("\n[3/6] Clasificando...")

def clasificar(row):
    if row['is_key']:
        return 'clave'
    if row['poblacion_total_2026'] >= POB_UMBRAL:
        return 'descartar'
    return 'complementaria'

df['categoria'] = df.apply(clasificar, axis=1)

print("  Distribución:")
for cat, cnt in df['categoria'].value_counts().items():
    print(f"    {cat}: {cnt}")

# ─── 4. GRID + SPATIAL JOIN (solo para emparejamiento) ───────────────────────
print("\n[4/6] Creando grid y spatial join para emparejamiento...")
t0 = time.time()

# Crear fishnet sobre bounds de isocronas
bounds = list(gdf_iso.total_bounds)
xmin, ymin, xmax, ymax = bounds
xmin = np.floor(xmin / CELL_SIZE_M) * CELL_SIZE_M
ymin = np.floor(ymin / CELL_SIZE_M) * CELL_SIZE_M
xmax = np.ceil(xmax / CELL_SIZE_M) * CELL_SIZE_M
ymax = np.ceil(ymax / CELL_SIZE_M) * CELL_SIZE_M
cols = int(np.ceil((xmax - xmin) / CELL_SIZE_M))
rows = int(np.ceil((ymax - ymin) / CELL_SIZE_M))

polygons = []
ids = []
for i in range(cols):
    for j in range(rows):
        x0 = xmin + i * CELL_SIZE_M
        y0 = ymin + j * CELL_SIZE_M
        polygons.append(box(x0, y0, x0 + CELL_SIZE_M, y0 + CELL_SIZE_M))
        ids.append(f"{i}_{j}")

fishnet = gpd.GeoDataFrame({'cell_id': ids, 'geometry': polygons}, crs=gdf_iso.crs)
print(f"  Grid: {cols}x{rows} = {len(fishnet)} celdas")

# Spatial join: isocronas -> celdas
joined = gpd.sjoin(
    gdf_iso[['clues', 'geometry']],
    fishnet[['cell_id', 'geometry']],
    how='inner', predicate='intersects'
)
print(f"  Pares isocrona-celda: {len(joined)}")
print(f"  Grid+join en {time.time()-t0:.1f}s")

# ─── 5. EMPAREJAR COMPLEMENTARIAS CON MAYORES ────────────────────────────────
print("\n[5/6] Emparejando complementarias con CLUES de mayor población...")
t0 = time.time()

# Crear diccionario: cell_id -> lista de clues que la cubren
cell_to_clues = joined.groupby('cell_id')['clues'].apply(set).to_dict()

# Crear diccionario: clues -> datos de población (para lookup rápido)
clues_data = df.set_index('clues')[['poblacion_total_2026', 'consultas_generales', 'categoria', 'institucion']].to_dict('index')

# Para cada complementaria, encontrar vecinos que compartan celda
complementarias = df[df['categoria'] == 'complementaria']['clues'].tolist()
print(f"  Complementarias a emparejar: {len(complementarias)}")

vinculos = []
sin_vinculo = 0

for clues_menor in complementarias:
    # Celdas que cubre esta CLUES
    celdas_menor = set(joined[joined['clues'] == clues_menor]['cell_id'])
    
    # Vecinos = todas las CLUES que cubren esas celdas (excluyéndose a sí misma)
    vecinos = set()
    for celda in celdas_menor:
        vecinos.update(cell_to_clues.get(celda, set()))
    vecinos.discard(clues_menor)
    
    # Filtrar vecinos que existen en la base de población
    vecinos_validos = [v for v in vecinos if v in clues_data]
    
    if not vecinos_validos:
        sin_vinculo += 1
        vinculos.append({
            'clues_complementaria': clues_menor,
            'clues_vinculada': None,
            'pob_complementaria': clues_data[clues_menor]['poblacion_total_2026'],
            'pob_vinculada': None,
            'consultas_complementaria': clues_data[clues_menor]['consultas_generales'],
            'consultas_vinculada': None,
            'inst_vinculada': None,
            'motivo': 'sin_vecinos_en_base'
        })
        continue
    
    # Seleccionar vecino con MAYOR población (tie-breaker: consultas)
    mejor = max(vecinos_validos, key=lambda v: (
        clues_data[v]['poblacion_total_2026'],
        clues_data[v]['consultas_generales']
    ))
    
    vinculos.append({
        'clues_complementaria': clues_menor,
        'clues_vinculada': mejor,
        'pob_complementaria': clues_data[clues_menor]['poblacion_total_2026'],
        'pob_vinculada': clues_data[mejor]['poblacion_total_2026'],
        'consultas_complementaria': clues_data[clues_menor]['consultas_generales'],
        'consultas_vinculada': clues_data[mejor]['consultas_generales'],
        'inst_vinculada': clues_data[mejor]['institucion'],
        'motivo': 'mayor_poblacion_zona_comun'
    })

print(f"  Emparejadas: {len(vinculos) - sin_vinculo} | Sin vínculo: {sin_vinculo}")
print(f"  Tiempo: {time.time()-t0:.1f}s")

# Crear DataFrame de vínculos
df_vinculos = pd.DataFrame(vinculos)

# Agregar columna de vínculo a la base principal
df = df.merge(
    df_vinculos[['clues_complementaria', 'clues_vinculada', 'pob_vinculada', 'consultas_vinculada', 'inst_vinculada', 'motivo']].rename(
        columns={'clues_complementaria': 'clues'}
    ),
    on='clues', how='left'
)

# ─── 6. EXPORTAR RESULTADOS ──────────────────────────────────────────────────
print("\n[6/6] Exportando...")

# Base completa categorizada
cols_export = [
    'clues', 'institucion', 'categoria',
    'poblacion_total_2026', 'poblacion_sin_derechohabiencia_2026',
    'poblacion_con_derechohabiencia_2026', 'consultas_generales',
    'is_key', 'pct_exclusiva', 'area_exclusiva_km2',
    'clues_vinculada', 'pob_vinculada', 'consultas_vinculada', 'inst_vinculada', 'motivo'
]
# Solo columnas que existan
cols_export = [c for c in cols_export if c in df.columns]
df[cols_export].to_csv(os.path.join(OUT_DIR, 'base_categorizada.csv'), index=False)
print(f"  Base categorizada: {OUT_DIR}\\base_categorizada.csv")

# Resumen por institución
resumen_inst = df.groupby('institucion').apply(
    lambda g: pd.Series({
        'total': len(g),
        'clave': (g['categoria'] == 'clave').sum(),
        'descartar': (g['categoria'] == 'descartar').sum(),
        'complementaria': (g['categoria'] == 'complementaria').sum(),
        'por_debajo_3000_redundante': ((g['poblacion_total_2026'] < 3000) & (~g['is_key'])).sum(),
        'por_encima_3000_redundante': ((g['poblacion_total_2026'] >= 3000) & (~g['is_key'])).sum(),
        'complementarias_vinculadas': g['clues_vinculada'].notna().sum(),
        'complementarias_sin_vinculo': ((g['categoria'] == 'complementaria') & (g['clues_vinculada'].isna())).sum(),
    })
).reset_index()

resumen_inst.to_csv(os.path.join(OUT_DIR, 'conteo_por_institucion.csv'), index=False)
print(f"  Conteo por institución: {OUT_DIR}\\conteo_por_institucion.csv")

# Vínculos detallados
df_vinculos.to_csv(os.path.join(OUT_DIR, 'vinculos_complementarias.csv'), index=False)
print(f"  Vínculos: {OUT_DIR}\\vinculos_complementarias.csv")

# Mostrar resumen
print("\n=== RESUMEN POR INSTITUCIÓN ===")
print(resumen_inst.to_string(index=False))

print(f"\n=== TOP 10 VÍNCULOS (complementaria -> vinculada) ===")
print(df_vinculos[df_vinculos['clues_vinculada'].notna()].head(10).to_string(index=False))

print("\n✅ Proceso completado.")
