import pandas as pd

# Leer CSV de indispensabilidad
df = pd.read_csv('resultados_indispensabilidad/indispensabilidad.csv')

# Agregar columna de redundancia (inverso de exclusividad)
df['pct_redundancia'] = 100.0 - df['pct_exclusiva']

# Ordenar por % exclusiva descendente (más indispensables primero)
df = df.sort_values('pct_exclusiva', ascending=False).reset_index(drop=True)

# Guardar como Excel
excel_path = 'resultados_indispensabilidad/indispensabilidad.xlsx'
df.to_excel(excel_path, index=False, sheet_name='Indispensabilidad')

print(f"Excel guardado: {excel_path}")
print(f"Total registros: {len(df)}")
print(f"\nResumen de pct_exclusiva:")
print(df['pct_exclusiva'].describe())
print(f"\nResumen de pct_redundancia:")
print(df['pct_redundancia'].describe())
print(f"\nTop 20 isocronas más indispensables:")
print(df[['clues', 'area_km2', 'pct_exclusiva', 'pct_redundancia', 'area_exclusiva_km2', 'is_key']].head(20).to_string(index=False))
print(f"\nBottom 20 isocronas más redundantes:")
print(df[['clues', 'area_km2', 'pct_exclusiva', 'pct_redundancia', 'area_exclusiva_km2', 'is_key']].tail(20).to_string(index=False))
