import pandas as pd

# Verificar el cruce completo
cruce = pd.read_excel(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx')
casas = pd.read_excel('casas_de_salud.xlsx')

print(f'Total en CSUS_CRUCE: {len(cruce)}')
print(f'Total en casas_de_salud: {len(casas)}')

# Cuántas del cruce están en casas_de_salud
en_ambos = cruce['ID_TEMP_SUS'].isin(casas['ID_TEMP_SUS']).sum()
print(f'Cruce con coordenadas: {en_ambos}')
print(f'Cruce SIN coordenadas: {len(cruce) - en_ambos}')

# Ver los que faltan
faltan = cruce[~cruce['ID_TEMP_SUS'].isin(casas['ID_TEMP_SUS'])]
print(f'\nPrimeros 10 sin coordenadas:')
print(faltan[['ID_TEMP_SUS', 'CLUES_ASIGNADA', 'ENTIDAD']].head(10).to_string())
