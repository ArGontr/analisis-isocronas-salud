import geopandas as gpd
import time

file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km_sample10.gpkg"
gdf = gpd.read_file(file_path)
print(f"Cargadas {len(gdf)} isocronas")
print(f"CRS: {gdf.crs}")

# Estadísticas de complejidad
gdf['n_coords'] = gdf.geometry.apply(lambda g: len(list(g.exterior.coords)) if g.geom_type == 'Polygon' else sum(len(p.exterior.coords) for p in g.geoms))
print(f"Vértices promedio: {gdf['n_coords'].mean():.0f}")
print(f"Vértices max: {gdf['n_coords'].max()}")
print(f"Vértices min: {gdf['n_coords'].min()}")

# Probar simplificación a diferentes tolerancias
for tol in [50, 100, 200, 500]:
    t0 = time.time()
    simp = gdf.copy()
    simp['geometry'] = simp.geometry.simplify(tolerance=tol, preserve_topology=True)
    elapsed = time.time() - t0
    simp['n_coords'] = simp.geometry.apply(lambda g: len(list(g.exterior.coords)) if g.geom_type == 'Polygon' else sum(len(p.exterior.coords) for p in g.geoms))
    print(f"Tol={tol}m: {simp['n_coords'].mean():.0f} vértices promedio, tiempo={elapsed:.2f}s")
