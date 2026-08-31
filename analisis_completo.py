"""
Análisis de isocronas de centros de salud - versión completa optimizada.
Identifica redundancia (>50%) y desiertos, genera reporte HTML interactivo.

Requiere: geopandas, shapely, matplotlib, numpy, folium, branca
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import unary_union
from shapely.geometry import box
import matplotlib.pyplot as plt
import argparse
import json
import os
import time
from itertools import combinations
import folium
from folium.plugins import MarkerCluster, HeatMap
import branca.colormap as cm
from paleta_institucional import *


def simplify_geoms(gdf, tolerance_m=200.0):
    """Simplifica geometrías RÁPIDO (preserve_topology=False)."""
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


def analyze(gdf, cell_size_m=10000.0, redundancy_threshold_pct=50.0, buffer_cells=0):
    """
    Analiza redundancia y desiertos con un grid.
    """
    gdf = gdf.copy()
    gdf['_iso_idx'] = range(len(gdf))
    gdf['area_km2'] = gdf.geometry.area / 1e6
    
    print(f"  Creando grid...")
    t0 = time.time()
    bounds = list(gdf.total_bounds)
    if buffer_cells > 0:
        bounds[0] -= buffer_cells * cell_size_m
        bounds[1] -= buffer_cells * cell_size_m
        bounds[2] += buffer_cells * cell_size_m
        bounds[3] += buffer_cells * cell_size_m
    fishnet = create_fishnet(bounds, cell_size_m=cell_size_m)
    print(f"    Tiempo: {time.time()-t0:.1f}s")
    
    print("  Spatial join isocronas-celdas...")
    t0 = time.time()
    joined = gpd.sjoin(
        gdf[['_iso_idx', 'clues', 'geometry']],
        fishnet[['cell_id', 'geometry']],
        how='inner', predicate='intersects'
    )
    print(f"    Pares: {len(joined)}. Tiempo: {time.time()-t0:.1f}s")
    
    print("  Contando superposiciones por celda...")
    t0 = time.time()
    cell_counts = joined.groupby('cell_id').size().reset_index(name='n_isocronas')
    joined = joined.merge(cell_counts, on='cell_id', how='left')
    print(f"    Tiempo: {time.time()-t0:.1f}s")
    
    print("  Calculando redundancia...")
    t0 = time.time()
    iso_stats = joined.groupby('_iso_idx').agg(
        total_celdas=('cell_id', 'nunique'),
        celdas_compartidas=('n_isocronas', lambda x: int((x > 1).sum()))
    ).reset_index()
    iso_stats['redundancia_pct'] = (iso_stats['celdas_compartidas'] / iso_stats['total_celdas'] * 100.0).fillna(0)
    iso_stats['is_redundant'] = iso_stats['redundancia_pct'] >= redundancy_threshold_pct
    
    gdf = gdf.merge(iso_stats, on='_iso_idx', how='left')
    gdf['redundancia_pct'] = gdf['redundancia_pct'].fillna(0)
    gdf['is_redundant'] = gdf['is_redundant'].fillna(False)
    print(f"    Tiempo: {time.time()-t0:.1f}s")
    
    print("  Identificando desiertos...")
    t0 = time.time()
    cells_with_data = set(joined['cell_id'].unique())
    desert_cells = fishnet[~fishnet['cell_id'].isin(cells_with_data)].copy()
    desert_cells['area_km2'] = desert_cells.geometry.area / 1e6
    print(f"    Celdas desierto: {len(desert_cells)}. Tiempo: {time.time()-t0:.1f}s")
    
    redundancy_df = gdf[['clues', 'area_km2', 'redundancia_pct', 'is_redundant', 'geometry']].copy()
    redundancy_df = redundancy_df.rename(columns={'redundancia_pct': 'overlap_pct'})
    redundancy_df['overlapped_area_km2'] = redundancy_df['area_km2'] * redundancy_df['overlap_pct'] / 100.0
    redundancy_df['neighbor_count'] = 0
    
    return redundancy_df, desert_cells, fishnet, joined


def generate_static_map(gdf, redundancy_df, desert_gdf, output_dir):
    """Genera visualización estática con matplotlib."""
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    
    ax = axes[0]
    gdf.boundary.plot(ax=ax, color='lightgray', linewidth=0.2, alpha=0.4)
    redundant = redundancy_df[redundancy_df['is_redundant'] == True]
    non_redundant = redundancy_df[redundancy_df['is_redundant'] == False]
    if not redundant.empty:
        redundant.plot(ax=ax, color=ALERTA, alpha=0.4, label=f'Redundante (n={len(redundant)})')
    if not non_redundant.empty:
        non_redundant.plot(ax=ax, color=EXITO, alpha=0.2, label=f'No redundante (n={len(non_redundant)})')
    ax.set_title('Redundancia de áreas de servicio (>50%)', color=TEXTO)
    ax.legend(); ax.set_axis_off()
    
    ax = axes[1]
    gdf.plot(ax=ax, color=EXITO, alpha=0.2, label='Isocronas')
    if not desert_gdf.empty:
        desert_gdf.plot(ax=ax, color=AMARILLO_PRECAUCION, alpha=0.5, label=f'Desiertos (n={len(desert_gdf)})')
    ax.set_title('Desiertos de atención', color=TEXTO)
    ax.legend(); ax.set_axis_off()
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, 'analisis_isocronas.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Mapa estático guardado en: {out_path}")


def generate_interactive_report(gdf, redundancy_df, desert_gdf, output_dir, summary):
    """Genera un reporte HTML interactivo con folium."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("  Convirtiendo a WGS84 para mapa interactivo...")
    gdf_wgs = redundancy_df.to_crs('EPSG:4326')
    desert_wgs = desert_gdf.to_crs('EPSG:4326') if not desert_gdf.empty else gpd.GeoDataFrame(crs='EPSG:4326')
    
    center = [gdf_wgs.geometry.centroid.y.mean(), gdf_wgs.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=6, tiles='OpenStreetMap')
    
    print("  Agregando capa de isocronas...")
    def style_isocrona(feature):
        is_red = feature['properties']['is_redundant']
        return {
            'fillColor': ALERTA if is_red else EXITO,
            'color': NEGRO,
            'weight': 0.5,
            'fillOpacity': 0.4,
        }
    
    gdf_wgs['geometry'] = gdf_wgs.geometry.simplify(tolerance=0.01, preserve_topology=False)
    
    folium.GeoJson(
        gdf_wgs[['clues', 'area_km2', 'overlap_pct', 'is_redundant', 'geometry']],
        name='Isocronas',
        style_function=style_isocrona,
        tooltip=folium.GeoJsonTooltip(
            fields=['clues', 'area_km2', 'overlap_pct', 'is_redundant'],
            aliases=['CLUES:', 'Área (km²):', 'Superposición (%):', 'Redundante:'],
            localize=True
        ),
        popup=folium.GeoJsonPopup(
            fields=['clues', 'area_km2', 'overlap_pct', 'is_redundant'],
            aliases=['CLUES', 'Área km²', 'Superposición %', 'Redundante'],
        )
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
                'fillOpacity': 0.6,
            },
            tooltip=folium.GeoJsonTooltip(fields=['cell_id', 'area_km2'],
                                          aliases=['Celda:', 'Área (km²):']),
            show=False
        ).add_to(m)
    
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px;
                background-color: white; border: 2px solid {NEGRO};
                border-radius: 8px; padding: 12px; font-size: 13px;
                box-shadow: 3px 3px 10px rgba(0,0,0,0.3);
                z-index: 9999;">
        <h4 style="margin-top:0; color:{NEGRO};">📊 Resumen del Análisis</h4>
        <b>Total isocronas:</b> {summary['total_isocronas']:,}<br>
        <b>Redundantes (>50%):</b> <span style="color:{ALERTA};">{summary['redundantes']:,} ({summary['pct_redundantes']}%)</span><br>
        <b>No redundantes:</b> <span style="color:{EXITO};">{summary['no_redundantes']:,}</span><br>
        <b>Superposición promedio:</b> {summary['promedio_overlap_pct']}%<br>
        <b>Desiertos (celdas):</b> {summary['num_desiertos_celdas']:,}<br>
        <b>Área desiertos:</b> {summary['area_total_desiertos_km2']:,.0f} km²<br>
        <hr style="margin:8px 0;">
        <span style="display:inline-block;width:12px;height:12px;background:{ALERTA};opacity:0.6;"></span> Redundante<br>
        <span style="display:inline-block;width:12px;height:12px;background:{EXITO};opacity:0.6;"></span> No redundante<br>
        <span style="display:inline-block;width:12px;height:12px;background:{AMARILLO_PRECAUCION};opacity:0.6;"></span> Desierto
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
        Análisis de Isocronas de Centros de Salud
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    folium.LayerControl().add_to(m)
    
    out_path = os.path.join(output_dir, 'reporte_interactivo.html')
    m.save(out_path)
    print(f"  Reporte interactivo guardado en: {out_path}")
    return out_path


