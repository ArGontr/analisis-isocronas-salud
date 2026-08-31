"""
Análisis de isocronas de centros de salud - versión ultra-rápida con grid.
Identifica redundancia y desiertos de atención usando un grid de celdas.

Requiere: geopandas, shapely, matplotlib, numpy
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


def simplify_geoms(gdf, tolerance_m=100.0):
    """Simplifica geometrías para acelerar operaciones."""
    gdf = gdf.copy()
    gdf['geometry'] = gdf.geometry.simplify(tolerance=tolerance_m, preserve_topology=True)
    return gdf


def create_fishnet(bounds, cell_size_m=5000.0):
    """Crea un grid regular sobre los bounds dados."""
    xmin, ymin, xmax, ymax = bounds
    xmin = np.floor(xmin / cell_size_m) * cell_size_m
    ymin = np.floor(ymin / cell_size_m) * cell_size_m
    xmax = np.ceil(xmax / cell_size_m) * cell_size_m
    ymax = np.ceil(ymax / cell_size_m) * cell_size_m
    
    cols = int(np.ceil((xmax - xmin) / cell_size_m))
    rows = int(np.ceil((ymax - ymin) / cell_size_m))
    
    print(f"    Grid: {cols} x {rows} = {cols*rows} celdas ({cell_size_m/1000:.1f}km)")
    
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


def analyze(gdf, cell_size_m=5000.0, redundancy_threshold_pct=30.0, buffer_cells=1,
            skip_pairs=False, max_pairs_per_cell=50):
    """
    Analiza redundancia y desiertos con un grid.
    """
    gdf = gdf.copy()
    gdf['_iso_idx'] = range(len(gdf))
    gdf['area_km2'] = gdf.geometry.area / 1e6
    
    # 1. Crear fishnet sobre bounds + buffer
    print(f"  Creando grid...")
    t0 = time.time()
    bounds = list(gdf.total_bounds)
    bounds[0] -= buffer_cells * cell_size_m
    bounds[1] -= buffer_cells * cell_size_m
    bounds[2] += buffer_cells * cell_size_m
    bounds[3] += buffer_cells * cell_size_m
    fishnet = create_fishnet(bounds, cell_size_m=cell_size_m)
    print(f"    Tiempo: {time.time()-t0:.1f}s")
    
    # 2. Spatial join isocronas -> celdas
    print("  Spatial join isocronas-celdas...")
    t0 = time.time()
    joined = gpd.sjoin(
        gdf[['_iso_idx', 'clues', 'geometry']],
        fishnet[['cell_id', 'geometry']],
        how='inner', predicate='intersects'
    )
    print(f"    Pares: {len(joined)}. Tiempo: {time.time()-t0:.1f}s")
    
    # 3. Contar isocronas por celda
    print("  Contando superposiciones por celda...")
    t0 = time.time()
    cell_counts = joined.groupby('cell_id').size().reset_index(name='n_isocronas')
    joined = joined.merge(cell_counts, on='cell_id', how='left')
    print(f"    Tiempo: {time.time()-t0:.1f}s")
    
    # 4. Redundancia por isocrona
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
    
    # 5. Desiertos: celdas con n_isocronas == 0
    print("  Identificando desiertos...")
    t0 = time.time()
    cells_with_data = set(joined['cell_id'].unique())
    desert_cells = fishnet[~fishnet['cell_id'].isin(cells_with_data)].copy()
    desert_cells['area_km2'] = desert_cells.geometry.area / 1e6
    print(f"    Celdas desierto: {len(desert_cells)}. Tiempo: {time.time()-t0:.1f}s")
    
    # 6. Pares de superposición (opcional, optimizado)
    overlap_gdf = gpd.GeoDataFrame({'geometry': []}, crs=gdf.crs)
    if not skip_pairs:
        print("  Identificando pares de superposición...")
        t0 = time.time()
        overlap_cells_df = joined[joined['n_isocronas'] > 1][['cell_id', 'clues']].drop_duplicates()
        
        pair_records = []
        skipped_cells = 0
        for cell_id, group in overlap_cells_df.groupby('cell_id'):
            clues_list = sorted(group['clues'].tolist())
            n = len(clues_list)
            if n > max_pairs_per_cell:
                skipped_cells += 1
                continue  # Celda con demasiadas isocronas, skip pares detallados
            # itertools.combinations es mucho más rápido que loop manual
            for ca, cb in combinations(clues_list, 2):
                pair_records.append((ca, cb, cell_id))
        
        if skipped_cells:
            print(f"    Celdas omitidas (>{max_pairs_per_cell} isocronas): {skipped_cells}")
        
        if pair_records:
            pairs_df = pd.DataFrame(pair_records, columns=['clues_a', 'clues_b', 'cell_id'])
            pair_summary = pairs_df.groupby(['clues_a', 'clues_b']).size().reset_index(name='shared_cells')
            
            # Geometría: unión de celdas compartidas
            geom_map = {}
            for (ca, cb), group in pairs_df.groupby(['clues_a', 'clues_b']):
                cell_ids = set(group['cell_id'].tolist())
                cells = fishnet[fishnet['cell_id'].isin(cell_ids)]
                if not cells.empty:
                    geom_map[(ca, cb)] = unary_union(cells.geometry)
            
            pair_summary['geometry'] = pair_summary.apply(lambda r: geom_map.get((r['clues_a'], r['clues_b'])), axis=1)
            overlap_gdf = gpd.GeoDataFrame(pair_summary, crs=gdf.crs)
        
        print(f"    Pares únicos: {len(overlap_gdf)}. Tiempo: {time.time()-t0:.1f}s")
    
    # Preparar outputs
    redundancy_df = gdf[['clues', 'area_km2', 'redundancia_pct', 'is_redundant', 'geometry']].copy()
    redundancy_df = redundancy_df.rename(columns={'redundancia_pct': 'overlap_pct'})
    redundancy_df['overlapped_area_km2'] = redundancy_df['area_km2'] * redundancy_df['overlap_pct'] / 100.0
    redundancy_df['neighbor_count'] = 0
    
    return overlap_gdf, redundancy_df, desert_cells, fishnet, joined


def visualize_results(gdf, redundancy_df, desert_gdf, fishnet, joined, output_dir, cell_size_m):
    """Genera visualizaciones."""
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    
    ax = axes[0]
    gdf.boundary.plot(ax=ax, color='lightgray', linewidth=0.3, alpha=0.5)
    redundant = redundancy_df[redundancy_df['is_redundant'] == True]
    non_redundant = redundancy_df[redundancy_df['is_redundant'] == False]
    if not redundant.empty:
        redundant.plot(ax=ax, color='red', alpha=0.5, label=f'Redundante (n={len(redundant)})')
    if not non_redundant.empty:
        non_redundant.plot(ax=ax, color='green', alpha=0.3, label=f'No redundante (n={len(non_redundant)})')
    ax.set_title('Redundancia de áreas de servicio')
    ax.legend(); ax.set_axis_off()
    
    ax = axes[1]
    gdf.plot(ax=ax, color='green', alpha=0.3, label='Isocronas')
    
    if not joined.empty:
        overlap_cell_ids = joined[joined['n_isocronas'] > 1]['cell_id'].unique()
        cells_gdf = fishnet[fishnet['cell_id'].isin(overlap_cell_ids)]
        if not cells_gdf.empty:
            cells_gdf.plot(ax=ax, color='purple', alpha=0.3, label='Superposición')
    
    if not desert_gdf.empty:
        desert_gdf.plot(ax=ax, color='orange', alpha=0.6, label=f'Desiertos (n={len(desert_gdf)})')
    ax.set_title('Desiertos de atención')
    ax.legend(); ax.set_axis_off()
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, 'analisis_isocronas.png')
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  Visualización guardada en: {out_path}")


def export_results(redundancy_df, desert_gdf, overlap_gdf, output_dir):
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
    if not overlap_gdf.empty:
        overlap_gdf.to_file(os.path.join(output_dir, 'superposiciones.gpkg'), driver='GPKG')


def generate_summary(redundancy_df, desert_gdf, overlap_gdf, output_dir):
    """Genera resumen JSON."""
    total = len(redundancy_df)
    redundant_count = int(redundancy_df['is_redundant'].sum())
    summary = {
        'total_isocronas': total,
        'redundantes': redundant_count,
        'no_redundantes': total - redundant_count,
        'pct_redundantes': round(redundant_count / total * 100, 2) if total else 0,
        'total_superposiciones': len(overlap_gdf),
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
    parser = argparse.ArgumentParser(description='Análisis de isocronas de centros de salud (grid rápido)')
    parser.add_argument('input', help='Ruta al archivo GeoPackage de isocronas')
    parser.add_argument('-o', '--output', default='resultados', help='Directorio de salida')
    parser.add_argument('--threshold', type=float, default=30.0,
                        help='Umbral de superposición (%%) para considerar redundante')
    parser.add_argument('--cell-size', type=float, default=5000.0,
                        help='Tamaño de celda del grid (m, default=5000=5km)')
    parser.add_argument('--simplify', type=float, default=100.0,
                        help='Tolerancia de simplificación (m, default=100)')
    parser.add_argument('--skip-pairs', action='store_true',
                        help='Omitir cálculo de pares de superposición detallados')
    parser.add_argument('--max-pairs-per-cell', type=int, default=50,
                        help='Máximo de isocronas por celda para calcular pares')
    args = parser.parse_args()
    
    print(f"Leyendo {args.input} ...")
    gdf = gpd.read_file(args.input)
    print(f"  {len(gdf)} isocronas cargadas. CRS: {gdf.crs}")
    
    if args.simplify > 0:
        print(f"\nSimplificando geometrías (tolerancia={args.simplify}m)...")
        gdf = simplify_geoms(gdf, tolerance_m=args.simplify)
    
    t0 = time.time()
    print(f"\n[1/2] Analizando redundancia y desiertos con grid de {args.cell_size/1000:.1f}km...")
    overlap_gdf, redundancy_df, desert_gdf, fishnet, joined = analyze(
        gdf, cell_size_m=args.cell_size, redundancy_threshold_pct=args.threshold,
        skip_pairs=args.skip_pairs, max_pairs_per_cell=args.max_pairs_per_cell)
    print(f"  Completado en {time.time()-t0:.1f}s")
    
    print("\n[2/2] Exportando resultados ...")
    export_results(redundancy_df, desert_gdf, overlap_gdf, args.output)
    visualize_results(gdf, redundancy_df, desert_gdf, fishnet, joined, args.output, args.cell_size)
    generate_summary(redundancy_df, desert_gdf, overlap_gdf, args.output)
    print("\n✅ Análisis completado.")


if __name__ == '__main__':
    main()
