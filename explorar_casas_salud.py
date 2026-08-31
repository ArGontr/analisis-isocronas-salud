import pandas as pd
import os

# Buscar archivos de casas de salud
for f in ['casas_de_salud.xlsx', 'CSUS_CRUCE.xlsx']:
    if os.path.exists(f):
        print(f'=== {f} ===')
        df = pd.read_excel(f)
        print('Columnas:', df.columns.tolist())
        print('Shape:', df.shape)
        print(df.head(10).to_string())
        print('\nTipos:')
        print(df.dtypes)
        print('\n' + '='*60 + '\n')
    else:
        print(f'{f} no encontrado en el directorio actual')
