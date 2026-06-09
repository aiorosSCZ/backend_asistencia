from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import time
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- CRUD Cliente ---
def get_cliente(db: Session, cliente_id: int):
    return db.query(models.Cliente).filter(models.Cliente.id_cliente == cliente_id).first()

def get_cliente_by_email(db: Session, email: str):
    return db.query(models.Cliente).filter(models.Cliente.correo == email).first()

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cliente).offset(skip).limit(limit).all()

def create_cliente(db: Session, cliente: schemas.ClienteCreate):
    hashed_password = get_password_hash(cliente.password)
    db_cliente = models.Cliente(
        nombres=cliente.nombres,
        apellidos=cliente.apellidos,
        ci_dni=cliente.ci_dni,
        telefono=cliente.telefono,
        correo=cliente.correo,
        password_hash=hashed_password,
        foto_perfil_url=cliente.foto_perfil_url
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

# --- CRUD Taller ---
def get_talleres(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Taller).offset(skip).limit(limit).all()

def create_taller(db: Session, taller: schemas.TallerCreate):
    hashed_password = get_password_hash(taller.password)
    
    db_taller = models.Taller(
        id_tenant=taller.id_tenant,
        razon_social=taller.razon_social,
        nombre_representante=taller.nombre_representante,
        nit=taller.nit,
        correo=taller.correo,
        ubicacion_base_latitud=taller.ubicacion_base_latitud,
        ubicacion_base_longitud=taller.ubicacion_base_longitud,
        direccion_fisica=taller.direccion_fisica,
        telefono_taller=taller.telefono_taller,
        logo_url=taller.logo_url,
        es_24_7=taller.es_24_7,
        horario_apertura=taller.horario_apertura,
        horario_cierre=taller.horario_cierre,
        horario_cierre_sabado=taller.horario_cierre_sabado,
        foto_nit_url=taller.foto_nit_url,
        foto_local_url=taller.foto_local_url,
        cuenta_bancaria=taller.cuenta_bancaria,
        password_hash=hashed_password
    )
    db.add(db_taller)
    db.commit()
    db.refresh(db_taller)
    return db_taller

# --- CRUD Incidente ---
def create_incidente(db: Session, incidente: schemas.IncidenteCreate):
    if incidente.uuid_offline:
        existing = db.query(models.Incidente).filter(models.Incidente.uuid_offline == incidente.uuid_offline).first()
        if existing:
            return existing

    db_incidente = models.Incidente(**incidente.model_dump())
    db.add(db_incidente)
    db.commit()
    db.refresh(db_incidente)
    return db_incidente

def get_incidentes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Incidente).offset(skip).limit(limit).all()

# --- CRUD Tecnico ---
def get_tecnico_by_email(db: Session, email: str):
    return db.query(models.Tecnico).filter(models.Tecnico.correo == email).first()

def get_tecnicos_by_taller(db: Session, id_taller: int):
    return db.query(models.Tecnico).filter(models.Tecnico.id_taller == id_taller).all()

def create_tecnico(db: Session, tecnico: schemas.TecnicoCreate, id_taller: int = None, correo: str = None):
    hashed_password = get_password_hash(tecnico.password)
    taller_id = id_taller if id_taller is not None else tecnico.id_taller
    email_to_use = correo if correo is not None else tecnico.correo
    
    # Obtener el taller para sacar el id_tenant
    db_taller = db.query(models.Taller).filter(models.Taller.id_taller == taller_id).first()
    taller_tenant_id = db_taller.id_tenant if db_taller else None
    
    db_tecnico = models.Tecnico(
        id_taller=taller_id,
        id_tenant=taller_tenant_id,
        nombres=tecnico.nombres,
        apellidos=tecnico.apellidos,
        ci_tecnico=tecnico.ci_tecnico,
        telefono_contacto=tecnico.telefono_contacto,
        correo=email_to_use,
        password_hash=hashed_password
    )
    db.add(db_tecnico)
    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico


