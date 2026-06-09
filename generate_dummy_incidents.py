import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

# Configurar BD
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/emergencias_vehiculares"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Obtener el primer cliente y vehículo
    cliente = db.query(models.Cliente).first()
    vehiculo = db.query(models.Vehiculo).first()
    tenant = db.query(models.Tenant).first()

    if not cliente or not vehiculo:
        print("No hay clientes o vehículos en la BD. Por favor crea uno primero.")
        sys.exit()

    id_cliente = cliente.id_cliente
    id_vehiculo = vehiculo.id_vehiculo
    id_tenant = tenant.id_tenant if tenant else None

    # Coordenadas alrededor de Santa Cruz de la Sierra (-17.7833, -63.1821)
    puntos_calientes = [
        (-17.7800, -63.1800, "Mecánica"), # Cerca del centro
        (-17.7850, -63.1850, "Llanta"),
        (-17.7780, -63.1750, "Batería"),
        (-17.7900, -63.1900, "Mecánica"), # Más alejados
        (-17.7700, -63.1700, "Choque"),
        (-17.7810, -63.1810, "Mecánica"), # Aglomeración en el centro
        (-17.7820, -63.1830, "Llanta")
    ]

    for lat, lng, tipo in puntos_calientes:
        nuevo_incidente = models.Incidente(
            id_cliente=id_cliente,
            id_vehiculo=id_vehiculo,
            id_tenant=id_tenant,
            ubicacion_latitud=lat,
            ubicacion_longitud=lng,
            tipo_problema=tipo,
            estado_solicitud="Pendiente"
        )
        db.add(nuevo_incidente)
    
    db.commit()
    print("¡Generados 7 incidentes falsos en Santa Cruz para probar el mapa!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
