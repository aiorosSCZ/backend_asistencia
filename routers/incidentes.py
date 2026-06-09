from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
import crud, schemas, models
from database import get_db
from services.ai_service import AIService
import os
import uuid
import dependencies
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.IncidenteResponse)
def create_incidente(incidente: schemas.IncidenteCreate, db: Session = Depends(get_db)):
    return crud.create_incidente(db=db, incidente=incidente)

@router.get("/{id_incidente}", response_model=schemas.IncidenteResponse)
def read_incidente(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id) if 'dependencies' in globals() else Depends(lambda: None)
):
    from dependencies import get_current_tenant_id, get_current_user
    try:
        current_user = get_current_user(current_user) if hasattr(current_user, "credentials") else current_user
        id_tenant = get_current_tenant_id(current_user)
    except Exception:
        pass

    db_incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not db_incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    if rol == "superadmin":
        pass
    elif rol == "cliente":
        if db_incidente.id_cliente != user_id:
            raise HTTPException(status_code=403, detail="No autorizado para ver este incidente")
    else:
        # Taller/Admin/Tecnico
        if db_incidente.id_tenant is not None and db_incidente.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado para ver este incidente")
            
    return db_incidente

@router.get("/{id_incidente}/tracking")
def get_incidente_tracking(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    if rol == "cliente" and incidente.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    elif rol in ["admin", "taller", "tecnico"] and incidente.id_tenant is not None and incidente.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
    
    lat_tec, lng_tec = None, None
    tecnico_nombre = None
    tecnico_telefono = None
    if asistencia and asistencia.tecnico:
        lat_tec = asistencia.tecnico.ubicacion_actual_latitud
        lng_tec = asistencia.tecnico.ubicacion_actual_longitud
        tecnico_nombre = f"{asistencia.tecnico.nombres} {asistencia.tecnico.apellidos}"
        tecnico_telefono = asistencia.tecnico.telefono_contacto
        
    # Determinar costo real: si requiere remolque/traslado, se cobra la tarifa de grúa (150 Bs)
    # en lugar de la cotización de reparación en camino.
    es_remolque = incidente.estado_solicitud in [
        'Requiere Traslado', 
        'En Remolque', 
        'En Remolque al Taller', 
        'Ingresado a Taller'
    ] or (
        asistencia and 
        asistencia.observaciones_tecnico and 
        "Destino seleccionado" in asistencia.observaciones_tecnico
    )

    if es_remolque:
        costo = 150.0
    else:
        cotizacion_aceptada = db.query(models.Cotizacion).filter(
            models.Cotizacion.id_incidente == id_incidente,
            models.Cotizacion.estado == 'Aceptada'
        ).first()
        
        if cotizacion_aceptada:
            costo = float(cotizacion_aceptada.monto_estimado)
        else:
            costo = 50.0
            if incidente.nivel_prioridad == "Alta":
                costo = 80.0
            elif incidente.nivel_prioridad == "Media":
                costo = 50.0
            elif incidente.nivel_prioridad == "Baja":
                costo = 30.0

    monto_adicional = float(asistencia.monto_adicional) if (asistencia and asistencia.monto_adicional) else 0.0
    motivo_adicional = asistencia.motivo_adicional if (asistencia and asistencia.motivo_adicional) else None
    monto_final = costo + monto_adicional

    pago_completado = False
    if asistencia and asistencia.pago:
        if asistencia.pago.estado_transaccion in ["Aprobado", "Completado"]:
            pago_completado = True

    orden = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_incidente_origen == id_incidente).first()
    id_orden = orden.id_orden if orden else None

    return {
        "estado": incidente.estado_solicitud,
        "tipo_problema": incidente.tipo_problema,
        "nivel_prioridad": incidente.nivel_prioridad,
        "diagnostico_ia": incidente.analisis_ia.diagnostico_cliente if (incidente.analisis_ia and incidente.analisis_ia.diagnostico_cliente) else (incidente.analisis_ia.resumen_estructurado if incidente.analisis_ia else "Sin diagnóstico"),
        "lat_cliente": incidente.ubicacion_latitud,
        "lng_cliente": incidente.ubicacion_longitud,
        "lat_tecnico": lat_tec or -17.7780,
        "lng_tecnico": lng_tec or -63.1750,
        "taller_nombre": asistencia.taller.razon_social if (asistencia and asistencia.taller) else "Taller Asiscar",
        "tecnico_nombre": tecnico_nombre,
        "tecnico_telefono": tecnico_telefono,
        "monto_base": costo,
        "monto_adicional": monto_adicional,
        "motivo_adicional": motivo_adicional,
        "monto_pago": monto_final,
        "pago_completado": pago_completado,
        "id_asistencia": asistencia.id_asistencia if asistencia else None,
        "observaciones_tecnico": asistencia.observaciones_tecnico if asistencia else None,
        "id_orden": id_orden
    }




