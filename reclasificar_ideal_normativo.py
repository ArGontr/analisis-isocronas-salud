import pandas as pd
import os

# Leer base normalizada
df = pd.read_csv('resultados_indispensabilidad/base_clues_normalizada.csv')

print('Categorias antes del cambio:')
print(df['categoria'].value_counts())

# Cambiar: las que tienen poblacion >= 3000 y son descartar -> ideal_normativo
mascara = (df['poblacion_total_2026'] >= 3000) & (df['categoria'] == 'descartar')
df.loc[mascara, 'categoria'] = 'ideal_normativo'

# Tambien actualizar el motivo
df.loc[mascara, 'motivo'] = 'poblacion_mayor_3000'

print(f'\nRegistros cambiados de descartar a ideal_normativo: {mascara.sum()}')

print('\nCategorias despues del cambio:')
print(df['categoria'].value_counts())

# Guardar base actualizada
df.to_csv('resultados_indispensabilidad/base_clues_normalizada.csv', index=False)
print('\nGuardado: resultados_indispensabilidad/base_clues_normalizada.csv')

# Regenerar resumen
resumen = df.groupby(['institucion', 'categoria']).agg(
    n_clues=('clues', 'count'),
    pob_total=('poblacion_total_2026', 'sum'),
    consultas_total=('consultas_generales', 'sum'),
    pct_exclusiva_prom=('pct_exclusiva', 'mean')
).round(1).reset_index()

print('\n=== RESUMEN AGREGADO ACTUALIZADO ===')
print(resumen.to_string(index=False))

resumen.to_csv('resultados_indispensabilidad/resumen_por_institucion_categoria.csv', index=False)
print('\nGuardado: resultados_indispensabilidad/resumen_por_institucion_categoria.csv')
