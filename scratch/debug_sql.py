import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models
from datetime import datetime, timedelta
import calendar

db = SessionLocal()
try:
    filter_value = "2026-06"
    start_date = datetime.strptime(filter_value, "%Y-%m")
    _, last_day = calendar.monthrange(start_date.year, start_date.month)
    end_date = start_date.replace(day=last_day) + timedelta(days=1)
    
    print(f"Filtering between {start_date} and {end_date}")
    
    q_incidente = db.query(models.Incidente)
    print(f"Base query count: {q_incidente.count()}")
    
    q_filtered = q_incidente.filter(
        models.Incidente.fecha_hora_reporte >= start_date, 
        models.Incidente.fecha_hora_reporte < end_date
    )
    print(f"Filtered query count: {q_filtered.count()}")
    
    # Let's print the actual SQL compiled
    print("\nSQL Query:")
    print(str(q_filtered.statement.compile(compile_kwargs={"literal_binds": True})))
    
finally:
    db.close()