# Eliminado endpoint duplicado /aceptar

@router.post("/reportar")
async def reportar_incidente(
    id_cliente: int = Form(...),
    id_vehiculo: int = Form(...),
    ubicacion_latitud: float = Form(...),
    ubicacion_longitud: float = Form(...),
    descripcion_manual: str = Form(""),
    audio: UploadFile = File(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Guardar archivos si existen
    audio_path = None
    foto_path = None
    
    if audio:
        ext = os.path.splitext(audio.filename)[1]
        audio_name = f"audio_{uuid.uuid4()}{ext}"
        audio_path = os.path.join(UPLOAD_DIR, audio_name)
        with open(audio_path, "wb") as buffer:
            buffer.write(await audio.read())
            
    if foto:
        ext = os.path.splitext(foto.filename)[1]
        foto_name = f"foto_{uuid.uuid4()}{ext}"
        foto_path = os.path.join(UPLOAD_DIR, foto_name)
        with open(foto_path, "wb") as buffer:
            buffer.write(await foto.read())

    # Crear el incidente en BD
    # Nota: Como models.Incidente podría no tener aún campos para las rutas de archivos en models.py,
    # los guardamos en la descripción o simplemente devolvemos éxito para la Fase 1.
    # Vamos a crear el registro usando el crud básico
    incidente_data = schemas.IncidenteCreate(
        id_cliente=id_cliente,
        id_vehiculo=id_vehiculo,
        ubicacion_latitud=ubicacion_latitud,
        ubicacion_longitud=ubicacion_longitud,
        descripcion_manual=descripcion_manual,
        tipo_problema="Buscando..."
    )
    db_incidente = crud.create_incidente(db=db, incidente=incidente_data)
    
    # Análisis Multimodal con IA (Gemini 1.5 Flash)
    from starlette.concurrency import run_in_threadpool
    ai_result = await run_in_threadpool(AIService.analizar_incidente, audio_path, foto_path, descripcion_manual)
    
    # Actualizar los datos del incidente con el veredicto de la IA
    db_incidente.tipo_problema = ai_result.get("categoria", "Otro")
    db_incidente.nivel_prioridad = ai_result.get("urgencia", "Media")
    db.commit()
    db.refresh(db_incidente)
    
    # Guardar en Evidencia
    if audio_path:
        db_audio = models.Evidencia(
            id_incidente=db_incidente.id_incidente,
            tipo_recurso="Audio",
            url_archivo=f"uploads/{os.path.basename(audio_path)}"
        )
        db.add(db_audio)
        
    if foto_path:
        db_foto = models.Evidencia(
            id_incidente=db_incidente.id_incidente,
            tipo_recurso="Foto",
            url_archivo=f"uploads/{os.path.basename(foto_path)}"
        )
        db.add(db_foto)
    db.commit()

    # Guardar el desglose detallado en AnalisisIA
    db_analisis = models.AnalisisIA(
        id_incidente=db_incidente.id_incidente,
        clasificacion_sugerida=ai_result.get("categoria", "Otro"),
        resumen_estructurado=ai_result.get("diagnostico_ia", "Sin diagnóstico disponible."),
        diagnostico_cliente=ai_result.get("diagnostico_cliente", "Sin diagnóstico disponible.")
    )
    db.add(db_analisis)
    db.commit()

    
    # Búsqueda Geoespacial de Talleres (Fase 3)
    from services.matching_service import buscar_talleres_cercanos
    talleres_cercanos = buscar_talleres_cercanos(
        db, 
        lat_cliente=ubicacion_latitud, 
        lon_cliente=ubicacion_longitud, 
        radio_km=10.0,
        tipo_problema=db_incidente.tipo_problema
    )
    
    # Escalado automático si no hay talleres en 10 km
    if not talleres_cercanos:
        talleres_cercanos = buscar_talleres_cercanos(
            db, 
            lat_cliente=ubicacion_latitud, 
            lon_cliente=ubicacion_longitud, 
            radio_km=20.0,
            tipo_problema=db_incidente.tipo_problema
        )
    
    # Notificaciones WebSocket en tiempo real
    from main import manager
    
    for taller in talleres_cercanos:
        payload = {
            "type": "NUEVA_EMERGENCIA",
            "id_incidente": db_incidente.id_incidente,
            "problema": db_incidente.tipo_problema,
            "prioridad": db_incidente.nivel_prioridad,
            "distancia_km": taller["distancia_km"],
            "latitud": ubicacion_latitud,
            "longitud": ubicacion_longitud,
            "transcripcion_audio": descripcion_manual,
            "descripcion_manual": descripcion_manual,
            "url_audio_evidencia": f"uploads/{os.path.basename(audio_path)}" if audio_path else None,
            "url_foto_evidencia": f"uploads/{os.path.basename(foto_path)}" if foto_path else None,
            "evaluacion_ia": ai_result
        }
        await manager.send_personal_message(payload, taller["id_taller"])

    return {
        "status": "success",
        "message": "Incidente reportado, analizado por IA y talleres asignados.",
        "id_incidente": db_incidente.id_incidente,
        "evaluacion_ia": ai_result,
        "talleres_notificados": talleres_cercanos
    }

@router.post("/{id_incidente}/aceptar")
def aceptar_incidente(
    id_incidente: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    id_taller = payload.get("id_taller")
    if not id_taller:
        raise HTTPException(status_code=400, detail="El ID del taller es requerido")
        
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    # Validar que el usuario sea superadmin o que su tenant coincida con el del taller
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    id_tecnico = payload.get("id_tecnico")
    if id_tecnico:
        tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    else:
        tecnico = db.query(models.Tecnico).filter(
            models.Tecnico.id_taller == id_taller,
            models.Tecnico.estado_operativo == 'Disponible'
        ).first()
        if not tecnico:
            tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_taller == id_taller).first()
        
    if not tecnico:
        raise HTTPException(status_code=400, detail="Este taller no tiene técnicos registrados")
          
    # Asociar el incidente al tenant del taller y marcarlo como taller asignado
    incidente.id_tenant = taller.id_tenant
    incidente.estado_solicitud = 'Aceptado'
    
    # Marcar el técnico como asignado (no en camino todavía)
    tecnico.estado_operativo = 'Asignado'
    
    # Verificar si ya existe asistencia
    existente = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
    if existente:
        return {"status": "success", "message": "El servicio ya fue tomado por este u otro taller."}

    asistencia = models.Asistencia(
        id_incidente=id_incidente,
        id_taller=id_taller,
        id_tecnico=tecnico.id_tecnico,
        id_tenant=taller.id_tenant
    )
    db.add(asistencia)
    db.commit()
    
    # Enviar notificaciones Firebase
    try:
        from services.firebase_service import send_push_notification
        
        cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == incidente.id_cliente).first()
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="¡Taller Asignado!",
                mensaje="Tu solicitud ha sido aceptada por el taller. Esperando confirmación del técnico."
            )
            
        if tecnico and tecnico.fcm_token:
            send_push_notification(
                fcm_token=tecnico.fcm_token,
                titulo="Nuevo Servicio Asignado",
                mensaje="Se te ha asignado un nuevo incidente vehicular."
            )
    except Exception as e:
        print(f"Error disparando notificaciones push: {e}")

    return {"status": "success", "message": "Servicio tomado correctamente"}

