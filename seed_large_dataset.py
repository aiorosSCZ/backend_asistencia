import sys
import os
import random
from datetime import datetime, timedelta, time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
from crud import get_password_hash
import routers.talleres as talleres_router

# Listas de nombres y apellidos para generación masiva
NOMBRES_VARONES = ["Juan", "Pedro", "Luis", "José", "Carlos", "Miguel", "Fernando", "David", "Jorge", "Diego", "Andrés", "Javier", "Alejandro", "Manuel", "Roberto", "Francisco", "Raúl", "Santiago", "Daniel", "Ángel", "Ignacio", "Hugo", "Oscar", "Mauricio", "Roberto", "Felipe", "Ricardo", "Eduardo", "Jaime", "Cesar", "Fabio", "Marcelo", "Javier", "Diego", "Wilson", "Alex", "Alvaro", "Sebastian", "Adrian", "Gabriel"]
NOMBRES_MUJERES = ["María", "Ana", "Lucía", "Sofía", "Elena", "Patricia", "Laura", "Paula", "Rosa", "Isabel", "Carmen", "Gabriela", "Silvia", "Beatriz", "Clara", "Teresa", "Victoria", "Margarita", "Sara", "Elena", "Sandra", "Paola", "Claudia", "Andrea", "Camila", "Natalia", "Valeria", "Daniela", "Monica", "Diana", "Lorena", "Verónica", "Alicia", "Marta", "Julia", "Cecilia", "Irene", "Luisa", "Adela", "Regina"]
APELLIDOS = ["Pérez", "Gómez", "Rodríguez", "López", "Martínez", "Sánchez", "García", "Fernández", "Díaz", "Álvarez", "Torres", "Ruiz", "Vargas", "Castro", "Morales", "Mendoza", "Paz", "Arias", "Ortiz", "Rojas", "Herrera", "Medina", "Flores", "Jiménez", "Benítez", "Silva", "Romero", "Ríos", "Molina", "Guzmán", "Mendez", "Mamani", "Torrico", "Sandoval", "Pinto", "Ramos", "Cardozo", "Llanos", "Salazar", "Suárez", "Zarate", "Justiniano", "Valdez", "Carrasco", "Llanos", "Salazar"]

MARCAS_VEHICULOS = [
    ("Toyota", ["Corolla", "Hilux", "RAV4", "Yaris", "Land Cruiser", "Prado"]),
    ("Nissan", ["Sentra", "Frontier", "Kicks", "Versa", "Pathfinder", "Patrol"]),
    ("Suzuki", ["Swift", "Grand Vitara", "Jimny", "Celerio", "Ertiga", "Baleno"]),
    ("Honda", ["Civic", "CR-V", "Fit", "HR-V", "Pilot"]),
    ("Hyundai", ["Tucson", "Accent", "Creta", "i10", "Santa Fe", "Elantra"]),
    ("Ford", ["Ranger", "Explorer", "Focus", "EcoSport", "F-150"]),
    ("Mitsubishi", ["L200", "Montero", "Outlander", "ASX"]),
    ("Chevrolet", ["Onix", "Tracker", "S10", "Cruze", "Captiva"]),
    ("Kia", ["Sportage", "Picanto", "Rio", "Sorento", "Cerato"])
]

COLORES = ["Blanco", "Negro", "Gris Oscuro", "Rojo", "Azul Marino", "Plateado", "Verde", "Dorado", "Bronce", "Beige"]

PROBLEMAS = [
    ("Falla Eléctrica y Electrónica", "El carro se apagó repentinamente y no quiere dar arranque, huele a plástico quemado."),
    ("Frenos y Suspensión", "Ruido fuerte de fricción de metal al frenar y pedal de freno muy esponjoso."),
    ("Paso de Corriente (Batería)", "Dejé los faros encendidos toda la noche y la batería se descargó completamente."),
    ("Auxilio de Llanta Pinchada", "Llanta delantera derecha pinchada en plena avenida por un clavo."),
    ("Remolque y Grúa", "Choque leve, el radiador está roto y gotea refrigerante, necesito grúa para llevarlo."),
    ("Sistema de Enfriamiento", "Temperatura de motor al máximo, vapor saliendo del capot."),
    ("Cerrajería Automotriz", "Se quedaron las llaves dentro del vehículo con el motor encendido y cerrado."),
    ("Mecánica de Motor", "Pérdida severa de potencia del motor y testigo de Check Engine parpadeando."),
    ("Combustible o Carga de Emergencia", "Me quedé sin gasolina a mitad de la autopista.")
]

