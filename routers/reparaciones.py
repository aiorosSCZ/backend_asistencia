from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import crud
import schemas
import models
import dependencies
from typing import List, Optional

router = APIRouter()

@router.post("/ordenes", response_model=schemas.OrdenTrabajoResponse)
def create_orden(
    orden: schemas.OrdenTrabajoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    # Solo administradores del taller o taller pueden crear órdenes
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol not in ["taller", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para crear órdenes de trabajo"
        )
    
    # Si es SuperAdmin, debe poder especificar o heredar el tenant de alguna forma,
    # pero como es para un taller específico, tomamos el del taller o del payload si corresponde.
    # En producción o pruebas, un admin de tenant tiene su id_tenant inyectado.
    if id_tenant is None:
        # Fallback a un tenant por defecto si es superadmin y no se deduce
        id_tenant = 1
        
    return crud.create_orden_trabajo(db=db, orden=orden, id_tenant=id_tenant)

@router.get("/ordenes", response_model=List[schemas.OrdenTrabajoResponse])
def read_ordenes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")

    if rol == "superadmin":
        # Superadmin ve todas las órdenes
        return db.query(models.OrdenTrabajo).offset(skip).limit(limit).all()
    elif rol == "cliente":
        # Cliente ve solo sus propias órdenes
        return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_cliente == user_id).offset(skip).limit(limit).all()
    else:
        # Taller/Admin ve solo las de su tenant
        return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_tenant == id_tenant).offset(skip).limit(limit).all()

@router.get("/ordenes/{id_orden}", response_model=schemas.OrdenTrabajoResponse)
def read_orden(
    id_orden: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    db_orden = crud.get_orden_trabajo(db, id_orden=id_orden)
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    # Validar permisos/tenancy
    if rol == "superadmin":
        pass
    elif rol == "cliente" and db_orden.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta orden")
    elif rol != "superadmin" and rol != "cliente" and db_orden.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado para ver esta orden")
        
    return db_orden

@router.post("/ordenes/{id_orden}/presupuestos", response_model=schemas.PresupuestoResponse)
def create_presupuesto_orden(
    id_orden: int,
    presupuesto: schemas.PresupuestoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    db_orden = crud.get_orden_trabajo(db, id_orden=id_orden)
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    # Validar tenancy
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and db_orden.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado para modificar esta orden")
        
    # Cambiar estado de la orden a 'Presupuestado'
    estado_anterior = db_orden.estado_trabajo
    db_orden.estado_trabajo = "Presupuestado"
    
    db_presupuesto = crud.create_presupuesto(db=db, id_orden=id_orden, presupuesto=presupuesto)
    
    crud.create_bitacora_estado(
        db=db,
        id_orden=id_orden,
        estado_anterior=estado_anterior,
        nuevo_estado="Presupuestado",
        comentario=f"Se ha registrado el presupuesto versión {db_presupuesto.version} para revisión del cliente."
    )
    
    # Intentar enviar notificación push al cliente
    try:
        from services.firebase_service import send_push_notification
        cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == db_orden.id_cliente).first()
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Presupuesto Listo",
                mensaje=f"Tu taller ha subido un nuevo presupuesto para tu revisión. ¡Entra a la app para verlo!"
            )
    except Exception as e:
        print(f"Error enviando push de presupuesto: {e}")
        
    return db_presupuesto