# --- CRUD Órdenes de Trabajo ---
def create_orden_trabajo(db: Session, orden: schemas.OrdenTrabajoCreate, id_tenant: int):
    db_orden = models.OrdenTrabajo(
        id_tenant=id_tenant,
        id_cliente=orden.id_cliente,
        id_vehiculo=orden.id_vehiculo,
        id_incidente_origen=orden.id_incidente_origen,
        estado_recepcion=orden.estado_recepcion,
        fecha_compromiso_entrega=orden.fecha_compromiso_entrega
    )
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    
    # Registrar el hito inicial
    create_bitacora_estado(
        db=db,
        id_orden=db_orden.id_orden,
        estado_anterior=None,
        nuevo_estado=db_orden.estado_trabajo,
        comentario="Ingreso de vehículo al taller e inicio de fase de diagnóstico."
    )
    return db_orden

def get_orden_trabajo(db: Session, id_orden: int):
    return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()

def get_ordenes_trabajo_by_tenant(db: Session, id_tenant: int, skip: int = 0, limit: int = 100):
    return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_tenant == id_tenant).offset(skip).limit(limit).all()

def get_ordenes_trabajo_by_cliente(db: Session, id_cliente: int, skip: int = 0, limit: int = 100):
    return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_cliente == id_cliente).offset(skip).limit(limit).all()


# --- CRUD Presupuestos ---
def create_presupuesto(db: Session, id_orden: int, presupuesto: schemas.PresupuestoCreate):
    # Obtener la orden de trabajo para sacar el id_tenant
    db_orden = db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id_orden == id_orden).first()
    orden_tenant_id = db_orden.id_tenant if db_orden else None

    # Calcular el total estimado sumando los subtotales
    total = 0.0
    db_detalles = []
    
    for d in presupuesto.detalles:
        sub = float(d.cantidad) * float(d.precio_unitario)
        total += sub
        db_detalles.append(models.DetallePresupuesto(
            id_tenant=orden_tenant_id,
            categoria=d.categoria,
            grupo_falla=d.grupo_falla,
            es_critico=d.es_critico,
            tipo_item=d.tipo_item,
            item_descripcion=d.item_descripcion,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            subtotal=sub
        ))

    db_presupuesto = models.Presupuesto(
        id_orden=id_orden,
        id_tenant=orden_tenant_id,
        descripcion_general=presupuesto.descripcion_general,
        version=presupuesto.version,
        total_estimado=total,
        detalles=db_detalles
    )
    db.add(db_presupuesto)
    db.commit()
    db.refresh(db_presupuesto)
    return db_presupuesto

def get_presupuesto(db: Session, id_presupuesto: int):
    return db.query(models.Presupuesto).filter(models.Presupuesto.id_presupuesto == id_presupuesto).first()


# --- CRUD Bitácora ---
def create_bitacora_estado(db: Session, id_orden: int, estado_anterior: str, nuevo_estado: str, comentario: str):
    db_bitacora = models.BitacoraEstadoReparacion(
        id_orden=id_orden,
        estado_anterior=estado_anterior,
        nuevo_estado=nuevo_estado,
        comentario=comentario
    )
    db.add(db_bitacora)
    db.commit()
    db.refresh(db_bitacora)
    return db_bitacora


# --- CRUD Cotizaciones ---
def create_cotizacion(db: Session, cotizacion: schemas.CotizacionCreate, id_incidente: int, id_taller: int):
    if cotizacion.uuid_offline:
        existing = db.query(models.Cotizacion).filter(models.Cotizacion.uuid_offline == cotizacion.uuid_offline).first()
        if existing:
            return existing

    # Obtener el taller para sacar el id_tenant
    db_taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    taller_tenant_id = db_taller.id_tenant if db_taller else None

    db_cotizacion = models.Cotizacion(
        id_incidente=id_incidente,
        id_taller=id_taller,
        id_tenant=taller_tenant_id,
        monto_estimado=cotizacion.monto_estimado,
        tiempo_estimado_minutos=cotizacion.tiempo_estimado_minutos,
        comentario=cotizacion.comentario,
        uuid_offline=cotizacion.uuid_offline
    )
    db.add(db_cotizacion)
    db.commit()
    db.refresh(db_cotizacion)
    return db_cotizacion

def get_cotizaciones_by_incidente(db: Session, id_incidente: int):
    return db.query(models.Cotizacion).filter(models.Cotizacion.id_incidente == id_incidente).all()

def get_cotizacion(db: Session, id_cotizacion: int):
    return db.query(models.Cotizacion).filter(models.Cotizacion.id_cotizacion == id_cotizacion).first()

