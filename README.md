# Análisis de Isocronas de Centros de Salud

Este repositorio contiene un análisis reproducible para identificar **áreas de servicio redundantes**, **desiertos de atención** y **isocronas clave/indispensables** a partir de isocronas de centros de salud (CLUES).

## ¿Qué hace?

Dado un conjunto de isocronas (áreas de cobertura) de centros de salud, los scripts determinan:

1. **Redundancia**: ¿Qué isocronas tienen una superposición significativa con otras? Una isocrona se marca como redundante cuando más del 50% de su área (medida en celdas de un grid) también está cubierta por al menos otra isocrona.

2. **Indispensabilidad**: ¿Qué isocronas son clave porque cubren zonas que ninguna otra cubre?

3. **Clasificación con población**: Integra datos de población y producción para clasificar CLUES en:
   - **clave**: Indispensables (tienen cobertura exclusiva)
   - **complementaria**: Redundantes, población < 3,000 (vinculables a otra CLUES)
   - **ideal_normativo**: Redundantes, población ≥ 3,000 (cumplen ideal normativo)

4. **Desiertos de atención**: ¿Qué áreas quedarían descubiertas si se eliminan isocronas?

## Método

Para hacer el análisis escalable a miles de isocronas, se utiliza un **enfoque de grid (rasterización vectorial)** en lugar de intersecciones polígono-a-polígono:

1. Se simplifican las geometrías para reducir vértices (~200m de tolerancia).
2. Se crea un grid regular (fishnet) sobre la extensión de las isocronas (10km).
3. Se hace un *spatial join* entre isocronas y celdas del grid.
4. Se cuentan isocronas por celda.
5. Se calculan métricas de redundancia, indispensabilidad y desiertos.

Este método es **O(n)** con respecto al número de isocronas y permite procesar ~11,500 polígonos en ~12 segundos.

## Requisitos

```bash
pip install -r requirements.txt
```

Dependencias principales:
- `geopandas`
- `shapely`
- `matplotlib`
- `numpy`
- `pandas`
- `folium`
- `openpyxl`

## Uso

### Análisis de redundancia y desiertos

```bash
python analisis_completo.py iso_upn_unido_15km.gpkg -o resultados_completos
```

### Análisis de indispensabilidad

```bash
python indispensabilidad.py iso_upn_unido_15km.gpkg -o resultados_indispensabilidad
```

### Clasificación completa con población

```bash
python clasificacion_completa.py
```

Requiere el archivo `datos_pob_y_prod.xlsx` con columnas: `clues`, `institucion`, `poblacion_total_2026`, `poblacion_sin_derechohabiencia_2026`, `poblacion_con_derechohabiencia_2026`, `consultas_generales`.

### Normalizar CLUES (IMS → IMO)

```bash
python normalizar_clues.py
```

Requiere `equivalencia.xlsx` con columnas `clues_imo` y `clues_ims`.

## Resultados principales

Sobre **11,494 isocronas** de 15 km de radio:

| Métrica | Valor |
|---------|-------|
| Isocronas clave (indispensables) | 759 (6.6%) |
| Isocronas redundantes | 10,735 (93.4%) |
| Zonas vulnerables (solo 1 isocrona) | 1,899 celdas |
| Área vulnerable | 189,900 km² |

### Clasificación con población

| Categoría | N° CLUES | Descripción |
|-----------|----------|-------------|
| clave | 759 | Indispensables (cobertura exclusiva) |
| complementaria | 5,521 | Redundantes, población < 3,000 |
| ideal_normativo | 5,214 | Redundantes, población ≥ 3,000 |

### Por institución

| Institución | clave | complementaria | ideal_normativo |
|-------------|-------|----------------|-----------------|
| IMB | 463 | 3,655 | 4,120 |
| IMO | 296 | 1,831 | 1,094 |

## Archivos generados

| Archivo | Descripción |
|---------|-------------|
| `indispensabilidad.gpkg` / `.csv` | Isocronas con métricas de exclusividad |
| `zonas_vulnerables.gpkg` / `.csv` | Celdas con cobertura única |
| `reporte_indispensabilidad.html` | Mapa interactivo (OpenStreetMap) |
| `indispensabilidad.png` | Mapa estático |
| `base_categorizada.csv` | CLUES con categoría, población, vínculo |
| `base_clues_normalizada.csv` | CLUES con código IMS normalizado a IMO |
| `vinculos_complementarias.csv` | Pares complementaria ↔ centro vinculado |
| `resumen_por_institucion_categoria.csv` | Resumen agregado |

## Estructura del repositorio

```
.
├── analisis_completo.py              # Análisis de redundancia
├── indispensabilidad.py              # Análisis de indispensabilidad
├── clasificacion_completa.py         # Clasificación con población
├── normalizar_clues.py               # Normaliza IMS → IMO
├── reclasificar_ideal_normativo.py   # Reclasifica ≥3,000 a ideal_normativo
├── tabla_indispensables_bajo_3000.py # Tabla de clave con <3,000 pob
├── tabla_complementarias_corregido.py # Resumen de vínculos por institución
├── requirements.txt                  # Dependencias
├── README.md                         # Este archivo
└── resultados_indispensabilidad/     # Resultados
```

## Licencia

MIT
