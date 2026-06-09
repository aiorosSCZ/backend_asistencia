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

def get_test_tokens():
    # Bypass OAuth/SMS flows for unit testing by generating JWT tokens directly
    cliente_token = utils.create_access_token({
        "sub": "1",
        "user_id": 1,
        "role": "cliente",
        "id_tenant": None
    })
    taller_token = utils.create_access_token({
        "sub": "1",
        "user_id": 1,
        "role": "taller",
        "id_tenant": 1
    })
    return cliente_token, taller_token

def test_cuw19_pagos_y_comisiones():
    print("======================================================================")
    print("INICIANDO PRUEBAS DE CAJA BLANCA: CUW-19 - PAGOS Y COMISIONES")
    print("======================================================================")
    
    cliente_token, taller_token = get_test_tokens()
    cliente_headers = {"Authorization": f"Bearer {cliente_token}"}
    taller_headers = {"Authorization": f"Bearer {taller_token}"}
    
    db = SessionLocal()
    
    try:
        # -------------------------------------------------------------
        # ESCENARIO A: Pago y Comisión de Asistencia Vial (10% Comisión)
        # -------------------------------------------------------------
        print("\n--- ESCENARIO A: Asistencia Vial (10% de Comisión de Plataforma) ---")
        
        # 1. Crear un incidente de prueba
        incidente = models.Incidente(
            id_cliente=1,
            id_vehiculo=1,
            id_tenant=1,
            ubicacion_latitud=-17.7780,
            ubicacion_longitud=-63.1750,
            tipo_problema="Llanta Pinchada",
            estado_solicitud="Pendiente"
        )
        db.add(incidente)
        db.commit()
        db.refresh(incidente)
        print(f"[Caja Blanca] Incidente creado con ID: {incidente.id_incidente}")
        
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
        print(f"[Caja Blanca] Asistencia creada con ID: {asistencia.id_asistencia}")
        
        # 3. Crear Intento de Pago vía API
        pago_payload = {
            "id_incidente": incidente.id_incidente,
            "monto": 5000  # 50.00 BOB
        }
        
        print("[Ruta de Código] Llamando POST /api/pagos/crear-intento")
        response = client.post("/api/pagos/crear-intento", json=pago_payload)
        assert response.status_code == 200, f"Error al crear intento de pago: {response.text}"
        
        # Verificar en base de datos el registro del pago y sus comisiones
        db_pago = db.query(models.Pago).filter(models.Pago.id_asistencia == asistencia.id_asistencia).first()
        assert db_pago is not None, "El registro de Pago no se guardó en la BD"
        
        # Fórmulas de caja blanca:
        # subtotal = monto / 100 = 50.0
        # comision = subtotal * 0.10 = 5.0 (10%)
        # total = subtotal = 50.0
        print(f"[Validación Interna] Monto total: {db_pago.monto_total_cliente}")
        print(f"[Validación Interna] Subtotal: {db_pago.monto_subtotal}")
        print(f"[Validación Interna] Comisión calculada (10%): {db_pago.monto_comision_plataforma}")
        
        assert float(db_pago.monto_total_cliente) == 50.0
        assert float(db_pago.monto_subtotal) == 50.0
        assert float(db_pago.monto_comision_plataforma) == 5.0
        assert db_pago.estado_transaccion == "Pendiente"
        print("[OK] Cálculos de comisión del 10% para Asistencia Vial correctos.")

        # -------------------------------------------------------------
        # ESCENARIO B: Pago y Comisión de Reparación Física (5% Comisión)
        # -------------------------------------------------------------
        print("\n--- ESCENARIO B: Reparación en Taller Físico (5% de Comisión de Plataforma) ---")
        
        # 1. Crear Orden de Trabajo
        orden = models.OrdenTrabajo(
            id_tenant=1,
            id_cliente=1,
            id_vehiculo=1,
            estado_trabajo="Diagnóstico"
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)
        print(f"[Caja Blanca] Orden de Trabajo creada con ID: {orden.id_orden}")
        
        # 2. Crear Presupuesto Aprobado
        presupuesto = models.Presupuesto(
            id_orden=orden.id_orden,
            id_tenant=1,
            descripcion_general="Reparación física general",
            estado="Aprobado",
            total_estimado=1000.00  # Bs. 1000.00
        )
        db.add(presupuesto)
        db.commit()
        db.refresh(presupuesto)
        print(f"[Caja Blanca] Presupuesto aprobado creado para Orden #{orden.id_orden} por Bs. {presupuesto.total_estimado}")
        
        # 3. Registrar Pago Reparación vía API
        reparacion_pago_payload = {
            "id_orden": orden.id_orden,
            "metodo_pago": "QR"
        }
        
        print("[Ruta de Código] Llamando POST /api/pagos/reparacion")
        response = client.post("/api/pagos/reparacion", json=reparacion_pago_payload)
        assert response.status_code == 200, f"Error al registrar pago de reparación: {response.text}"
        
        pago_rep_data = response.json()
        
        # Fórmulas de caja blanca para reparación:
        # total_cliente = monto_presupuesto = 1000.00
        # comision_plataforma = total_cliente * 0.05 = 50.00 (5%)
        # subtotal_taller = total_cliente - comision_plataforma = 950.00
        print(f"[Validación Interna] Pago Reparación ID: {pago_rep_data['id_pago']}")
        print(f"[Validación Interna] Monto total cliente: {pago_rep_data['monto_total_cliente']}")
        print(f"[Validación Interna] Comisión Plataforma (5%): {pago_rep_data['monto_comision_plataforma']}")
        print(f"[Validación Interna] Subtotal neto taller: {pago_rep_data['monto_subtotal']}")
        
        assert float(pago_rep_data["monto_total_cliente"]) == 1000.0
        assert float(pago_rep_data["monto_comision_plataforma"]) == 50.0
        assert float(pago_rep_data["monto_subtotal"]) == 950.0
        assert pago_rep_data["estado_transaccion"] == "Completado"
        print("[OK] Cálculos de comisión del 5% para Reparación Física correctos.")
        
        # Verificar cambio de estado en la Orden de Trabajo
        db.refresh(orden)
        print(f"[Caja Blanca] Estado final de Orden de Trabajo #{orden.id_orden}: '{orden.estado_trabajo}'")
        assert orden.estado_trabajo == "Entregado", "La orden de trabajo debería estar en estado 'Entregado'"
        print("[OK] Transición de estado a 'Entregado' realizada con éxito.")

        # -------------------------------------------------------------
        # ESCENARIO C: Intentar duplicar pago de reparación (Debe fallar)
        # -------------------------------------------------------------
        print("\n--- ESCENARIO C: Validación de pago duplicado ---")
        print("[Ruta de Código] Llamando POST /api/pagos/reparacion por segunda vez para la misma orden...")
        response = client.post("/api/pagos/reparacion", json=reparacion_pago_payload)
        assert response.status_code == 400, "Se esperaba error 400 al duplicar pago"
        print(f"[OK] Validación de duplicados exitosa. Mensaje recibido: {response.json()['detail']}")
        
        # -------------------------------------------------------------
        # ESCENARIO D: Intentar pagar orden sin presupuesto aprobado (Debe fallar)
        # -------------------------------------------------------------
        print("\n--- ESCENARIO D: Validación de pago sin presupuesto aprobado ---")
        orden_sin_pres = models.OrdenTrabajo(
            id_tenant=1,
            id_cliente=1,
            id_vehiculo=1,
            estado_trabajo="Diagnóstico"
        )
        db.add(orden_sin_pres)
        db.commit()
        db.refresh(orden_sin_pres)
        
        payload_sin_pres = {
            "id_orden": orden_sin_pres.id_orden,
            "metodo_pago": "Tarjeta"
        }
        print("[Ruta de Código] Llamando POST /api/pagos/reparacion para orden sin presupuesto...")
        response = client.post("/api/pagos/reparacion", json=payload_sin_pres)
        assert response.status_code == 400, "Se esperaba error 400"
        print(f"[OK] Validación de presupuesto ausente exitosa. Mensaje recibido: {response.json()['detail']}")

        print("\n======================================================================")
        print("🎉 ¡TODAS LAS PRUEBAS DE CAJA BLANCA PARA CUW-19 PASARON CON ÉXITO! 🎉")
        print("======================================================================")

    finally:
        # Limpieza de registros de prueba creados para evitar contaminar la BD local
        print("\n[Limpieza] Eliminando registros temporales de prueba...")
        db.query(models.PagoReparacion).delete()
        db.query(models.Pago).delete()
        db.query(models.Presupuesto).delete()
        db.query(models.OrdenTrabajo).delete()
        db.query(models.Asistencia).delete()
        db.query(models.Incidente).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_cuw19_pagos_y_comisiones()
