import geopandas as gpd
import numpy as np

file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km.gpkg"
gdf = gpd.read_file(file_path)

# Muestra del 10% estratificada por CLUES para mantener representatividad
np.random.seed(42)
unique_clues = gdf['clues'].unique()
sample_clues = np.random.choice(unique_clues, size=int(len(unique_clues) * 0.10), replace=False)
gdf_sample = gdf[gdf['clues'].isin(sample_clues)].copy()

print(f"Total isocronas: {len(gdf)}")
print(f"CLUES únicos: {len(unique_clues)}")
print(f"Muestra CLUES: {len(sample_clues)}")
print(f"Isocronas en muestra: {len(gdf_sample)}")

# Guardar muestra
sample_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km_sample10.gpkg"
gdf_sample.to_file(sample_path, driver="GPKG")
print(f"Muestra guardada en: {sample_path}")
