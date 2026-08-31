import pandas as pd

# Verificar instituciones en la base categorizada original
df = pd.read_csv('resultados_indispensabilidad/base_categorizada.csv')
print('Instituciones en base_categorizada.csv:')
print(df['institucion'].value_counts())

# Verificar en datos de poblacion
pob = pd.read_excel('datos_pob_y_prod.xlsx')
print('\nInstituciones en datos_pob_y_prod.xlsx:')
print(pob['institucion'].value_counts() if 'institucion' in pob.columns else 'No hay columna institucion')

# Verificar algunos codigos CLUES de complementarias
vinc = pd.read_csv('resultados_indispensabilidad/vinculos_complementarias.csv')
print('\nMuestra de CLUES complementarias:')
print(vinc['clues_complementaria'].head(20).tolist())
print('\nMuestra de CLUES vinculadas (centros):')
print(vinc['clues_vinculada'].head(20).tolist())
