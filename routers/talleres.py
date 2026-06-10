from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
import crud, schemas, schemas_auth, models
from database import get_db
import dependencies
from typing import Optional

router = APIRouter()

@router.post("/", response_model=schemas.TallerResponse)
def create_taller(taller: schemas.TallerRegistroPublico, db: Session = Depends(get_db)):
    # 1. Verificar si el correo ya existe
    existing_email = get_taller_by_email(db, taller.correo)
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="Este correo electrónico ya está registrado en el sistema."
        )
        
    # Verificar si el correo ya existe como Administrador
    import models
    existing_admin = db.query(models.Admin).filter(models.Admin.correo == taller.correo).first()
    if existing_admin:
        raise HTTPException(
            status_code=400, 
            detail="Este correo ya tiene un administrador asociado."
        )
    
    # 2. Verificar si el NIT ya existe
    existing_nit = db.query(models.Taller).filter(models.Taller.nit == taller.nit).first()
    if existing_nit:
        raise HTTPException(
            status_code=400, 
            detail=f"El NIT {taller.nit} ya se encuentra registrado. Si es un error, contacta a soporte."
        )

    # 3. Crear el Tenant
    import re
    base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', taller.razon_social.lower()).strip('-')
    if not base_slug:
        base_slug = "taller"
    slug = base_slug
    contador = 1
    while db.query(models.Tenant).filter(models.Tenant.subdominio_slug == slug).first():
        slug = f"{base_slug}-{contador}"
        contador += 1
        
    nuevo_tenant = models.Tenant(
        nombre=taller.razon_social,
        subdominio_slug=slug
    )
    db.add(nuevo_tenant)
    db.commit()
    db.refresh(nuevo_tenant)

    # 4. Crear el Taller asociado al nuevo Tenant
    taller_create_dict = taller.model_dump()
    taller_create_dict["id_tenant"] = nuevo_tenant.id_tenant
    taller_create = schemas.TallerCreate(**taller_create_dict)
    nuevo_taller = crud.create_taller(db=db, taller=taller_create)

    return nuevo_taller

@router.get("/servicios-disponibles")
def get_servicios_disponibles(db: Session = Depends(get_db)):
    return db.query(models.Servicio).all()

@router.get("/especialidades-disponibles")
def get_especialidades_disponibles(db: Session = Depends(get_db)):
    import models
    standards = [
        {"nombre_especialidad": "Electricista Automotriz", "descripcion": "Experto en diagnóstico por escáner, baterías, alternadores y cableados"},
        {"nombre_especialidad": "Técnico en Suspensión y Neumáticos", "descripcion": "Diagnóstico y cambio de amortiguadores, frenos, rines y llantas"},
        {"nombre_especialidad": "Mecánico de Auxilio Rápido", "descripcion": "Reparaciones rápidas de motor, correas, bujías y suministro de fluidos"},
        {"nombre_especialidad": "Cerrajero de Vehículos", "descripcion": "Apertura de cerraduras y reprogramación de llaves inteligentes"},
        {"nombre_especialidad": "Operador de Grúas y Rescate", "descripcion": "Amarre, izaje y traslado seguro de vehículos siniestrados"},
        {"nombre_especialidad": "Especialista en Sistemas de Enfriamiento", "descripcion": "Control de radiadores, bombas de agua, fugas de refrigerante y termostatos"}
    ]
    # Limpieza de especialidades obsoletas
    nombres_validos_esp = [sp["nombre_especialidad"] for sp in standards]
    obsoletas = db.query(models.Especialidad).filter(~models.Especialidad.nombre_especialidad.in_(nombres_validos_esp)).all()
    for obs in obsoletas:
        # Remover relaciones muchos a muchos
        obs.tecnicos.clear()
        db.delete(obs)
    db.commit()

    for sp in standards:
        existente = db.query(models.Especialidad).filter(models.Especialidad.nombre_especialidad == sp["nombre_especialidad"]).first()
        if not existente:
            db.add(models.Especialidad(**sp))
    db.commit()
    return db.query(models.Especialidad).all()

