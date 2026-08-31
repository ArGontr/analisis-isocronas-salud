import pandas as pd

# Cargar vinculos
vinc = pd.read_csv('resultados_indispensabilidad/vinculos_complementarias.csv')

# Extraer institucion de la complementaria del codigo CLUES
vinc['institucion_complementaria'] = vinc['clues_complementaria'].str[2:5]

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

# Tabla cruzada: promedio de poblacion
tabla_pob_mean = pd.crosstab(
    vinc['institucion_complementaria'],
    vinc['institucion_centro'],
    values=vinc['pob_complementaria'],
    aggfunc='mean',
    margins=True,
    margins_name='Total'
).round(1)
print('\n=== POBLACION PROMEDIO (complementaria) ===')
print(tabla_pob_mean)

# Guardar
resumen = pd.DataFrame({
    'inst_complementaria': vinc['institucion_complementaria'],
    'inst_centro': vinc['institucion_centro'],
    'clues_complementaria': vinc['clues_complementaria'],
    'clues_centro': vinc['clues_vinculada'],
    'pob_complementaria': vinc['pob_complementaria'],
    'pob_centro': vinc['pob_vinculada'],
    'consultas_complementaria': vinc['consultas_complementaria'],
    'consultas_centro': vinc['consultas_vinculada'],
    'motivo': vinc['motivo']
})

# Tabla resumen consolidada: una fila por combinacion
resumen_grupo = resumen.groupby(['inst_complementaria', 'inst_centro']).agg(
    n_clues=('clues_complementaria', 'count'),
    pob_total_comp=('pob_complementaria', 'sum'),
    pob_prom_comp=('pob_complementaria', 'mean'),
    consultas_total_comp=('consultas_complementaria', 'sum'),
    consultas_prom_comp=('consultas_complementaria', 'mean'),
    pob_total_centro=('pob_centro', 'sum'),
    pob_prom_centro=('pob_centro', 'mean'),
    consultas_total_centro=('consultas_centro', 'sum'),
    consultas_prom_centro=('consultas_centro', 'mean')
).round(1).reset_index()

print('\n=== RESUMEN POR COMBINACION DE INSTITUCIONES ===')
print(resumen_grupo.to_string(index=False))

# Guardar todo
resumen.to_csv('resultados_indispensabilidad/complementarias_con_instituciones.csv', index=False)
resumen_grupo.to_csv('resultados_indispensabilidad/resumen_complementarias_por_institucion.csv', index=False)

print('\nArchivos guardados:')
print('- resultados_indispensabilidad/complementarias_con_instituciones.csv')
print('- resultados_indispensabilidad/resumen_complementarias_por_institucion.csv')
