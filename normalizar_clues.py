import pandas as pd
import os

# Leer datos
base = pd.read_csv('resultados_indispensabilidad/base_categorizada.csv')
equiv = pd.read_excel('equivalencia.xlsx')

# Crear diccionario de equivalencia: IMS -> IMO
equiv_dict = dict(zip(equiv['clues_ims'], equiv['clues_imo']))

# Normalizar CLUES: si es IMS, reemplazar por IMO
base['clues_original'] = base['clues']
base['clues'] = base['clues'].replace(equiv_dict)

# Verificar que no hay duplicados
print(f'Total registros: {len(base)}')
print(f'CLUES unicas: {base["clues"].nunique()}')
print(f'Duplicados: {len(base) - base["clues"].nunique()}')

# Si hay duplicados, mostrar
if len(base) != base['clues'].nunique():
    dups = base[base.duplicated('clues', keep=False)]
    print('\nDuplicados encontrados:')
    print(dups[['clues', 'clues_original', 'institucion', 'categoria']].to_string())

# Seleccionar columnas relevantes para el usuario
cols_final = [
    'clues', 'institucion', 'categoria', 'poblacion_total_2026',
    'poblacion_sin_derechohabiencia_2026', 'poblacion_con_derechohabiencia_2026',
    'consultas_generales', 'is_key', 'pct_exclusiva', 'area_exclusiva_km2',
    'clues_vinculada', 'motivo'
]

# Filtrar columnas que existen
cols_final = [c for c in cols_final if c in base.columns]
resultado = base[cols_final].copy()

# Ordenar por clues
resultado = resultado.sort_values('clues').reset_index(drop=True)

print('\n=== PRIMERAS 10 FILAS ===')
print(resultado.head(10).to_string())

print('\n=== RESUMEN POR ESTATUS ===')
print(resultado['categoria'].value_counts())

print('\n=== RESUMEN POR INSTITUCION ===')
print(resultado['institucion'].value_counts())

# Guardar
os.makedirs('resultados_indispensabilidad', exist_ok=True)
resultado.to_csv('resultados_indispensabilidad/base_clues_normalizada.csv', index=False)
print('\nGuardado: resultados_indispensabilidad/base_clues_normalizada.csv')

# Tambien guardar una version resumida
resumen = resultado.groupby(['institucion', 'categoria']).agg(
    n_clues=('clues', 'count'),
    pob_total=('poblacion_total_2026', 'sum'),
    consultas_total=('consultas_generales', 'sum'),
    pct_exclusiva_prom=('pct_exclusiva', 'mean')
).round(1).reset_index()

print('\n=== RESUMEN AGREGADO ===')
print(resumen.to_string(index=False))

resumen.to_csv('resultados_indispensabilidad/resumen_por_institucion_categoria.csv', index=False)
print('Guardado: resultados_indispensabilidad/resumen_por_institucion_categoria.csv')
