import sys
print("Python:", sys.version)
try:
    import geopandas as gpd
    print("geopandas:", gpd.__version__)
except Exception as e:
    print("geopandas error:", e)
try:
    import fiona
    print("fiona:", fiona.__version__)
except Exception as e:
    print("fiona error:", e)
try:
    import shapely
    print("shapely:", shapely.__version__)
except Exception as e:
    print("shapely error:", e)
try:
    import pyproj
    print("pyproj:", pyproj.__version__)
except Exception as e:
    print("pyproj error:", e)
