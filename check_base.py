import pandas as pd

df = pd.read_csv('resultados_indispensabilidad/base_categorizada.csv')
print('Columnas:', df.columns.tolist())
print('Filas:', df.shape[0])
print('Categorias:')
print(df['categoria'].value_counts())
print('\nPoblacion nulos:', df['poblacion_total_2026'].isna().sum())
print('Primeras filas categoria clave:')
print(df[df['categoria'] == 'clave'].head(3).to_string())