def export_results(redundancy_df, desert_gdf, output_dir):
    """Exporta resultados."""
    os.makedirs(output_dir, exist_ok=True)
    redundancy_df[['clues', 'area_km2', 'overlapped_area_km2', 'overlap_pct',
                   'is_redundant', 'geometry']].to_file(
        os.path.join(output_dir, 'redundancia.gpkg'), driver='GPKG')
    redundancy_df[['clues', 'area_km2', 'overlapped_area_km2', 'overlap_pct',
                   'is_redundant']].to_csv(
        os.path.join(output_dir, 'redundancia.csv'), index=False)
    if not desert_gdf.empty:
        desert_gdf.to_file(os.path.join(output_dir, 'desiertos.gpkg'), driver='GPKG')
        desert_gdf[['cell_id', 'area_km2']].to_csv(
            os.path.join(output_dir, 'desiertos.csv'), index=False)


def generate_summary(redundancy_df, desert_gdf, output_dir):
    """Genera resumen JSON."""
    total = len(redundancy_df)
    redundant_count = int(redundancy_df['is_redundant'].sum())
    summary = {
        'total_isocronas': total,
        'redundantes': redundant_count,
        'no_redundantes': total - redundant_count,
        'pct_redundantes': round(redundant_count / total * 100, 2) if total else 0,
        'num_desiertos_celdas': len(desert_gdf),
        'area_total_desiertos_km2': round(float(desert_gdf['area_km2'].sum()), 2) if not desert_gdf.empty else 0.0,
        'promedio_overlap_pct': round(float(redundancy_df['overlap_pct'].mean()), 2) if not redundancy_df.empty else 0.0
    }
    path = os.path.join(output_dir, 'resumen.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\n=== RESUMEN ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


def main():
    parser = argparse.ArgumentParser(description='Análisis completo de isocronas con reporte interactivo')
    parser.add_argument('input', help='Ruta al archivo GeoPackage de isocronas')
    parser.add_argument('-o', '--output', default='resultados_completos', help='Directorio de salida')
    parser.add_argument('--threshold', type=float, default=50.0,
                        help='Umbral de superposición (%%) para considerar redundante')
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
    print(f"\n[1/3] Analizando redundancia y desiertos con grid de {args.cell_size/1000:.0f}km...")
    redundancy_df, desert_gdf, fishnet, joined = analyze(
        gdf, cell_size_m=args.cell_size, redundancy_threshold_pct=args.threshold)
    print(f"  Análisis completado en {time.time()-t0:.1f}s")
    
    print("\n[2/3] Exportando resultados y generando mapa estático...")
    export_results(redundancy_df, desert_gdf, args.output)
    generate_static_map(gdf, redundancy_df, desert_gdf, args.output)
    summary = generate_summary(redundancy_df, desert_gdf, args.output)
    
    print("\n[3/3] Generando reporte interactivo HTML...")
    generate_interactive_report(gdf, redundancy_df, desert_gdf, args.output, summary)
    
    print("\n✅ Análisis completado.")


if __name__ == '__main__':
    main()
