from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, time

# --- Tenant Schemas ---
class TenantBase(BaseModel):
    nombre: str
    subdominio_slug: str

class TenantCreate(TenantBase):
    pass

class TenantResponse(TenantBase):
    id_tenant: int
    activo: bool
    model_config = ConfigDict(from_attributes=True)

# --- Cliente Schemas ---
class ClienteBase(BaseModel):
    nombres: str
    apellidos: str
    ci_dni: str
    telefono: str
    correo: EmailStr
    foto_perfil_url: Optional[str] = None

class ClienteCreate(ClienteBase):
    password: str

class ClienteResponse(ClienteBase):
    id_cliente: int
    estado_cuenta: str
    calificacion_promedio: float

    model_config = ConfigDict(from_attributes=True)

# --- Taller Schemas ---
class TallerBase(BaseModel):
    razon_social: str
    nombre_representante: str
    nit: str = Field(..., pattern=r"^[0-9]+$")
    correo: EmailStr
    ubicacion_base_latitud: float
    ubicacion_base_longitud: float
    direccion_fisica: Optional[str] = None
    telefono_taller: Optional[str] = None
    logo_url: Optional[str] = None
    es_24_7: bool = False
    horario_apertura: Optional[time] = None
    horario_cierre: Optional[time] = None
    horario_cierre_sabado: Optional[time] = None
    foto_nit_url: Optional[str] = None
    foto_local_url: Optional[str] = None
    cuenta_bancaria: Optional[str] = None

class TallerCreate(TallerBase):
    password: str
    id_tenant: int

class TallerRegistroPublico(TallerBase):
    password: str

class TallerResponse(TallerBase):
    id_taller: int
    id_tenant: int
    id_admin_aprobador: Optional[int] = None
    estado_aprobacion: str
    calificacion_promedio: float

    model_config = ConfigDict(from_attributes=True)

# --- Especialidad Schemas ---
class EspecialidadBase(BaseModel):
    nombre_especialidad: str
    descripcion: Optional[str] = None

class EspecialidadResponse(EspecialidadBase):
    id_especialidad: int
    model_config = ConfigDict(from_attributes=True)

# --- Tecnico Schemas ---
class TecnicoBase(BaseModel):
    nombres: str
    apellidos: str
    ci_tecnico: str
    telefono_contacto: str
    correo: Optional[EmailStr] = None
    foto_perfil_url: Optional[str] = None

class TecnicoCreate(TecnicoBase):
    id_taller: int
    password: str

class TecnicoResponse(TecnicoBase):
    id_tecnico: int
    id_taller: int
    en_turno: bool
    primer_login: bool
    estado_operativo: str
    ubicacion_actual_latitud: Optional[float] = None
    ubicacion_actual_longitud: Optional[float] = None
    especialidades: List[EspecialidadResponse] = []

    model_config = ConfigDict(from_attributes=True)



# schemas/responses intermedios
class VehiculoBase(BaseModel):
    placa: str
    marca: str
    modelo: str
    año: int
    color: str
    tipo_transmision: str
    tipo_combustible: str

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoResponse(VehiculoBase):
    id_vehiculo: int
    id_cliente: int

# --- Vehiculo Schemas ---
class VehiculoBase(BaseModel):
    placa: str
    marca: str
    modelo: str
    año: int
    color: str
    tipo_transmision: str
    tipo_combustible: str

class VehiculoCreate(VehiculoBase):
    id_cliente: int

class VehiculoResponse(VehiculoBase):
    id_vehiculo: int
    id_cliente: int
    model_config = ConfigDict(from_attributes=True)

# --- Cotizacion Schemas ---
class CotizacionBase(BaseModel):
    monto_estimado: float
    tiempo_estimado_minutos: int
    comentario: Optional[str] = None

class CotizacionCreate(CotizacionBase):
    uuid_offline: Optional[str] = None

class CotizacionResponse(CotizacionBase):
    id_cotizacion: int
    id_incidente: int
    id_taller: int
    estado: str
    created_at: datetime
    taller_nombre: Optional[str] = None
    taller_latitud: Optional[float] = None
    taller_longitud: Optional[float] = None
    taller_calificacion: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

# --- Incidente Schemas ---
class IncidenteBase(BaseModel):
    ubicacion_latitud: float
    ubicacion_longitud: float
    tipo_problema: str
    descripcion_manual: Optional[str] = None
    nivel_prioridad: Optional[str] = None

