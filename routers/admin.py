from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models
import crud
import dependencies
from datetime import datetime, timedelta
import calendar

router = APIRouter(prefix="/api/admin", tags=["SuperAdmin"])

# Endpoint de inicialización segura
@router.post("/setup_initial_superuser")
def setup_initial_superuser(db: Session = Depends(get_db)):
    from crud import get_password_hash
    admin = db.query(models.Admin).first()
    
    if admin:
        # Si ya existe, simplemente le reiniciamos las credenciales a las correctas
        admin.correo = "asiscar.asistente@gmail.com"
        admin.password_hash = get_password_hash("AsiscarAsistente2026")
        admin.nombre = "Limberth (SuperAdmin)"
        db.commit()
        return {"message": "✅ Credenciales de SuperAdmin forzadas a: asiscar.asistente@gmail.com / AsiscarAsistente2026. Ya puedes iniciar sesión."}
    
    # Si no existe, lo creamos
    nuevo_admin = models.Admin(
        nombre="Limberth (SuperAdmin)",
        correo="asiscar.asistente@gmail.com",
        password_hash=get_password_hash("AsiscarAsistente2026"),
        rol="Admin"
    )
    db.add(nuevo_admin)
    db.commit()
    return {"message": "✅ Superusuario inicial creado con éxito. Ya puedes iniciar sesión."}
@router.post("/login")
def login_admin(payload: dict, db: Session = Depends(get_db)):
    import models
    import crud
    import utils
    correo = payload.get("correo")
    password = payload.get("password")
    
    admin = db.query(models.Admin).filter(models.Admin.correo == correo).first()
    if not admin or not crud.verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas para Administrador")
        
    role_name = "superadmin" if admin.rol == "Superadmin" else "admin"
    token = utils.create_access_token({
        "sub": str(admin.id_admin),
        "user_id": admin.id_admin,
        "role": role_name,
        "id_tenant": admin.id_tenant
    })
    
    return {
        "access_token": token,
        "role": role_name,
        "user_name": admin.nombre,
        "id_admin": admin.id_admin
    }

