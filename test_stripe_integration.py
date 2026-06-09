import sys
import os

# Append current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stderr for UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models
import utils

client = TestClient(app)

def test_stripe_payment_flow():
    print("======================================================================")
    print("INICIANDO PRUEBAS DE INTEGRACIÓN: FLUJO DE PAGO Y CONFIRMACIÓN STRIPE")
    print("======================================================================")
    
    db = SessionLocal()
    
    try:
        # 1. Crear un incidente de prueba en estado 'Por Pagar'
        incidente = models.Incidente(
            id_cliente=1,
            id_vehiculo=1,
            id_tenant=1,
            ubicacion_latitud=-17.7780,
            ubicacion_longitud=-63.1750,
            tipo_problema="Llanta Pinchada",
            estado_solicitud="Por Pagar"
        )
        db.add(incidente)
        db.commit()
        db.refresh(incidente)
        print(f"[Paso 1] Incidente creado en BD con ID: {incidente.id_incidente} y estado: {incidente.estado_solicitud}")
        
        # 2. Crear una asistencia asociada
        asistencia = models.Asistencia(
            id_incidente=incidente.id_incidente,
            id_taller=1,
            id_tecnico=1,
            id_tenant=1
        )
        db.add(asistencia)
        db.commit()
        db.refresh(asistencia)
        print(f"[Paso 2] Asistencia creada en BD con ID: {asistencia.id_asistencia}")
        
        # 3. Llamar a crear-intento (debe crear y auto-confirmar el intent en Stripe ya que usa sk_test)
        pago_payload = {
            "id_incidente": incidente.id_incidente,
            "monto": 5000  # 50.00 BOB
        }
        print("[Paso 3] Llamando a POST /api/pagos/crear-intento...")
        response = client.post("/api/pagos/crear-intento", json=pago_payload)
        assert response.status_code == 200, f"Error al crear intento de pago: {response.text}"
        
        res_data = response.json()
        payment_intent_id = res_data.get("paymentIntentId")
        print(f"         [OK] Intento de pago creado. Stripe PaymentIntentID: {payment_intent_id}")
        assert payment_intent_id is not None, "El paymentIntentId no debe ser nulo"
        
        # Verificar que el pago se haya guardado como 'Pendiente' inicialmente
        db_pago = db.query(models.Pago).filter(models.Pago.id_asistencia == asistencia.id_asistencia).first()
        assert db_pago is not None, "El pago no se registró en base de datos"
        assert db_pago.estado_transaccion == "Pendiente", f"El estado esperado era 'Pendiente', se obtuvo: {db_pago.estado_transaccion}"
        print(f"         [OK] Registro de Pago en BD guardado como 'Pendiente'. Subtotal: {db_pago.monto_subtotal}")
        
        # 4. Confirmar el pago llamando a /confirmar-pago
        confirmar_payload = {
            "id_incidente": incidente.id_incidente,
            "payment_intent_id": payment_intent_id
        }
        print("[Paso 4] Llamando a POST /api/pagos/confirmar-pago...")
        confirm_response = client.post("/api/pagos/confirmar-pago", json=confirmar_payload)
        assert confirm_response.status_code == 200, f"Error al confirmar el pago: {confirm_response.text}"
        print(f"         [OK] Respuesta del backend: {confirm_response.json()}")
        
        # 5. Validar que el pago ahora esté en estado 'Aprobado' y el incidente en 'Completado'
        db.refresh(db_pago)
        db.refresh(incidente)
        
        assert db_pago.estado_transaccion == "Aprobado", f"Se esperaba estado de pago 'Aprobado', se obtuvo: {db_pago.estado_transaccion}"
        assert incidente.estado_solicitud == "Completado", f"Se esperaba estado de incidente 'Completado', se obtuvo: {incidente.estado_solicitud}"
        print(f"[Paso 5] Verificación de BD exitosa:")
        print(f"         - Estado transacción de pago: {db_pago.estado_transaccion}")
        print(f"         - Estado solicitud incidente: {incidente.estado_solicitud}")
        
        print("\n======================================================================")
        print("🎉 ¡EL FLUJO DE PAGO Y CONFIRMACIÓN DE STRIPE SE VERIFICÓ CON ÉXITO! 🎉")
        print("======================================================================")
        
    finally:
        # Limpieza
        print("\n[Limpieza] Eliminando registros temporales de prueba...")
        db.query(models.Pago).filter(models.Pago.id_asistencia == asistencia.id_asistencia).delete()
        db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == asistencia.id_asistencia).delete()
        db.query(models.Incidente).filter(models.Incidente.id_incidente == incidente.id_incidente).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_stripe_payment_flow()
