import pandas as pd
clues = pd.read_csv('resultados_indispensabilidad/base_clues_normalizada.csv')
print('Antes del filtro:')
print(clues['institucion'].value_counts())
clues = clues[clues['institucion'] != 'DESCONOCIDA']
print('\nDespues del filtro:')
print(clues['institucion'].value_counts())
print('\nTabla:')
print(clues.groupby('institucion')['categoria'].value_counts().unstack(fill_value=0))