class IncidenteCreate(IncidenteBase):
    id_cliente: int
    id_vehiculo: int
    uuid_offline: Optional[str] = None

class IncidenteResponse(IncidenteBase):
    id_incidente: int
    id_cliente: int
    id_vehiculo: int
    id_tenant: Optional[int] = None
    estado_solicitud: str
    fecha_hora_reporte: datetime
    distancia_km_calculada: Optional[float]
    cotizaciones: List[CotizacionResponse] = []
    model_config = ConfigDict(from_attributes=True)

# --- Pago Schemas ---
class PagoBase(BaseModel):
    monto_subtotal: float
    metodo_pago: str

class PagoResponse(PagoBase):
    id_pago: int
    monto_comision_plataforma: float
    monto_total_cliente: float
    estado_transaccion: str
    fecha_pago: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# --- Auth Schemas ---
class ForgotPasswordRequest(BaseModel):
    correo: EmailStr

class VerifyTokenRequest(BaseModel):
    correo: EmailStr
    token: str

class ResetPasswordRequest(BaseModel):
    correo: EmailStr
    token: str
    nueva_password: str

class UpdateFCMTokenRequest(BaseModel):
    fcm_token: str

# --- Valoracion Schemas ---
class ValoracionCreate(BaseModel):
    puntuacion: int
    comentario: Optional[str] = None

class ValoracionResponse(BaseModel):
    id_valoracion: int
    id_asistencia: int
    puntuacion: int
    comentario: Optional[str] = None
    fecha_valoracion: datetime
    model_config = ConfigDict(from_attributes=True)

# --- DetallePresupuesto Schemas ---
class DetallePresupuestoBase(BaseModel):
    categoria: str
    grupo_falla: str = "General"
    es_critico: bool = False
    tipo_item: str = "Repuesto"  # "Repuesto" o "Mano de Obra"
    item_descripcion: str
    cantidad: int = 1
    precio_unitario: float

class DetallePresupuestoCreate(DetallePresupuestoBase):
    pass

class DetallePresupuestoResponse(DetallePresupuestoBase):
    id_detalle: int
    id_presupuesto: int
    subtotal: float
    estado_item: str
    model_config = ConfigDict(from_attributes=True)

# --- Presupuesto Schemas ---
class PresupuestoBase(BaseModel):
    descripcion_general: Optional[str] = None
    version: str = "Inicial"

class PresupuestoCreate(PresupuestoBase):
    detalles: List[DetallePresupuestoCreate]

class PresupuestoResponse(PresupuestoBase):
    id_presupuesto: int
    id_orden: int
    estado: str
    total_estimado: float
    fecha_creacion: datetime
    detalles: List[DetallePresupuestoResponse]
    model_config = ConfigDict(from_attributes=True)

# --- OrdenTrabajo Schemas ---
class OrdenTrabajoBase(BaseModel):
    id_cliente: int
    id_vehiculo: int
    id_incidente_origen: Optional[int] = None
    estado_recepcion: Optional[str] = None
    fecha_compromiso_entrega: Optional[datetime] = None

class OrdenTrabajoCreate(OrdenTrabajoBase):
    pass

class BitacoraEstadoReparacionResponse(BaseModel):
    id_bitacora: int
    id_orden: int
    estado_anterior: Optional[str]
    nuevo_estado: str
    comentario: Optional[str]
    fecha_cambio: datetime
    model_config = ConfigDict(from_attributes=True)

class OrdenTrabajoResponse(OrdenTrabajoBase):
    id_orden: int
    id_tenant: int
    estado_trabajo: str
    fecha_ingreso: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Presupuesto Aprobacion Schemas (por grupo de falla) ---
class GrupoAprobacion(BaseModel):
    grupo_falla: str
    aprobado: bool

class PresupuestoAprobarRequest(BaseModel):
    grupos: List[GrupoAprobacion]

# --- Pago de Reparación Schemas ---
class PagoReparacionCreate(BaseModel):
    id_orden: int
    metodo_pago: str = "Tarjeta"  # "Tarjeta", "QR", "Transferencia"

class PagoReparacionResponse(BaseModel):
    id_pago: int
    id_orden: int
    monto_subtotal: float
    monto_comision_plataforma: float
    monto_total_cliente: float
    metodo_pago: str
    estado_transaccion: str
    fecha_pago: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