@router.get("/ordenes/{id_orden}/presupuestos", response_model=List[schemas.PresupuestoResponse])
def read_presupuestos_orden(
    id_orden: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    db_orden = crud.get_orden_trabajo(db, id_orden=id_orden)
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    if rol == "superadmin":
        pass
    elif rol == "cliente" and db_orden.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    elif rol != "superadmin" and rol != "cliente" and db_orden.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    return db_orden.presupuestos

@router.put("/presupuestos/{id_presupuesto}/aprobar", response_model=schemas.PresupuestoResponse)
def aprobar_presupuesto(
    id_presupuesto: int,
    request: schemas.PresupuestoAprobarRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    db_presupuesto = crud.get_presupuesto(db, id_presupuesto=id_presupuesto)
    if not db_presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
    db_orden = db_presupuesto.orden
    
    # Validar que el cliente que aprueba sea el dueño de la orden
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol != "superadmin" and (rol != "cliente" or db_orden.id_cliente != user_id):
        raise HTTPException(status_code=403, detail="No autorizado para aprobar este presupuesto")

    # Mapear los grupos de falla solicitados
    aprobaciones = {g.grupo_falla.strip().lower(): g.aprobado for g in request.grupos}
    
    # Agrupar los detalles por grupo_falla (clave normalizada) para validaciones de criticidad
    grupos_nombres = {}
    grupos_criticos = {}
    for d in db_presupuesto.detalles:
        gf_key = d.grupo_falla.strip().lower()
        grupos_nombres[gf_key] = d.grupo_falla
        if d.es_critico:
            grupos_criticos[gf_key] = True

    # Validar criticidad: si un grupo es crítico, no puede ser rechazado
    for gf_key in grupos_criticos:
        aprobado = aprobaciones.get(gf_key, None)
        if aprobado is False:
            raise HTTPException(
                status_code=400,
                detail=f"El grupo de reparación '{grupos_nombres[gf_key]}' es crítico y obligatorio para realizar la reparación."
            )

    # Actualizar los ítems del presupuesto
    total_aprobado = 0.0
    algun_aprobado = False
    algun_rechazado = False
    
    for d in db_presupuesto.detalles:
        gf_key = d.grupo_falla.strip().lower()
        # Si es crítico, se aprueba por defecto si no se menciona. Si es opcional y no se menciona, se rechaza.
        aprobado = aprobaciones.get(gf_key, d.es_critico)
        
        d.estado_item = "Aprobado" if aprobado else "Rechazado"
        if aprobado:
            total_aprobado += float(d.subtotal)
            algun_aprobado = True
        else:
            algun_rechazado = True

    # Determinar el estado general del presupuesto
    if algun_aprobado and not algun_rechazado:
        db_presupuesto.estado = "Aprobado"
    elif algun_aprobado and algun_rechazado:
        db_presupuesto.estado = "Aprobado Parcial"
    else:
        db_presupuesto.estado = "Rechazado"
        
    db_presupuesto.total_estimado = total_aprobado
    
    # Si hay aprobación (total o parcial), la orden pasa a 'En Reparación'
    estado_anterior = db_orden.estado_trabajo
    if algun_aprobado:
        db_orden.estado_trabajo = "En Reparación"
        comentario_bitacora = f"Presupuesto {db_presupuesto.estado}. Iniciando fase de reparación del vehículo."
    else:
        db_orden.estado_trabajo = "Diagnóstico"
        comentario_bitacora = "Presupuesto Rechazado. Esperando instrucciones o rectificación de presupuesto."
        
    db.commit()
    db.refresh(db_presupuesto)
    
    # Registrar en la bitácora
    crud.create_bitacora_estado(
        db=db,
        id_orden=db_orden.id_orden,
        estado_anterior=estado_anterior,
        nuevo_estado=db_orden.estado_trabajo,
        comentario=comentario_bitacora
    )
    
    return db_presupuesto

@router.post("/ordenes/{id_orden}/estado", response_model=schemas.OrdenTrabajoResponse)
def update_estado_orden(
    id_orden: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    db_orden = crud.get_orden_trabajo(db, id_orden=id_orden)
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    # Validar tenancy
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and db_orden.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    nuevo_estado = payload.get("estado_trabajo")
    comentario = payload.get("comentario") or f"Cambio de estado a {nuevo_estado}."
    
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="El parámetro 'estado_trabajo' es requerido")
        
    estado_anterior = db_orden.estado_trabajo
    db_orden.estado_trabajo = nuevo_estado
    
    db.commit()
    db.refresh(db_orden)
    
    # Registrar hito en bitácora
    crud.create_bitacora_estado(
        db=db,
        id_orden=id_orden,
        estado_anterior=estado_anterior,
        nuevo_estado=nuevo_estado,
        comentario=comentario
    )
    
    # Notificar al cliente
    try:
        from services.firebase_service import send_push_notification
        cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == db_orden.id_cliente).first()
        if cliente and cliente.fcm_token:
            send_push_notification(
                fcm_token=cliente.fcm_token,
                titulo="Actualización de Reparación",
                mensaje=f"Tu vehículo ha cambiado a estado: {nuevo_estado}. Comentario: {comentario}"
            )
    except Exception as e:
        print(f"Error notificando cambio de estado: {e}")
        
    return db_orden

@router.get("/ordenes/{id_orden}/bitacora", response_model=List[schemas.BitacoraEstadoReparacionResponse])
def get_bitacora_orden(
    id_orden: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    db_orden = crud.get_orden_trabajo(db, id_orden=id_orden)
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    
    if rol == "superadmin":
        pass
    elif rol == "cliente" and db_orden.id_cliente != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    elif rol != "superadmin" and rol != "cliente" and db_orden.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    return db_orden.bitacoras
