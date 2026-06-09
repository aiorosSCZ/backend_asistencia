"""
Script de Seed Masivo para la Base de Datos AsisCar
- Actualiza la contrasena del superadmin
- Crea ~22 talleres nuevos (con tenants, admins, tecnicos)
- Crea ~28 clientes con vehiculos
- Crea ~70 incidentes con asistencias, pagos y valoraciones
- Distribuidos en los ultimos 6 meses para KPIs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from crud import get_password_hash
import models
from datetime import datetime, timedelta
import random

db = SessionLocal()

# ============================================================
# 1. ACTUALIZAR CONTRASENA DEL SUPERADMIN
# ============================================================
print("=" * 60)
print("1. Actualizando contrasena del Superadministrador...")
superadmin = db.query(models.Admin).filter(models.Admin.rol == 'SuperAdmin').first()
if superadmin:
    superadmin.password_hash = get_password_hash("123456789")
    db.commit()
    print(f"   Superadmin '{superadmin.nombre}' actualizado. Nueva contrasena: 123456789")
else:
    print("   No se encontro el superadmin.")

# ============================================================
# 2. CREAR TALLERES NUEVOS (con tenants y admins)
# ============================================================
print("\n" + "=" * 60)
print("2. Creando talleres nuevos...")

talleres_data = [
    {"razon": "AutoExpress Bolivia", "rep": "Carlos Mendoza", "nit": "1029384756", "lat": -17.7645, "lng": -63.1823, "dir": "Av. Cristo Redentor #450", "tel": "33445566", "slug": "autoexpress"},
    {"razon": "Taller Veloz SRL", "rep": "Maria Gutierrez", "nit": "2038475610", "lat": -17.7912, "lng": -63.1956, "dir": "Av. Santos Dumont #780", "tel": "33556677", "slug": "veloz"},
    {"razon": "MecaPro Santa Cruz", "rep": "Roberto Flores", "nit": "3047561029", "lat": -17.7734, "lng": -63.2101, "dir": "3er Anillo Interno #120", "tel": "33667788", "slug": "mecapro"},
    {"razon": "Taller El Paisa", "rep": "Andres Vargas", "nit": "4056172038", "lat": -17.8023, "lng": -63.1678, "dir": "Av. Banzer Km 5", "tel": "33778899", "slug": "elpaisa"},
    {"razon": "Full Motor Bolivia", "rep": "Patricia Rojas", "nit": "5065283047", "lat": -17.7556, "lng": -63.1534, "dir": "Av. Roca y Coronado #890", "tel": "33889900", "slug": "fullmotor"},
    {"razon": "TecniCenter SCZ", "rep": "Fernando Salazar", "nit": "6074394056", "lat": -17.7889, "lng": -63.2234, "dir": "4to Anillo #567", "tel": "33990011", "slug": "tecnicenter"},
    {"razon": "Garage Premium", "rep": "Luis Pereira", "nit": "7083405165", "lat": -17.7501, "lng": -63.1789, "dir": "Av. Busch #345", "tel": "34001122", "slug": "garagepremium"},
    {"razon": "AutoFix Express", "rep": "Diana Suarez", "nit": "8092516274", "lat": -17.8134, "lng": -63.1567, "dir": "Av. Pirai #678", "tel": "34112233", "slug": "autofixexpress"},
    {"razon": "Taller Don Pepe", "rep": "Jose Mamani", "nit": "9001627383", "lat": -17.7678, "lng": -63.2345, "dir": "Plan 3000 UV-45", "tel": "34223344", "slug": "donpepe"},
    {"razon": "Mecanica Industrial SCZ", "rep": "Ricardo Montano", "nit": "1110738492", "lat": -17.7423, "lng": -63.1678, "dir": "Parque Industrial #234", "tel": "34334455", "slug": "mecindustrial"},
    {"razon": "Taller Los Andes", "rep": "Miguel Quispe", "nit": "1220849501", "lat": -17.7987, "lng": -63.2012, "dir": "Av. El Trompillo #456", "tel": "34445566", "slug": "losandes"},
    {"razon": "Euro Motors Bolivia", "rep": "Stefan Keller", "nit": "1330950612", "lat": -17.7612, "lng": -63.1456, "dir": "Av. Equipetrol #789", "tel": "34556677", "slug": "euromotors"},
    {"razon": "Rapido Taller 24/7", "rep": "Oscar Torrez", "nit": "1441061723", "lat": -17.7834, "lng": -63.1890, "dir": "2do Anillo #321", "tel": "34667788", "slug": "rapido247"},
    {"razon": "MultiServicios Automotriz", "rep": "Claudia Paz", "nit": "1551172834", "lat": -17.7745, "lng": -63.2178, "dir": "Av. Brasil #654", "tel": "34778899", "slug": "multiservicios"},
    {"razon": "Taller Santa Rosa", "rep": "Ernesto Coca", "nit": "1661283945", "lat": -17.8078, "lng": -63.1734, "dir": "Barrio Santa Rosa #12", "tel": "34889900", "slug": "santarosa"},
    {"razon": "Speed Fix Bolivia", "rep": "Alejandra Morales", "nit": "1771395056", "lat": -17.7534, "lng": -63.1956, "dir": "Av. Monsenor Rivero #890", "tel": "34990011", "slug": "speedfix"},
    {"razon": "Taller La Guardia", "rep": "Jorge Choque", "nit": "1881406167", "lat": -17.8234, "lng": -63.3234, "dir": "La Guardia Centro #456", "tel": "35001122", "slug": "laguardia"},
    {"razon": "ProTech Automotriz", "rep": "Natalia Fernandez", "nit": "1991517278", "lat": -17.7656, "lng": -63.1612, "dir": "Av. Irala #234", "tel": "35112233", "slug": "protech"},
    {"razon": "Taller San Martin", "rep": "Victor Arce", "nit": "2001628389", "lat": -17.7890, "lng": -63.2056, "dir": "Villa 1ro de Mayo #567", "tel": "35223344", "slug": "sanmartin"},
    {"razon": "Turbo Mecanica SRL", "rep": "Sandra Vaca", "nit": "2111739490", "lat": -17.7478, "lng": -63.1823, "dir": "Av. Urubo #123", "tel": "35334455", "slug": "turbomecanica"},
    {"razon": "Master Car Bolivia", "rep": "Gonzalo Roca", "nit": "2221840501", "lat": -17.7956, "lng": -63.1534, "dir": "Av. Alemana #456", "tel": "35445566", "slug": "mastercar"},
    {"razon": "Taller Warnes Express", "rep": "Ramiro Justiniano", "nit": "2331951612", "lat": -17.7312, "lng": -63.1678, "dir": "Warnes Centro #789", "tel": "35556677", "slug": "warnesexpress"},
]

existing_tenant_count = db.query(models.Tenant).count()
existing_taller_count = db.query(models.Taller).count()
talleres_creados = []

for i, td in enumerate(talleres_data):
    # Verificar si ya existe por NIT
    if db.query(models.Taller).filter(models.Taller.nit == td["nit"]).first():
        print(f"   Taller '{td['razon']}' ya existe, omitiendo.")
        continue

    # Crear Tenant
    tenant = models.Tenant(
        nombre=td["razon"],
        subdominio_slug=td["slug"],
        activo=True,
        created_at=datetime.now() - timedelta(days=random.randint(10, 180))
    )
    db.add(tenant)
    db.flush()

    # Crear Admin del Taller
    admin = models.Admin(
        id_tenant=tenant.id_tenant,
        nombre=td["rep"],
        correo=f"admin@{td['slug']}.asiscar.com",
        password_hash=get_password_hash("admin123"),
        rol="Admin"
    )
    db.add(admin)
    db.flush()

    # Estado: la mayoria aprobados, algunos pendientes
    estado = "Aprobado" if random.random() < 0.82 else "Pendiente"
    es_24_7 = random.random() < 0.25

    taller = models.Taller(
        id_tenant=tenant.id_tenant,
        razon_social=td["razon"],
        nombre_representante=td["rep"],
        id_admin_aprobador=superadmin.id_admin if estado == "Aprobado" and superadmin else None,
        nit=td["nit"],
        ubicacion_base_latitud=td["lat"],
        ubicacion_base_longitud=td["lng"],
        direccion_fisica=td["dir"],
        telefono_taller=td["tel"],
        es_24_7=es_24_7,
        horario_apertura=None if es_24_7 else "08:00",
        horario_cierre=None if es_24_7 else "18:00",
        horario_cierre_sabado=None if es_24_7 else "13:00",
        calificacion_promedio=round(random.uniform(3.5, 5.0), 2),
        estado_aprobacion=estado,
        correo=f"taller@{td['slug']}.asiscar.com",
        password_hash=get_password_hash("taller123"),
        created_at=tenant.created_at
    )
    db.add(taller)
    db.flush()
    talleres_creados.append(taller)

    # Asignar servicios aleatorios (entre 4 y 10 servicios)
    all_servicios = db.query(models.Servicio).all()
    servicios_elegidos = random.sample(all_servicios, min(random.randint(4, 10), len(all_servicios)))
    for s in servicios_elegidos:
        ts = models.TallerServicio(
            id_taller=taller.id_taller,
            id_servicio=s.id_servicio,
            precio_especifico_taller=float(s.tarifa_base_estimada) * round(random.uniform(0.8, 1.3), 2),
            tiempo_estimado_minutos=random.randint(20, 120),
            estado_disponible=True
        )
        db.add(ts)

    # Crear 2-3 tecnicos por taller
    nombres_tecnicos = [
        ("Juan", "Perez"), ("Pedro", "Garcia"), ("Miguel", "Lopez"), ("Carlos", "Rodriguez"),
        ("Luis", "Martinez"), ("Jorge", "Hernandez"), ("Andres", "Gonzalez"), ("David", "Sanchez"),
        ("Mario", "Ramirez"), ("Pablo", "Torres"), ("Diego", "Flores"), ("Marco", "Rios"),
        ("Ivan", "Cruz"), ("Sergio", "Moreno"), ("Oscar", "Castillo"), ("Felix", "Nunez"),
        ("Hugo", "Ramos"), ("Raul", "Soto"), ("Daniel", "Ortiz"), ("Enrique", "Silva")
    ]
    num_tecnicos = random.randint(2, 3)
    for j in range(num_tecnicos):
        nombre, apellido = random.choice(nombres_tecnicos)
        ci = f"{random.randint(4000000, 9999999)}"
        tecnico = models.Tecnico(
            id_taller=taller.id_taller,
            id_tenant=tenant.id_tenant,
            nombres=nombre,
            apellidos=apellido,
            ci_tecnico=ci,
            telefono_contacto=f"7{random.randint(0000000, 9999999):07d}",
            correo=f"tecnico.{ci}@{td['slug']}.asiscar.com",
            password_hash=get_password_hash("tecnico123"),
            en_turno=random.random() < 0.6,
            ubicacion_actual_latitud=td["lat"] + random.uniform(-0.01, 0.01),
            ubicacion_actual_longitud=td["lng"] + random.uniform(-0.01, 0.01),
            estado_operativo=random.choice(["Disponible", "Disponible", "Ocupado"]),
            created_at=tenant.created_at + timedelta(days=random.randint(1, 15))
        )
        db.add(tecnico)

db.commit()
print(f"   {len(talleres_creados)} talleres nuevos creados con sus tenants, admins y tecnicos.")

# ============================================================
# 3. CREAR CLIENTES CON VEHICULOS
# ============================================================
print("\n" + "=" * 60)
print("3. Creando clientes y vehiculos...")

clientes_data = [
    {"nom": "Ana", "ape": "Gutierrez", "ci": "7012345", "tel": "76012345"},
    {"nom": "Luis", "ape": "Mamani", "ci": "7023456", "tel": "76023456"},
    {"nom": "Carmen", "ape": "Flores", "ci": "7034567", "tel": "76034567"},
    {"nom": "Roberto", "ape": "Salazar", "ci": "7045678", "tel": "76045678"},
    {"nom": "Patricia", "ape": "Rojas", "ci": "7056789", "tel": "76056789"},
    {"nom": "Fernando", "ape": "Coca", "ci": "7067890", "tel": "76067890"},
    {"nom": "Diana", "ape": "Suarez", "ci": "7078901", "tel": "76078901"},
    {"nom": "Jorge", "ape": "Vargas", "ci": "7089012", "tel": "76089012"},
    {"nom": "Claudia", "ape": "Montano", "ci": "7090123", "tel": "76090123"},
    {"nom": "Ricardo", "ape": "Pereira", "ci": "7001234", "tel": "76001234"},
    {"nom": "Alejandra", "ape": "Torrez", "ci": "7112345", "tel": "76112345"},
    {"nom": "Oscar", "ape": "Quispe", "ci": "7123456", "tel": "76123456"},
    {"nom": "Natalia", "ape": "Arce", "ci": "7134567", "tel": "76134567"},
    {"nom": "Victor", "ape": "Choque", "ci": "7145678", "tel": "76145678"},
    {"nom": "Sandra", "ape": "Vaca", "ci": "7156789", "tel": "76156789"},
    {"nom": "Gonzalo", "ape": "Justiniano", "ci": "7167890", "tel": "76167890"},
    {"nom": "Ramiro", "ape": "Fernandez", "ci": "7178901", "tel": "76178901"},
    {"nom": "Carla", "ape": "Morales", "ci": "7189012", "tel": "76189012"},
    {"nom": "Ernesto", "ape": "Paz", "ci": "7190123", "tel": "76190123"},
    {"nom": "Monica", "ape": "Roca", "ci": "7201234", "tel": "76201234"},
    {"nom": "Sergio", "ape": "Cruz", "ci": "7212345", "tel": "76212345"},
    {"nom": "Paola", "ape": "Soto", "ci": "7223456", "tel": "76223456"},
    {"nom": "Gabriel", "ape": "Ortiz", "ci": "7234567", "tel": "76234567"},
    {"nom": "Marcela", "ape": "Silva", "ci": "7245678", "tel": "76245678"},
    {"nom": "Rodrigo", "ape": "Mendoza", "ci": "7256789", "tel": "76256789"},
    {"nom": "Valeria", "ape": "Herrera", "ci": "7267890", "tel": "76267890"},
    {"nom": "Cristian", "ape": "Rivero", "ci": "7278901", "tel": "76278901"},
    {"nom": "Jimena", "ape": "Sandoval", "ci": "7289012", "tel": "76289012"},
]

marcas_modelos = [
    ("Toyota", "Corolla", 2018), ("Toyota", "Hilux", 2020), ("Hyundai", "Tucson", 2019),
    ("Nissan", "Sentra", 2017), ("Kia", "Sportage", 2021), ("Chevrolet", "Cruze", 2018),
    ("Ford", "Ranger", 2020), ("Suzuki", "Swift", 2019), ("Mitsubishi", "L200", 2020),
    ("Honda", "Civic", 2019), ("Volkswagen", "Gol", 2016), ("Toyota", "RAV4", 2021),
    ("Hyundai", "Accent", 2018), ("Nissan", "Frontier", 2019), ("Kia", "Rio", 2020),
    ("Chevrolet", "Onix", 2021), ("Toyota", "Land Cruiser", 2017), ("Ford", "EcoSport", 2019),
    ("Suzuki", "Vitara", 2020), ("Honda", "CR-V", 2018), ("Volkswagen", "Tiguan", 2021),
    ("Hyundai", "Santa Fe", 2019), ("Nissan", "Kicks", 2021), ("Kia", "Seltos", 2022),
    ("Chevrolet", "Tracker", 2022), ("Toyota", "Yaris", 2020), ("Ford", "Focus", 2017),
    ("Suzuki", "Jimny", 2021),
]
colores = ["Blanco", "Negro", "Gris", "Rojo", "Azul", "Plata", "Verde"]
transmisiones = ["Manual", "Automatica"]
combustibles = ["Gasolina", "Diesel", "GNV"]

clientes_creados = []
vehiculos_creados = []

for i, cd in enumerate(clientes_data):
    if db.query(models.Cliente).filter(models.Cliente.ci_dni == cd["ci"]).first():
        print(f"   Cliente '{cd['nom']} {cd['ape']}' ya existe, omitiendo.")
        continue

    created_date = datetime.now() - timedelta(days=random.randint(5, 180))
    cliente = models.Cliente(
        nombres=cd["nom"],
        apellidos=cd["ape"],
        ci_dni=cd["ci"],
        telefono=cd["tel"],
        correo=f"{cd['nom'].lower()}.{cd['ape'].lower()}{random.randint(1,99)}@gmail.com",
        password_hash=get_password_hash("cliente123"),
        estado_cuenta="Activo",
        calificacion_promedio=round(random.uniform(4.0, 5.0), 2),
        created_at=created_date
    )
    db.add(cliente)
    db.flush()
    clientes_creados.append(cliente)

    # Crear 1 vehiculo por cliente
    marca, modelo, anio = marcas_modelos[i % len(marcas_modelos)]
    placa = f"{random.randint(100, 999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
    vehiculo = models.Vehiculo(
        id_cliente=cliente.id_cliente,
        placa=placa,
        marca=marca,
        modelo=modelo,
        color=random.choice(colores),
        tipo_transmision=random.choice(transmisiones),
        tipo_combustible=random.choice(combustibles),
        **{"a\u00f1o": anio}
    )
    db.add(vehiculo)
    db.flush()
    vehiculos_creados.append(vehiculo)

db.commit()
print(f"   {len(clientes_creados)} clientes y {len(vehiculos_creados)} vehiculos creados.")

# ============================================================
# 4. CREAR INCIDENTES, ASISTENCIAS, PAGOS Y VALORACIONES
# ============================================================
print("\n" + "=" * 60)
print("4. Creando incidentes con asistencias, pagos y valoraciones...")

# Obtener todos los talleres aprobados y sus tecnicos
talleres_aprobados = db.query(models.Taller).filter(models.Taller.estado_aprobacion == "Aprobado").all()
todos_clientes = db.query(models.Cliente).all()
todos_vehiculos = db.query(models.Vehiculo).all()

tipos_problema = [
    "Falla Electrica", "Llanta Pinchada", "Motor Sobrecalentado",
    "Bateria Descargada", "Frenos Defectuosos", "Fuga de Aceite",
    "Problema de Transmision", "Aire Acondicionado", "Falla en Suspension",
    "Problema Electrico", "Cerrajeria", "Falla de Motor",
    "Radiador", "Sistema de Enfriamiento", "Alternador"
]
niveles_prioridad = ["Alta", "Media", "Baja"]
estados_finales = ["Completado", "Completado", "Completado", "Completado", "Cancelado"]  # 80% completado

# Centro de Santa Cruz con variaciones
lat_centro = -17.7833
lng_centro = -63.1821

incidentes_count = 0
asistencias_count = 0
pagos_count = 0

for _ in range(70):
    cliente = random.choice(todos_clientes)
    vehiculo = db.query(models.Vehiculo).filter(models.Vehiculo.id_cliente == cliente.id_cliente).first()
    if not vehiculo:
        continue

    taller = random.choice(talleres_aprobados)
    tecnicos_taller = db.query(models.Tecnico).filter(models.Tecnico.id_taller == taller.id_taller).all()
    if not tecnicos_taller:
        continue

    tecnico = random.choice(tecnicos_taller)

    # Fecha aleatoria en los ultimos 6 meses
    dias_atras = random.randint(0, 180)
    fecha_reporte = datetime.now() - timedelta(days=dias_atras, hours=random.randint(0, 23), minutes=random.randint(0, 59))

    estado = random.choice(estados_finales)
    tipo = random.choice(tipos_problema)
    prioridad = random.choice(niveles_prioridad)

    # Ubicacion aleatoria en Santa Cruz
    lat = lat_centro + random.uniform(-0.06, 0.06)
    lng = lng_centro + random.uniform(-0.06, 0.06)

    incidente = models.Incidente(
        id_cliente=cliente.id_cliente,
        id_vehiculo=vehiculo.id_vehiculo,
        id_tenant=taller.id_tenant,
        fecha_hora_reporte=fecha_reporte,
        ubicacion_latitud=lat,
        ubicacion_longitud=lng,
        tipo_problema=tipo,
        descripcion_manual=f"El vehiculo presento {tipo.lower()} mientras circulaba.",
        nivel_prioridad=prioridad,
        estado_solicitud=estado,
        distancia_km_calculada=round(random.uniform(0.5, 15.0), 2),
        motivo_cancelacion="Cliente cancelo la solicitud" if estado == "Cancelado" else None
    )
    db.add(incidente)
    db.flush()
    incidentes_count += 1

    if estado == "Completado":
        # Tiempos de asistencia
        minutos_asignacion = random.randint(2, 15)
        minutos_llegada = random.randint(10, 45)
        minutos_resolucion = random.randint(30, 180)

        fecha_asignacion = fecha_reporte + timedelta(minutes=minutos_asignacion)
        fecha_llegada = fecha_asignacion + timedelta(minutes=minutos_llegada)
        fecha_finalizacion = fecha_llegada + timedelta(minutes=minutos_resolucion)

        asistencia = models.Asistencia(
            id_incidente=incidente.id_incidente,
            id_taller=taller.id_taller,
            id_tecnico=tecnico.id_tecnico,
            id_tenant=taller.id_tenant,
            fecha_hora_asignacion=fecha_asignacion,
            fecha_hora_llegada_tecnico=fecha_llegada,
            fecha_hora_finalizacion=fecha_finalizacion,
            observaciones_tecnico=f"Se realizo {tipo.lower()} exitosamente.",
            monto_adicional=round(random.uniform(0, 50), 2) if random.random() < 0.3 else 0
        )
        db.add(asistencia)
        db.flush()
        asistencias_count += 1

        # Pago
        subtotal = round(random.uniform(50, 500), 2)
        comision = round(subtotal * 0.10, 2)
        total = round(subtotal + comision, 2)

        pago = models.Pago(
            id_asistencia=asistencia.id_asistencia,
            id_tenant=taller.id_tenant,
            monto_subtotal=subtotal,
            monto_comision_plataforma=comision,
            monto_total_cliente=total,
            metodo_pago=random.choice(["Efectivo", "QR", "Tarjeta", "Stripe"]),
            estado_transaccion="Completado",
            fecha_pago=fecha_finalizacion + timedelta(minutes=random.randint(5, 30))
        )
        db.add(pago)
        pagos_count += 1

        # Valoracion (80% de las completadas)
        if random.random() < 0.8:
            valoracion = models.Valoracion(
                id_asistencia=asistencia.id_asistencia,
                id_tenant=taller.id_tenant,
                puntuacion=random.choices([5, 4, 3, 2, 1], weights=[45, 30, 15, 7, 3])[0],
                comentario=random.choice([
                    "Excelente servicio, muy rapido.",
                    "Buen trabajo del tecnico.",
                    "Llego a tiempo y resolvio el problema.",
                    "Regular, tardo un poco mas de lo esperado.",
                    "Muy profesional y amable.",
                    "Satisfecho con el servicio.",
                    "Podria mejorar el tiempo de llegada.",
                    "Todo perfecto, lo recomiendo.",
                    None
                ]),
                fecha_valoracion=fecha_finalizacion + timedelta(hours=random.randint(1, 48))
            )
            db.add(valoracion)

db.commit()
print(f"   {incidentes_count} incidentes creados.")
print(f"   {asistencias_count} asistencias con pagos creadas.")
print(f"   {pagos_count} pagos registrados.")

# ============================================================
# 5. RESUMEN FINAL
# ============================================================
print("\n" + "=" * 60)
print("RESUMEN FINAL DE LA BASE DE DATOS:")
print(f"  Tenants:       {db.query(models.Tenant).count()}")
print(f"  Admins:        {db.query(models.Admin).count()}")
print(f"  Talleres:      {db.query(models.Taller).count()}")
print(f"  Tecnicos:      {db.query(models.Tecnico).count()}")
print(f"  Clientes:      {db.query(models.Cliente).count()}")
print(f"  Vehiculos:     {db.query(models.Vehiculo).count()}")
print(f"  Incidentes:    {db.query(models.Incidente).count()}")
print(f"  Asistencias:   {db.query(models.Asistencia).count()}")
print(f"  Pagos:         {db.query(models.Pago).count()}")
print(f"  Valoraciones:  {db.query(models.Valoracion).count()}")
print("=" * 60)

db.close()
print("\nSeed completado exitosamente.")
