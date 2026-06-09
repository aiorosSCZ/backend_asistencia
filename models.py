from sqlalchemy import Column, Integer, String, Float, Time, Boolean, DECIMAL, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id_tenant = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    subdominio_slug = Column(String(50), unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    admins = relationship("Admin", back_populates="tenant")
    talleres = relationship("Taller", back_populates="tenant")
    incidentes = relationship("Incidente", back_populates="tenant")
    ordenes_trabajo = relationship("OrdenTrabajo", back_populates="tenant")
    tecnicos = relationship("Tecnico", back_populates="tenant")
    cotizaciones = relationship("Cotizacion", back_populates="tenant")
    asistencias = relationship("Asistencia", back_populates="tenant")
    pagos = relationship("Pago", back_populates="tenant")
    valoraciones = relationship("Valoracion", back_populates="tenant")
    presupuestos = relationship("Presupuesto", back_populates="tenant")
    detalles_presupuesto = relationship("DetallePresupuesto", back_populates="tenant")
    pagos_reparacion = relationship("PagoReparacion", back_populates="tenant")


class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    ci_dni = Column(String(20), unique=True, nullable=False) # Obligatorio por seguridad
    telefono = Column(String(20), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    foto_perfil_url = Column(String(255), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    estado_cuenta = Column(String(20), default='Activo')
    calificacion_promedio = Column(DECIMAL(3, 2), default=5.00)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    vehiculos = relationship("Vehiculo", back_populates="cliente", cascade="all, delete-orphan")
    incidentes = relationship("Incidente", back_populates="cliente")
    ordenes_trabajo = relationship("OrdenTrabajo", back_populates="cliente")


class Admin(Base):
    __tablename__ = "admins"

    id_admin = Column(Integer, primary_key=True, index=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='SET NULL'), nullable=True) # NULL para Superadmin
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default='Admin')
    created_at = Column(TIMESTAMP, server_default=func.now())

    tenant = relationship("Tenant", back_populates="admins")


class Taller(Base):
    __tablename__ = "talleres"

    id_taller = Column(Integer, primary_key=True, index=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    razon_social = Column(String(150), nullable=False)
    nombre_representante = Column(String(150), nullable=False)
    id_admin_aprobador = Column(Integer, ForeignKey('admins.id_admin'), nullable=True)
    nit = Column(String(30), unique=True, nullable=False)
    ubicacion_base_latitud = Column(Float, nullable=False)
    ubicacion_base_longitud = Column(Float, nullable=False)
    direccion_fisica = Column(Text, nullable=True)
    telefono_taller = Column(String(20), nullable=True)
    logo_url = Column(String(255), nullable=True)
    es_24_7 = Column(Boolean, default=False) # Para asignación automática del sistema
    horario_apertura = Column(Time, nullable=True)
    horario_cierre = Column(Time, nullable=True)
    horario_cierre_sabado = Column(Time, nullable=True)
    foto_nit_url = Column(String(255), nullable=True)
    foto_local_url = Column(String(255), nullable=True)
    cuenta_bancaria = Column(String(50), nullable=True)
    calificacion_promedio = Column(DECIMAL(3, 2), default=5.00)
    estado_aprobacion = Column(String(20), default='Pendiente')
    correo = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="talleres")
    tecnicos = relationship("Tecnico", back_populates="taller", cascade="all, delete-orphan")
    taller_servicios = relationship("TallerServicio", back_populates="taller", cascade="all, delete-orphan")
    asistencias = relationship("Asistencia", back_populates="taller")


class Especialidad(Base):
    __tablename__ = "especialidades"

    id_especialidad = Column(Integer, primary_key=True, index=True)
    nombre_especialidad = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)


class TecnicoEspecialidad(Base):
    __tablename__ = "tecnico_especialidades"

    id_tecnico = Column(Integer, ForeignKey('tecnicos.id_tecnico', ondelete='CASCADE'), primary_key=True)
    id_especialidad = Column(Integer, ForeignKey('especialidades.id_especialidad', ondelete='CASCADE'), primary_key=True)


