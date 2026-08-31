import geopandas as gpd
import fiona

file_path = r"C:\Users\armando.gonzalez\Documents\Kimi\Workspaces\empalme de áreas de servicio\iso_upn_unido_15km.gpkg"

# List layers
print("Layers:", fiona.listlayers(file_path))

# Read first layer
gdf = gpd.read_file(file_path)
print("\n--- GeoDataFrame Info ---")
print(f"CRS: {gdf.crs}")
print(f"Rows: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"Dtypes:\n{gdf.dtypes}")
print(f"\nHead:\n{gdf.head()}")
print(f"\nGeometry type counts:\n{gdf.geometry.type.value_counts()}")
print(f"\nTotal bounds: {gdf.total_bounds}")
