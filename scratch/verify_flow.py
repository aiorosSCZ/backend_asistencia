import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_flow():
    print("--- INICIANDO VERIFICACIÓN DE FLUJO ---")

    # 1. Login Cliente
    print("\n1. Autenticando Cliente...")
    c_res = requests.post(f"{BASE_URL}/api/clientes/login", json={
        "correo": "cliente@gmail.com",
        "password": "cliente123"
    })
    if c_res.status_code != 200:
        print(f"Error login cliente: {c_res.text}")
        sys.exit(1)
    c_token = c_res.json()["access_token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}
    print("Cliente autenticado con éxito.")

    # 2. Login Taller
    print("\n2. Autenticando Taller...")
    t_res = requests.post(f"{BASE_URL}/api/talleres/login", json={
        "correo": "taller.norte@asiscar.com",
        "password": "taller123"
    })
    if t_res.status_code != 200:
        print(f"Error login taller: {t_res.text}")
        sys.exit(1)
    t_token = t_res.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}
    print("Taller autenticado con éxito.")

    # 3. Crear Incidente
    print("\n3. Creando Incidente para Cliente...")
    inc_res = requests.post(f"{BASE_URL}/api/incidentes/reportar", data={
        "id_cliente": 1,
        "id_vehiculo": 1,
        "ubicacion_latitud": -17.7780,
        "ubicacion_longitud": -63.1750,
        "tipo_problema": "Eléctrico",
        "descripcion_manual": "El vehículo no arranca."
    }, headers=c_headers)
    if inc_res.status_code != 200:
        print(f"Error al crear incidente: {inc_res.text}")
        sys.exit(1)
    inc_data = inc_res.json()
    id_incidente = inc_data["id_incidente"]
    print(f"Incidente #{id_incidente} creado con éxito.")

    # 4. Crear Cotización
    print("\n4. Taller crea cotización...")
    cot_res = requests.post(f"{BASE_URL}/api/incidentes/{id_incidente}/cotizaciones", json={
        "monto_estimado": 150.00,
        "tiempo_estimado_minutos": 30,
        "comentario": "Diagnóstico inicial rápido"
    }, headers=t_headers)
    if cot_res.status_code != 200:
        # Si no existe la ruta de cotizaciones, tal vez use aceptar directamente
        print(f"Nota: Endpoint de cotización falló (puede que no se requiera cotización en este flujo): {cot_res.text}")
    else:
        id_cot = cot_res.json()["id_cotizacion"]
        print(f"Cotización #{id_cot} creada.")
        # Cliente acepta cotización
        ac_res = requests.post(f"{BASE_URL}/api/incidentes/{id_incidente}/cotizaciones/{id_cot}/aceptar", headers=c_headers)
        print(f"Cliente acepta cotización: {ac_res.status_code}")

    # Forzar estado de la solicitud a 'Ingresado a Taller' para crear la orden
    print("\n5. Actualizando estado del incidente a 'Ingresado a Taller'...")
    est_res = requests.post(f"{BASE_URL}/api/incidentes/{id_incidente}/estado", json={
        "estado": "Ingresado a Taller"
    }, headers=t_headers)
    if est_res.status_code != 200:
        print(f"Error actualizando estado del incidente: {est_res.text}")
        sys.exit(1)
    print("Estado actualizado a 'Ingresado a Taller'.")

    # 6. Crear Orden de Trabajo
    print("\n6. Creando Orden de Trabajo en Taller...")
    ord_res = requests.post(f"{BASE_URL}/api/reparaciones/ordenes", json={
        "id_cliente": 1,
        "id_vehiculo": 1,
        "id_incidente_origen": id_incidente,
        "estado_recepcion": "Ingresa en grúa por falla de arranque.",
        "fecha_compromiso_entrega": "2026-06-10T12:00:00"
    }, headers=t_headers)
    if ord_res.status_code != 200:
        print(f"Error creando orden de trabajo: {ord_res.text}")
        sys.exit(1)
    ord_data = ord_res.json()
    id_orden = ord_data["id_orden"]
    print(f"Orden de Trabajo #{id_orden} creada con éxito.")

    # 7. Crear Presupuesto con items críticos y opcionales
    print("\n7. Creando Presupuesto para la Orden...")
    pres_res = requests.post(f"{BASE_URL}/api/reparaciones/ordenes/{id_orden}/presupuestos", json={
        "descripcion_general": "Fallas detectadas en sistema eléctrico y frenos.",
        "version": "1.0",
        "detalles": [
            {
                "categoria": "Eléctrico",
                "grupo_falla": "Sistema Eléctrico",
                "es_critico": True,
                "tipo_item": "Repuesto",
                "item_descripcion": "Alternador 12V",
                "cantidad": 1,
                "precio_unitario": 850.00
            },
            {
                "categoria": "Eléctrico",
                "grupo_falla": "Sistema Eléctrico",
                "es_critico": True,
                "tipo_item": "Mano de Obra",
                "item_descripcion": "Instalación de alternador",
                "cantidad": 1,
                "precio_unitario": 150.00
            },
            {
                "categoria": "Frenos",
                "grupo_falla": "Pastillas de Freno",
                "es_critico": False,
                "tipo_item": "Repuesto",
                "item_descripcion": "Pastillas delanteras",
                "cantidad": 1,
                "precio_unitario": 180.00
            }
        ]
    }, headers=t_headers)
    if pres_res.status_code != 200:
        print(f"Error creando presupuesto: {pres_res.text}")
        sys.exit(1)
    pres_data = pres_res.json()
    id_presupuesto = pres_data["id_presupuesto"]
    print(f"Presupuesto #{id_presupuesto} creado con éxito.")

    # 8. Cliente aprueba presupuesto (aprueba eléctrico que es crítico, y rechaza pastillas que es opcional)
    print("\n8. Cliente respondiendo al presupuesto (Aprueba Eléctrico, Rechaza Pastillas)...")
    aprob_res = requests.put(f"{BASE_URL}/api/reparaciones/presupuestos/{id_presupuesto}/aprobar", json={
        "grupos": [
            {
                "grupo_falla": "Sistema Eléctrico",
                "aprobado": True
            },
            {
                "grupo_falla": "Pastillas de Freno",
                "aprobado": False
            }
        ]
    }, headers=c_headers)
    if aprob_res.status_code != 200:
        print(f"Error aprobando presupuesto: {aprob_res.text}")
        sys.exit(1)
    pres_aprobado = aprob_res.json()
    print(f"Presupuesto respondido con éxito. Estado: {pres_aprobado['estado']}. Total Aprobado: Bs. {pres_aprobado['total_estimado']}")

    # 9. Taller finaliza la reparación -> Listo para Entrega
    print("\n9. Taller marca la reparación como 'Listo para Entrega'...")
    est_ord_res = requests.post(f"{BASE_URL}/api/reparaciones/ordenes/{id_orden}/estado", json={
        "estado_trabajo": "Listo para Entrega",
        "comentario": "Reparación del sistema eléctrico completada con éxito. Listo para retiro."
    }, headers=t_headers)
    if est_ord_res.status_code != 200:
        print(f"Error actualizando estado de orden: {est_ord_res.text}")
        sys.exit(1)
    print("Orden marcada como 'Listo para Entrega'.")

    # 10. Cliente paga el saldo
    print("\n10. Cliente realiza el pago de la reparación...")
    pago_res = requests.post(f"{BASE_URL}/api/pagos/reparacion", json={
        "id_orden": id_orden,
        "metodo_pago": "Tarjeta"
    }, headers=c_headers)
    if pago_res.status_code != 200:
        print(f"Error registrando pago: {pago_res.text}")
        sys.exit(1)
    pago_data = pago_res.json()
    print(f"Pago procesado con éxito. ID Pago: {pago_data['id_pago']}. Monto: Bs. {pago_data['monto_total_cliente']}. Comisión: Bs. {pago_data['monto_comision_plataforma']}")
    print("\n--- VERIFICACIÓN COMPLETADA EXITOSAMENTE ---")

if __name__ == "__main__":
    test_flow()