class Tecnico(Base):
    __tablename__ = "tecnicos"

    id_tecnico = Column(Integer, primary_key=True, index=True)
    id_taller = Column(Integer, ForeignKey('talleres.id_taller', ondelete='CASCADE'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    ci_tecnico = Column(String(20), unique=True, nullable=False) # Obligatorio
    telefono_contacto = Column(String(20), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    primer_login = Column(Boolean, default=True)
    foto_perfil_url = Column(String(255), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    en_turno = Column(Boolean, default=False)
    ubicacion_actual_latitud = Column(Float, nullable=True)
    ubicacion_actual_longitud = Column(Float, nullable=True)
    estado_operativo = Column(String(20), default='Disponible')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    taller = relationship("Taller", back_populates="tecnicos")
    tenant = relationship("Tenant", back_populates="tecnicos")
    asistencias = relationship("Asistencia", back_populates="tecnico")
    especialidades = relationship("Especialidad", secondary="tecnico_especialidades")


class Servicio(Base):
    __tablename__ = "servicios"

    id_servicio = Column(Integer, primary_key=True, index=True)
    nombre_servicio = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    tarifa_base_estimada = Column(DECIMAL(10, 2), nullable=False)

    taller_servicios = relationship("TallerServicio", back_populates="servicio")


class TallerServicio(Base):
    __tablename__ = "taller_servicios"

    id_taller_servicio = Column(Integer, primary_key=True, index=True)
    id_taller = Column(Integer, ForeignKey('talleres.id_taller', ondelete='CASCADE'), nullable=False)
    id_servicio = Column(Integer, ForeignKey('servicios.id_servicio', ondelete='CASCADE'), nullable=False)
    precio_especifico_taller = Column(DECIMAL(10, 2), nullable=False)
    tiempo_estimado_minutos = Column(Integer, nullable=True)
    estado_disponible = Column(Boolean, default=True)

    taller = relationship("Taller", back_populates="taller_servicios")
    servicio = relationship("Servicio", back_populates="taller_servicios")


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente', ondelete='CASCADE'), nullable=False)
    placa = Column(String(15), unique=True, nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    año = Column(Integer, nullable=False)
    color = Column(String(30), nullable=False)
    tipo_transmision = Column(String(20), nullable=False)
    tipo_combustible = Column(String(20), nullable=False)

    cliente = relationship("Cliente", back_populates="vehiculos")
    incidentes = relationship("Incidente", back_populates="vehiculo")
    ordenes_trabajo = relationship("OrdenTrabajo", back_populates="vehiculo")


class Incidente(Base):
    __tablename__ = "incidentes"

    id_incidente = Column(Integer, primary_key=True, index=True)
    uuid_offline = Column(String(36), unique=True, nullable=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id_vehiculo'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='SET NULL'), nullable=True)
    fecha_hora_reporte = Column(TIMESTAMP, server_default=func.now())
    ubicacion_latitud = Column(Float, nullable=False)
    ubicacion_longitud = Column(Float, nullable=False)
    tipo_problema = Column(String(50), nullable=False)
    descripcion_manual = Column(Text, nullable=True)
    nivel_prioridad = Column(String(15), nullable=True)
    estado_solicitud = Column(String(50), default='Pendiente')
    distancia_km_calculada = Column(DECIMAL(5, 2), nullable=True)
    motivo_cancelacion = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="incidentes")
    vehiculo = relationship("Vehiculo", back_populates="incidentes")
    tenant = relationship("Tenant", back_populates="incidentes")
    evidencias = relationship("Evidencia", back_populates="incidente", cascade="all, delete-orphan")
    analisis_ia = relationship("AnalisisIA", back_populates="incidente", uselist=False, cascade="all, delete-orphan")
    asistencia = relationship("Asistencia", back_populates="incidente", uselist=False)
    orden_trabajo = relationship("OrdenTrabajo", back_populates="incidente_origen", uselist=False)
    cotizaciones = relationship("Cotizacion", back_populates="incidente", cascade="all, delete-orphan")


class Evidencia(Base):
    __tablename__ = "evidencias"

    id_evidencia = Column(Integer, primary_key=True, index=True)
    id_incidente = Column(Integer, ForeignKey('incidentes.id_incidente', ondelete='CASCADE'), nullable=False)
    tipo_recurso = Column(String(20), nullable=False)
    url_archivo = Column(String(255), nullable=False)
    fecha_subida = Column(TIMESTAMP, server_default=func.now())

    incidente = relationship("Incidente", back_populates="evidencias")


class AnalisisIA(Base):
    __tablename__ = "analisis_ia"

    id_analisis = Column(Integer, primary_key=True, index=True)
    id_incidente = Column(Integer, ForeignKey('incidentes.id_incidente', ondelete='CASCADE'), nullable=False, unique=True)
    transcripcion_audio = Column(Text, nullable=True)
    clasificacion_sugerida = Column(String(50), nullable=True)
    resumen_estructurado = Column(Text, nullable=True)
    diagnostico_cliente = Column(Text, nullable=True)
    nivel_confianza_porcentaje = Column(Integer, nullable=True)
    requiere_revision_manual = Column(Boolean, default=False)

    incidente = relationship("Incidente", back_populates="analisis_ia")


class Asistencia(Base):
    __tablename__ = "asistencias"

    id_asistencia = Column(Integer, primary_key=True, index=True)
    id_incidente = Column(Integer, ForeignKey('incidentes.id_incidente'), nullable=False, unique=True)
    id_taller = Column(Integer, ForeignKey('talleres.id_taller'), nullable=False)
    id_tecnico = Column(Integer, ForeignKey('tecnicos.id_tecnico'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    fecha_hora_asignacion = Column(TIMESTAMP, server_default=func.now())
    fecha_hora_llegada_tecnico = Column(TIMESTAMP, nullable=True)
    fecha_hora_finalizacion = Column(TIMESTAMP, nullable=True)
    observaciones_tecnico = Column(Text, nullable=True)
    monto_adicional = Column(DECIMAL(10, 2), default=0.00)
    motivo_adicional = Column(Text, nullable=True)

    incidente = relationship("Incidente", back_populates="asistencia")
    taller = relationship("Taller", back_populates="asistencias")
    tecnico = relationship("Tecnico", back_populates="asistencias")
    tenant = relationship("Tenant", back_populates="asistencias")
    pago = relationship("Pago", back_populates="asistencia", uselist=False)
    valoracion = relationship("Valoracion", back_populates="asistencia", uselist=False)


class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_asistencia = Column(Integer, ForeignKey('asistencias.id_asistencia'), nullable=False, unique=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    monto_subtotal = Column(DECIMAL(10, 2), nullable=False)
    monto_comision_plataforma = Column(DECIMAL(10, 2), nullable=False)
    monto_total_cliente = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    estado_transaccion = Column(String(20), default='Pendiente')
    fecha_pago = Column(TIMESTAMP, nullable=True)

    asistencia = relationship("Asistencia", back_populates="pago")
    tenant = relationship("Tenant", back_populates="pagos")


class Valoracion(Base):
    __tablename__ = "valoraciones"

    id_valoracion = Column(Integer, primary_key=True, index=True)
    id_asistencia = Column(Integer, ForeignKey('asistencias.id_asistencia'), nullable=False, unique=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)
    fecha_valoracion = Column(TIMESTAMP, server_default=func.now())

    asistencia = relationship("Asistencia", back_populates="valoracion")
    tenant = relationship("Tenant", back_populates="valoraciones")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_usuario_destino = Column(Integer, nullable=False)
    tipo_usuario_destino = Column(String(20), nullable=False)
    titulo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)
    fecha_envio = Column(TIMESTAMP, server_default=func.now())


class Bitacora(Base):
    __tablename__ = "bitacora"

    id_log = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=True)
    tipo_usuario = Column(String(20), nullable=True)
    accion = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    fecha_hora = Column(TIMESTAMP, server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id_token = Column(Integer, primary_key=True, index=True)
    correo = Column(String(100), nullable=False)
    token = Column(String(6), nullable=False)
    expiracion = Column(TIMESTAMP, nullable=False)
    utilizado = Column(Boolean, default=False)


class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"

    id_orden = Column(Integer, primary_key=True, index=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente', ondelete='CASCADE'), nullable=False)
    id_vehiculo = Column(Integer, ForeignKey('vehiculos.id_vehiculo', ondelete='CASCADE'), nullable=False)
    id_incidente_origen = Column(Integer, ForeignKey('incidentes.id_incidente', ondelete='SET NULL'), nullable=True)
    estado_recepcion = Column(Text, nullable=True)
    estado_trabajo = Column(String(30), default='Diagnóstico')
    fecha_ingreso = Column(TIMESTAMP, server_default=func.now())
    fecha_compromiso_entrega = Column(TIMESTAMP, nullable=True)

    tenant = relationship("Tenant", back_populates="ordenes_trabajo")
    cliente = relationship("Cliente", back_populates="ordenes_trabajo")
    vehiculo = relationship("Vehiculo", back_populates="ordenes_trabajo")
    incidente_origen = relationship("Incidente", back_populates="orden_trabajo")
    presupuestos = relationship("Presupuesto", back_populates="orden", cascade="all, delete-orphan")
    bitacoras = relationship("BitacoraEstadoReparacion", back_populates="orden", cascade="all, delete-orphan")
    pago_reparacion = relationship("PagoReparacion", uselist=False, back_populates="orden", cascade="all, delete-orphan")


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id_presupuesto = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey('ordenes_trabajo.id_orden', ondelete='CASCADE'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    descripcion_general = Column(Text, nullable=True)
    version = Column(String(50), default='Inicial')
    estado = Column(String(30), default='Pendiente')
    total_estimado = Column(DECIMAL(10, 2), default=0.00)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())

    orden = relationship("OrdenTrabajo", back_populates="presupuestos")
    tenant = relationship("Tenant", back_populates="presupuestos")
    detalles = relationship("DetallePresupuesto", back_populates="presupuesto", cascade="all, delete-orphan")


class DetallePresupuesto(Base):
    __tablename__ = "detalles_presupuesto"

    id_detalle = Column(Integer, primary_key=True, index=True)
    id_presupuesto = Column(Integer, ForeignKey('presupuestos.id_presupuesto', ondelete='CASCADE'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    categoria = Column(String(50), nullable=False) # Motor, Chaperia, Pintura, Electrico, etc.
    grupo_falla = Column(String(100), nullable=False, default='General') # Ej: "Sistema Eléctrico", "Frenos"
    es_critico = Column(Boolean, default=False) # True = Obligatorio, False = Opcional/Recomendado
    tipo_item = Column(String(30), default='Repuesto') # "Repuesto" o "Mano de Obra"
    item_descripcion = Column(Text, nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    estado_item = Column(String(20), default='Pendiente') # Pendiente, Aprobado, Rechazado

    presupuesto = relationship("Presupuesto", back_populates="detalles")
    tenant = relationship("Tenant", back_populates="detalles_presupuesto")


class BitacoraEstadoReparacion(Base):
    __tablename__ = "bitacora_estados_reparacion"

    id_bitacora = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey('ordenes_trabajo.id_orden', ondelete='CASCADE'), nullable=False)
    estado_anterior = Column(String(30), nullable=True)
    nuevo_estado = Column(String(30), nullable=False)
    comentario = Column(Text, nullable=True)
    fecha_cambio = Column(TIMESTAMP, server_default=func.now())

    orden = relationship("OrdenTrabajo", back_populates="bitacoras")


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id_cotizacion = Column(Integer, primary_key=True, index=True)
    uuid_offline = Column(String(36), unique=True, nullable=True, index=True)
    id_incidente = Column(Integer, ForeignKey('incidentes.id_incidente', ondelete='CASCADE'), nullable=False)
    id_taller = Column(Integer, ForeignKey('talleres.id_taller', ondelete='CASCADE'), nullable=False)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    monto_estimado = Column(DECIMAL(10, 2), nullable=False)
    tiempo_estimado_minutos = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)
    estado = Column(String(20), default='Pendiente') # Pendiente, Aceptada, Rechazada
    created_at = Column(TIMESTAMP, server_default=func.now())

    incidente = relationship("Incidente", back_populates="cotizaciones")
    taller = relationship("Taller")
    tenant = relationship("Tenant", back_populates="cotizaciones")


class PagoReparacion(Base):
    __tablename__ = "pagos_reparacion"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey('ordenes_trabajo.id_orden', ondelete='CASCADE'), nullable=False, unique=True)
    id_tenant = Column(Integer, ForeignKey('tenants.id_tenant', ondelete='CASCADE'), nullable=False)
    monto_subtotal = Column(DECIMAL(10, 2), nullable=False)
    monto_comision_plataforma = Column(DECIMAL(10, 2), nullable=False)  # 5% comisión
    monto_total_cliente = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    estado_transaccion = Column(String(20), default='Completado')
    fecha_pago = Column(TIMESTAMP, server_default=func.now())

    orden = relationship("OrdenTrabajo", back_populates="pago_reparacion")
    tenant = relationship("Tenant", back_populates="pagos_reparacion")


