"""
Seed Adicional: +120 clientes con vehiculos y +250 incidentes
Para proporciones realistas en los KPIs del Superadmin.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from crud import get_password_hash
import models
from datetime import datetime, timedelta
import random

db = SessionLocal()

# Pre-generar UN SOLO hash para todos los clientes (mismo password = "cliente123")
# Esto ahorra ~2 minutos de bcrypt
print("Generando hash de contrasena (1 sola vez)...")
HASH_CLIENTE = get_password_hash("cliente123")
print("Hash listo.")

# ============================================================
# 1. CREAR 120 CLIENTES ADICIONALES
# ============================================================
print("\n" + "=" * 60)
print("1. Creando 120 clientes adicionales con vehiculos...")

nombres_m = ["Alejandro", "Benjamin", "Cristian", "Daniel", "Eduardo", "Fabian", "Gustavo",
             "Hector", "Ignacio", "Javier", "Kevin", "Leonardo", "Martin", "Nicolas", "Omar",
             "Pablo", "Rafael", "Santiago", "Tomas", "Ulises", "Vicente", "Walter", "Xavier"]
nombres_f = ["Adriana", "Beatriz", "Camila", "Daniela", "Elena", "Fernanda", "Gabriela",
             "Helena", "Isabella", "Juliana", "Karla", "Lorena", "Mariana", "Noelia", "Olivia",
             "Pamela", "Raquel", "Sofia", "Tatiana", "Ursula", "Valentina", "Wendy", "Ximena"]
apellidos = ["Arana", "Balcazar", "Camacho", "Delgado", "Espinoza", "Franco", "Gallardo",
             "Hurtado", "Ibarra", "Jimenez", "Kuno", "Lara", "Maldonado", "Navarro", "Olmos",
             "Paniagua", "Quiroga", "Romero", "Soliz", "Tapia", "Urzagaste", "Velasco",
             "Yucra", "Zambrana", "Apaza", "Bustamante", "Cuellar", "Duran", "Escalante",
             "Fuentes", "Guarachi", "Hinojosa", "Illanes", "Jaldin", "Lazarte", "Mercado",
             "Nogales", "Orellana", "Paredes", "Quiroz", "Rocha", "Saavedra", "Terrazas",
             "Ugarte", "Villarroel", "Zarate", "Aguirre", "Barriga", "Cardozo", "Daza"]

marcas_modelos = [
    ("Toyota", "Corolla", 2018), ("Toyota", "Hilux", 2020), ("Toyota", "RAV4", 2021),
    ("Toyota", "Yaris", 2019), ("Toyota", "Land Cruiser", 2017), ("Toyota", "Fortuner", 2022),
    ("Hyundai", "Tucson", 2019), ("Hyundai", "Accent", 2020), ("Hyundai", "Santa Fe", 2018),
    ("Hyundai", "Creta", 2022), ("Nissan", "Sentra", 2017), ("Nissan", "Frontier", 2019),
    ("Nissan", "Kicks", 2021), ("Nissan", "Versa", 2020), ("Kia", "Sportage", 2021),
    ("Kia", "Rio", 2020), ("Kia", "Seltos", 2022), ("Kia", "Picanto", 2019),
    ("Chevrolet", "Cruze", 2018), ("Chevrolet", "Onix", 2021), ("Chevrolet", "Tracker", 2022),
    ("Chevrolet", "Sail", 2017), ("Ford", "Ranger", 2020), ("Ford", "EcoSport", 2019),
    ("Ford", "Territory", 2022), ("Suzuki", "Swift", 2019), ("Suzuki", "Vitara", 2020),
    ("Suzuki", "Jimny", 2021), ("Suzuki", "Ertiga", 2020), ("Mitsubishi", "L200", 2020),
    ("Mitsubishi", "Outlander", 2019), ("Honda", "Civic", 2019), ("Honda", "CR-V", 2018),
    ("Honda", "HR-V", 2021), ("Volkswagen", "Gol", 2016), ("Volkswagen", "Tiguan", 2021),
    ("Volkswagen", "T-Cross", 2022), ("Renault", "Duster", 2020), ("Renault", "Kwid", 2021),
    ("Changan", "CS35", 2022), ("BYD", "Song Plus", 2023), ("MG", "ZS", 2022),
]
colores = ["Blanco", "Negro", "Gris Oscuro", "Gris Plata", "Rojo", "Azul", "Azul Marino",
           "Verde Oscuro", "Beige", "Dorado", "Bordo", "Celeste"]
transmisiones = ["Manual", "Automatica"]
combustibles = ["Gasolina", "Diesel", "GNV", "Gasolina"]  # mas gasolina

clientes_creados = []
vehiculos_creados = []
ci_base = 8000000

for i in range(120):
    if random.random() < 0.5:
        nombre = random.choice(nombres_m)
    else:
        nombre = random.choice(nombres_f)
    apellido1 = random.choice(apellidos)
    apellido2 = random.choice(apellidos)
    ci = str(ci_base + i)

    # Verificar duplicado
    if db.query(models.Cliente).filter(models.Cliente.ci_dni == ci).first():
        continue

    created_date = datetime.now() - timedelta(days=random.randint(1, 210))
    cliente = models.Cliente(
        nombres=nombre,
        apellidos=f"{apellido1} {apellido2}",
        ci_dni=ci,
        telefono=f"7{random.randint(0, 9)}{random.randint(100000, 999999)}",
        correo=f"{nombre.lower()}.{apellido1.lower()}.{ci}@gmail.com",
        password_hash=HASH_CLIENTE,
        estado_cuenta="Activo",
        calificacion_promedio=round(random.uniform(3.8, 5.0), 2),
        created_at=created_date
    )
    db.add(cliente)
    db.flush()
    clientes_creados.append(cliente)

    # Vehiculo
    marca, modelo, anio = random.choice(marcas_modelos)
    placa = f"{random.randint(100, 999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
    # Evitar placas duplicadas
    while db.query(models.Vehiculo).filter(models.Vehiculo.placa == placa).first():
        placa = f"{random.randint(100, 999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"

    vehiculo = models.Vehiculo(
        id_cliente=cliente.id_cliente,
        placa=placa,
        marca=marca,
        modelo=modelo,
        color=random.choice(colores),
        tipo_transmision=random.choice(transmisiones),
        tipo_combustible=random.choice(combustibles),
    )
    vehiculo.año = anio
    db.add(vehiculo)
    db.flush()
    vehiculos_creados.append(vehiculo)

db.commit()
print(f"   {len(clientes_creados)} clientes y {len(vehiculos_creados)} vehiculos creados.")

# ============================================================
# 2. CREAR ~250 INCIDENTES ADICIONALES
# ============================================================
print("\n" + "=" * 60)
print("2. Creando ~250 incidentes adicionales...")

talleres_aprobados = db.query(models.Taller).filter(models.Taller.estado_aprobacion == "Aprobado").all()
todos_clientes = db.query(models.Cliente).all()

tipos_problema = [
    "Falla Electrica", "Llanta Pinchada", "Motor Sobrecalentado",
    "Bateria Descargada", "Frenos Defectuosos", "Fuga de Aceite",
    "Problema de Transmision", "Aire Acondicionado", "Falla en Suspension",
    "Problema Electrico", "Cerrajeria", "Falla de Motor",
    "Radiador", "Sistema de Enfriamiento", "Alternador",
    "Falla en Arranque", "Luces Fundidas", "Clutch Patina",
    "Fuga de Refrigerante", "Sensor de Oxigeno"
]
niveles_prioridad = ["Alta", "Media", "Media", "Baja"]  # mas medianas
estados_finales = ["Completado"] * 7 + ["Cancelado"] * 2 + ["Pendiente"]  # 70% completado, 20% cancelado, 10% pendiente

lat_centro = -17.7833
lng_centro = -63.1821

inc_count = 0
asi_count = 0
pag_count = 0

for _ in range(250):
    cliente = random.choice(todos_clientes)
    vehiculo = db.query(models.Vehiculo).filter(models.Vehiculo.id_cliente == cliente.id_cliente).first()
    if not vehiculo:
        continue

    taller = random.choice(talleres_aprobados)
    tecnicos_taller = db.query(models.Tecnico).filter(models.Tecnico.id_taller == taller.id_taller).all()
    if not tecnicos_taller:
        continue
    tecnico = random.choice(tecnicos_taller)

    # Distribuir: mas incidentes en meses recientes
    dias_atras = int(random.triangular(0, 210, 30))  # sesgo hacia fechas recientes
    fecha_reporte = datetime.now() - timedelta(days=dias_atras, hours=random.randint(6, 22), minutes=random.randint(0, 59))

    estado = random.choice(estados_finales)
    tipo = random.choice(tipos_problema)
    prioridad = random.choice(niveles_prioridad)

    lat = lat_centro + random.uniform(-0.07, 0.07)
    lng = lng_centro + random.uniform(-0.07, 0.07)

    incidente = models.Incidente(
        id_cliente=cliente.id_cliente,
        id_vehiculo=vehiculo.id_vehiculo,
        id_tenant=taller.id_tenant,
        fecha_hora_reporte=fecha_reporte,
        ubicacion_latitud=lat,
        ubicacion_longitud=lng,
        tipo_problema=tipo,
        descripcion_manual=f"Vehiculo {vehiculo.marca} {vehiculo.modelo} presento {tipo.lower()}.",
        nivel_prioridad=prioridad,
        estado_solicitud=estado,
        distancia_km_calculada=round(random.uniform(0.3, 18.0), 2),
        motivo_cancelacion="Cliente cancelo la solicitud" if estado == "Cancelado" else None
    )
    db.add(incidente)
    db.flush()
    inc_count += 1

    if estado == "Completado":
        min_asig = random.randint(1, 12)
        min_llegada = random.randint(8, 40)
        min_resolucion = random.randint(20, 150)

        f_asig = fecha_reporte + timedelta(minutes=min_asig)
        f_lleg = f_asig + timedelta(minutes=min_llegada)
        f_fin = f_lleg + timedelta(minutes=min_resolucion)

        asistencia = models.Asistencia(
            id_incidente=incidente.id_incidente,
            id_taller=taller.id_taller,
            id_tecnico=tecnico.id_tecnico,
            id_tenant=taller.id_tenant,
            fecha_hora_asignacion=f_asig,
            fecha_hora_llegada_tecnico=f_lleg,
            fecha_hora_finalizacion=f_fin,
            observaciones_tecnico=f"Servicio de {tipo.lower()} completado satisfactoriamente.",
            monto_adicional=round(random.uniform(0, 80), 2) if random.random() < 0.25 else 0
        )
        db.add(asistencia)
        db.flush()
        asi_count += 1

        subtotal = round(random.uniform(30, 600), 2)
        comision = round(subtotal * 0.10, 2)
        total = round(subtotal + comision, 2)

        pago = models.Pago(
            id_asistencia=asistencia.id_asistencia,
            id_tenant=taller.id_tenant,
            monto_subtotal=subtotal,
            monto_comision_plataforma=comision,
            monto_total_cliente=total,
            metodo_pago=random.choice(["Efectivo", "Efectivo", "QR", "QR", "Tarjeta", "Stripe"]),
            estado_transaccion="Completado",
            fecha_pago=f_fin + timedelta(minutes=random.randint(2, 20))
        )
        db.add(pago)
        pag_count += 1

        # Valoracion (75%)
        if random.random() < 0.75:
            comentarios = [
                "Excelente servicio, muy rapido y profesional.",
                "Buen trabajo, llego a tiempo.",
                "El tecnico fue muy amable y resolvio todo.",
                "Regular, espere un poco mas de lo previsto.",
                "Muy satisfecho, lo recomiendo.",
                "Servicio aceptable.",
                "Rapido y eficiente, gracias.",
                "Podria mejorar la comunicacion.",
                "Todo perfecto, 10/10.",
                "Buen servicio pero caro.",
                "El tecnico sabia lo que hacia.",
                "Me salvo de una situacion complicada.",
                None, None  # algunos sin comentario
            ]
            valoracion = models.Valoracion(
                id_asistencia=asistencia.id_asistencia,
                id_tenant=taller.id_tenant,
                puntuacion=random.choices([5, 4, 3, 2, 1], weights=[40, 30, 18, 8, 4])[0],
                comentario=random.choice(comentarios),
                fecha_valoracion=f_fin + timedelta(hours=random.randint(1, 72))
            )
            db.add(valoracion)

    # Commit cada 50 incidentes para no sobrecargar
    if inc_count % 50 == 0:
        db.commit()
        print(f"   ... {inc_count} incidentes procesados")

db.commit()
print(f"   {inc_count} incidentes creados.")
print(f"   {asi_count} asistencias con pagos creadas.")
print(f"   {pag_count} pagos registrados.")

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "=" * 60)
print("RESUMEN FINAL DE LA BASE DE DATOS:")
print(f"  Tenants:       {db.query(models.Tenant).count()}")
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
print("\nSeed adicional completado.")
