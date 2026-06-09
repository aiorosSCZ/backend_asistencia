import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models
from sqlalchemy import func, extract

db = SessionLocal()
try:
    total = db.query(models.Incidente).count()
    print(f"Total incidents: {total}")
    
    # Count by year/month
    by_month = db.query(
        extract('year', models.Incidente.fecha_hora_reporte).label('year'),
        extract('month', models.Incidente.fecha_hora_reporte).label('month'),
        func.count(models.Incidente.id_incidente)
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    print("\nIncidents by month:")
    for y, m, count in by_month:
        print(f"  {int(y)}-{int(m):02d}: {count}")
        
    # Let's print some sample incidents from June 2026 (year 2026, month 6)
    sample = db.query(models.Incidente).filter(
        extract('year', models.Incidente.fecha_hora_reporte) == 2026,
        extract('month', models.Incidente.fecha_hora_reporte) == 6
    ).limit(5).all()
    print("\nSamples from June 2026:")
    for inc in sample:
        print(f"  ID: {inc.id_incidente}, Date: {inc.fecha_hora_reporte}, Lat: {inc.ubicacion_latitud}, Lng: {inc.ubicacion_longitud}")
finally:
    db.close()
