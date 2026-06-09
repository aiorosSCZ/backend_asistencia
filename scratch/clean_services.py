import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from routers.talleres import get_all_servicios

def clean():
    db = SessionLocal()
    try:
        print("Iniciando limpieza y sincronizacion de servicios en la base de datos...")
        servicios = get_all_servicios(db)
        print(f"Sincronizacion completada. Total servicios registrados: {len(servicios)}")
        for s in servicios:
            print(f"  - [{s['id_servicio']}] {s['nombre_servicio']}")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean()