COMENTARIOS_VALORACION = [
    "Excelente servicio, muy rápido y profesional el técnico.",
    "Llegaron en el tiempo estimado y el mecánico sabía muy bien su trabajo. Recomendado.",
    "Trato amable del técnico y solución efectiva del problema de batería.",
    "Buen trabajo en general, el cobro adicional fue justo por el repuesto.",
    "Tardó un poco más de lo esperado en llegar, pero la atención fue excelente.",
    "Servicio de primera, resolvieron el fallo eléctrico en minutos.",
    "Muy buen trato y la grúa llegó rápido a recogerme.",
    "El cerrajero abrió mi coche en segundos sin rayar la pintura, excelente.",
    "Solución rápida para la llanta pinchada. El técnico fue muy amable.",
    "Se agradece la honradez y la rapidez del servicio brindado hoy."
]

BARRIOS_SANTA_CRUZ = [
    "Equipetrol", "Sirari", "Urbarí", "Las Palmas", "Polanco", "Hamacas", "La Morita", "Villa Primero de Mayo",
    "Plan Tres Mil", "Pampa de la Isla", "El Trompillo", "Cochabamba", "Las Misiones", "Los Cusis", "San Aurelio",
    "Los Olivos", "Guapay", "Roca y Coronado", "Grigotá", "Virgen de Cotoca", "Banzer", "Doble Vía", "Santos Dumont"
]

NOMBRES_TALLERES = [
    "CarService", "AutoFix", "Mecánica", "Taller", "Centro Automotriz", "Clínica del Automóvil", 
    "Servicio Mecánico", "Multiservicio", "AutoSpeed", "Express Car", "Vial Rescate", "Doctor Car"
]

