import os
import sys

# Agregar el directorio backend al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models
import asyncio

async def test_cancel():
    db = SessionLocal()
    try:
        incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == 19).first()
        if not incidente:
            print("No existe el incidente 19.")
            return
            
        print(f"Incidente 19: id_cliente={incidente.id_cliente}, estado={incidente.estado_solicitud}")
        
        # Simular lo que hace el endpoint /cancelar
        motivo = "Prueba de cancelación"
        incidente.estado_solicitud = 'cancelado'
        incidente.motivo_cancelacion = motivo
        
        asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == 19).first()
        if asistencia and asistencia.tecnico:
            print("Liberando técnico...")
            asistencia.tecnico.estado_operativo = 'Disponible'
            
        db.commit()
        print("Commit de base de datos exitoso!")
        
        if asistencia and asistencia.id_taller:
            print(f"Enviando notificación WS al taller {asistencia.id_taller}...")
            # Importar manager de main
            from main import manager
            await manager.send_personal_message({
                "type": "INCIDENTE_CANCELADO",
                "id_incidente": 19,
                "motivo": motivo
            }, asistencia.id_taller)
            print("WebSocket enviado exitosamente!")
        else:
            print("No hay asistencia asociada o no tiene taller asignado. No se requiere enviar WebSocket.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test_cancel())
