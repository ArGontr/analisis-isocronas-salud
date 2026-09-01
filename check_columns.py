import pandas as pd
df = pd.read_csv('resultados_casas_salud/casas_salud_clasificadas.csv')
print(df.columns.tolist())
print(df.head(3).to_string())