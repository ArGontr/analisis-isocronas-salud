"""
Paleta de colores institucionales para todos los reportes y mapas.
Extraída de 'colores institucionales.html'.
"""

# =============================================================================
# PALETA NEUTRA Y ESPECIALIDADES
# =============================================================================
NEGRO          = "#161a1d"  # PANTONE Neutral Black C
VINO           = "#9b2247"  # PANTONE 7420 C – Borgoña principal
VERDE_OSCURO   = "#1e5b4f"  # PANTONE 626 C
AMARILLO_MOSTAZA = "#a57f2c"  # Amarillo mostaza
GRIS           = "#98989A"  # PANTONE Cool Gray 7 C
BORGONA_OSCURO = "#611232"  # PANTONE Borgoña Oscuro
VERDE_PETROLEO = "#002f2a"  # PANTONE Verde Petróleo
CREMA_DORADA   = "#e6d194"  # PANTONE Crema Dorada

# =============================================================================
# SEMÁFORO COMPACTO (4 colores)
# =============================================================================
ROJO_ALERTA        = "#D41111"  # 🔴 Rojo Alerta
AMARILLO_PRECAUCION = "#F1D54A"  # 🟡 Amarillo Precaución
VERDE_CLARO        = "#88A91E"  # 🌿 Verde Claro
VERDE_CONSOLIDADO  = "#0D5D2A"  # 🌲 Verde Consolidado

# =============================================================================
# SEMÁFORO EXTENDIDO
# =============================================================================
ROJO_URGENTE       = "#b52920"  # ⚠️ Rojo Urgente
AMBAR              = "#ffa000"  # 🧡 Ámbar
VERDE_OPTIMO       = "#009639"  # ✅ Verde Óptimo
VERDE_SATISFACTORIO = "#78be3c"  # 🌿 Verde Satisfactorio
NARANJA            = "#f27822"  # 🟠 Naranja
VERDE_OSCURO_SEMAFORO = "#226030"  # 🌲 Verde Consolidado (alternativo)

# =============================================================================
# COLORES SEMÁNTICOS PARA REPORTES
# =============================================================================
# Uso recomendado en gráficos, tablas y mapas
PRIMARIO      = VINO               # Headers, acentos principales
SECUNDARIO    = BORGONA_OSCURO     # Headers de tabla, énfasis fuerte
EXITO         = VERDE_CONSOLIDADO  # Clave, estratégico, óptimo
EXITO_ALT     = VERDE_OSCURO       # Alternativa verde
ADVERTENCIA   = AMARILLO_PRECAUCION # Precaución, intermedio
ALERTA        = ROJO_ALERTA        # Alerta, redundante, problemas
ALERTA_ALT    = ROJO_URGENTE       # Urgencia extrema
VULNERABLE    = NARANJA            # Zonas vulnerables
NEUTRO        = GRIS               # Redundante suave, neutral
FONDO_DESTACADO = CREMA_DORADA     # Fondos destacados
TEXTO         = NEGRO              # Texto principal

# =============================================================================
# ESCALAS PREARMADAS
# =============================================================================
ESCALA_SEMAFORO_4 = [ROJO_ALERTA, AMARILLO_PRECAUCION, VERDE_CLARO, VERDE_CONSOLIDADO]
ESCALA_SEMAFORO_3 = [ROJO_ALERTA, AMARILLO_PRECAUCION, VERDE_CONSOLIDADO]
ESCALA_BORGONA    = [BORGONA_OSCURO, VINO, CREMA_DORADA]
ESCALA_VERDE      = [VERDE_PETROLEO, VERDE_OSCURO, VERDE_CONSOLIDADO, VERDE_CLARO]

# Paleta categórica para gráficos de barras / pastel
PALETA_CATEGORICA = [VERDE_CONSOLIDADO, VINO, AMARILLO_PRECAUCION, VERDE_OSCURO,
                     ROJO_ALERTA, NARANJA, VERDE_CLARO, GRIS, CREMA_DORADA]

# =============================================================================
# MAPEO SEMÁNTICO PARA MAPAS FOLIUM
# =============================================================================
COLORES_MAPA_CASAS = {
    "estrategica_muy_descubierta": VERDE_CONSOLIDADO,   # >50% descubierta
    "estrategica_algo_descubierta": AMARILLO_PRECAUCION, # >0% descubierta
    "estrategica_vulnerable": NARANJA,                  # cubre vulnerable
    "estrategica_otra": VERDE_OSCURO,                   # otra estratégica
    "redundante": GRIS,                                  # redundante
}

COLORES_MAPA_ISOCRONAS = {
    "redundante": ROJO_ALERTA,
    "no_redundante": VERDE_CONSOLIDADO,
    "desierto": AMARILLO_PRECAUCION,
    "clave_alta": BORGONA_OSCURO,      # ≥50% exclusiva
    "clave_media": VINO,               # 25-50% exclusiva
    "clave_baja": AMARILLO_PRECAUCION, # <25% exclusiva
    "vulnerable": ROJO_ALERTA,
    "alta_redundancia": VERDE_OSCURO,
}
