import geopandas as gpd
import time

file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km.gpkg"
print("Leyendo archivo...")
t0 = time.time()
gdf = gpd.read_file(file_path)
print(f"  Cargado en {time.time()-t0:.1f}s: {len(gdf)} isocronas")

print("\nProbando simplificación preserve_topology=False, tol=200m...")
t0 = time.time()
gdf_s = gdf.copy()
gdf_s['geometry'] = gdf_s.geometry.simplify(tolerance=200, preserve_topology=False)
print(f"  Simplificado en {time.time()-t0:.1f}s")

print("\nProbando simplify preserve_topology=True, tol=200m...")
t0 = time.time()
gdf_s2 = gdf.copy()
gdf_s2['geometry'] = gdf_s2.geometry.simplify(tolerance=200, preserve_topology=True)
print(f"  Simplificado en {time.time()-t0:.1f}s")
