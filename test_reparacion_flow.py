import sys
import os

# Append current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force stdout/stderr to use UTF-8 to handle any unicode characters safely on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models
import utils

client = TestClient(app)

def get_tokens():
    # Helper to generate JWT tokens directly to bypass SMS/external login flows for testing
    taller_token = utils.create_access_token({
        "sub": "1",
        "user_id": 1,
        "role": "taller",
        "id_tenant": 1
    })
    
    cliente_token = utils.create_access_token({
        "sub": "1",
        "user_id": 1,
        "role": "cliente",
        "id_tenant": None
    })
    
    return taller_token, cliente_token

def test_full_reparacion_flow():
    print("Iniciando pruebas del Flujo Completo de Reparacion Fisica en Taller...")
    
    # 1. Obtener tokens JWT
    taller_token, cliente_token = get_tokens()
    taller_headers = {"Authorization": f"Bearer {taller_token}"}
    cliente_headers = {"Authorization": f"Bearer {cliente_token}"}
    
    # 2. Crear una Orden de Trabajo (Taller)
    print("\n[Paso 1] Creando Orden de Trabajo desde Taller...")
    orden_payload = {
        "id_cliente": 1,
        "id_vehiculo": 1,
        "estado_recepcion": "Abolladura leve en puerta, 1/4 tanque",
        "fecha_compromiso_entrega": "2026-06-15T18:00:00"
    }
    
    response = client.post("/api/reparaciones/ordenes", json=orden_payload, headers=taller_headers)
    assert response.status_code == 200, f"Error creando orden: {response.text}"
    orden_data = response.json()
    id_orden = orden_data["id_orden"]
    print(f"[OK] Orden de Trabajo creada con ID: {id_orden}. Estado actual: {orden_data['estado_trabajo']}")
    assert orden_data["estado_trabajo"] == "Diagnóstico"
    
    # 3. Crear Presupuesto con items (Taller)
    print("\n[Paso 2] Registrando Presupuesto con categorias, criticidad y grupos de falla...")
    presupuesto_payload = {
        "descripcion_general": "Presupuesto de reparacion general",
        "version": "v1",
        "detalles": [
            {
                "categoria": "Motor",
                "grupo_falla": "Sistema de Transmision",
                "es_critico": True,
                "tipo_item": "Repuesto",
                "item_descripcion": "Kit de embrague nuevo",
                "cantidad": 1,
                "precio_unitario": 350.0
            },
            {
                "categoria": "Suspension",
                "grupo_falla": "Amortiguadores",
                "es_critico": False,
                "tipo_item": "Mano de Obra",
                "item_descripcion": "Cambio amortiguadores delanteros",
                "cantidad": 1,
                "precio_unitario": 100.0
            }
        ]
    }
    
    response = client.post(f"/api/reparaciones/ordenes/{id_orden}/presupuestos", json=presupuesto_payload, headers=taller_headers)
    assert response.status_code == 200, f"Error creando presupuesto: {response.text}"
    presupuesto_data = response.json()
    id_presupuesto = presupuesto_data["id_presupuesto"]
    print(f"[OK] Presupuesto creado con ID: {id_presupuesto}. Total estimado: {presupuesto_data['total_estimado']}")
    assert len(presupuesto_data["detalles"]) == 2
    
    # Verificar que el estado de la orden paso a "Presupuestado"
    response = client.get(f"/api/reparaciones/ordenes/{id_orden}", headers=taller_headers)
    assert response.json()["estado_trabajo"] == "Presupuestado"
    print("[OK] Estado de la orden cambio automaticamente a 'Presupuestado'")
    
    # 4. Intentar rechazar un grupo critico (debe fallar)
    print("\n[Paso 3] Probando validacion de criticidad (Intentar rechazar item critico)...")
    aprobacion_invalida_payload = {
        "grupos": [
            {"grupo_falla": "Sistema de Transmision", "aprobado": False},  # Critico
            {"grupo_falla": "Amortiguadores", "aprobado": True}  # No critico
        ]
    }
    response = client.put(f"/api/reparaciones/presupuestos/{id_presupuesto}/aprobar", json=aprobacion_invalida_payload, headers=cliente_headers)
    assert response.status_code == 400, "Se esperaba error 400 al intentar rechazar un grupo critico"
    print("[OK] Rechazo bloqueado correctamente con mensaje:", response.json()["detail"])
    
    # 5. Aprobacion valida (Aprobar critico, rechazar no critico)
    print("\n[Paso 4] Aprobacion parcial valida (Aprobar critico, rechazar no critico)...")
    aprobacion_valida_payload = {
        "grupos": [
            {"grupo_falla": "Sistema de Transmision", "aprobado": True},  # Critico
            {"grupo_falla": "Amortiguadores", "aprobado": False}  # No critico
        ]
    }
    response = client.put(f"/api/reparaciones/presupuestos/{id_presupuesto}/aprobar", json=aprobacion_valida_payload, headers=cliente_headers)
    assert response.status_code == 200, f"Error al aprobar presupuesto: {response.text}"
    aprobado_data = response.json()
    print(f"[OK] Presupuesto aprobado parcialmente. Estado: {aprobado_data['estado']}. Total aprobado: {aprobado_data['total_estimado']}")
    assert aprobado_data["estado"] == "Aprobado Parcial"
    assert aprobado_data["total_estimado"] == 350.0  # Solo el del embrague
    
    # Verificar que el estado de la orden paso a "En Reparación"
    response = client.get(f"/api/reparaciones/ordenes/{id_orden}", headers=taller_headers)
    assert response.json()["estado_trabajo"] == "En Reparación"
    print("[OK] Estado de la orden cambio a 'En Reparación'")
    
    # 6. Cambiar estado a "Listo para Entrega" (Taller)
    print("\n[Paso 5] Taller finaliza la reparacion y la marca como 'Listo para Entrega'...")
    estado_payload = {
        "estado_trabajo": "Listo para Entrega",
        "comentario": "Reparacion del sistema de transmision finalizada con exito."
    }
    response = client.post(f"/api/reparaciones/ordenes/{id_orden}/estado", json=estado_payload, headers=taller_headers)
    assert response.status_code == 200, f"Error actualizando estado: {response.text}"
    assert response.json()["estado_trabajo"] == "Listo para Entrega"
    print("[OK] Estado de la orden cambiado a 'Listo para Entrega'")
    
    # 7. Realizar pago de la reparacion (Cliente)
    print("\n[Paso 6] Registrando pago de reparacion...")
    pago_payload = {
        "id_orden": id_orden,
        "metodo_pago": "Tarjeta de Credito"
    }
    response = client.post("/api/pagos/reparacion", json=pago_payload, headers=cliente_headers)
    assert response.status_code == 200, f"Error registrando pago: {response.text}"
    pago_data = response.json()
    print(f"[OK] Pago registrado con exito. ID Pago: {pago_data['id_pago']}, Total: Bs. {pago_data['monto_total_cliente']}, Comision Plataforma (5%): Bs. {pago_data['monto_comision_plataforma']}")
    assert pago_data["estado_transaccion"] == "Completado"
    
    # Verificar que la orden cambio a "Entregado"
    response = client.get(f"/api/reparaciones/ordenes/{id_orden}", headers=taller_headers)
    assert response.json()["estado_trabajo"] == "Entregado"
    print("[OK] Estado final de la orden cambio automaticamente a 'Entregado'")
    
    # 8. Consultar la bitacora/timeline
    print("\n[Paso 7] Verificando historial/bitacora de cambios de estado...")
    response = client.get(f"/api/reparaciones/ordenes/{id_orden}/bitacora", headers=taller_headers)
    assert response.status_code == 200, f"Error obteniendo bitacora: {response.text}"
    bitacoras = response.json()
    print(f"[OK] Se encontraron {len(bitacoras)} hitos en la bitacora:")
    for b in bitacoras:
        print(f"   - {b['estado_anterior']} -> {b['nuevo_estado']} | Comentario: {b['comentario']}")
    
    assert len(bitacoras) >= 5  # Ingreso/Diagnostico -> Presupuestado -> En Reparacion -> Listo para Entrega -> Entregado
    print("\n=== ¡Flujo completo verificado y correcto! ===")

if __name__ == "__main__":
    try:
        test_full_reparacion_flow()
    except AssertionError as e:
        print(f"\n[ERROR] ERROR DE ASERCION: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        sys.exit(1)
