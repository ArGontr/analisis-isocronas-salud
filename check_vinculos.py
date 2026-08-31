import pandas as pd

# Cargar vinculos
vinc = pd.read_csv('resultados_indispensabilidad/vinculos_complementarias.csv')
print('Columnas:', vinc.columns.tolist())
print('Shape:', vinc.shape)
print(vinc.head(3).to_string())
print('\nInstituciones complementarias:', vinc['institucion_complementaria'].value_counts())
print('\nInstituciones centro:', vinc['institucion_centro'].value_counts())
