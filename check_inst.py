import pandas as pd
df = pd.read_csv('resultados_indispensabilidad/base_clues_normalizada.csv')
print(df.institucion.value_counts())