@router.post("/{id_incidente}/tecnico-acepta")
def tecnico_acepta_incidente(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    import models
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada para este incidente")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin" and rol != "tecnico" and incidente.id_tenant != current_user.get("id_tenant"):
        raise HTTPException(status_code=403, detail="No autorizado")
    if rol == "tecnico" and asistencia.id_tecnico != user_id:
        raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado")

    # Cambiar estado a En Camino
    incidente.estado_solicitud = 'En Camino'
    if asistencia.tecnico:
        asistencia.tecnico.estado_operativo = 'En camino'

    db.commit()

    # Enviar notificación push al cliente
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente
        if cliente and cliente.fcm_token:
            tecnico_nombre = f"{asistencia.tecnico.nombres} {asistencia.tecnico.apellidos}" if asistencia.tecnico else "Un técnico"
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Técnico en Camino",
                mensaje=f"{tecnico_nombre} va en camino a tu ubicación."
            )
    except Exception as e:
        print(f"Error enviando notificación push al cliente: {e}")

    return {"status": "success", "message": "Servicio aceptado por el técnico. Estado cambiado a En Camino."}


@router.get("/", response_model=list[schemas.IncidenteResponse])
def read_incidentes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user) if 'dependencies' in globals() else Depends(lambda: None)
):
    # Dependencia inline para evitar problemas de circularidad si no está importado arriba
    from dependencies import get_current_user
    try:
        current_user = get_current_user(current_user) if hasattr(current_user, "credentials") else current_user
    except Exception:
        pass
    
    # Si no se pasó token, fallback a listado completo de la fase anterior (o lanzar excepción en producción)
    if not current_user or not isinstance(current_user, dict):
        return db.query(models.Incidente).offset(skip).limit(limit).all()

    rol = current_user.get("role") or current_user.get("rol")
    id_tenant = current_user.get("id_tenant")
    user_id = current_user.get("user_id")

    query = db.query(models.Incidente)

    if rol == "superadmin":
        # Superadmin ve absolutamente todos los incidentes
        pass
    elif rol == "cliente":
        # Cliente ve únicamente sus propios incidentes
        query = query.filter(models.Incidente.id_cliente == user_id)
    elif rol in ["taller", "admin", "tecnico"]:
        # Ven incidentes asociados a su tenant, o incidentes globales sin asignar en estado 'Pendiente' (para cotizar)
        query = query.filter(
            (models.Incidente.id_tenant == id_tenant) |
            ((models.Incidente.id_tenant == None) & (models.Incidente.estado_solicitud == 'Pendiente'))
        )
    else:
        raise HTTPException(status_code=403, detail="Rol no autorizado para listar incidentes")

    return query.offset(skip).limit(limit).all()

