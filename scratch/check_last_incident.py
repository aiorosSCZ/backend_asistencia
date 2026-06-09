import os
import sys

# Agregar el directorio backend al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
import models

db = SessionLocal()
try:
    print("--- Últimos 5 Incidentes ---")
    incidentes = db.query(models.Incidente).order_by(models.Incidente.id_incidente.desc()).limit(5).all()
    if not incidentes:
        print("No hay incidentes.")
    else:
        for incidente in incidentes:
            print(f"ID Incidente: {incidente.id_incidente}")
            print(f"Cliente: {incidente.cliente.nombres if incidente.cliente else 'N/A'}")
            print(f"Estado Solicitud: {incidente.estado_solicitud}")
            print(f"Tipo Problema: {incidente.tipo_problema}")
            print(f"Nivel Prioridad: {incidente.nivel_prioridad}")
            print(f"Descripción Manual: {incidente.descripcion_manual}")
            print(f"Fecha Reporte: {incidente.fecha_hora_reporte}")
            
            print("Evidencias:")
            evidencias = db.query(models.Evidencia).filter(models.Evidencia.id_incidente == incidente.id_incidente).all()
            for ev in evidencias:
                print(f"  - Tipo: {ev.tipo_recurso}, Archivo: {ev.url_archivo}")
                
            print("Análisis IA:")
            analisis = db.query(models.AnalisisIA).filter(models.AnalisisIA.id_incidente == incidente.id_incidente).first()
            if analisis:
                print(f"  - Clasificación sugerida: {analisis.clasificacion_sugerida}")
                print(f"  - Resumen estructurado: {analisis.resumen_estructurado}")
                print(f"  - Diagnóstico cliente: {analisis.diagnostico_cliente}")
            else:
                print("  - No hay registro de Análisis IA.")
            print("-" * 40)
finally:
    db.close()
