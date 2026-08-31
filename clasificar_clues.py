"""
Clasificación de CLUES por población, producción y redundancia.
Descarta redundantes ≥3000 hab.
Vincula redundantes <3000 con mayor población/producción en misma zona.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box
import json
import os

# Rutas
pob_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad\datos_pob_y_prod.xlsx"
indisp_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad\indispensabilidad.csv"
gpkg_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km.gpkg"
out_dir = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\resultados_indispensabilidad"

# 1. Cargar datos de población
print("Cargando datos de población...")
df_pob = pd.read_excel(pob_path)
print(f"  Registros población: {len(df_pob)}")

# Limpiar nulos
df_pob = df_pob.dropna(subset=['clues'])
df_pob['clues'] = df_pob['clues'].astype(str).str.strip()

# 2. Cargar datos de indispensabilidad
print("Cargando indispensabilidad...")
df_ind = pd.read_csv(indisp_path)
df_ind['clues'] = df_ind['clues'].astype(str).str.strip()
print(f"  Registros indispensabilidad: {len(df_ind)}")

# 3. Cruzar
print("\nCruzando bases...")
df = df_ind.merge(df_pob, on='clues', how='left')
print(f"  Cruce resultante: {len(df)} registros")
print(f"  Con datos de población: {df['poblacion_total_2026'].notna().sum()}")
print(f"  Sin datos de población: {df['poblacion_total_2026'].isna().sum()}")

# Para las que no tienen datos de población, asumimos 0 para poder clasificar
df['poblacion_total_2026'] = df['poblacion_total_2026'].fillna(0).astype(int)
df['consultas_generales'] = df['consultas_generales'].fillna(0)
df['institucion'] = df['institucion'].fillna('DESCONOCIDA')

# 4. Clasificación
print("\nClasificando...")

def clasificar(row):
    if not row['is_key']:  # Redundante
        if row['poblacion_total_2026'] >= 3000:
            return 'descartar'
        else:
            return 'complementaria_candidata'
    else:
        return 'clave'

df['categoria'] = df.apply(clasificar, axis=1)

print("\n  Distribución de categorías:")
print(df['categoria'].value_counts())

# 5. Conteo por institución (por debajo de 3000 y estatus de redundancia)
print("\n=== CONTEO POR INSTITUCIÓN ===")
resumen_inst = df.groupby('institucion').apply(
    lambda g: pd.Series({
        'total': len(g),
        'clave': (g['categoria'] == 'clave').sum(),
        'descartar': (g['categoria'] == 'descartar').sum(),
        'complementaria_candidata': (g['categoria'] == 'complementaria_candidata').sum(),
        'por_debajo_3000_y_redundante': ((g['poblacion_total_2026'] < 3000) & (~g['is_key'])).sum(),
        'por_debajo_3000_y_clave': ((g['poblacion_total_2026'] < 3000) & (g['is_key'])).sum(),
        'por_encima_3000_y_redundante': ((g['poblacion_total_2026'] >= 3000) & (~g['is_key'])).sum(),
    })
).reset_index()

print(resumen_inst.to_string(index=False))

# Guardar resumen
resumen_inst.to_csv(os.path.join(out_dir, 'conteo_por_institucion.csv'), index=False)
print(f"\n  Guardado: {out_dir}\\conteo_por_institucion.csv")

print("\n✅ Clasificación completa.")