def seed_large_dataset():
    print("🧹 Limpiando base de datos existente...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("🌱 Creando catálogos estándar (servicios y especialidades)...")
        talleres_router.get_especialidades_disponibles(db)
        talleres_router.get_all_servicios(db)
        
        especialidades = db.query(models.Especialidad).all()
        servicios = db.query(models.Servicio).all()
        
        print("🌱 Creando Superadministrador...")
        sa = models.Admin(
            nombre="Limberth (SuperAdmin)",
            correo="asiscar.asistente@gmail.com",
            password_hash=get_password_hash("Asistencia2026"),
            rol="Superadmin",
            id_tenant=None
        )
        db.add(sa)
        db.commit()
        db.refresh(sa)
        
        # 1. Crear 55 Tenants y 55 Talleres
        print("🌱 Creando 55 Tenants y 55 Talleres en memoria...")
        talleres = []
        tenants = []
        
        taller_nombres_unicos = set()
        while len(taller_nombres_unicos) < 55:
            barrio = random.choice(BARRIOS_SANTA_CRUZ)
            nombre_base = random.choice(NOMBRES_TALLERES)
            nombre_taller = f"{nombre_base} {barrio}"
            if random.choice([True, False]):
                nombre_taller += f" {random.choice(['Express', 'Pro', '24H', 'VIP', 'Premium', 'Central', 'Sur', 'Norte'])}"
            taller_nombres_unicos.add(nombre_taller)
            
        taller_nombres_unicos = list(taller_nombres_unicos)
        
        # Guardaremos todo para un único batch commit
        batch_objects = []
        
        for idx, nombre_taller in enumerate(taller_nombres_unicos):
            import re
            base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', nombre_taller.lower()).strip('-')
            slug = base_slug
            
            tenant = models.Tenant(nombre=nombre_taller, subdominio_slug=slug)
            batch_objects.append(tenant)
            tenants.append(tenant)
            
            admin_email = f"admin.{slug}@asiscar.com"
            admin = models.Admin(
                nombre=f"Admin {nombre_taller}",
                correo=admin_email,
                password_hash=get_password_hash("admin123"),
                rol="Admin",
                tenant=tenant  # Relación enlazada
            )
            batch_objects.append(admin)
            
            lat = -17.7833 + random.uniform(-0.06, 0.06)
            lng = -63.1821 + random.uniform(-0.06, 0.06)
            taller_email = f"{slug}@asiscar.com"
            
            taller = models.Taller(
                tenant=tenant,  # Relación enlazada
                razon_social=nombre_taller,
                nombre_representante=f"{random.choice(NOMBRES_VARONES)} {random.choice(APELLIDOS)}",
                id_admin_aprobador=sa.id_admin,
                nit=f"2049{idx:06d}028",
                ubicacion_base_latitud=lat,
                ubicacion_base_longitud=lng,
                direccion_fisica=f"Av. Principal, Barrio {nombre_taller.split()[-1]}, Santa Cruz",
                telefono_taller=f"789{random.randint(10000, 99999)}",
                es_24_7=random.choice([True, False, False]),
                horario_apertura=time(8, 0),
                horario_cierre=time(19, 0),
                horario_cierre_sabado=time(13, 0),
                estado_aprobacion="Aprobado",
                correo=taller_email,
                password_hash=get_password_hash("taller123")
            )
            batch_objects.append(taller)
            talleres.append(taller)
            
            # Asociar servicios al taller
            num_servicios = random.randint(6, 12)
            selected_servicios = random.sample(servicios, num_servicios)
            for ser in selected_servicios:
                t_serv = models.TallerServicio(
                    taller=taller,  # Enlace relación
                    servicio=ser,   # Enlace relación
                    precio_especifico_taller=float(ser.tarifa_base_estimada) * random.choice([0.9, 1.0, 1.1, 1.15, 1.2]),
                    tiempo_estimado_minutos=random.choice([25, 30, 45, 60, 90, 120]),
                    estado_disponible=True
                )
                batch_objects.append(t_serv)
                
        # 2. Crear Técnicos
        print("🌱 Creando 110 Técnicos en memoria...")
        tecnicos = []
        for idx, tal in enumerate(talleres):
            for t_idx in range(2):
                nombre = random.choice(NOMBRES_VARONES)
                apellido = random.choice(APELLIDOS)
                clean_nom = nombre.lower().replace(" ", "")
                clean_ape = apellido.lower().replace(" ", "")
                correo_tec = f"{clean_nom}.{clean_ape}-{tal.tenant.subdominio_slug[:3]}@asiscar.com"
                
                tecnico = models.Tecnico(
                    taller=tal,
                    tenant=tal.tenant,
                    nombres=nombre,
                    apellidos=apellido,
                    ci_tecnico=f"{3000000 + idx*2 + t_idx}",
                    telefono_contacto=f"7{random.randint(1000000, 9999999)}",
                    correo=correo_tec,
                    password_hash=get_password_hash("tecnico123"),
                    primer_login=False,
                    en_turno=True,
                    estado_operativo="Disponible",
                    ubicacion_actual_latitud=tal.ubicacion_base_latitud + random.uniform(-0.015, 0.015),
                    ubicacion_actual_longitud=tal.ubicacion_base_longitud + random.uniform(-0.015, 0.015)
                )
                # Asociar 1-2 especialidades
                tecnico.especialidades.extend(random.sample(especialidades, random.randint(1, 2)))
                batch_objects.append(tecnico)
                tecnicos.append(tecnico)

        # 3. Crear 230 Clientes
        print("🌱 Creando 230 Clientes en memoria...")
        clientes = []
        
        cli_prueba = models.Cliente(
            nombres="Juan",
            apellidos="Perez Cliente",
            ci_dni="333333",
            telefono="73333333",
            correo="cliente@gmail.com",
            password_hash=get_password_hash("cliente123"),
            estado_cuenta="Activo"
        )
        batch_objects.append(cli_prueba)
        clientes.append(cli_prueba)
        
        clientes_generados = set()
        while len(clientes_generados) < 229:
            gen = random.choice([True, False])
            nom = random.choice(NOMBRES_VARONES) if gen else random.choice(NOMBRES_MUJERES)
            ape = random.choice(APELLIDOS)
            clientes_generados.add((nom, ape))
            
        clientes_generados = list(clientes_generados)
        
        for idx, (nom, ape) in enumerate(clientes_generados):
            clean_nom = nom.lower().replace(" ", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
            clean_ape = ape.lower().replace(" ", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
            correo = f"{clean_nom}.{clean_ape}.{idx}@gmail.com"
            
            cli = models.Cliente(
                nombres=nom,
                apellidos=ape,
                ci_dni=f"{4000000 + idx}",
                telefono=f"7{random.randint(1000000, 9999999)}",
                correo=correo,
                password_hash=get_password_hash("cliente123"),
                estado_cuenta="Activo"
            )
            batch_objects.append(cli)
            clientes.append(cli)

        # 4. Crear Vehículos
        print("🌱 Creando Vehículos en memoria...")
        vehiculos = []
        for cl in clientes:
            num_veh = random.randint(1, 2)
            for v_idx in range(num_veh):
                marca, modelos_lista = random.choice(MARCAS_VEHICULOS)
                modelo = random.choice(modelos_lista)
                placa = f"{random.randint(1000, 9999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
                
                veh = models.Vehiculo(
                    cliente=cl,
                    placa=placa,
                    marca=marca,
                    modelo=modelo,
                    año=random.randint(2010, 2025),
                    color=random.choice(COLORES),
                    tipo_transmision=random.choice(["Manual", "Automática"]),
                    tipo_combustible=random.choice(["Gasolina", "Diésel", "Gas natural (GNV)"])
                )
                batch_objects.append(veh)
                vehiculos.append(veh)

        # Confirmamos la estructura básica (talleres, tecnicos, clientes, vehiculos)
        # para que obtengan IDs y podamos enlazarlos en los incidentes
        print("💾 Guardando estructura base en la base de datos (Batch 1)...")
        db.add_all(batch_objects)
        db.commit()
        print("✅ Estructura base guardada.")

        # 5. Crear 650 Incidentes en estado "Finalizado"
        print("🌱 Generando 650 Incidentes en memoria...")
        batch_incidentes_relacionados = []
        
        for idx in range(650):
            cli = random.choice(clientes)
            cli_vehiculos = [v for v in vehiculos if v.id_cliente == cli.id_cliente]
            veh = random.choice(cli_vehiculos) if cli_vehiculos else random.choice(vehiculos)
            
            tipo_p, desc_p = random.choice(PROBLEMAS)
            lat = -17.7833 + random.uniform(-0.06, 0.06)
            lng = -63.1821 + random.uniform(-0.06, 0.06)
            
            fecha_incidente = datetime.now() - timedelta(
                days=random.randint(1, 365), 
                hours=random.randint(0, 23), 
                minutes=random.randint(0, 59)
            )
            
            taller_ganador = random.choice(talleres)
            
            incidente = models.Incidente(
                id_cliente=cli.id_cliente,
                id_vehiculo=veh.id_vehiculo,
                id_tenant=taller_ganador.id_tenant,
                fecha_hora_reporte=fecha_incidente,
                ubicacion_latitud=lat,
                ubicacion_longitud=lng,
                tipo_problema=tipo_p,
                descripcion_manual=desc_p,
                nivel_prioridad=random.choice(["Alta", "Media", "Baja"]),
                estado_solicitud="Finalizado",
                distancia_km_calculada=random.uniform(1.0, 9.5)
            )
            batch_incidentes_relacionados.append((incidente, taller_ganador, fecha_incidente))
            db.add(incidente)
            
        db.commit() # Commit para obtener IDs de incidente
        print("✅ Incidentes guardados.")

        # Generar Cotizaciones, Asistencias, Pagos y Valoraciones en lote
        print("🌱 Generando Cotizaciones, Asistencias, Pagos y Valoraciones...")
        lote_final = []
        
        for idx, (inc, taller_ganador, fecha_incidente) in enumerate(batch_incidentes_relacionados):
            monto = random.uniform(130, 450)
            
            # 1. Cotización Ganadora
            cot_ganadora = models.Cotizacion(
                id_incidente=inc.id_incidente,
                id_taller=taller_ganador.id_taller,
                id_tenant=taller_ganador.id_tenant,
                monto_estimado=monto,
                tiempo_estimado_minutos=random.choice([20, 30, 45, 60, 90]),
                comentario="Técnico disponible de inmediato.",
                estado="Aceptada",
                created_at=fecha_incidente + timedelta(minutes=random.randint(1, 5))
            )
            lote_final.append(cot_ganadora)
            
            # 2. Cotizaciones Rechazadas
            otros_talleres = [t for t in talleres if t.id_taller != taller_ganador.id_taller]
            for tal_perdedor in random.sample(otros_talleres, 2):
                cot_perdedora = models.Cotizacion(
                    id_incidente=inc.id_incidente,
                    id_taller=tal_perdedor.id_taller,
                    id_tenant=tal_perdedor.id_tenant,
                    monto_estimado=monto * random.uniform(1.15, 1.40),
                    tiempo_estimado_minutos=random.choice([40, 55, 80]),
                    comentario="Auxilio móvil de guardia.",
                    estado="Rechazada",
                    created_at=fecha_incidente + timedelta(minutes=random.randint(2, 8))
                )
                lote_final.append(cot_perdedora)
                
            # 3. Asistencia
            tecnicos_taller = [tec for tec in tecnicos if tec.id_taller == taller_ganador.id_taller]
            tecnico_asignado = random.choice(tecnicos_taller) if tecnicos_taller else random.choice(tecnicos)
            
            fecha_asignacion = fecha_incidente + timedelta(minutes=7)
            fecha_llegada = fecha_asignacion + timedelta(minutes=random.randint(12, 30))
            fecha_fin = fecha_llegada + timedelta(minutes=random.randint(20, 70))
            
            monto_adicional = random.choice([0.0, 0.0, 0.0, 0.0, 60.0, 120.0])
            asistencia = models.Asistencia(
                id_incidente=inc.id_incidente,
                id_taller=taller_ganador.id_taller,
                id_tecnico=tecnico_asignado.id_tecnico,
                id_tenant=taller_ganador.id_tenant,
                fecha_hora_asignacion=fecha_asignacion,
                fecha_hora_llegada_tecnico=fecha_llegada,
                fecha_hora_finalizacion=fecha_fin,
                observaciones_tecnico="Falla reparada. Vehículo operativo.",
                monto_adicional=monto_adicional,
                motivo_adicional="Repuesto básico de auxilio rápido" if monto_adicional > 0 else None
            )
            lote_final.append(asistencia)
            
            # 4. Pago
            subtotal = monto + monto_adicional
            comision = round(subtotal * 0.10, 2)
            total_cliente = subtotal + comision
            
            pago = models.Pago(
                asistencia=asistencia,  # Enlace de relación SQLAlchemy
                id_tenant=taller_ganador.id_tenant,
                monto_subtotal=subtotal,
                monto_comision_plataforma=comision,
                monto_total_cliente=total_cliente,
                metodo_pago=random.choice(["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"]),
                estado_transaccion="Completado",
                fecha_pago=fecha_fin + timedelta(minutes=2)
            )
            lote_final.append(pago)
            
            # 5. Valoración
            valoracion = models.Valoracion(
                asistencia=asistencia,  # Enlace de relación SQLAlchemy
                id_tenant=taller_ganador.id_tenant,
                puntuacion=random.choice([4, 5, 5, 5, 3]),
                comentario=random.choice(COMENTARIOS_VALORACION),
                fecha_valoracion=fecha_fin + timedelta(minutes=5)
            )
            lote_final.append(valoracion)
            
        db.add_all(lote_final)
        db.commit()
        print("✅ Cotizaciones, asistencias, pagos y valoraciones guardados.")

        # 6. Crear Órdenes de Trabajo de Taller en estado "Entregado"
        print("🌱 Creando 45 Órdenes de Trabajo SaaS en memoria...")
        lote_saas = []
        for idx in range(45):
            cli = random.choice(clientes)
            cli_vehiculos = [v for v in vehiculos if v.id_cliente == cli.id_cliente]
            veh = random.choice(cli_vehiculos) if cli_vehiculos else random.choice(vehiculos)
            taller_orden = random.choice(talleres)
            
            fecha_ingreso = datetime.now() - timedelta(days=random.randint(5, 360), hours=random.randint(1, 12))
            fecha_compromiso = fecha_ingreso + timedelta(days=random.randint(2, 5))
            fecha_entrega = fecha_compromiso + timedelta(hours=random.randint(-8, 8))
            
            orden = models.OrdenTrabajo(
                id_tenant=taller_orden.id_tenant,
                id_cliente=cli.id_cliente,
                id_vehiculo=veh.id_vehiculo,
                estado_recepcion="Inspección básica del vehículo al ingreso.",
                estado_trabajo="Entregado",
                fecha_ingreso=fecha_ingreso,
                fecha_compromiso_entrega=fecha_compromiso
            )
            lote_saas.append(orden)
            
            # Bitácoras
            b1 = models.BitacoraEstadoReparacion(orden=orden, estado_anterior=None, nuevo_estado="Diagnóstico", comentario="Revisión técnica iniciada.", fecha_cambio=fecha_ingreso)
            b2 = models.BitacoraEstadoReparacion(orden=orden, estado_anterior="Diagnóstico", nuevo_estado="Presupuestado", comentario="Presupuesto elaborado.", fecha_cambio=fecha_ingreso + timedelta(days=1))
            b3 = models.BitacoraEstadoReparacion(orden=orden, estado_anterior="Presupuestado", nuevo_estado="En Reparación", comentario="Presupuesto aprobado, se inicia el trabajo físico.", fecha_cambio=fecha_ingreso + timedelta(days=1, hours=4))
            b4 = models.BitacoraEstadoReparacion(orden=orden, estado_anterior="En Reparación", nuevo_estado="Entregado", comentario="Reparación finalizada. Vehículo entregado.", fecha_cambio=fecha_entrega)
            lote_saas.extend([b1, b2, b3, b4])
            
            # Presupuesto
            total_est = random.choice([850.0, 1100.0, 1450.0, 2000.0, 2900.0, 3800.0])
            presupuesto = models.Presupuesto(
                orden=orden,
                id_tenant=orden.id_tenant,
                descripcion_general="Plan de reparación detallado.",
                version="Inicial",
                estado="Aprobado",
                total_estimado=total_est,
                fecha_creacion=fecha_ingreso + timedelta(hours=6)
            )
            lote_saas.append(presupuesto)
            
            # Detalles
            det1 = models.DetallePresupuesto(
                presupuesto=presupuesto,
                id_tenant=orden.id_tenant,
                categoria="Mecánica",
                grupo_falla="Motor/Transmisión",
                es_critico=True,
                tipo_item="Repuesto",
                item_descripcion="Kit de reparación / Repuestos requeridos",
                cantidad=1,
                precio_unitario=total_est * 0.65,
                subtotal=total_est * 0.65,
                estado_item="Aprobado"
            )
            det2 = models.DetallePresupuesto(
                presupuesto=presupuesto,
                id_tenant=orden.id_tenant,
                categoria="Servicio",
                grupo_falla="Mano de Obra",
                es_critico=True,
                tipo_item="Mano de Obra",
                item_descripcion="Mano de obra calificada",
                cantidad=1,
                precio_unitario=total_est * 0.35,
                subtotal=total_est * 0.35,
                estado_item="Aprobado"
            )
            lote_saas.extend([det1, det2])
            
            # Pago
            monto_total = float(total_est)
            comision_p = round(monto_total * 0.05, 2)
            subt = monto_total - comision_p
            
            pago_rep = models.PagoReparacion(
                orden=orden,
                id_tenant=orden.id_tenant,
                monto_subtotal=subt,
                monto_comision_plataforma=comision_p,
                monto_total_cliente=monto_total,
                metodo_pago=random.choice(["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"]),
                estado_transaccion="Completado",
                fecha_pago=fecha_entrega
            )
            lote_saas.append(pago_rep)
            
        db.add_all(lote_saas)
        db.commit()
        print(f"   Órdenes de Trabajo SaaS completadas (Entregadas): 45")
        print("✅ ¡Gran dataset semilla optimizado e insertado exitosamente en Supabase!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar datos semilla: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_large_dataset()
