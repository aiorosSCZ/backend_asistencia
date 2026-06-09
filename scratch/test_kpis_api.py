import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from routers.admin import get_admin_kpis

db = SessionLocal()
try:
    res = get_admin_kpis(
        filter_type="mes",
        filter_value="2026-06",
        taller_id=None,
        db=db,
        current_user={"role": "superadmin"}
    )
    print("KPI call done. Heatmap length:", len(res["heatmap"]))
finally:
    db.close()
