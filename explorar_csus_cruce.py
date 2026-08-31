import pandas as pd

df = pd.read_excel(r'C:\Users\armando.gonzalez\Downloads\CSUS_CRUCE.xlsx')
print('Columnas:', df.columns.tolist())
print('Shape:', df.shape)
print(df.head(10).to_string())
print('\nTipos:')
print(df.dtypes)
