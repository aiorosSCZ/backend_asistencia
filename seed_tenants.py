import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
from crud import get_password_hash

def seed_data():
    # Asegurar que las tablas estén limpias y actualizadas en desarrollo
    print("Limpiando base de datos y recreando tablas...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Iniciando insercion de datos semilla...")

        # 1. Crear Tenants
        t1 = db.query(models.Tenant).filter(models.Tenant.subdominio_slug == "auxilio-norte").first()
        if not t1:
            t1 = models.Tenant(nombre="Auxilio Norte", subdominio_slug="auxilio-norte")
            db.add(t1)
            db.commit()
            db.refresh(t1)
            print("Tenant 'Auxilio Norte' creado.")
        
        t2 = db.query(models.Tenant).filter(models.Tenant.subdominio_slug == "mecanicos-express").first()
        if not t2:
            t2 = models.Tenant(nombre="Mecánicos Express", subdominio_slug="mecanicos-express")
            db.add(t2)
            db.commit()
            db.refresh(t2)
            print("Tenant 'Mecánicos Express' creado.")

        # 2. Crear Superadministrador Global
        sa = db.query(models.Admin).filter(models.Admin.correo == "asiscar.asistente@gmail.com").first()
        if not sa:
            sa = models.Admin(
                nombre="Limberth (SuperAdmin)",
                correo="asiscar.asistente@gmail.com",
                password_hash=get_password_hash("AsiscarAsistente2026"),
                rol="Superadmin",
                id_tenant=None
            )
            db.add(sa)
            print("SuperAdmin global creado.")
        else:
            sa.rol = "Superadmin"
            sa.id_tenant = None

        # 3. Crear Administradores de Tenant
        adm1 = db.query(models.Admin).filter(models.Admin.correo == "admin.norte@asiscar.com").first()
        if not adm1:
            adm1 = models.Admin(
                nombre="Admin Auxilio Norte",
                correo="admin.norte@asiscar.com",
                password_hash=get_password_hash("admin123"),
                rol="Admin",
                id_tenant=t1.id_tenant
            )
            db.add(adm1)
            print("Admin de Tenant Auxilio Norte creado.")

        adm2 = db.query(models.Admin).filter(models.Admin.correo == "admin.express@asiscar.com").first()
        if not adm2:
            adm2 = models.Admin(
                nombre="Admin Mecánicos Express",
                correo="admin.express@asiscar.com",
                password_hash=get_password_hash("admin123"),
                rol="Admin",
                id_tenant=t2.id_tenant
            )
            db.add(adm2)
            print("Admin de Tenant Mecánicos Express creado.")

        # 4. Crear Talleres asociados a Tenants
        tal1 = db.query(models.Taller).filter(models.Taller.correo == "taller.norte@asiscar.com").first()
        if not tal1:
            tal1 = models.Taller(
                id_tenant=t1.id_tenant,
                razon_social="Taller Auxilio Norte Central",
                nombre_representante="Carlos Representante",
                nit="111111111",
                ubicacion_base_latitud=-17.7780,
                ubicacion_base_longitud=-63.1750,
                direccion_fisica="Av. Banzer 4to Anillo",
                telefono_taller="77777777",
                correo="taller.norte@asiscar.com",
                password_hash=get_password_hash("taller123"),
                estado_aprobacion="Aprobado"
            )
            db.add(tal1)
            db.commit()
            db.refresh(tal1)
            print("Taller de Tenant Auxilio Norte creado.")

        tal2 = db.query(models.Taller).filter(models.Taller.correo == "taller.express@asiscar.com").first()
        if not tal2:
            tal2 = models.Taller(
                id_tenant=t2.id_tenant,
                razon_social="Taller Express Sur",
                nombre_representante="Jorge Representante",
                nit="222222222",
                ubicacion_base_latitud=-17.8100,
                ubicacion_base_longitud=-63.1900,
                direccion_fisica="Av. Doble Vía La Guardia 5to Anillo",
                telefono_taller="88888888",
                correo="taller.express@asiscar.com",
                password_hash=get_password_hash("taller123"),
                estado_aprobacion="Aprobado"
            )
            db.add(tal2)
            db.commit()
            db.refresh(tal2)
            print("Taller de Tenant Mecánicos Express creado.")

        # 5. Crear Técnicos para cada taller
        tec1 = db.query(models.Tecnico).filter(models.Tecnico.correo == "tecnico.norte@asiscar.com").first()
        if not tec1:
            tec1 = models.Tecnico(
                id_taller=tal1.id_taller,
                id_tenant=tal1.id_tenant,
                nombres="Pedro",
                apellidos="Mecánico Norte",
                ci_tecnico="111111",
                telefono_contacto="71111111",
                correo="tecnico.norte@asiscar.com",
                password_hash=get_password_hash("tecnico123"),
                estado_operativo="Disponible",
                en_turno=True
            )
            db.add(tec1)
            print("Tecnico para Auxilio Norte creado.")

        tec2 = db.query(models.Tecnico).filter(models.Tecnico.correo == "tecnico.express@asiscar.com").first()
        if not tec2:
            tec2 = models.Tecnico(
                id_taller=tal2.id_taller,
                id_tenant=tal2.id_tenant,
                nombres="Lucas",
                apellidos="Mecánico Express",
                ci_tecnico="222222",
                telefono_contacto="72222222",
                correo="tecnico.express@asiscar.com",
                password_hash=get_password_hash("tecnico123"),
                estado_operativo="Disponible",
                en_turno=True
            )
            db.add(tec2)
            print("Tecnico para Mecánicos Express creado.")

        # 6. Crear un cliente global para pruebas
        cli = db.query(models.Cliente).filter(models.Cliente.correo == "cliente@gmail.com").first()
        if not cli:
            cli = models.Cliente(
                nombres="Juan",
                apellidos="Perez Cliente",
                ci_dni="333333",
                telefono="73333333",
                correo="cliente@gmail.com",
                password_hash=get_password_hash("cliente123"),
                estado_cuenta="Activo"
            )
            db.add(cli)
            db.commit()
            db.refresh(cli)
            print("Cliente global creado.")

        # 7. Registrar un vehículo para el cliente
        veh = db.query(models.Vehiculo).filter(models.Vehiculo.id_cliente == cli.id_cliente).first()
        if not veh:
            veh = models.Vehiculo(
                id_cliente=cli.id_cliente,
                placa="1234ABC",
                marca="Toyota",
                modelo="Corolla",
                año=2020,
                color="Blanco",
                tipo_transmision="Automática",
                tipo_combustible="Gasolina"
            )
            db.add(veh)
            print("Vehiculo del cliente creado.")

        db.commit()

        # 8. Registrar Orden de Trabajo, Presupuesto e Hito de prueba
        ord_tr = models.OrdenTrabajo(
            id_tenant=t1.id_tenant,
            id_cliente=cli.id_cliente,
            id_vehiculo=veh.id_vehiculo,
            estado_recepcion="Abolladura leve en puerta conductor, 1/4 tanque de gasolina",
            estado_trabajo="Diagnóstico"
        )
        db.add(ord_tr)
        db.commit()
        db.refresh(ord_tr)
        
        # Hito inicial
        bit = models.BitacoraEstadoReparacion(
            id_orden=ord_tr.id_orden,
            estado_anterior=None,
            nuevo_estado="Diagnóstico",
            comentario="Ingreso de vehículo al taller e inicio de fase de diagnóstico."
        )
        db.add(bit)
        
        # Crear presupuesto de prueba
        pres = models.Presupuesto(
            id_orden=ord_tr.id_orden,
            id_tenant=ord_tr.id_tenant,
            descripcion_general="Reparación del sistema de embrague y amortiguadores delanteros.",
            version="Inicial",
            estado="Pendiente",
            total_estimado=650.00
        )
        db.add(pres)
        db.commit()
        db.refresh(pres)
        
        # Detalles del presupuesto
        det1 = models.DetallePresupuesto(
            id_presupuesto=pres.id_presupuesto,
            id_tenant=ord_tr.id_tenant,
            categoria="Motor",
            grupo_falla="Sistema de Embrague",
            es_critico=True,
            tipo_item="Repuesto",
            item_descripcion="Kit de Embrague",
            cantidad=1,
            precio_unitario=400.00,
            subtotal=400.00
        )
        det2 = models.DetallePresupuesto(
            id_presupuesto=pres.id_presupuesto,
            id_tenant=ord_tr.id_tenant,
            categoria="Suspensión",
            grupo_falla="Amortiguadores",
            es_critico=False,
            tipo_item="Mano de Obra",
            item_descripcion="Cambio de Amortiguadores delanteros",
            cantidad=2,
            precio_unitario=125.00,
            subtotal=250.00
        )
        db.add(det1)
        db.add(det2)
        db.commit()
        print("Órdenes de Trabajo y Presupuestos Semilla creados con éxito.")
        
        # Sincronizar catálogo estándar
        import routers.talleres as talleres
        talleres.get_all_servicios(db)
        talleres.get_especialidades_disponibles(db)
        
        print("Insercion de datos semilla completada con exito!")
    except Exception as e:
        db.rollback()
        print(f"Error al insertar datos semilla: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
