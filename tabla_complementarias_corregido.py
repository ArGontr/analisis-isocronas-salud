import pandas as pd

# Cargar vinculos
vinc = pd.read_csv('resultados_indispensabilidad/vinculos_complementarias.csv')

# Extraer institucion de la complementaria del codigo CLUES y unificar IMS->IMO
vinc['institucion_complementaria'] = vinc['clues_complementaria'].str[2:5].replace('IMS', 'IMO')

# Renombrar para claridad
vinc = vinc.rename(columns={'inst_vinculada': 'institucion_centro'})

# Tabla cruzada: conteo
tabla_conteo = pd.crosstab(
    vinc['institucion_complementaria'],
    vinc['institucion_centro'],
    margins=True,
    margins_name='Total'
)
print('=== CONTEO DE VINCULOS ===')
print(tabla_conteo)

# Tabla cruzada: poblacion agregada
tabla_pob = pd.crosstab(
    vinc['institucion_complementaria'],
    vinc['institucion_centro'],
    values=vinc['pob_complementaria'],
    aggfunc='sum',
    margins=True,
    margins_name='Total'
)
print('\n=== POBLACION AGREGADA (complementaria) ===')
print(tabla_pob)

# Resumen consolidado: una fila por combinacion
resumen_grupo = vinc.groupby(['institucion_complementaria', 'institucion_centro']).agg(
    n_clues=('clues_complementaria', 'count'),
    pob_total_comp=('pob_complementaria', 'sum'),
    pob_prom_comp=('pob_complementaria', 'mean'),
    consultas_total_comp=('consultas_complementaria', 'sum'),
    consultas_prom_comp=('consultas_complementaria', 'mean'),
    pob_total_centro=('pob_vinculada', 'sum'),
    pob_prom_centro=('pob_vinculada', 'mean'),
    consultas_total_centro=('consultas_vinculada', 'sum'),
    consultas_prom_centro=('consultas_vinculada', 'mean')
).round(1).reset_index()

print('\n=== RESUMEN POR COMBINACION DE INSTITUCIONES (CORREGIDO) ===')
print(resumen_grupo.to_string(index=False))

# Guardar
resumen_grupo.to_csv('resultados_indispensabilidad/resumen_complementarias_por_institucion.csv', index=False)
print('\nGuardado: resultados_indispensabilidad/resumen_complementarias_por_institucion.csv')
