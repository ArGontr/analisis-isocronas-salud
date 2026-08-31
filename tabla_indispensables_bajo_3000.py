import pandas as pd
import os

df = pd.read_csv('resultados_indispensabilidad/base_categorizada.csv')

# Filtrar CLUES clave (indispensables) con poblacion < 3000
clave = df[df['categoria'] == 'clave'].copy()

# Manejar poblacion: algunas pueden ser DESCONOCIDA o NaN
# Ver cuantas tienen poblacion numerica < 3000
clave['poblacion_num'] = pd.to_numeric(clave['poblacion_total_2026'], errors='coerce')

indispensables_bajo_3000 = clave[clave['poblacion_num'] < 3000].copy()

print(f"Total CLUES clave (indispensables): {len(clave)}")
print(f"CLUES clave con poblacion < 3000: {len(indispensables_bajo_3000)}")
print(f"CLUES clave con poblacion >= 3000: {len(clave[clave['poblacion_num'] >= 3000])}")
print(f"CLUES clave sin dato de poblacion: {clave['poblacion_num'].isna().sum()}")

print("\n=== DESGLOSE POR INSTITUCION ===")
resumen_inst = clave.groupby('institucion').agg(
    total_clave=('clues','count'),
    bajo_3000=('poblacion_num', lambda x: (x < 3000).sum()),
    sobre_3000=('poblacion_num', lambda x: (x >= 3000).sum()),
    sin_dato=('poblacion_num', lambda x: x.isna().sum())
).sort_values('bajo_3000', ascending=False)
print(resumen_inst.to_string())

print("\n=== LISTADO: CLAVE CON < 3000 POBLACION ===")
cols_mostrar = ['clues','institucion','poblacion_total_2026','poblacion_sin_derechohabiencia_2026',
                'poblacion_con_derechohabiencia_2026','consultas_generales','pct_exclusiva','area_exclusiva_km2']
cols_mostrar = [c for c in cols_mostrar if c in indispensables_bajo_3000.columns]
print(indispensables_bajo_3000[cols_mostrar].to_string())

# Guardar resultados
os.makedirs('resultados_indispensabilidad', exist_ok=True)

# Tabla resumen por institucion
resumen_inst.to_csv('resultados_indispensabilidad/indispensables_bajo_3000_resumen.csv')
print("\nGuardado: resultados_indispensabilidad/indispensables_bajo_3000_resumen.csv")

# Listado detallado
indispensables_bajo_3000[cols_mostrar].to_csv('resultados_indispensabilidad/indispensables_bajo_3000_detalle.csv', index=False)
print("Guardado: resultados_indispensabilidad/indispensables_bajo_3000_detalle.csv")
