import pandas as pd

df = pd.read_excel('equivalencia.xlsx')
print('Columnas:', df.columns.tolist())
print('Shape:', df.shape)
print(df.head(20).to_string())
print('\nTipos:')
print(df.dtypes)
