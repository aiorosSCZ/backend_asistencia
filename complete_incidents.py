from database import SessionLocal
import models

def complete_all_active_incidents():
    db = SessionLocal()
    try:
        # Buscar incidentes en estado 'Pendiente' o 'Cotización Aceptada'
        active_incidents = db.query(models.Incidente).filter(
            models.Incidente.estado_solicitud.in_(['Pendiente', 'Cotización Aceptada'])
        ).all()
        
        count = len(active_incidents)
        print(f"Encontrados {count} incidentes activos pendientes/aceptados.")
        
        for inc in active_incidents:
            inc.estado_solicitud = 'Completado'
            
        db.commit()
        print(f"SUCCESS: Se han completado {count} incidentes con exito.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: Error al completar incidentes: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    complete_all_active_incidents()
