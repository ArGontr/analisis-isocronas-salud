import pandas as pd

vinc = pd.read_csv('resultados_indispensabilidad/vinculos_complementarias.csv')

# Extraer institucion de la CLUES complementaria (posiciones 2-4 del codigo)
# Ej: BCIMB000133 -> IMB, BCIMO000542 -> IMO
vinc['institucion_complementaria'] = vinc['clues_complementaria'].str[2:5]

print('Instituciones complementarias:')
print(vinc['institucion_complementaria'].value_counts())
print('\nInstituciones centro (inst_vinculada):')
print(vinc['inst_vinculada'].value_counts())

# Verificar si hay valores inesperados
print('\nUnicos inst complementaria:', vinc['institucion_complementaria'].unique())
print('Unicos inst centro:', vinc['inst_vinculada'].unique())
