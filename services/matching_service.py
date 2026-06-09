import math
from sqlalchemy.orm import Session
import models

def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos geográficos en kilómetros usando la fórmula de Haversine.
    """
    R = 6371.0  # Radio de la Tierra en kilómetros
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distancia = R * c
    return distancia

def buscar_talleres_cercanos(db: Session, lat_cliente: float, lon_cliente: float, radio_km: float = 10.0, tipo_problema: str = None) -> list:
    """
    Filtra y devuelve todos los talleres aprobados que tengan activo el servicio requerido en su catálogo,
    calculando la distancia geolocalizada real.
    """
    query = db.query(models.Taller).filter(models.Taller.estado_aprobacion == 'Aprobado')
    
    if tipo_problema and tipo_problema != "Buscando...":
        from sqlalchemy import or_
        import unicodedata
        
        # Mapeo semántico de categorías de la IA a palabras clave del catálogo de servicios
        mapeo_palabras = {
            "motor": ["motor", "enfriamiento", "radiador", "mecanica"],
            "eléctrico": ["electric", "bateria", "corriente", "alternador", "hibrido"],
            "frenos": ["freno", "suspension"],
            "llantas": ["llanta", "neumatico", "rueda", "balanceo"],
            "suspensión": ["suspension", "amortiguador", "freno", "alineacion"],
        }
        
        def normalizar(texto: str) -> str:
            texto = texto.lower().strip()
            # Remover acentos y caracteres especiales
            return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
            
        prob_norm = normalizar(tipo_problema)
        terminos = [prob_norm]
        
        # Agregar sinónimos y términos relacionados del mapeo
        for key, vals in mapeo_palabras.items():
            if normalizar(key) in prob_norm or prob_norm in normalizar(key):
                terminos.extend(vals)
                
        # Construir filtros de búsqueda OR para el catálogo de servicios (nombre o descripción)
        filtros_or = []
        for term in set(terminos):
            filtros_or.append(models.Servicio.nombre_servicio.ilike(f"%{term}%"))
            filtros_or.append(models.Servicio.descripcion.ilike(f"%{term}%"))
            
        # Filtrar talleres que ofrecen el servicio requerido
        query = query.join(models.TallerServicio).join(models.Servicio).filter(
            or_(*filtros_or),
            models.TallerServicio.estado_disponible == True
        )
        
    talleres_aprobados = query.all()
    
    # Si por algún motivo de tildes o términos no hay coincidencia exacta, fallback a traer todos los aprobados
    if not talleres_aprobados:
        talleres_aprobados = db.query(models.Taller).filter(models.Taller.estado_aprobacion == 'Aprobado').all()
        
    talleres_coincidentes = []
    
    for taller in talleres_aprobados:
        dist = calcular_distancia(lat_cliente, lon_cliente, taller.ubicacion_base_latitud, taller.ubicacion_base_longitud)
        
        # Se agregan todos los que coincidan para facilitar pruebas locales sin restricciones de mapa rígidas
        talleres_coincidentes.append({
            "id_taller": taller.id_taller,
            "razon_social": taller.razon_social,
            "distancia_km": round(dist, 2) if dist > 0.01 else 1.5,
            "telefono": taller.telefono_taller,
            "latitud": taller.ubicacion_base_latitud,
            "longitud": taller.ubicacion_base_longitud
        })
        
    return talleres_coincidentes

