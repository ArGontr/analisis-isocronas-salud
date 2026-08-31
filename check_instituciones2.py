import pandas as pd

# Verificar instituciones en datos de poblacion
pob = pd.read_excel('resultados_indispensabilidad/datos_pob_y_prod.xlsx')
print('Columnas:', pob.columns.tolist())
print('\nInstituciones en datos_pob_y_prod.xlsx:')
if 'institucion' in pob.columns:
    print(pob['institucion'].value_counts())
else:
    print('No hay columna institucion')

# Extraer codigo de institucion del CLUES
pob['inst_codigo'] = pob['clues'].str[2:5]
print('\nInstitucion extraida del codigo CLUES:')
print(pob['inst_codigo'].value_counts())

# Verificar si hay diferencias
if 'institucion' in pob.columns:
    print('\nCruce institucion vs codigo:')
    print(pd.crosstab(pob['institucion'], pob['inst_codigo'], margins=True))
