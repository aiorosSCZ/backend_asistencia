import os
from fastapi import APIRouter, Depends, HTTPException
import stripe
from database import get_db
from sqlalchemy.orm import Session
import models
import schemas

router = APIRouter(prefix="/api/pagos", tags=["pagos"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/crear-intento")
def crear_intento_pago(payload: dict, db: Session = Depends(get_db)):
    id_incidente = payload.get("id_incidente")
    monto = payload.get("monto", 5000) # 50.00 USD por defecto
    
    if not id_incidente:
        raise HTTPException(status_code=400, detail="Falta el ID del incidente")

    try:
        currency = os.getenv("STRIPE_CURRENCY", "bob").lower()
        
        # En modo test (sk_test_...), confirmamos el intento de pago inmediatamente en el backend
        # con una tarjeta de prueba ("pm_card_visa") para simular el éxito en Stripe sin requerir
        # de la integración del SDK en el frontend móvil.
        is_test = stripe.api_key and stripe.api_key.startswith("sk_test")
        
        create_params = {
            "amount": int(monto),
            "currency": currency,
        }
        if is_test:
            create_params.update({
                "payment_method": "pm_card_visa",
                "confirm": True,
                "automatic_payment_methods": {
                    "enabled": True,
                    "allow_redirects": "never",
                }
            })
        else:
            create_params.update({
                "automatic_payment_methods": {
                    "enabled": True,
                }
            })
            
        intent = stripe.PaymentIntent.create(**create_params)
        
        # Intentar guardar el registro en la BD (Fase 4)
        asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
        if asistencia:
            pago_existente = db.query(models.Pago).filter(models.Pago.id_asistencia == asistencia.id_asistencia).first()
            if not pago_existente:
                nuevo_pago = models.Pago(
                    id_asistencia=asistencia.id_asistencia,
                    id_tenant=asistencia.id_tenant,
                    monto_subtotal=monto / 100,
                    monto_comision_plataforma=(monto / 100) * 0.10,
                    monto_total_cliente=monto / 100,
                    metodo_pago="Tarjeta de Crédito (Stripe)",
                    estado_transaccion="Pendiente"
                )
                db.add(nuevo_pago)
                db.commit()

        return {
            "paymentIntent": intent.client_secret,
            "publishableKey": os.getenv("STRIPE_PUBLISHABLE_KEY"),
            "paymentIntentId": intent.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirmar-pago")
def confirmar_pago(payload: dict, db: Session = Depends(get_db)):
    id_incidente = payload.get("id_incidente")
    payment_intent_id = payload.get("payment_intent_id")

    if not id_incidente or not payment_intent_id:
        raise HTTPException(status_code=400, detail="Faltan parámetros requeridos (id_incidente, payment_intent_id)")

    try:
        # Consultar estado real en Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status != "succeeded":
            raise HTTPException(
                status_code=400,
                detail=f"El pago no ha sido completado en Stripe. Estado actual: {intent.status}"
            )

        # Buscar la asistencia correspondiente al incidente
        asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
        if not asistencia:
            raise HTTPException(status_code=404, detail="No se encontró una asistencia asociada a este incidente")

        # Buscar el pago pendiente
        pago = db.query(models.Pago).filter(models.Pago.id_asistencia == asistencia.id_asistencia).first()
        if not pago:
            raise HTTPException(status_code=404, detail="No se encontró un registro de pago para esta asistencia")

        import datetime
        # Actualizar estado de pago e incidente
        pago.estado_transaccion = "Aprobado"
        pago.fecha_pago = datetime.datetime.utcnow()

        incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
        if incidente:
            incidente.estado_solicitud = "Completado"

        db.commit()

        # Enviar notificación Push al técnico informando que ya se pagó
        try:
            from services.firebase_service import send_push_notification
            if asistencia.tecnico and asistencia.tecnico.fcm_token:
                send_push_notification(
                    fcm_token=asistencia.tecnico.fcm_token,
                    titulo="¡Pago Recibido! 💰",
                    mensaje="El cliente ha pagado el servicio. El incidente ha sido marcado como Completado."
                )
        except Exception as e:
            print(f"Error enviando notificación de pago: {e}")

        return {
            "status": "success",
            "message": "Pago confirmado exitosamente y servicio completado."
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Error de Stripe: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cliente/{id_cliente}")
def get_cliente_pagos(id_cliente: int, db: Session = Depends(get_db)):
    import models
    incidentes = db.query(models.Incidente).filter(models.Incidente.id_cliente == id_cliente).all()
    if not incidentes:
        return []
        
    id_incidentes = [inc.id_incidente for inc in incidentes]
    asistencias = db.query(models.Asistencia).filter(models.Asistencia.id_incidente.in_(id_incidentes)).all()
    if not asistencias:
        return []
        
    id_asistencias = [asis.id_asistencia for asis in asistencias]
    pagos = db.query(models.Pago).filter(models.Pago.id_asistencia.in_(id_asistencias)).all()
    
    resultados = []
    for pago in pagos:
        asis = pago.asistencia
        inc = asis.incidente if asis else None
        
        resultados.append({
            "id_pago": pago.id_pago,
            "id_asistencia": pago.id_asistencia,
            "id_incidente": inc.id_incidente if inc else None,
            "monto": float(pago.monto_total_cliente),
            "metodo": pago.metodo_pago,
            "estado": pago.estado_transaccion,
            "fecha": inc.fecha_hora_reporte.strftime("%Y-%m-%d %H:%M") if inc and inc.fecha_hora_reporte else "N/A",
            "taller": asis.taller.razon_social if asis and asis.taller else "Taller Desconocido",
            "problema": inc.tipo_problema if inc else "Auxilio Vial"
        })

    return resultados

@router.post("/reparacion", response_model=schemas.PagoReparacionResponse)
async def registrar_pago_reparacion(payload: schemas.PagoReparacionCreate, db: Session = Depends(get_db)):
    import crud
    
    id_orden = payload.id_orden
    metodo = payload.metodo_pago
    
    orden = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    # Verificar si ya existe un pago para esta orden
    pago_existente = db.query(models.PagoReparacion).filter(models.PagoReparacion.id_orden == id_orden).first()
    if pago_existente:
        raise HTTPException(status_code=400, detail="Esta orden de trabajo ya cuenta con un pago registrado.")

    # Buscar el presupuesto aprobado de esta orden
    presupuesto = db.query(models.Presupuesto).filter(
        models.Presupuesto.id_orden == id_orden,
        models.Presupuesto.estado.in_(["Aprobado", "Aprobado Parcial"])
    ).first()
    
    if not presupuesto:
        raise HTTPException(status_code=400, detail="No se encontró un presupuesto aprobado para esta orden.")
        
    monto = float(presupuesto.total_estimado)
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del presupuesto aprobado debe ser mayor a 0.")
        
    # Calcular comisiones (5% para reparaciones en taller físico)
    comision = monto * 0.05
    
    nuevo_pago = models.PagoReparacion(
        id_orden=id_orden,
        id_tenant=orden.id_tenant,
        monto_subtotal=monto - comision,
        monto_comision_plataforma=comision,
        monto_total_cliente=monto,
        metodo_pago=metodo,
        estado_transaccion="Completado"
    )
    db.add(nuevo_pago)
    
    # Actualizar estado de la orden a 'Entregado'
    estado_anterior = orden.estado_trabajo
    orden.estado_trabajo = "Entregado"
    
    db.commit()
    db.refresh(nuevo_pago)
    db.refresh(orden)
    
    # Registrar hito en bitácora
    crud.create_bitacora_estado(
        db=db,
        id_orden=id_orden,
        estado_anterior=estado_anterior,
        nuevo_estado="Entregado",
        comentario=f"Pago de reparación de Bs. {monto:.2f} recibido. Método: {metodo}. Comisión de la plataforma del 5% (Bs. {comision:.2f}) registrada."
    )
    
    # Notificaciones WebSocket al taller
    try:
        from main import manager
        taller = db.query(models.Taller).filter(models.Taller.id_tenant == orden.id_tenant).first()
        if taller:
            await manager.send_personal_message({
                "type": "PAGO_REPARACION_RECIBIDO",
                "id_orden": id_orden,
                "monto": monto,
                "message": f"Se ha recibido el pago de la reparación para la Orden #{id_orden}. El vehículo está listo para ser retirado."
            }, taller.id_taller)
    except Exception as e:
        print(f"Error enviando notificación WS al taller: {e}")
        
    return nuevo_pago

