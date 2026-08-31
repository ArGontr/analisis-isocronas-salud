import pandas as pd

# Leer base categorizada y equivalencia
base = pd.read_csv('resultados_indispensabilidad/base_categorizada.csv')
equiv = pd.read_excel('equivalencia.xlsx')

print('Total en base:', len(base))
print('\nInstituciones en base:')
print(base['institucion'].value_counts())

# Ver cuantas tienen IMS en el codigo
base['inst_codigo'] = base['clues'].str[2:5]
print('\nCodigo institucion en base:')
print(base['inst_codigo'].value_counts())

# Ver cuantas IMS estan en la base
ims_en_base = base[base['inst_codigo'] == 'IMS']
print(f'\nCLUES con IMS en base: {len(ims_en_base)}')

# Verificar cuantas de esas IMS tienen equivalencia en el archivo
ims_con_equiv = ims_en_base['clues'].isin(equiv['clues_ims'])
print(f'IMS con equivalencia: {ims_con_equiv.sum()}')
print(f'IMS sin equivalencia: {(~ims_con_equiv).sum()}')

# Verificar si hay IMO en la base
imo_en_base = base[base['inst_codigo'] == 'IMO']
print(f'\nCLUES con IMO en base: {len(imo_en_base)}')

# Verificar si los IMO de la base estan en la equivalencia
imo_con_equiv = imo_en_base['clues'].isin(equiv['clues_imo'])
print(f'IMO con equivalencia: {imo_con_equiv.sum()}')
print(f'IMO sin equivalencia: {(~imo_con_equiv).sum()}')
