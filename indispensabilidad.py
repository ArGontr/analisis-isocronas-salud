"""
Análisis de isocronas: identificación de isocronas clave/indispensables.

CORRECCIÓN CRÍTICA v2:
- El grid/fishnet ya NO se usa para determinar redundancia o indispensabilidad.
- Se calculan intersecciones REALES entre isocronas mediante overlay espacial.
- El grid se conserva ÚNICAMENTE para identificar desiertos (celdas sin cobertura).

Requiere: geopandas, shapely, matplotlib, numpy, folium, branca
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import matplotlib.pyplot as plt
import argparse
import json
import os
import time
import folium
from paleta_institucional import *


def simplify_geoms(gdf, tolerance_m=200.0):
    """Simplifica geometrías RÁPIDO."""
    gdf = gdf.copy()
    gdf['geometry'] = gdf.geometry.simplify(tolerance=tolerance_m, preserve_topology=False)
    return gdf


def create_fishnet(bounds, cell_size_m=10000.0):
    """Crea un grid regular sobre los bounds dados."""
    xmin, ymin, xmax, ymax = bounds
    xmin = np.floor(xmin / cell_size_m) * cell_size_m
    ymin = np.floor(ymin / cell_size_m) * cell_size_m
    xmax = np.ceil(xmax / cell_size_m) * cell_size_m
    ymax = np.ceil(ymax / cell_size_m) * cell_size_m
    
    cols = int(np.ceil((xmax - xmin) / cell_size_m))
    rows = int(np.ceil((ymax - ymin) / cell_size_m))
    
    print(f"    Grid: {cols} x {rows} = {cols*rows} celdas ({cell_size_m/1000:.0f}km)")
    
    polygons = []
    ids = []
    for i in range(cols):
        for j in range(rows):
            x0 = xmin + i * cell_size_m
            y0 = ymin + j * cell_size_m
            x1 = x0 + cell_size_m
            y1 = y0 + cell_size_m
            polygons.append(box(x0, y0, x1, y1))
            ids.append(f"{i}_{j}")
    
    return gpd.GeoDataFrame({'cell_id': ids, 'geometry': polygons}, crs='EPSG:8858')


def calcular_indispensabilidad_real(gdf, cell_size_m=10000.0):
    """
    Analiza qué isocronas son clave/indispensables usando intersecciones REALES.
    
    El grid solo se usa para desiertos. Para indispensabilidad se usa overlay espacial.
    """
    gdf = gdf.copy()
    gdf['_iso_idx'] = range(len(gdf))
    gdf['area_km2'] = gdf.geometry.area / 1e6
    
    # =====================================================================
    # 1. GRID — solo para desiertos (celdas sin cobertura)
    # =====================================================================
    print(f"  Creando grid para desiertos...")
    t0 = time.time()
    fishnet = create_fishnet(gdf.total_bounds, cell_size_m=cell_size_m)
    
    joined_grid = gpd.sjoin(
        gdf[['_iso_idx', 'clues', 'geometry']],
        fishnet[['cell_id', 'geometry']],
        how='inner', predicate='intersects'
    )
    cells_with_data = set(joined_grid['cell_id'].unique())
    desert_cells = fishnet[~fishnet['cell_id'].isin(cells_with_data)].copy()
    desert_cells['area_km2'] = desert_cells.geometry.area / 1e6
    print(f"    Celdas desierto: {len(desert_cells)}. Tiempo: {time.time()-t0:.1f}s")
    
    # =====================================================================
    # 2. INDISPENSABILIDAD REAL — overlay entre isocronas
    # =====================================================================
    print("  Calculando intersecciones reales entre isocronas...")
    t0 = time.time()
    
    # Encontrar pares de isocronas que REALMENTE se intersectan
    pares = gpd.sjoin(
        gdf[['_iso_idx', 'geometry']],
        gdf[['_iso_idx', 'geometry']].rename(columns={'_iso_idx': '_iso_idx_other'}),
        how='inner', predicate='intersects'
    )
    # Eliminar auto-intersecciones
    pares = pares[pares['_iso_idx'] != pares['_iso_idx_other']]
    print(f"    Pares que se intersectan realmente: {len(pares)}. Tiempo: {time.time()-t0:.1f}s")
    
    # Para cada isocrona, calcular área superpuesta con otras isocronas
    print("  Calculando áreas de superposición real...")
    t0 = time.time()
    
    # Preparar resultado
    resultados = []
    total = len(gdf)
    
    for i, row in gdf.iterrows():
        iso_idx = row['_iso_idx']
        geom = row.geometry
        area_total = geom.area
        
        # Encontrar vecinos reales de esta isocrona
        vecinos = pares[pares['_iso_idx'] == iso_idx]['_iso_idx_other'].unique()
        
        if len(vecinos) == 0:
            # Sin vecinos reales: TODA el área es exclusiva
            area_exclusiva = area_total
            area_superpuesta = 0
        else:
            # Unir geometrías de vecinos reales
            geoms_vecinos = gdf[gdf['_iso_idx'].isin(vecinos)].geometry
            union_vecinos = geoms_vecinos.unary_union
            
            # Área exclusiva = isocrona - unión de vecinos
            exclusive = geom.difference(union_vecinos)
            area_exclusiva = exclusive.area
            area_superpuesta = area_total - area_exclusiva
        
        resultados.append({
            '_iso_idx': iso_idx,
            'area_total_m2': area_total,
            'area_exclusiva_m2': area_exclusiva,
            'area_superpuesta_m2': area_superpuesta,
            'pct_exclusiva': (area_exclusiva / area_total * 100.0) if area_total > 0 else 0,
            'is_key': area_exclusiva > 0,
            'n_vecinos_reales': len(vecinos)
        })
        
        if (i + 1) % 100 == 0 or i == total - 1:
            print(f"    Procesadas {i+1}/{total} isocronas...")
    
    result_df = pd.DataFrame(resultados)
    gdf = gdf.merge(result_df, on='_iso_idx', how='left')
    print(f"    Tiempo total: {time.time()-t0:.1f}s")
    
    # =====================================================================
    # 3. Zonas vulnerables: celdas del grid cubiertas por UNA SOLA isocrona
    #    CORRECCIÓN: verificar que solo una isocrona REALMENTE intersecta la celda
    # =====================================================================
    print("  Identificando zonas vulnerables (cobertura única REAL)...")
    t0 = time.time()
    
    # Para cada celda con datos, contar isocronas que REALMENTE la intersectan
    cell_real_counts = joined_grid.groupby('cell_id')['_iso_idx'].nunique().reset_index(name='n_isocronas_real')
    
    # Celdas vulnerables = las que solo 1 isocrona intersecta realmente
    vulnerable_cells_ids = cell_real_counts[cell_real_counts['n_isocronas_real'] == 1]['cell_id']
    vulnerable_cells = fishnet[fishnet['cell_id'].isin(vulnerable_cells_ids)].copy()
    vulnerable_cells['area_km2'] = vulnerable_cells.geometry.area / 1e6
    
    # Merge con clues responsable
    vulnerable_joined = joined_grid[joined_grid['cell_id'].isin(vulnerable_cells_ids)][['cell_id', 'clues']].drop_duplicates()
    vulnerable_cells = vulnerable_cells.merge(vulnerable_joined, on='cell_id', how='left')
    
    print(f"    Celdas vulnerables: {len(vulnerable_cells)}. Tiempo: {time.time()-t0:.1f}s")
    
    # Zonas de alta redundancia: celdas con ≥5 isocronas reales
    high_red_ids = cell_real_counts[cell_real_counts['n_isocronas_real'] >= 5]['cell_id']
    high_red = fishnet[fishnet['cell_id'].isin(high_red_ids)].copy()
    high_red['area_km2'] = high_red.geometry.area / 1e6
    
    key_df = gdf[['clues', 'area_km2', 'area_total_m2', 'area_exclusiva_m2',
                  'area_superpuesta_m2', 'pct_exclusiva', 'is_key', 'n_vecinos_reales', 'geometry']].copy()
    
    return key_df, vulnerable_cells, high_red, fishnet, desert_cells


def generate_static_map(gdf, key_df, vulnerable_gdf, output_dir):
    """Genera visualización estática."""
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    
    ax = axes[0]
    gdf.boundary.plot(ax=ax, color='lightgray', linewidth=0.2, alpha=0.3)
    key = key_df[key_df['is_key'] == True]
    non_key = key_df[key_df['is_key'] == False]
    if not key.empty:
        key.plot(ax=ax, color=ALERTA, alpha=0.5, label=f'Clave (n={len(key)})')
    if not non_key.empty:
        non_key.plot(ax=ax, color=NEUTRO, alpha=0.2, label=f'Redundante (n={len(non_key)})')
    ax.set_title('Isocronas clave (tienen cobertura exclusiva REAL)', color=TEXTO)
    ax.legend(); ax.set_axis_off()
    
    ax = axes[1]
    gdf.plot(ax=ax, color=EXITO, alpha=0.15, label='Isocronas')
    if not vulnerable_gdf.empty:
        vulnerable_gdf.plot(ax=ax, color=ALERTA, alpha=0.6, label=f'Zonas vulnerables (n={len(vulnerable_gdf)})')
    ax.set_title('Zonas que quedarían descubiertas si se elimina una isocrona', color=TEXTO)
    ax.legend(); ax.set_axis_off()
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, 'indispensabilidad.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Mapa estático guardado en: {out_path}")


def generate_interactive_report(key_df, vulnerable_gdf, high_red, desert_cells, output_dir, summary):
    """Genera reporte HTML interactivo con folium."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("  Convirtiendo a WGS84 para mapa interactivo...")
    key_wgs = key_df.to_crs('EPSG:4326')
    vuln_wgs = vulnerable_gdf.to_crs('EPSG:4326') if not vulnerable_gdf.empty else gpd.GeoDataFrame(crs='EPSG:4326')
    high_wgs = high_red.to_crs('EPSG:4326') if not high_red.empty else gpd.GeoDataFrame(crs='EPSG:4326')
    desert_wgs = desert_cells.to_crs('EPSG:4326') if not desert_cells.empty else gpd.GeoDataFrame(crs='EPSG:4326')
    
    center = [key_wgs.geometry.centroid.y.mean(), key_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')
    
    print("  Agregando capa de isocronas...")
    def style_isocrona(feature):
        is_key = feature['properties']['is_key']
        pct = feature['properties']['pct_exclusiva']
        if is_key:
            if pct >= 50:
                return {'fillColor': BORGONA_OSCURO, 'color': NEGRO, 'weight': 0.5, 'fillOpacity': 0.6}
            elif pct >= 25:
                return {'fillColor': VINO, 'color': NEGRO, 'weight': 0.5, 'fillOpacity': 0.5}
            else:
                return {'fillColor': AMARILLO_PRECAUCION, 'color': NEGRO, 'weight': 0.5, 'fillOpacity': 0.4}
        else:
            return {'fillColor': GRIS, 'color': NEGRO, 'weight': 0.3, 'fillOpacity': 0.2}
    
    key_wgs['geometry'] = key_wgs.geometry.simplify(tolerance=0.01, preserve_topology=False)
    
    folium.GeoJson(
        key_wgs[['clues', 'area_km2', 'pct_exclusiva', 'area_exclusiva_m2', 'area_superpuesta_m2', 'is_key', 'geometry']],
        name='Isocronas (por indispensabilidad)',
        style_function=style_isocrona,
        tooltip=folium.GeoJsonTooltip(
            fields=['clues', 'area_km2', 'pct_exclusiva', 'area_exclusiva_m2', 'area_superpuesta_m2', 'is_key'],
            aliases=['CLUES:', 'Área (km²):', '% Exclusiva:', 'Área exclusiva (km²):', 'Área superpuesta (km²):', 'Es clave:'],
            localize=True
        ),
    ).add_to(m)
    
    if not vuln_wgs.empty:
        print("  Agregando capa de zonas vulnerables...")
        vuln_wgs['geometry'] = vuln_wgs.geometry.simplify(tolerance=0.01, preserve_topology=False)
        folium.GeoJson(
            vuln_wgs[['cell_id', 'clues', 'area_km2', 'geometry']],
            name='Zonas vulnerables (solo 1 isocrona real)',
            style_function=lambda f: {
                'fillColor': ALERTA,
                'color': BORGONA_OSCURO,
                'weight': 0.5,
                'fillOpacity': 0.7,
            },
            tooltip=folium.GeoJsonTooltip(fields=['cell_id', 'clues', 'area_km2'],
                                          aliases=['Celda:', 'CLUES responsable:', 'Área (km²):']),
            show=True
        ).add_to(m)
    
    if not high_wgs.empty:
        print("  Agregando capa de alta redundancia...")
        high_wgs['geometry'] = high_wgs.geometry.simplify(tolerance=0.01, preserve_topology=False)
        folium.GeoJson(
            high_wgs[['cell_id', 'area_km2', 'geometry']],
            name='Alta redundancia (≥5 isocronas reales)',
            style_function=lambda f: {
                'fillColor': VERDE_OSCURO,
                'color': VERDE_PETROLEO,
                'weight': 0.5,
                'fillOpacity': 0.4,
            },
            tooltip=folium.GeoJsonTooltip(fields=['cell_id', 'area_km2'],
                                          aliases=['Celda:', 'Área (km²):']),
            show=False
        ).add_to(m)
    
    if not desert_wgs.empty:
        print("  Agregando capa de desiertos...")
        desert_wgs['geometry'] = desert_wgs.geometry.simplify(tolerance=0.01, preserve_topology=False)
        folium.GeoJson(
            desert_wgs[['cell_id', 'area_km2', 'geometry']],
            name='Desiertos de atención',
            style_function=lambda f: {
                'fillColor': AMARILLO_PRECAUCION,
                'color': AMARILLO_MOSTAZA,
                'weight': 0.5,
                'fillOpacity': 0.5,
            },
            tooltip=folium.GeoJsonTooltip(fields=['cell_id', 'area_km2'],
                                          aliases=['Celda:', 'Área (km²):']),
            show=False
        ).add_to(m)
    
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 340px;
                background-color: white; border: 2px solid {NEGRO};
                border-radius: 8px; padding: 12px; font-size: 13px;
                box-shadow: 3px 3px 10px rgba(0,0,0,0.3);
                z-index: 9999;">
        <h4 style="margin-top:0; color:{NEGRO};">🔑 Indispensabilidad (Intersecciones Reales)</h4>
        <b>Total isocronas:</b> {summary['total_isocronas']:,}<br>
        <b>Isocronas clave:</b> <span style="color:{BORGONA_OSCURO};">{summary['isocronas_clave']:,} ({summary['pct_clave']}%)</span><br>
        <b>Redundantes:</b> <span style="color:{NEUTRO};">{summary['isocronas_redundantes']:,}</span><br>
        <b>Zonas vulnerables:</b> {summary['zonas_vulnerables']:,} celdas<br>
        <b>Área vulnerable:</b> {summary['area_vulnerable_km2']:,.0f} km²<br>
        <b>Desiertos:</b> {summary['zonas_desiertos']:,} celdas<br>
        <hr style="margin:8px 0;">
        <span style="display:inline-block;width:12px;height:12px;background:{BORGONA_OSCURO};opacity:0.6;"></span> Clave (≥50% exclusiva)<br>
        <span style="display:inline-block;width:12px;height:12px;background:{VINO};opacity:0.6;"></span> Clave (25-50% exclusiva)<br>
        <span style="display:inline-block;width:12px;height:12px;background:{AMARILLO_PRECAUCION};opacity:0.6;"></span> Clave (&lt;25% exclusiva)<br>
        <span style="display:inline-block;width:12px;height:12px;background:{ALERTA};opacity:0.6;"></span> Zona vulnerable (1 isocrona real)<br>
        <span style="display:inline-block;width:12px;height:12px;background:{AMARILLO_PRECAUCION};opacity:0.6;"></span> Desierto (sin cobertura)<br>
        <span style="display:inline-block;width:12px;height:12px;background:{GRIS};opacity:0.6;"></span> Redundante (0% exclusiva)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50%; transform: translateX(-50%);
                background-color: rgba(255,255,255,0.9);
                border: 2px solid {NEGRO}; border-radius: 8px;
                padding: 10px 20px; font-size: 16px; font-weight: bold;
                z-index: 9999; color: {NEGRO};">
        Isocronas Clave / Indispensables (Intersecciones Reales)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    folium.LayerControl().add_to(m)
    
    out_path = os.path.join(output_dir, 'reporte_indispensabilidad.html')
    m.save(out_path)
    print(f"  Reporte interactivo guardado en: {out_path}")
    return out_path


def export_results(key_df, vulnerable_gdf, output_dir):
    """Exporta resultados."""
    os.makedirs(output_dir, exist_ok=True)
    key_df[['clues', 'area_km2', 'area_total_m2', 'area_exclusiva_m2', 
            'area_superpuesta_m2', 'pct_exclusiva', 'is_key', 'n_vecinos_reales', 'geometry']].to_file(
        os.path.join(output_dir, 'indispensabilidad.gpkg'), driver='GPKG')
    key_df[['clues', 'area_km2', 'area_total_m2', 'area_exclusiva_m2', 
            'area_superpuesta_m2', 'pct_exclusiva', 'is_key', 'n_vecinos_reales']].to_csv(
        os.path.join(output_dir, 'indispensabilidad.csv'), index=False)
    if not vulnerable_gdf.empty:
        vulnerable_gdf.to_file(os.path.join(output_dir, 'zonas_vulnerables.gpkg'), driver='GPKG')
        vulnerable_gdf[['cell_id', 'clues', 'area_km2']].to_csv(
            os.path.join(output_dir, 'zonas_vulnerables.csv'), index=False)


def generate_summary(key_df, vulnerable_gdf, high_red, desert_cells, output_dir):
    """Genera resumen JSON."""
    total = len(key_df)
    key_count = int(key_df['is_key'].sum())
    redundant_count = total - key_count
    
    summary = {
        'total_isocronas': total,
        'isocronas_clave': key_count,
        'isocronas_redundantes': redundant_count,
        'pct_clave': round(key_count / total * 100, 2) if total else 0,
        'zonas_vulnerables': len(vulnerable_gdf),
        'area_vulnerable_km2': round(float(vulnerable_gdf['area_km2'].sum()), 2) if not vulnerable_gdf.empty else 0.0,
        'zonas_alta_redundancia': len(high_red),
        'zonas_desiertos': len(desert_cells),
        'area_desiertos_km2': round(float(desert_cells['area_km2'].sum()), 2) if not desert_cells.empty else 0.0,
        'promedio_pct_exclusiva': round(float(key_df['pct_exclusiva'].mean()), 2),
        'max_pct_exclusiva': round(float(key_df['pct_exclusiva'].max()), 2),
        'top_10_clave': key_df.nlargest(10, 'pct_exclusiva')[['clues', 'pct_exclusiva', 'area_exclusiva_m2']].to_dict('records')
    }
    path = os.path.join(output_dir, 'resumen_indispensabilidad.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\n=== RESUMEN DE INDISPENSABILIDAD (REAL) ===")
    for k, v in summary.items():
        if k != 'top_10_clave':
            print(f"  {k}: {v}")
    print(f"\n  Top 10 isocronas más clave:")
    for i, row in enumerate(summary['top_10_clave'], 1):
        print(f"    {i}. {row['clues']} — {row['pct_exclusiva']:.1f}% exclusiva ({row['area_exclusiva_m2']:,.0f} m²)")
    return summary


def main():
    parser = argparse.ArgumentParser(description='Análisis de isocronas clave/indispensables (intersecciones reales)')
    parser.add_argument('input', help='Ruta al archivo GeoPackage de isocronas')
    parser.add_argument('-o', '--output', default='indispensabilidad', help='Directorio de salida')
    parser.add_argument('--cell-size', type=float, default=10000.0,
                        help='Tamaño de celda del grid (m, default=10000=10km)')
    parser.add_argument('--simplify', type=float, default=200.0,
                        help='Tolerancia de simplificación (m, default=200)')
    args = parser.parse_args()
    
    print(f"Leyendo {args.input} ...")
    gdf = gpd.read_file(args.input)
    print(f"  {len(gdf)} isocronas cargadas. CRS: {gdf.crs}")
    
    if args.simplify > 0:
        print(f"\nSimplificando geometrías (tolerancia={args.simplify}m, fast mode)...")
        t0 = time.time()
        gdf = simplify_geoms(gdf, tolerance_m=args.simplify)
        print(f"  Simplificado en {time.time()-t0:.1f}s")
    
    t0 = time.time()
    print(f"\n[1/3] Analizando indispensabilidad con intersecciones reales...")
    key_df, vulnerable_gdf, high_red, fishnet, desert_cells = calcular_indispensabilidad_real(
        gdf, cell_size_m=args.cell_size)
    print(f"  Análisis completado en {time.time()-t0:.1f}s")
    
    print("\n[2/3] Exportando resultados y generando mapa estático...")
    export_results(key_df, vulnerable_gdf, args.output)
    generate_static_map(gdf, key_df, vulnerable_gdf, args.output)
    summary = generate_summary(key_df, vulnerable_gdf, high_red, desert_cells, args.output)
    
    print("\n[3/3] Generando reporte interactivo HTML...")
    generate_interactive_report(key_df, vulnerable_gdf, high_red, desert_cells, args.output, summary)
    
    print("\n✅ Análisis de indispensabilidad completado.")


if __name__ == '__main__':
    main()
