import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

print("Iniciando eliminación de incidentes estáticos...")
db = SessionLocal()
try:
    # IDs de incidentes estáticos (semilla 1 a 7)
    static_ids = [1, 2, 3, 4, 5, 6, 7]
    
    # 1. Eliminar Asistencias asociadas
    asistencias_deleted = db.query(models.Asistencia).filter(models.Asistencia.id_incidente.in_(static_ids)).delete(synchronize_session=False)
    print(f"Asistencias eliminadas: {asistencias_deleted}")
    
    # 2. Eliminar Cotizaciones asociadas
    cotizaciones_deleted = db.query(models.Cotizacion).filter(models.Cotizacion.id_incidente.in_(static_ids)).delete(synchronize_session=False)
    print(f"Cotizaciones eliminadas: {cotizaciones_deleted}")
    
    # 3. Eliminar Evidencias asociadas
    evidencias_deleted = db.query(models.Evidencia).filter(models.Evidencia.id_incidente.in_(static_ids)).delete(synchronize_session=False)
    print(f"Evidencias eliminadas: {evidencias_deleted}")
    
    # 4. Eliminar Analisis IA asociados
    analisis_deleted = db.query(models.AnalisisIA).filter(models.AnalisisIA.id_incidente.in_(static_ids)).delete(synchronize_session=False)
    print(f"Análisis IA eliminados: {analisis_deleted}")
    
    # 5. Eliminar los Incidentes
    incidentes_deleted = db.query(models.Incidente).filter(models.Incidente.id_incidente.in_(static_ids)).delete(synchronize_session=False)
    print(f"Incidentes estáticos eliminados: {incidentes_deleted}")
    
    db.commit()
    print("¡Operación completada con éxito!")
except Exception as e:
    db.rollback()
    print(f"Error al eliminar datos estáticos: {e}")
finally:
    db.close()