@router.post("/{id_incidente}/cancelar")
async def cancelar_incidente(
    id_incidente: int, 
    payload: dict, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        if id_incidente == 1:
            return {"status": "success", "message": "Incidente de simulación cancelado correctamente."}
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "cliente" and incidente.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    elif rol in ["admin", "taller", "tecnico"] and incidente.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    motivo = payload.get("motivo_cancelacion") or "Cancelado por el cliente"
    
    incidente.estado_solicitud = 'cancelado'
    incidente.motivo_cancelacion = motivo
    
    # Liberar técnico si estaba asignado
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
    if asistencia and asistencia.tecnico:
        asistencia.tecnico.estado_operativo = 'Disponible'
        
    db.commit()
    
    # Enviar notificación en tiempo real vía WebSocket al taller
    if asistencia and asistencia.id_taller:
        from main import manager
        try:
            await manager.send_personal_message({
                "type": "INCIDENTE_CANCELADO",
                "id_incidente": id_incidente,
                "motivo": motivo
            }, asistencia.id_taller)
        except Exception as e:
            print(f"Error enviando WebSocket de cancelación: {e}")
            
    return {"status": "success", "message": "Incidente cancelado y técnico liberado."}

@router.post("/{id_incidente}/calificar", response_model=schemas.ValoracionResponse)
def calificar_incidente(
    id_incidente: int, 
    request: schemas.ValoracionCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    # 1. Buscar la asistencia
    db_asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_incidente == id_incidente).first()
    if not db_asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada para este incidente")
        
    # Validar que el cliente calificador sea el dueño del incidente
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "cliente" and db_asistencia.incidente.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # 2. Verificar si ya fue calificada
    db_valoracion = db.query(models.Valoracion).filter(models.Valoracion.id_asistencia == db_asistencia.id_asistencia).first()
    if db_valoracion:
        raise HTTPException(status_code=400, detail="Este servicio ya ha sido calificado")
        
    # 3. Crear la valoración con id_tenant
    nueva_valoracion = models.Valoracion(
        id_asistencia=db_asistencia.id_asistencia,
        id_tenant=db_asistencia.id_tenant,
        puntuacion=request.puntuacion,
        comentario=request.comentario
    )
    db.add(nueva_valoracion)
    db.commit()
    db.refresh(nueva_valoracion)
    return nueva_valoracion

@router.post("/{id_incidente}/estado")
def actualizar_estado_incidente(
    id_incidente: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and incidente.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    nuevo_estado = payload.get("estado")
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="El estado es requerido")
        
    incidente.estado_solicitud = nuevo_estado
    db.commit()

    # Enviar notificación push al cliente informando el cambio de estado
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente
        if cliente and cliente.fcm_token:
            titulo = "Estado de Asistencia"
            mensaje = f"Tu asistencia ha cambiado al estado: {nuevo_estado}."
            if nuevo_estado in ["Atendido", "Atendiendo"]:
                titulo = "¡Vehículo en Atención! 🛠️"
                mensaje = "El técnico ha comenzado a trabajar en tu vehículo."
            elif nuevo_estado == "Por Pagar":
                titulo = "Servicio Terminado 💳"
                mensaje = "El técnico ha finalizado. Por favor, procede con el pago en tu aplicación."
            elif nuevo_estado == "Completado":
                titulo = "Servicio Completado 🎉"
                mensaje = "¡Gracias por confiar en nosotros! Tu vehículo está listo."

            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo=titulo,
                mensaje=mensaje
            )
    except Exception as e:
        print(f"Error enviando push de cambio de estado al cliente: {e}")

    return {"status": "success", "message": f"Estado actualizado a {nuevo_estado}"}