@router.get("/panel", response_class=HTMLResponse)
def get_superadmin_panel():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Admin General - SegurIA</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-main: #f3f4f6;
                --bg-sidebar: #ffffff;
                --bg-card: #ffffff;
                --primary: #4f46e5;
                --primary-hover: #4338ca;
                --text-main: #1f2937;
                --text-muted: #6b7280;
                --border-color: #e5e7eb;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Inter', sans-serif;
            }

            body {
                background-color: var(--bg-main);
                color: var(--text-main);
                display: flex;
                height: 100vh;
                overflow: hidden;
            }

            /* SIDEBAR */
            aside {
                width: 260px;
                background-color: var(--bg-sidebar);
                border-right: 1px solid var(--border-color);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 24px;
            }

            .brand {
                font-size: 1.5rem;
                font-weight: bold;
                color: var(--primary);
                margin-bottom: 32px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .nav-links {
                list-style: none;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .nav-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                border-radius: 8px;
                color: var(--text-muted);
                text-decoration: none;
                font-weight: 500;
                transition: all 0.2s;
                cursor: pointer;
            }

            .nav-item:hover, .nav-item.active {
                background-color: rgba(79, 70, 229, 0.08);
                color: var(--primary);
            }

            .nav-item.active {
                background-color: rgba(79, 70, 229, 0.1);
                font-weight: 600;
            }

            .nav-item-left {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .sidebar-footer {
                display: flex;
                flex-direction: column;
                gap: 12px;
                border-top: 1px solid var(--border-color);
                padding-top: 16px;
            }

            .footer-link {
                text-decoration: none;
                font-size: 0.9rem;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                text-align: center;
            }

            .logout-btn {
                color: #ef4444;
                background-color: rgba(239, 68, 68, 0.05);
            }

            .home-btn {
                color: #2563eb;
                background-color: rgba(37, 99, 235, 0.05);
            }

            /* MAIN CONTENT */
            main {
                flex: 1;
                padding: 40px;
                overflow-y: auto;
            }

            .header {
                margin-bottom: 32px;
            }

            .header h1 {
                font-size: 1.875rem;
                font-weight: 700;
                color: #111827;
            }

            .header p {
                color: var(--text-muted);
                margin-top: 4px;
            }

            /* GRIDS */
            .grid-top {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 24px;
                margin-bottom: 24px;
            }

            .grid-small {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 24px;
                margin-bottom: 32px;
            }

            .grid-bottom {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 24px;
            }

            /* CARDS */
            .card {
                background-color: var(--bg-card);
                border-radius: 12px;
                padding: 24px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
            }

            .card-gradient-blue {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                color: white;
            }

            .card-gradient-green {
                background: linear-gradient(135deg, #059669 0%, #047857 100%);
                color: white;
            }

            .card-title {
                font-size: 0.875rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 12px;
                opacity: 0.9;
            }

            .card-value {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 8px;
            }

            .card-subtitle {
                font-size: 0.75rem;
                opacity: 0.8;
            }

            /* SMALL CARDS */
            .card-small {
                border-left: 4px solid var(--primary);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .card-small-blue { border-left-color: #3b82f6; }
            .card-small-green { border-left-color: #10b981; }
            .card-small-orange { border-left-color: #f59e0b; }
            .card-small-purple { border-left-color: #8b5cf6; }

            .card-small-info h3 {
                font-size: 0.875rem;
                color: var(--text-muted);
                font-weight: 500;
            }

            .card-small-info .value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #111827;
                margin-top: 4px;
            }

            .card-small-icon {
                font-size: 1.5rem;
                opacity: 0.2;
            }

            /* TABLES & LISTS */
            .section-title {
                font-size: 1.125rem;
                font-weight: 600;
                color: #111827;
                margin-bottom: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .badge-count {
                background-color: rgba(16, 185, 129, 0.1);
                color: #10b981;
                padding: 4px 8px;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
            }

            .empty-state {
                text-align: center;
                padding: 40px 20px;
                color: var(--text-muted);
                font-size: 0.875rem;
            }

            /* UTILS */
            .text-purple { color: #6366f1; }
            .adjust-link {
                color: #6366f1;
                text-decoration: none;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            /* TABLAS */
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
                font-size: 0.875rem;
            }
            th {
                color: var(--text-muted);
                font-weight: 500;
            }
            .badge {
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .badge-pending { background: #fef3c7; color: #d97706; }
            .badge-approved { background: #d1fae5; color: #059669; }
            .btn-action {
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.75rem;
            }
            .btn-approve { background: #10b981; color: white; margin-right: 8px;}
            .btn-approve:hover { background: #059669; }
            .btn-reject { background: #ef4444; color: white;}
            .btn-reject:hover { background: #dc2626; }
        </style>
    </head>
    <body>
        <aside>
            <div>
                <div class="brand">
                    <span>🛡️</span> SegurIA
                </div>
                <nav>
                    <ul class="nav-links">
                        <li>
                            <a class="nav-item active">
                                <div class="nav-item-left"><span>📊</span> Dashboard</div>
                            </a>
                        </li>
                        <li>
                            <a class="nav-item">
                                <div class="nav-item-left"><span>👥</span> Usuarios</div>
                                <span>↓</span>
                            </a>
                        </li>
                        <li>
                            <a class="nav-item">
                                <div class="nav-item-left"><span>🛠️</span> Talleres</div>
                                <span>↓</span>
                            </a>
                        </li>
                        <li>
                            <a class="nav-item">
                                <div class="nav-item-left"><span>⚠️</span> Incidentes</div>
                                <span>↓</span>
                            </a>
                        </li>
                        <li>
                            <a class="nav-item">
                                <div class="nav-item-left"><span>💳</span> Finanzas</div>
                                <span>↓</span>
                            </a>
                        </li>
                        <li>
                            <a class="nav-item">
                                <div class="nav-item-left"><span>❓</span> Soporte Técnico</div>
                            </a>
                        </li>
                    </ul>
                </nav>
            </div>
            
            <div class="sidebar-footer">
                <a href="#" class="footer-link logout-btn">Cerrar sesión</a>
                <a href="/" class="footer-link home-btn">Ir al Inicio</a>
            </div>
        </aside>

        <main>
            <div class="header">
                <h1>Panel Admin General</h1>
                <p>Bienvenido, Super</p>
            </div>

            <!-- GRID TOP -->
            <div class="grid-top">
                <div class="card card-gradient-blue">
                    <div class="card-title">Total Recaudado (Pagos)</div>
                    <div class="card-value" id="total-recaudado">BOB 0.00</div>
                    <div class="card-subtitle">Métrica Total</div>
                </div>
                <div class="card card-gradient-green">
                    <div class="card-title">Ganancia Plataforma (10%)</div>
                    <div class="card-value" id="ganancia-plataforma">BOB 0.00</div>
                    <div class="card-subtitle">10% de cada servicio</div>
                </div>
                <div class="card">
                    <div class="card-title text-purple">Tasa de Comisión Actual</div>
                    <div class="card-value text-purple" id="tasa-comision">10%</div>
                    <a href="#" class="adjust-link">Ajustar Tasa</a>
                </div>
            </div>

            <!-- GRID SMALL -->
            <div class="grid-small">
                <div class="card card-small card-small-blue">
                    <div class="card-small-info">
                        <h3>Talleres</h3>
                        <div class="value" id="workshops-count">0</div>
                    </div>
                    <div class="card-small-icon">🔧</div>
                </div>
                <div class="card card-small card-small-green">
                    <div class="card-small-info">
                        <h3>Especialidades</h3>
                        <div class="value" id="specialties-count">0</div>
                    </div>
                    <div class="card-small-icon">⚙️</div>
                </div>
                <div class="card card-small card-small-orange">
                    <div class="card-small-info">
                        <h3>Usuarios</h3>
                        <div class="value" id="clients-count">0</div>
                    </div>
                    <div class="card-small-icon">👥</div>
                </div>
                <div class="card card-small card-small-purple">
                    <div class="card-small-info">
                        <h3>Incidentes</h3>
                        <div class="value" id="incidents-count">0</div>
                    </div>
                    <div class="card-small-icon">🚨</div>
                </div>
            </div>

            <!-- TABLA DE VALIDACIÓN DE TALLERES -->
            <div class="card" style="margin-bottom: 24px;">
                <div class="section-title">
                    <span>🛠️ Talleres Pendientes de Validación</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Taller</th>
                            <th>NIT</th>
                            <th>Dirección</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="workshops-table">
                        <!-- Dinámico -->
                    </tbody>
                </table>
            </div>

            <!-- GRID BOTTOM -->
            <div class="grid-bottom">
                <div class="card">
                    <div class="section-title">
                        <span>Especialidades Registradas</span>
                        <span class="badge-count" id="specialties-total">0 Total</span>
                    </div>
                    <div id="specialties-list">
                        <!-- Dinámico o Empty -->
                        <div class="empty-state">No hay especialidades registradas.</div>
                    </div>
                </div>
                <div class="card">
                    <div class="section-title">
                        <span>Usuarios Recientes</span>
                    </div>
                    <div id="users-list">
                        <!-- Dinámico o Empty -->
                        <div class="empty-state">Cargando usuarios...</div>
                    </div>
                </div>
            </div>
        </main>

        <script>
            async function loadData() {
                try {
                    const token = localStorage.getItem('admin_token');
                    const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
                    const res = await fetch('/api/admin/metrics', { headers });
                    if (!res.ok) {
                        console.error("No autorizado o error al cargar métricas");
                        return;
                    }
                    const data = await res.json();
                    
                    document.getElementById('clients-count').innerText = data.stats.clientes;
                    document.getElementById('workshops-count').innerText = data.stats.talleres;
                    document.getElementById('incidents-count').innerText = data.stats.incidentes;
                    document.getElementById('specialties-count').innerText = data.stats.especialidades || 0;
                    document.getElementById('specialties-total').innerText = `${data.stats.especialidades || 0} Total`;
                    
                    document.getElementById('total-recaudado').innerText = `BOB ${data.stats.total_recaudado.toFixed(2)}`;
                    document.getElementById('ganancia-plataforma').innerText = `BOB ${data.stats.ganancia_plataforma.toFixed(2)}`;
                    document.getElementById('tasa-comision').innerText = `${data.stats.tasa_comision}%`;

                    // Talleres
                    const wt = document.getElementById('workshops-table');
                    wt.innerHTML = '';
                    let pendientes = data.talleres.filter(t => t.estado_aprobacion === 'Pendiente');
                    
                    if (pendientes.length === 0) {
                        wt.innerHTML = '<tr><td colspan="5" class="empty-state">No hay talleres pendientes de validación.</td></tr>';
                    } else {
                        pendientes.forEach(t => {
                            wt.innerHTML += `
                                <tr>
                                    <td>${t.razon_social}</td>
                                    <td>${t.nit}</td>
                                    <td>${t.direccion || 'No especificada'}</td>
                                    <td><span class="badge badge-pending">${t.estado_aprobacion}</span></td>
                                    <td>
                                        <button class="btn-action btn-approve" onclick="approveWorkshop(${t.id_taller})">Aprobar</button>
                                        <button class="btn-action btn-reject" onclick="rejectWorkshop(${t.id_taller})">Rechazar</button>
                                    </td>
                                </tr>
                            `;
                        });
                    }

                    // Usuarios Recientes
                    const ul = document.getElementById('users-list');
                    ul.innerHTML = '';
                    if (data.clientes.length === 0) {
                        ul.innerHTML = '<div class="empty-state">No hay usuarios registrados.</div>';
                    } else {
                        let html = '<table><thead><tr><th>Nombre</th><th>Correo</th></tr></thead><tbody>';
                        data.clientes.slice(0, 5).forEach(c => {
                            html += `<tr><td>${c.nombre_completo}</td><td>${c.correo}</td></tr>`;
                        });
                        html += '</tbody></table>';
                        ul.innerHTML = html;
                    }

                } catch (e) {
                    console.error(e);
                }
            }

            async function approveWorkshop(id) {
                const token = localStorage.getItem('admin_token');
                const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
                await fetch(`/api/admin/talleres/${id}/aprobar`, { method: 'POST', headers });
                loadData();
            }

            async function rejectWorkshop(id) {
                const token = localStorage.getItem('admin_token');
                const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
                await fetch(`/api/admin/talleres/${id}/rechazar`, { method: 'POST', headers });
                loadData();
            }

            loadData();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/metrics")
def get_admin_metrics(
    filter_type: str = "historico",
    filter_value: str = "",
    taller_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user) if 'dependencies' in globals() else Depends(lambda: None)
):
    from dependencies import get_current_user
    try:
        current_user = get_current_user(current_user) if hasattr(current_user, "credentials") else current_user
    except Exception:
        pass

    rol = "superadmin"
    id_tenant = None
    if current_user and isinstance(current_user, dict):
        rol = (current_user.get("role") or current_user.get("rol") or "superadmin").lower()
        id_tenant = current_user.get("id_tenant")

    start_date = None
    end_date = None
    
    if filter_type == 'dia' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
        except: pass
    elif filter_type == 'mes' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y-%m")
            _, last_day = calendar.monthrange(start_date.year, start_date.month)
            end_date = start_date.replace(day=last_day) + timedelta(days=1)
        except: pass
    elif filter_type == 'anual' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y")
            end_date = start_date.replace(year=start_date.year + 1)
        except: pass
    elif filter_type == 'rango_fechas' and filter_value:
        try:
            parts = filter_value.split(":")
            start_date = datetime.strptime(parts[0], "%Y-%m-%d")
            end_date = datetime.strptime(parts[1], "%Y-%m-%d") + timedelta(days=1)
        except: pass
    elif filter_type == 'rango_meses' and filter_value:
        try:
            parts = filter_value.split(":")
            start_date = datetime.strptime(parts[0], "%Y-%m")
            end_month = datetime.strptime(parts[1], "%Y-%m")
            _, last_day = calendar.monthrange(end_month.year, end_month.month)
            end_date = end_month.replace(day=last_day) + timedelta(days=1)
        except: pass

    if rol == "superadmin" or id_tenant is None:
        q_clientes = db.query(models.Cliente)
        q_talleres = db.query(models.Taller)
        q_incidentes = db.query(models.Incidente)
        q_pago = db.query(models.Pago)
        
        if start_date and end_date:
            q_clientes = q_clientes.filter(models.Cliente.created_at >= start_date, models.Cliente.created_at < end_date)
            q_talleres = q_talleres.filter(models.Taller.created_at >= start_date, models.Taller.created_at < end_date)
            q_incidentes = q_incidentes.filter(models.Incidente.fecha_hora_reporte >= start_date, models.Incidente.fecha_hora_reporte < end_date)
            q_pago = q_pago.join(models.Asistencia).filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
            
        if taller_id:
            # no filtramos q_talleres para retornar la lista completa en talleres_lista
            q_incidentes = q_incidentes.join(models.Asistencia, isouter=True).filter(models.Asistencia.id_taller == taller_id)
            q_clientes = q_clientes.join(models.Incidente).join(models.Asistencia).filter(models.Asistencia.id_taller == taller_id)
            q_pago = q_pago.filter(models.Asistencia.id_taller == taller_id) if (start_date and end_date) else q_pago.join(models.Asistencia).filter(models.Asistencia.id_taller == taller_id)

        clientes_count = q_clientes.count()
        talleres_lista = q_talleres.all()
        talleres_count = 1 if taller_id else len(talleres_lista)
        incidentes_count = q_incidentes.count()
        especialidades_count = db.query(models.Especialidad).count()
        
        total_recaudado = q_pago.with_entities(func.sum(models.Pago.monto_total_cliente)).scalar() or 0.0
        ganancia_plataforma = q_pago.with_entities(func.sum(models.Pago.monto_comision_plataforma)).scalar() or 0.0
        
        clientes = q_clientes.all()
        incidentes = q_incidentes.all()
    else:
        q_talleres = db.query(models.Taller).filter(models.Taller.id_tenant == id_tenant)
        q_incidentes = db.query(models.Incidente).filter(models.Incidente.id_tenant == id_tenant)
        q_clientes = db.query(models.Cliente).join(models.Incidente).filter(models.Incidente.id_tenant == id_tenant)
        
        if start_date and end_date:
            q_talleres = q_talleres.filter(models.Taller.created_at >= start_date, models.Taller.created_at < end_date)
            q_incidentes = q_incidentes.filter(models.Incidente.fecha_hora_reporte >= start_date, models.Incidente.fecha_hora_reporte < end_date)
            q_clientes = q_clientes.filter(models.Incidente.fecha_hora_reporte >= start_date, models.Incidente.fecha_hora_reporte < end_date)

        if taller_id:
            # We don't filter q_talleres so it still returns the full list for the dropdown
            # OR we can just fetch all talleres for the list separately
            q_incidentes = q_incidentes.join(models.Asistencia, isouter=True).filter(models.Asistencia.id_taller == taller_id)
            q_clientes = q_clientes.join(models.Asistencia, isouter=True).filter(models.Asistencia.id_taller == taller_id)

        talleres_lista = q_talleres.all()
        talleres_ids = [t.id_taller for t in talleres_lista]
        
        # We apply the count of talleres based on filter if needed, but returning all is fine
        if taller_id:
            talleres_count = 1
        else:
            talleres_count = len(talleres_lista)
        
        # Para el filtrado de pagos, si hay taller id usamos ese
        filtro_talleres = [taller_id] if taller_id else talleres_ids
        
        incidentes = q_incidentes.all()
        incidentes_count = len(incidentes)
        
        clientes_count = q_clientes.distinct().count()
        
        # Especialidades en los talleres de este tenant
        if filtro_talleres:
            especialidades_count = db.query(models.Especialidad).join(models.TecnicoEspecialidad).join(models.Tecnico).filter(models.Tecnico.id_taller.in_(filtro_talleres)).distinct().count()
            q_pago = db.query(models.Pago).join(models.Asistencia).filter(models.Asistencia.id_taller.in_(filtro_talleres))
            if start_date and end_date:
                q_pago = q_pago.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
            
            total_recaudado = q_pago.with_entities(func.sum(models.Pago.monto_total_cliente)).scalar() or 0.0
            ganancia_plataforma = q_pago.with_entities(func.sum(models.Pago.monto_comision_plataforma)).scalar() or 0.0
        else:
            especialidades_count = 0
            total_recaudado = 0.0
            ganancia_plataforma = 0.0
            
        clientes = q_clientes.distinct().all()

    talleres_enriquecidos = []
    for t in talleres_lista:
        tecnicos_count = db.query(models.Tecnico).filter(models.Tecnico.id_taller == t.id_taller).count()
        q_asis = db.query(models.Asistencia).filter(models.Asistencia.id_taller == t.id_taller)
        q_pago = db.query(models.Pago).join(models.Asistencia).filter(models.Asistencia.id_taller == t.id_taller)
        if start_date and end_date:
            q_asis = q_asis.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
            q_pago = q_pago.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
        asistencias_count = q_asis.count()
        facturacion_total = q_pago.with_entities(func.sum(models.Pago.monto_total_cliente)).scalar() or 0.0
        comision_plataforma = q_pago.with_entities(func.sum(models.Pago.monto_comision_plataforma)).scalar() or 0.0
        
        talleres_enriquecidos.append({
            "id_taller": t.id_taller,
            "razon_social": t.razon_social,
            "nit": t.nit,
            "direccion": t.direccion_fisica,
            "estado_aprobacion": t.estado_aprobacion,
            "lat": t.ubicacion_base_latitud,
            "lng": t.ubicacion_base_longitud,
            "calificacion_promedio": float(t.calificacion_promedio or 5.0),
            "subdominio_slug": t.tenant.subdominio_slug if t.tenant else "",
            "tecnicos_count": tecnicos_count,
            "asistencias_count": asistencias_count,
            "facturacion_total": float(facturacion_total),
            "comision_plataforma": float(comision_plataforma)
        })

    return {
        "stats": {
            "clientes": clientes_count,
            "talleres": talleres_count,
            "incidentes": incidentes_count,
            "especialidades": especialidades_count,
            "total_recaudado": float(total_recaudado),
            "ganancia_plataforma": float(ganancia_plataforma),
            "tasa_comision": 10.0
        },
        "talleres": talleres_enriquecidos,
        "clientes": [
            {
                "id_cliente": c.id_cliente,
                "nombre_completo": f"{c.nombres} {c.apellidos}",
                "correo": c.correo,
                "telefono": c.telefono
            } for c in clientes
        ],
        "incidentes": [
            {
                "id_incidente": i.id_incidente,
                "tipo_problema": i.tipo_problema,
                "estado": i.estado_solicitud,
                "prioridad": i.nivel_prioridad,
                "fecha": i.fecha_hora_reporte
            } for i in incidentes
        ]
    }

@router.get("/kpis")
def get_admin_kpis(
    filter_type: str = "historico",
    filter_value: str = "",
    taller_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user) if 'dependencies' in globals() else Depends(lambda: None)
):
    print(f"DEBUG KPIS RUNNING: type={filter_type}, val={filter_value}, taller={taller_id}", flush=True)
    from sqlalchemy import extract, case, cast, Float
    
    rol = "superadmin"
    id_tenant = None
    if current_user and isinstance(current_user, dict):
        rol = (current_user.get("role") or current_user.get("rol") or "superadmin").lower()
        id_tenant = current_user.get("id_tenant")

    # Base Queries
    q_asistencia = db.query(models.Asistencia)
    q_incidente = db.query(models.Incidente)
    q_taller = db.query(models.Taller)

    if rol != "superadmin" and id_tenant is not None:
        q_asistencia = q_asistencia.filter(models.Asistencia.id_tenant == id_tenant)
        q_incidente = q_incidente.filter(models.Incidente.id_tenant == id_tenant)
        q_taller = q_taller.filter(models.Taller.id_tenant == id_tenant)

    # Time filters
    start_date = None
    end_date = None
    
    if filter_type == 'dia' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
        except Exception as e:
            print("EXCEPTION DIA PARSING:", e, flush=True)
    elif filter_type == 'mes' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y-%m")
            _, last_day = calendar.monthrange(start_date.year, start_date.month)
            end_date = start_date.replace(day=last_day) + timedelta(days=1)
        except Exception as e:
            print("EXCEPTION MES PARSING:", e, flush=True)
    elif filter_type == 'anual' and filter_value:
        try:
            start_date = datetime.strptime(filter_value, "%Y")
            end_date = start_date.replace(year=start_date.year + 1)
        except Exception as e:
            print("EXCEPTION ANUAL PARSING:", e, flush=True)
    elif filter_type == 'rango_fechas' and filter_value:
        try:
            parts = filter_value.split(":")
            start_date = datetime.strptime(parts[0], "%Y-%m-%d")
            end_date = datetime.strptime(parts[1], "%Y-%m-%d") + timedelta(days=1)
        except Exception as e:
            print("EXCEPTION RANGO FECHAS PARSING:", e, flush=True)
    elif filter_type == 'rango_meses' and filter_value:
        try:
            parts = filter_value.split(":")
            start_date = datetime.strptime(parts[0], "%Y-%m")
            end_month = datetime.strptime(parts[1], "%Y-%m")
            _, last_day = calendar.monthrange(end_month.year, end_month.month)
            end_date = end_month.replace(day=last_day) + timedelta(days=1)
        except Exception as e:
            print("EXCEPTION RANGO MESES PARSING:", e, flush=True)

    if start_date and end_date:
        q_asistencia = q_asistencia.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
        q_incidente = q_incidente.filter(models.Incidente.fecha_hora_reporte >= start_date, models.Incidente.fecha_hora_reporte < end_date)
        q_taller = q_taller.filter(models.Taller.created_at >= start_date, models.Taller.created_at < end_date)

    if taller_id:
        q_asistencia = q_asistencia.filter(models.Asistencia.id_taller == taller_id)
        q_incidente = q_incidente.join(models.Asistencia).filter(models.Asistencia.id_taller == taller_id)
        q_taller = q_taller.filter(models.Taller.id_taller == taller_id)

    # 1. Tiempo promedio de asignación (minutos)
    avg_asignacion = db.query(
        func.avg(
            extract('epoch', models.Asistencia.fecha_hora_asignacion) - 
            extract('epoch', models.Incidente.fecha_hora_reporte)
        )
    ).join(models.Incidente, models.Asistencia.id_incidente == models.Incidente.id_incidente)
    
    if rol != "superadmin" and id_tenant is not None:
        avg_asignacion = avg_asignacion.filter(models.Asistencia.id_tenant == id_tenant)
    if start_date and end_date:
        avg_asignacion = avg_asignacion.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
    if taller_id:
        avg_asignacion = avg_asignacion.filter(models.Asistencia.id_taller == taller_id)
    avg_asignacion_val = float(avg_asignacion.scalar() or 0.0) / 60.0

    # 2. Tiempo promedio de llegada (minutos)
    avg_llegada = q_asistencia.filter(models.Asistencia.fecha_hora_llegada_tecnico != None).with_entities(
        func.avg(
            extract('epoch', models.Asistencia.fecha_hora_llegada_tecnico) - 
            extract('epoch', models.Asistencia.fecha_hora_asignacion)
        )
    ).scalar() or 0.0
    avg_llegada_val = float(avg_llegada) / 60.0

    # 3. Incidentes por tipo
    incidentes_por_tipo_raw = q_incidente.with_entities(
        models.Incidente.tipo_problema,
        func.count(models.Incidente.id_incidente).label("count")
    ).group_by(models.Incidente.tipo_problema).all()
    
    incidentes_por_tipo = [{"tipo": i[0], "count": i[1]} for i in incidentes_por_tipo_raw]

    # 4. Talleres más eficientes
    eficiencia_talleres = db.query(
        models.Taller.razon_social,
        func.avg(
            extract('epoch', models.Asistencia.fecha_hora_finalizacion) - 
            extract('epoch', models.Asistencia.fecha_hora_asignacion)
        ).label("avg_time")
    ).join(models.Asistencia, models.Asistencia.id_taller == models.Taller.id_taller)\
     .filter(models.Asistencia.fecha_hora_finalizacion != None)
     
    if rol != "superadmin" and id_tenant is not None:
        eficiencia_talleres = eficiencia_talleres.filter(models.Taller.id_tenant == id_tenant)
    if start_date and end_date:
        eficiencia_talleres = eficiencia_talleres.filter(models.Asistencia.fecha_hora_asignacion >= start_date, models.Asistencia.fecha_hora_asignacion < end_date)
    if taller_id:
        eficiencia_talleres = eficiencia_talleres.filter(models.Taller.id_taller == taller_id)

    eficiencia_talleres = eficiencia_talleres.group_by(models.Taller.razon_social)\
        .order_by("avg_time").limit(5).all()

    talleres_eficientes = [
        {"taller": t[0], "avg_resolucion": float(t[1] or 0.0) / 60.0} 
        for t in eficiencia_talleres
    ]

    # 5. Casos cancelados
    casos_cancelados = q_incidente.filter(models.Incidente.estado_solicitud == 'Cancelado').count()

    # 6. Nivel de cumplimiento SLA (Llegada en < 30 minutos)
    total_llegadas = q_asistencia.filter(models.Asistencia.fecha_hora_llegada_tecnico != None).count()
    if total_llegadas > 0:
        cumplen_sla = q_asistencia.filter(
            models.Asistencia.fecha_hora_llegada_tecnico != None,
            (extract('epoch', models.Asistencia.fecha_hora_llegada_tecnico) - extract('epoch', models.Asistencia.fecha_hora_asignacion)) <= 1800
        ).count()
        sla_pct = (cumplen_sla / total_llegadas) * 100.0
    else:
        sla_pct = 100.0

    # 7. Heatmap / Puntos Interactivos
    zonas_raw = q_incidente.with_entities(
        models.Incidente.id_incidente,
        models.Incidente.ubicacion_latitud,
        models.Incidente.ubicacion_longitud,
        models.Incidente.tipo_problema,
        models.Incidente.estado_solicitud
    ).all()
    zonas = [
        {
            "id": z[0], 
            "lat": z[1], 
            "lng": z[2], 
            "tipo": z[3], 
            "estado": z[4]
        } for z in zonas_raw
    ]

    from sqlalchemy import extract, case, cast, Float, Date
    
    # 8. Gráfico de Barras Evolutivo (Incidentes por fecha)
    # Cast to date to group by day
    date_col = cast(models.Incidente.fecha_hora_reporte, Date)
    
    q_evol = q_incidente
    if taller_id:
        # q_incidente at base is just db.query(Incidente)
        q_evol = q_incidente.join(models.Asistencia, isouter=True).filter(models.Asistencia.id_taller == taller_id)
        
    incidentes_por_fecha_raw = q_evol.with_entities(
        date_col.label("fecha_dia"),
        func.count(models.Incidente.id_incidente).label("count")
    ).group_by(date_col).order_by(date_col).all()

    incidentes_por_fecha = [
        {"fecha": str(f[0]), "count": f[1]} 
        for f in incidentes_por_fecha_raw if f[0]
    ]

    # 9. Registros de Talleres y Conductores (Clientes) por período (Solo para Superadmin)
    registros_timeline = []
    total_talleres_reg = 0
    total_clientes_reg = 0

    if rol == "superadmin":
        q_talleres_reg = db.query(models.Taller.created_at)
        q_clientes_reg = db.query(models.Cliente.created_at)

        if start_date and end_date:
            q_talleres_reg = q_talleres_reg.filter(models.Taller.created_at >= start_date, models.Taller.created_at < end_date)
            q_clientes_reg = q_clientes_reg.filter(models.Cliente.created_at >= start_date, models.Cliente.created_at < end_date)

        talleres_reg_list = q_talleres_reg.all()
        clientes_reg_list = q_clientes_reg.all()
        
        total_talleres_reg = len(talleres_reg_list)
        total_clientes_reg = len(clientes_reg_list)

        def group_by_period(dates, period_format):
            counts = {}
            for d_tuple in dates:
                d = d_tuple[0]
                if d:
                    period = d.strftime(period_format)
                    counts[period] = counts.get(period, 0) + 1
            return counts

        if filter_type == 'dia':
            period_format = "%Y-%m-%d"
        elif filter_type == 'mes':
            period_format = "%Y-%m-%d"
        elif filter_type == 'anual':
            period_format = "%Y-%m"
        else:  # historico
            period_format = "%Y-%m"

        talleres_counts = group_by_period(talleres_reg_list, period_format)
        clientes_counts = group_by_period(clientes_reg_list, period_format)

        all_periods = []
        if filter_type == 'mes' and start_date:
            year, month = start_date.year, start_date.month
            num_days = calendar.monthrange(year, month)[1]
            for day in range(1, num_days + 1):
                all_periods.append(f"{year}-{month:02d}-{day:02d}")
        elif filter_type == 'anual' and start_date:
            year = start_date.year
            for m in range(1, 13):
                all_periods.append(f"{year}-{m:02d}")
        elif filter_type == 'dia' and start_date:
            all_periods.append(start_date.strftime("%Y-%m-%d"))
        else:
            # Historico: Generar últimos 6 meses para rellenar
            now = datetime.now()
            for i in range(5, -1, -1):
                prev_month = now - timedelta(days=i*30)
                all_periods.append(prev_month.strftime("%Y-%m"))
            # Agregar cualquier periodo con datos
            for p in list(set(talleres_counts.keys()) | set(clientes_counts.keys())):
                if p not in all_periods:
                    all_periods.append(p)
            all_periods.sort()

        for p in all_periods:
            registros_timeline.append({
                "periodo": p,
                "talleres": talleres_counts.get(p, 0),
                "clientes": clientes_counts.get(p, 0)
            })

    return {
        "avg_asignacion_minutos": float(avg_asignacion_val),
        "avg_llegada_minutos": float(avg_llegada_val),
        "incidentes_por_tipo": incidentes_por_tipo,
        "talleres_eficientes": talleres_eficientes,
        "casos_cancelados": casos_cancelados,
        "sla_cumplimiento_pct": float(sla_pct),
        "heatmap": zonas,
        "incidentes_por_fecha": incidentes_por_fecha,
        "registros_timeline": registros_timeline,
        "total_talleres_registrados": total_talleres_reg,
        "total_conductores_registrados": total_clientes_reg
    }

@router.post("/talleres/{id_taller}/aprobar")
def aprobar_taller(id_taller: int, admin_id: int = None, db: Session = Depends(get_db)):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    taller.estado_aprobacion = "Aprobado"
    taller.id_admin_aprobador = admin_id
    from utils import send_approval_email
    send_approval_email(destinatario=taller.correo, nombre_taller=taller.razon_social)
    
    # Registrar en Bitácora
    log = models.Bitacora(
        id_usuario=admin_id,
        tipo_usuario="SuperAdmin",
        accion="Aprobar Taller",
        descripcion=f"El taller {taller.razon_social} (NIT: {taller.nit}) ha sido aprobado para operar en la plataforma."
    )
    db.add(log)
    
    db.commit()
    return {"message": "Taller aprobado exitosamente."}

@router.post("/talleres/{id_taller}/rechazar")
def rechazar_taller(id_taller: int, admin_id: int = None, db: Session = Depends(get_db)):
    taller = db.query(models.Taller).filter(models.Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    taller.estado_aprobacion = "Rechazado"
    taller.id_admin_aprobador = admin_id
    
    # Registrar en Bitácora
    log = models.Bitacora(
        id_usuario=admin_id,
        tipo_usuario="SuperAdmin",
        accion="Rechazar Taller",
        descripcion=f"La solicitud del taller {taller.razon_social} (NIT: {taller.nit}) ha sido rechazada."
    )
    db.add(log)
    
    db.commit()
    return {"message": "Taller rechazado exitosamente."}

@router.get("/bitacora")
def obtener_bitacora(db: Session = Depends(get_db)):
    logs = db.query(models.Bitacora).order_by(models.Bitacora.fecha_hora.desc()).limit(50).all()
    return [
        {
            "id_log": l.id_log,
            "id_usuario": l.id_usuario,
            "tipo_usuario": l.tipo_usuario,
            "accion": l.accion,
            "descripcion": l.descripcion,
            "fecha_hora": l.fecha_hora
        } for l in logs
    ]

@router.get("/tenants")
def obtener_tenants(
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user)
):
    rol = current_user.get("role") or current_user.get("rol")
    if rol != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren permisos de Superadmin.")
        
    tenants = db.query(models.Tenant).all()
    return [
        {
            "id_tenant": t.id_tenant,
            "nombre": t.nombre,
            "subdominio_slug": t.subdominio_slug,
            "activo": t.activo,
            "created_at": t.created_at
        } for t in tenants
    ]