@router.get("/{id_taller}", response_model=schemas.TallerResponse)
def read_taller(
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and rol != "cliente" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado para acceder a este taller")
        
    return taller

@router.get("/", response_model=list[schemas.TallerResponse])
def read_talleres(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol == "superadmin" or rol == "cliente":
        return crud.get_talleres(db, skip=skip, limit=limit)
    else:
        return db.query(models.Taller).filter(models.Taller.id_tenant == id_tenant).offset(skip).limit(limit).all()

def get_taller_by_email(db: Session, email: str):
    return db.query(models.Taller).filter(models.Taller.correo == email).first()

@router.post("/login")
def login(request: schemas_auth.LoginRequest, db: Session = Depends(get_db)):
    correo_limpio = request.correo.strip().lower()
    clave_limpia = request.password.strip()
    import utils

    # 0. Cortocircuito para SuperAdmin (Garantiza velocidad y cero bloqueos)
    if correo_limpio == "admin@asiscar.com" and clave_limpia == "admin123":
        token = utils.create_access_token({
            "sub": "1",
            "user_id": 1,
            "role": "superadmin",
            "id_tenant": None
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": 1,
            "user_name": "SuperAdmin",
            "role": "superadmin"
        }

    # 1. Intentar como Taller
    db_taller = db.query(models.Taller).filter(models.Taller.correo == correo_limpio).first()
    if db_taller:
        if not crud.verify_password(request.password, db_taller.password_hash):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
        token = utils.create_access_token({
            "sub": str(db_taller.id_taller),
            "user_id": db_taller.id_taller,
            "role": "taller",
            "id_tenant": db_taller.id_tenant
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": db_taller.id_taller,
            "user_name": db_taller.razon_social,
            "nit": db_taller.nit,
            "direccion": db_taller.direccion_fisica,
            "role": "taller"
        }
    
    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

from fastapi import UploadFile, File
import os
import shutil

@router.post("/{id_taller}/upload-docs")
async def upload_documentos(
    id_taller: int,
    foto_nit: UploadFile = File(None),
    foto_local: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")

    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # TODO: Integración real con Supabase Storage. 
    # Por ahora, simularemos que subimos y obtenemos las URLs.
    
    if foto_nit:
        # Simulamos que subimos a Supabase y nos da esta URL:
        fake_url_nit = f"https://supabase.co/storage/v1/object/public/documentos_verificacion/nit_{id_taller}.jpg"
        taller.foto_nit_url = fake_url_nit
        
    if foto_local:
        # Simulamos que subimos a Supabase y nos da esta URL:
        fake_url_local = f"https://supabase.co/storage/v1/object/public/documentos_verificacion/local_{id_taller}.jpg"
        taller.foto_local_url = fake_url_local

    if foto_nit or foto_local:
        db.commit()
        db.refresh(taller)

    return {"message": "Documentos subidos exitosamente", "foto_nit_url": taller.foto_nit_url, "foto_local_url": taller.foto_local_url}

@router.post("/{id_taller}/horario")
def update_horario(
    id_taller: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    from datetime import time
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    taller.es_24_7 = payload.get("es_24_7", False)
    
    ha = payload.get("horario_apertura")
    hc = payload.get("horario_cierre")
    
    try:
        if ha and ":" in ha:
            h, m = map(int, ha.split(":"))
            taller.horario_apertura = time(hour=h, minute=m)
        if hc and ":" in hc:
            h, m = map(int, hc.split(":"))
            taller.horario_cierre = time(hour=h, minute=m)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Formato de hora inválido (Use HH:MM)")
            
    db.commit()
    return {"status": "success", "message": "Horario actualizado correctamente"}

@router.patch("/{id_taller}/aprobar")
def aprobar_taller(
    id_taller: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    """
    Endpoint para que el Superadmin apruebe un taller.
    Cambia el estado a 'Aprobado' y envía un correo de notificación.
    """
    import models
    from utils import send_approval_email
    
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin":
        raise HTTPException(status_code=403, detail="Solo el Superadministrador puede aprobar talleres")

    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    if taller.estado_aprobacion == 'Aprobado':
        return {"message": "El taller ya se encuentra aprobado."}

    # Cambiar estado
    taller.estado_aprobacion = 'Aprobado'
    db.commit()
    db.refresh(taller)
    
    # Enviar correo de notificación en segundo plano
    background_tasks.add_task(send_approval_email, destinatario=taller.correo, nombre_taller=taller.razon_social)
    
    mensaje = "Taller aprobado exitosamente. Se ha encolado el correo de notificación."

    return {
        "status": "success",
        "message": mensaje,
        "estado_actual": taller.estado_aprobacion
    }

@router.get("/{id_taller}/solicitudes")
def get_taller_solicitudes(
    id_taller: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    from services.matching_service import calcular_distancia
    
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Traer incidentes pendientes o que ya tengan cotización aceptada
    incidentes = db.query(models.Incidente).filter(models.Incidente.estado_solicitud.in_(['Pendiente', 'Cotización Aceptada'])).all()
    resultados = []
    
    for inc in incidentes:
        # Verificar si hay una cotización aceptada para este incidente
        cotizacion_aceptada = db.query(models.Cotizacion).filter(
            models.Cotizacion.id_incidente == inc.id_incidente,
            models.Cotizacion.estado == 'Aceptada'
        ).first()

        # Si ya hay una cotización aceptada y no es de nuestro taller, se descarta el incidente
        if cotizacion_aceptada and cotizacion_aceptada.id_taller != id_taller:
            continue

        # Obtener nuestra cotización para este incidente si existe
        mi_cotizacion = db.query(models.Cotizacion).filter(
            models.Cotizacion.id_incidente == inc.id_incidente,
            models.Cotizacion.id_taller == id_taller
        ).first()

        # Si ya rechazamos esta solicitud, la descartamos
        if mi_cotizacion and mi_cotizacion.estado == 'Rechazada':
            continue

        cot_data = None
        if mi_cotizacion:
            cot_data = {
                "id_cotizacion": mi_cotizacion.id_cotizacion,
                "monto_estimado": float(mi_cotizacion.monto_estimado),
                "tiempo_estimado_minutos": mi_cotizacion.tiempo_estimado_minutos,
                "comentario": mi_cotizacion.comentario,
                "estado": mi_cotizacion.estado
            }

        distancia = 0.0
        if taller and taller.ubicacion_base_latitud and taller.ubicacion_base_longitud and inc.ubicacion_latitud and inc.ubicacion_longitud:
            distancia = round(calcular_distancia(
                taller.ubicacion_base_latitud,
                taller.ubicacion_base_longitud,
                inc.ubicacion_latitud,
                inc.ubicacion_longitud
            ), 1)
            
        url_audio = None
        url_foto = None
        for ev in inc.evidencias:
            if ev.tipo_recurso == "Audio":
                url_audio = ev.url_archivo
            elif ev.tipo_recurso == "Foto":
                url_foto = ev.url_archivo

        evaluacion_ia = "Calculando diagnóstico..."
        if inc.analisis_ia:
            evaluacion_ia = inc.analisis_ia.resumen_estructurado or "Sin diagnóstico"

        baseUrl = str(request.base_url).rstrip("/")
            
        resultados.append({
            "id_incidente": inc.id_incidente,
            "tipo_problema": inc.tipo_problema,
            "nivel_prioridad": inc.nivel_prioridad or "Media",
            "distancia_km": distancia,
            "cliente": f"{inc.cliente.nombres} {inc.cliente.apellidos}" if inc.cliente else "Conductor en Ruta",
            "vehiculo": f"{inc.vehiculo.marca} {inc.vehiculo.modelo} ({inc.vehiculo.color})" if inc.vehiculo else "Vehículo",
            "transcripcion_audio": inc.descripcion_manual,
            "descripcion_manual": inc.descripcion_manual,
            "url_audio_evidencia": f"{baseUrl}/{url_audio}" if url_audio else None,
            "url_foto_evidencia": f"{baseUrl}/{url_foto}" if url_foto else None,
            "evaluacion_ia": evaluacion_ia,
            "latitud": inc.ubicacion_latitud,
            "longitud": inc.ubicacion_longitud,
            "cotizacion": cot_data
        })
    return resultados

from pydantic import BaseModel

class RechazoSolicitudRequest(BaseModel):
    justificacion: str

@router.post("/{id_taller}/solicitudes/{id_incidente}/rechazar")
def rechazar_solicitud_endpoint(
    id_taller: int,
    id_incidente: int,
    payload: RechazoSolicitudRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Verificar si el incidente existe
    incidente = db.query(models.Incidente).filter(models.Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    # Buscar si ya existe una cotización
    mi_cotizacion = db.query(models.Cotizacion).filter(
        models.Cotizacion.id_incidente == id_incidente,
        models.Cotizacion.id_taller == id_taller
    ).first()

    if mi_cotizacion:
        mi_cotizacion.estado = 'Rechazada'
        mi_cotizacion.comentario = payload.justificacion
    else:
        # Crear cotización rechazada
        mi_cotizacion = models.Cotizacion(
            id_incidente=id_incidente,
            id_taller=id_taller,
            id_tenant=taller.id_tenant,
            monto_estimado=0.0,
            tiempo_estimado_minutos=0,
            comentario=payload.justificacion,
            estado='Rechazada'
        )
        db.add(mi_cotizacion)

    db.commit()
    return {"status": "success", "message": "Solicitud rechazada correctamente"}



@router.post("/{id_taller}/tecnicos", response_model=schemas.TecnicoResponse)
def create_tecnico_endpoint(
    id_taller: int,
    tecnico: schemas.TecnicoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Generar correo dinámico basado en slug del tenant obligatoriamente
    import unicodedata
    
    def limpiar(texto: str) -> str:
        texto = texto.strip().lower()
        # Quitar acentos/tildes
        texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        # Tomar primera palabra
        return texto.split()[0]
        
    nom = limpiar(tecnico.nombres)
    ape = limpiar(tecnico.apellidos)
    
    # Obtener iniciales del slug
    slug = taller.tenant.subdominio_slug if (taller.tenant and taller.tenant.subdominio_slug) else "taller"
    slug_clean = "".join(c for c in unicodedata.normalize('NFD', slug.lower()) if unicodedata.category(c) != 'Mn')
    palabras = slug_clean.split('-')
    iniciales = "".join(p[0] for p in palabras if p)
    
    # Crear formato: nombre.apellido-iniciales@asiscar.com
    correo_generado = f"{nom}.{ape}-{iniciales}@asiscar.com"

    existing = crud.get_tecnico_by_email(db, email=correo_generado)
    if existing:
        base_email = correo_generado.split("@")[0]
        suffix = 1
        while existing:
            correo_generado = f"{base_email}{suffix}@asiscar.com"
            existing = crud.get_tecnico_by_email(db, email=correo_generado)
            suffix += 1
            
    return crud.create_tecnico(db=db, tecnico=tecnico, id_taller=id_taller, correo=correo_generado)

@router.get("/{id_taller}/tecnicos", response_model=list[schemas.TecnicoResponse])
def read_tecnicos(
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    return crud.get_tecnicos_by_taller(db=db, id_taller=id_taller)

@router.get("/servicios/todos")
def get_all_servicios(db: Session = Depends(get_db)):
    import models
    
    standard = [
        {
            "nombre_servicio": "Falla Eléctrica y Electrónica",
            "descripcion": "Diagnóstico por escáner OBD2, reparación de alternadores, luces, cableado dañado y fallas en sensores o computadora del vehículo.",
            "tarifa_base_estimada": 50.0
        },
        {
            "nombre_servicio": "Frenos y Suspensión",
            "descripcion": "Cambio de pastillas/discos de freno, amortiguadores, bujes, terminales de dirección y solución a ruidos en la suspensión.",
            "tarifa_base_estimada": 40.0
        },
        {
            "nombre_servicio": "Combustible o Carga de Emergencia",
            "descripcion": "Suministro de combustible en ruta o asistencia de remolque/carga rápida para vehículos eléctricos que se hayan quedado sin batería.",
            "tarifa_base_estimada": 30.0
        },
        {
            "nombre_servicio": "Cerrajería Automotriz",
            "descripcion": "Apertura técnica de puertas por llaves olvidadas dentro del carro, duplicados y reprogramación de llaves electrónicas o controles.",
            "tarifa_base_estimada": 80.0
        },
        {
            "nombre_servicio": "Remolque y Grúa",
            "descripcion": "Traslado seguro del vehículo siniestrado o averiado en grúa de plataforma o arrastre hasta el taller o domicilio seleccionado.",
            "tarifa_base_estimada": 150.0
        },
        {
            "nombre_servicio": "Mecánica de Motor",
            "descripcion": "Reparaciones complejas de motor, cambio de correa de distribución, empaquetaduras de culata, bujías y afinamiento de potencia.",
            "tarifa_base_estimada": 100.0
        },
        {
            "nombre_servicio": "Sistema de Enfriamiento",
            "descripcion": "Solución a problemas de sobrecalentamiento, fugas de refrigerante, cambio de mangueras, termostato, radiador y bomba de agua.",
            "tarifa_base_estimada": 60.0
        },
        {
            "nombre_servicio": "Chapería y Pintura",
            "descripcion": "Reparación de abolladuras por choques, cuadratura de chasis, pintura al horno de piezas individuales o pintado general del vehículo.",
            "tarifa_base_estimada": 200.0
        },
        {
            "nombre_servicio": "Paso de Corriente (Batería)",
            "descripcion": "Reinicio de batería muerta mediante cables de arranque o arrancador portátil en sitio, y diagnóstico del estado de carga del acumulador.",
            "tarifa_base_estimada": 20.0
        },
        {
            "nombre_servicio": "Auxilio de Llanta Pinchada",
            "descripcion": "Desmontaje de la rueda dañada y colocación de la llanta de auxilio del cliente en sitio, o traslado de la llanta a vulcanizadora para su parchado.",
            "tarifa_base_estimada": 25.0
        },
        {
            "nombre_servicio": "Aire Acondicionado y Calefacción",
            "descripcion": "Carga de gas refrigerante R134a, detección de fugas en el compresor/condensador, cambio de filtro de cabina y desinfección del sistema.",
            "tarifa_base_estimada": 45.0
        },
        {
            "nombre_servicio": "Transmisión y Embrague",
            "descripcion": "Reparación y mantenimiento de cajas de cambios automáticas y manuales, cambio de kit de embrague (disco y prensa) y aceite de transmisión.",
            "tarifa_base_estimada": 120.0
        },
        {
            "nombre_servicio": "Alineación y Balanceo",
            "descripcion": "Ajuste de los ángulos de las ruedas (camber/caster/convergencia) y balanceo dinámico de contrapesos para evitar vibraciones al conducir.",
            "tarifa_base_estimada": 35.0
        },
        {
            "nombre_servicio": "Inspección Técnica y Diagnóstico",
            "descripcion": "Revisión multipunto de seguridad, escaneo completo y evaluación mecánica detallada pre-viaje o previa a la compra/venta de un vehículo usado.",
            "tarifa_base_estimada": 50.0
        },
        {
            "nombre_servicio": "Lavado y Estética Automotriz",
            "descripcion": "Lavado a presión, aspirado profundo de interiores, pulido/encerado de pintura exterior y restauración de partes plásticas o faros.",
            "tarifa_base_estimada": 30.0
        },
        {
            "nombre_servicio": "Vehículos Eléctricos e Híbridos",
            "descripcion": "Diagnóstico y reparación de motores eléctricos, inversores, sistema de baterías de alta tensión, refrigeración de celdas de batería y cargadores integrados.",
            "tarifa_base_estimada": 110.0
        }
    ]
    
    # Limpieza de servicios antiguos/duplicados
    nombres_validos = [s["nombre_servicio"] for s in standard]
    obsoletos = db.query(models.Servicio).filter(~models.Servicio.nombre_servicio.in_(nombres_validos)).all()
    for obs in obsoletos:
        db.query(models.TallerServicio).filter(models.TallerServicio.id_servicio == obs.id_servicio).delete()
        db.delete(obs)
    db.commit()

    for s in standard:
        existente = db.query(models.Servicio).filter(models.Servicio.nombre_servicio == s["nombre_servicio"]).first()
        if existente:
            # Actualizar descripción y tarifa por si cambiaron
            existente.descripcion = s["descripcion"]
            existente.tarifa_base_estimada = s["tarifa_base_estimada"]
        else:
            db_s = models.Servicio(**s)
            db.add(db_s)
    db.commit()

    servicios = db.query(models.Servicio).all()
    return [{
        "id_servicio": s.id_servicio, 
        "nombre_servicio": s.nombre_servicio,
        "descripcion": s.descripcion,
        "tarifa_base_estimada": float(s.tarifa_base_estimada)
    } for s in servicios]




@router.post("/tecnicos/login", response_model=schemas_auth.TokenResponse)
def login_tecnico(request: schemas_auth.LoginRequest, db: Session = Depends(get_db)):
    db_tecnico = crud.get_tecnico_by_email(db, email=request.correo)
    if not db_tecnico or not crud.verify_password(request.password, db_tecnico.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    
    import utils
    token = utils.create_access_token({
        "sub": str(db_tecnico.id_tecnico),
        "user_id": db_tecnico.id_tecnico,
        "role": "tecnico",
        "id_tenant": db_tecnico.taller.id_tenant if db_tecnico.taller else None
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_tecnico.id_tecnico,
        "user_name": f"{db_tecnico.nombres} {db_tecnico.apellidos}",
        "primer_login": db_tecnico.primer_login
    }

@router.post("/tecnicos/{id_tecnico}/cambiar-password")
def cambiar_password_tecnico(
    id_tecnico: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if "new_password" not in data or not data["new_password"]:
        raise HTTPException(status_code=400, detail="La nueva contraseña es requerida")

    tecnico.password_hash = crud.get_password_hash(data["new_password"])
    tecnico.primer_login = False
    db.commit()
    
    return {"message": "Contraseña actualizada correctamente"}
    
@router.post("/tecnicos/{id_tecnico}/resetear-password")
def resetear_password_tecnico(
    id_tecnico: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if "new_password" not in data or not data["new_password"]:
        raise HTTPException(status_code=400, detail="La nueva contraseña es requerida")

    tecnico.password_hash = crud.get_password_hash(data["new_password"])
    tecnico.primer_login = True
    db.commit()
    
    return {"message": "Contraseña reseteada correctamente"}

@router.post("/tecnicos/{id_tecnico}/fcm-token")
def update_tecnico_fcm_token(
    id_tecnico: int,
    request: schemas.UpdateFCMTokenRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    db_tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not db_tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and db_tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    db_tecnico.fcm_token = request.fcm_token
    db.commit()
    return {"message": "Token FCM de Técnico actualizado exitosamente"}

@router.get("/{id_taller}/trabajos")
def get_taller_trabajos(
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    asistencias = db.query(models.Asistencia).filter(models.Asistencia.id_taller == id_taller).all()
    resultados = []
    for asis in asistencias:
        inc = asis.incidente
        if not inc:
            continue
        pago_monto = 0.0
        if asis.pago:
            pago_monto = float(asis.pago.monto_total_cliente)
        else:
            if inc.nivel_prioridad == "Alta":
                pago_monto = 80.0
            elif inc.nivel_prioridad == "Media":
                pago_monto = 50.0
            elif inc.nivel_prioridad == "Baja":
                pago_monto = 30.0
            else:
                pago_monto = 50.0

        resultados.append({
            "id_incidente": inc.id_incidente,
            "id_asistencia": asis.id_asistencia,
            "estado": inc.estado_solicitud,
            "cliente": f"{inc.cliente.nombres} {inc.cliente.apellidos}" if inc.cliente else "Conductor",
            "vehiculo": f"{inc.vehiculo.marca} {inc.vehiculo.modelo}" if inc.vehiculo else "Vehículo",
            "problema": inc.tipo_problema,
            "prioridad": inc.nivel_prioridad or "Media",
            "tecnico": f"{asis.tecnico.nombres} {asis.tecnico.apellidos}" if asis.tecnico else "Sin asignar",
            "monto": pago_monto,
            "latitud": inc.ubicacion_latitud,
            "longitud": inc.ubicacion_longitud
        })

    return resultados


@router.get("/tecnicos/{id_tecnico}/trabajos")
def get_tecnico_trabajos(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "tecnico" and user_id != id_tecnico:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if rol != "superadmin" and rol != "tecnico" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    asistencias = db.query(models.Asistencia).filter(models.Asistencia.id_tecnico == id_tecnico).all()
    
    resultados = []
    for asis in asistencias:
        inc = asis.incidente
        if not inc:
            continue
            
        pago_monto = 50.0
        if asis.pago:
            pago_monto = float(asis.pago.monto_total_cliente)
        else:
            if inc.nivel_prioridad == "Alta": pago_monto = 80.0
            elif inc.nivel_prioridad == "Baja": pago_monto = 30.0

        resultados.append({
            "id": f"INC-{inc.id_incidente}",
            "id_incidente": inc.id_incidente,
            "id_asistencia": asis.id_asistencia,
            "estado": inc.estado_solicitud,
            "cliente": f"{inc.cliente.nombres} {inc.cliente.apellidos}" if inc.cliente else "Conductor",
            "vehiculo": f"{inc.vehiculo.marca} {inc.vehiculo.modelo} ({inc.vehiculo.color}) | Placa: {inc.vehiculo.placa} | Año: {inc.vehiculo.año} | Transmisión: {inc.vehiculo.tipo_transmision}" if inc.vehiculo else "Vehículo",
            "problema": inc.tipo_problema,
            "servicio": inc.tipo_problema,
            "tipo": inc.tipo_problema,
            "fecha": inc.fecha_hora_reporte.strftime("%Y-%m-%d %H:%M") if inc.fecha_hora_reporte else "N/A",
            "monto": pago_monto,
            "prioridad": inc.nivel_prioridad or "Media",
            "lat": inc.ubicacion_latitud,
            "lng": inc.ubicacion_longitud
        })
    return resultados

@router.post("/tecnicos/{id_tecnico}/ubicacion")
def update_tecnico_ubicacion(
    id_tecnico: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "tecnico" and user_id != id_tecnico:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if rol != "superadmin" and rol != "tecnico" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if "latitud" not in request or "longitud" not in request:
        raise HTTPException(status_code=400, detail="Latitud y Longitud requeridas")
        
    tecnico.ubicacion_actual_latitud = request["latitud"]
    tecnico.ubicacion_actual_longitud = request["longitud"]
    db.commit()
    return {"status": "success", "message": "Ubicación actualizada"}

# --- NUEVOS ENDPOINTS PARA SERVICIOS Y ESPECIALIDADES ---

@router.get("/{id_taller}/servicios")
def get_taller_servicios(
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and rol != "cliente" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Retorna los servicios activos para el taller
    servicios = db.query(models.TallerServicio).filter(models.TallerServicio.id_taller == id_taller).all()
    # Mapear con datos legibles
    res = []
    for s in servicios:
        serv_base = db.query(models.Servicio).filter(models.Servicio.id_servicio == s.id_servicio).first()
        res.append({
            "id_taller_servicio": s.id_taller_servicio,
            "id_servicio": s.id_servicio,
            "nombre_servicio": serv_base.nombre_servicio if serv_base else "Servicio Desconocido",
            "precio_especifico_taller": s.precio_especifico_taller,
            "tiempo_estimado_minutos": s.tiempo_estimado_minutos,
            "estado_disponible": s.estado_disponible
        })
    return res

@router.post("/{id_taller}/servicios")
def vincular_taller_servicio(
    id_taller: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    # request: { id_servicio: int, precio: float, tiempo: int }
    if "id_servicio" not in request:
        raise HTTPException(status_code=400, detail="id_servicio es requerido")
    
    # Validar duplicados
    existe = db.query(models.TallerServicio).filter(
        models.TallerServicio.id_taller == id_taller,
        models.TallerServicio.id_servicio == request["id_servicio"]
    ).first()
    
    if existe:
        existe.precio_especifico_taller = request.get("precio", existe.precio_especifico_taller)
        existe.tiempo_estimado_minutos = request.get("tiempo", existe.tiempo_estimado_minutos)
        db.commit()
        return {"status": "updated"}
        
    nuevo = models.TallerServicio(
        id_taller=id_taller,
        id_servicio=request["id_servicio"],
        precio_especifico_taller=request.get("precio", 50.0),
        tiempo_estimado_minutos=request.get("tiempo", 30),
        estado_disponible=True
    )
    db.add(nuevo)
    db.commit()
    return {"status": "created"}



@router.get("/tecnicos/{id_tecnico}")
def get_tecnico_perfil(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    import models
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "tecnico" and user_id != id_tecnico:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if rol != "superadmin" and rol != "tecnico" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")

    return {
        "id_tecnico": tecnico.id_tecnico,
        "nombres": tecnico.nombres,
        "apellidos": tecnico.apellidos,
        "correo": tecnico.correo,
        "taller": tecnico.taller.razon_social if tecnico.taller else "Taller Central"
    }

@router.get("/tecnicos/{id_tecnico}/especialidades")
def get_tecnico_especialidades(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    # Consulta directa de relación
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")
    if rol == "tecnico" and user_id != id_tecnico:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if rol != "superadmin" and rol != "tecnico" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    return [{"id_especialidad": e.id_especialidad, "nombre_especialidad": e.nombre_especialidad} for e in tecnico.especialidades]

@router.post("/tecnicos/{id_tecnico}/especialidades")
def vincular_tecnico_especialidad(
    id_tecnico: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    # request: { id_especialidad: int }
    if "id_especialidad" not in request:
        raise HTTPException(status_code=400, detail="id_especialidad es requerido")
        
    tecnico = db.query(models.Tecnico).filter(models.Tecnico.id_tecnico == id_tecnico).first()
    esp = db.query(models.Especialidad).filter(models.Especialidad.id_especialidad == request["id_especialidad"]).first()
    
    if not tecnico or not esp:
        raise HTTPException(status_code=404, detail="Técnico o Especialidad no encontrada")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and tecnico.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if esp not in tecnico.especialidades:
        tecnico.especialidades.append(esp)
        db.commit()
        
    return {"status": "linked"}

@router.patch("/{id_taller}")
def update_taller_perfil(
    id_taller: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
        
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin" and taller.id_tenant != id_tenant:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    if "telefono_taller" in request:
        taller.telefono_taller = request["telefono_taller"]
    if "cuenta_bancaria" in request:
        taller.cuenta_bancaria = request["cuenta_bancaria"]
    if "horario_apertura" in request:
        taller.horario_apertura = request["horario_apertura"]
    if "horario_cierre" in request:
        taller.horario_cierre = request["horario_cierre"]
        
    db.commit()
    return {"status": "success", "message": "Perfil actualizado"}
