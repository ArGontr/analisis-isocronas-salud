import re

with open('indispensabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar y reemplazar la seccion del mapa
old_block = """    center = [key_wgs.geometry.centroid.y.mean(), key_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')
    
    # Tile gratuito OpenStreetMap (sin API key)
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap', show=True).add_to(m)
    
    # Capa de isocronas coloreadas por indispensabilidad
    # Capa de isocronas coloreadas por indispensabilidad
    print("  Agregando capa de isocronas...")
    m = folium.Map(location=center, zoom_start=6, tiles='CartoDB positron')
    
    # Capa de isocronas coloreadas por indispensabilidad
    print("  Agregando capa de isocronas...")
    def style_isocrona(feature):"""

new_block = """    center = [key_wgs.geometry.centroid.y.mean(), key_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')
    
    # Capa de isocronas coloreadas por indispensabilidad
    print("  Agregando capa de isocronas...")
    def style_isocrona(feature):"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('indispensabilidad.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Archivo corregido exitosamente.')
else:
    print('Bloque no encontrado. Buscando con regex...')
    # Fallback con regex
    pattern = r"    center = \[key_wgs\.geometry\.centroid\.y\.mean\(\), key_wgs\.geometry\.centroid\.x\.mean\(\)\]\n    m = folium\.Map\(location=center, zoom_start=6, tiles='OpenStreetMap'\)\n.*?    def style_isocrona\(feature\):"
    replacement = """    center = [key_wgs.geometry.centroid.y.mean(), key_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')
    
    # Capa de isocronas coloreadas por indispensabilidad
    print("  Agregando capa de isocronas...")
    def style_isocrona(feature):"""
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    if new_content != content:
        with open('indispensabilidad.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Archivo corregido con regex.')
    else:
        print('No se pudo corregir.')