@router.post("/asistencias/{id_asistencia}/ajustar-costo")
def ajustar_costo_asistencia(
    id_asistencia: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")

    # Validaciones multitenant estrictas
    if rol != "superadmin":
        if rol == "tecnico" and asistencia.id_tecnico != user_id:
            raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado a esta asistencia")
        elif rol in ["admin", "taller"] and asistencia.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado: Recurso de otro tenant")
        elif rol not in ["tecnico", "admin", "taller"]:
            raise HTTPException(status_code=403, detail="No autorizado")

    monto_adicional = payload.get("monto_adicional", 0.0)
    motivo_adicional = payload.get("motivo_adicional")

    asistencia.monto_adicional = monto_adicional
    asistencia.motivo_adicional = motivo_adicional
    db.commit()

    # Enviar notificación push al cliente con el ajuste
    try:
        from services.firebase_service import send_push_notification
        incidente = asistencia.incidente
        if incidente and incidente.cliente and incidente.cliente.fcm_token:
            send_push_notification(
                fcm_token=incidente.cliente.fcm_token,
                titulo="Costo Adicional Registrado 🛠️",
                mensaje=f"Se ha registrado un recargo de Bs. {monto_adicional:.2f} por: {motivo_adicional or 'Repuestos/Trabajo extra'}."
            )
    except Exception as e:
        print(f"Error enviando notificación push al cliente por costo adicional: {e}")

    return {"status": "success", "message": "Costo adicional registrado exitosamente"}


# --- Endpoints de Asistencia (Traslados y Veredicto) ---

@router.post("/asistencias/{id_asistencia}/veredicto-traslado")
def veredicto_traslado(
    id_asistencia: int, 
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "tecnico" and asistencia.id_tecnico != user_id:
            raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado a esta asistencia")
        elif rol in ["admin", "taller"] and asistencia.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado: Recurso de otro tenant")
        elif rol not in ["tecnico", "admin", "taller"]:
            raise HTTPException(status_code=403, detail="No autorizado")

    diagnostico = payload.get("diagnostico") or ""
    motivo = payload.get("motivo") or ""
    asistencia.observaciones_tecnico = f"Diagnóstico: {diagnostico}. Motivo: {motivo}."

    # Cambiar estado del incidente
    incidente = asistencia.incidente
    if incidente:
        incidente.estado_solicitud = 'Requiere Traslado'
        db.commit()
        
    # Notificar al cliente
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente if incidente else None
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Veredicto Técnico 🚛",
                mensaje=f"El técnico determinó que se requiere grúa: {diagnostico}. Selecciona el destino del traslado en la aplicación."
            )
    except Exception as e:
        print(f"Error enviando notificación de veredicto: {e}")
        
    return {"status": "success", "message": "Veredicto de traslado registrado. Esperando destino del cliente."}

@router.post("/asistencias/{id_asistencia}/destino")
def seleccionar_destino(
    id_asistencia: int, 
    payload: dict, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "cliente" and asistencia.incidente.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    elif rol in ["admin", "taller", "tecnico"] and asistencia.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    destino = payload.get("destino") # "Casa" o "Taller"
    direccion = payload.get("direccion_destino") or ""
    
    if destino not in ["Casa", "Taller"]:
        raise HTTPException(status_code=400, detail="El destino debe ser 'Casa' o 'Taller'")
        
    # Guardar en las observaciones (añadiendo al veredicto técnico)
    asistencia.observaciones_tecnico = f"{asistencia.observaciones_tecnico or ''}\nDestino seleccionado por cliente: {destino}. Dirección: {direccion}."
    
    # Cambiar estado del incidente según el destino elegido
    incidente = asistencia.incidente
    if incidente:
        if destino == "Taller":
            incidente.estado_solicitud = 'En Remolque al Taller'
        else:
            incidente.estado_solicitud = 'En Remolque'
            
    db.commit()
    
    # Notificar al técnico
    try:
        from services.firebase_service import send_push_notification
        tecnico = asistencia.tecnico
        if tecnico and tecnico.fcm_token:
            send_push_notification(
                fcm_token=tecnico.fcm_token,
                titulo="Destino de Traslado Seleccionado",
                mensaje=f"El cliente ha seleccionado trasladar el vehículo a: {destino}."
            )
    except Exception as e:
        print(f"Error enviando notificación de destino al técnico: {e}")
        
    return {"status": "success", "message": f"Destino registrado exitosamente como {destino}."}

@router.post("/asistencias/{id_asistencia}/arribo-cliente")
def arribo_cliente(
    id_asistencia: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "tecnico" and asistencia.id_tecnico != user_id:
            raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado a esta asistencia")
        elif rol in ["admin", "taller"] and asistencia.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado: Recurso de otro tenant")
        elif rol not in ["tecnico", "admin", "taller"]:
            raise HTTPException(status_code=403, detail="No autorizado")

    return {"status": "success", "message": "Arribo del cliente registrado."}

@router.post("/asistencias/{id_asistencia}/finalizar-en-casa")
def finalizar_en_casa(
    id_asistencia: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "tecnico" and asistencia.id_tecnico != user_id:
            raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado a esta asistencia")
        elif rol in ["admin", "taller"] and asistencia.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado: Recurso de otro tenant")
        elif rol not in ["tecnico", "admin", "taller"]:
            raise HTTPException(status_code=403, detail="No autorizado")

    incidente = asistencia.incidente
    if incidente:
        incidente.estado_solicitud = 'Por Pagar'
        
    # Liberar técnico
    tecnico = asistencia.tecnico
    if tecnico:
        tecnico.estado_operativo = 'Disponible'
        
    db.commit()
    
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente if incidente else None
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Vehículo Entregado 🚛",
                mensaje="El traslado a tu destino ha concluido con éxito. Por favor, procede con el pago en tu aplicación."
            )
    except Exception as e:
        print(f"Error enviando notificación de servicio finalizado: {e}")
        
    return {"status": "success", "message": "Servicio finalizado y técnico liberado."}

@router.post("/asistencias/{id_asistencia}/finalizar-en-taller")
def finalizar_en_taller(
    id_asistencia: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    asistencia = db.query(models.Asistencia).filter(models.Asistencia.id_asistencia == id_asistencia).first()
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "tecnico" and asistencia.id_tecnico != user_id:
            raise HTTPException(status_code=403, detail="No autorizado: No eres el técnico asignado a esta asistencia")
        elif rol in ["admin", "taller"] and asistencia.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado: Recurso de otro tenant")
        elif rol not in ["tecnico", "admin", "taller"]:
            raise HTTPException(status_code=403, detail="No autorizado")

    incidente = asistencia.incidente
    if incidente:
        incidente.estado_solicitud = 'Ingresado a Taller'
        
    # Liberar técnico
    tecnico = asistencia.tecnico
    if tecnico:
        tecnico.estado_operativo = 'Disponible'
        
    db.commit()
    
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente if incidente else None
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Ingreso a Taller Confirmado",
                mensaje="Tu vehículo ha ingresado formalmente al taller físico. Pronto recibirás el presupuesto."
            )
    except Exception as e:
        print(f"Error enviando notificación de ingreso a taller: {e}")
        
    return {"status": "success", "message": "Ingreso a taller completado, técnico liberado y listo para fase de taller físico."}


# --- Endpoints de Cotizaciones ---

@router.post("/{id_incidente}/cotizar", response_model=schemas.CotizacionResponse)
async def crear_cotizacion_incidente(
    id_incidente: int,
    request: schemas.CotizacionCreate,
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado para cotizar a nombre de este taller")

    # Registrar cotización
    db_cot = crud.create_cotizacion(db=db, cotizacion=request, id_incidente=id_incidente, id_taller=id_taller)

    # Notificar al cliente vía Push
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Nueva Cotización",
                mensaje=f"El taller {taller.razon_social} ha enviado una propuesta de Bs. {request.monto_estimado}."
            )
    except Exception as e:
        print(f"Error enviando push de cotización: {e}")

    return db_cot

@router.get("/{id_incidente}/cotizaciones")
def listar_cotizaciones_incidente(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    if rol != "superadmin":
        if rol == "cliente" and incidente.id_cliente != user_id:
            raise HTTPException(status_code=403, detail="No autorizado para ver cotizaciones de este incidente")
        elif rol in ["taller", "admin", "tecnico"] and incidente.id_tenant is not None and incidente.id_tenant != id_tenant:
            raise HTTPException(status_code=403, detail="No autorizado para ver cotizaciones de este incidente")
    
    cotizaciones = crud.get_cotizaciones_by_incidente(db, id_incidente)
    result = []
    for cot in cotizaciones:
        taller = cot.taller
        result.append({
            "id_cotizacion": cot.id_cotizacion,
            "id_incidente": cot.id_incidente,
            "id_taller": cot.id_taller,
            "monto_estimado": float(cot.monto_estimado),
            "tiempo_estimado_minutos": cot.tiempo_estimado_minutos,
            "comentario": cot.comentario,
            "estado": cot.estado,
            "created_at": cot.created_at.isoformat() if cot.created_at else None,
            "taller_nombre": taller.razon_social if taller else None,
            "taller_latitud": taller.ubicacion_base_latitud if taller else None,
            "taller_longitud": taller.ubicacion_base_longitud if taller else None,
            "taller_calificacion": float(taller.calificacion_promedio) if (taller and taller.calificacion_promedio) else None,
        })
    return result

@router.post("/{id_incidente}/cotizaciones/{id_cotizacion}/aceptar")
async def aceptar_cotizacion_incidente(
    id_incidente: int,
    id_cotizacion: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    cotizacion = crud.get_cotizacion(db, id_cotizacion)
    if not cotizacion or cotizacion.id_incidente != id_incidente:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    taller = db.query(models.Taller).filter(models.Taller.id_taller == cotizacion.id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "cliente" and incidente.id_cliente != user_id:
            raise HTTPException(status_code=403, detail="No autorizado para aceptar esta cotización")
        elif rol != "cliente":
            raise HTTPException(status_code=403, detail="Solo el cliente propietario puede aceptar cotizaciones")

    # 1. Actualizar estados
    cotizacion.estado = 'Aceptada'
    
    # Rechazar las otras cotizaciones de este incidente
    from main import manager
    otras_cots = db.query(models.Cotizacion).filter(
        models.Cotizacion.id_incidente == id_incidente,
        models.Cotizacion.id_cotizacion != id_cotizacion
    ).all()
    for oc in otras_cots:
        oc.estado = 'Rechazada'
        try:
            await manager.send_personal_message({
                "type": "COTIZACION_RECHAZADA",
                "id_incidente": id_incidente,
                "id_cotizacion": oc.id_cotizacion
            }, oc.id_taller)
        except Exception as e:
            print(f"Error WebSocket taller rechazado: {e}")

    # Cambiar estado del incidente a 'Cotización Aceptada'
    incidente.estado_solicitud = 'Cotización Aceptada'
    incidente.id_tenant = taller.id_tenant
    
    db.commit()

    # 2. Notificar al taller ganador vía WebSocket
    try:
        await manager.send_personal_message({
            "type": "COTIZACION_ACEPTADA",
            "id_incidente": id_incidente,
            "id_cotizacion": id_cotizacion
        }, cotizacion.id_taller)
    except Exception as e:
        print(f"Error WebSocket taller aceptado: {e}")

    # 3. Notificar al cliente vía Push
    try:
        from services.firebase_service import send_push_notification
        cliente = incidente.cliente
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Cotización Aceptada",
                mensaje=f"Has aceptado la cotización de {taller.razon_social}. El taller asignará un técnico pronto."
            )
    except Exception as e:
        print(f"Error enviando notificaciones post-aceptación cliente: {e}")

    return {"status": "success", "message": "Cotización aceptada. Esperando asignación de técnico por el taller."}


@router.post("/{id_incidente}/cotizaciones/{id_cotizacion}/rechazar")
async def rechazar_cotizacion_incidente(
    id_incidente: int,
    id_cotizacion: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    cotizacion = crud.get_cotizacion(db, id_cotizacion)
    if not cotizacion or cotizacion.id_incidente != id_incidente:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin":
        if rol == "cliente" and incidente.id_cliente != user_id:
            raise HTTPException(status_code=403, detail="No autorizado para rechazar esta cotización")
        elif rol != "cliente":
            raise HTTPException(status_code=403, detail="Solo el cliente propietario puede rechazar cotizaciones")

    cotizacion.estado = 'Rechazada'
    db.commit()

    # Notificar al taller vía WebSocket
    from main import manager
    try:
        await manager.send_personal_message({
            "type": "COTIZACION_RECHAZADA",
            "id_incidente": id_incidente,
            "id_cotizacion": id_cotizacion
        }, cotizacion.id_taller)
    except Exception as e:
        print(f"Error WebSocket taller rechazado: {e}")

    return {"status": "success", "message": "Cotización rechazada."}

