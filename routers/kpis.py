from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import get_db
import models
import dependencies
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import calendar

router = APIRouter()

def parse_date_range(
    tipo_filtro: str,
    fecha: Optional[str] = None,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    mes_inicio: Optional[int] = None,
    mes_fin: Optional[int] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
) -> tuple[datetime, datetime]:
    now = datetime.now()
    
    # Valores por defecto
    start_date = datetime(now.year, now.month, now.day, 0, 0, 0)
    end_date = datetime(now.year, now.month, now.day, 23, 59, 59)
    
    if tipo_filtro == "hoy":
        pass  # Ya están configurados por defecto
        
    elif tipo_filtro == "dia_especifico" and fecha:
        try:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            start_date = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
            end_date = datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
            
    elif tipo_filtro == "mes" and mes and anio:
        last_day = calendar.monthrange(anio, mes)[1]
        start_date = datetime(anio, mes, 1, 0, 0, 0)
        end_date = datetime(anio, mes, last_day, 23, 59, 59)
        
    elif tipo_filtro == "rango_meses" and mes_inicio and mes_fin and anio:
        last_day = calendar.monthrange(anio, mes_fin)[1]
        start_date = datetime(anio, mes_inicio, 1, 0, 0, 0)
        end_date = datetime(anio, mes_fin, last_day, 23, 59, 59)
        
    elif tipo_filtro == "anio" and anio:
        start_date = datetime(anio, 1, 1, 0, 0, 0)
        end_date = datetime(anio, 12, 31, 23, 59, 59)
        
    elif tipo_filtro == "rango_fechas" and fecha_inicio and fecha_fin:
        try:
            dt_in = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            dt_fn = datetime.strptime(fecha_fin, "%Y-%m-%d")
            start_date = datetime(dt_in.year, dt_in.month, dt_in.day, 0, 0, 0)
            end_date = datetime(dt_fn.year, dt_fn.month, dt_fn.day, 23, 59, 59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de rango de fechas inválido. Use YYYY-MM-DD")
            
    return start_date, end_date

@router.get("/")
def get_kpis(
    tipo_filtro: str = "hoy",
    fecha: Optional[str] = None,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    mes_inicio: Optional[int] = None,
    mes_fin: Optional[int] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(dependencies.get_current_user),
    id_tenant: Optional[int] = Depends(dependencies.get_current_tenant_id)
):
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    user_id = current_user.get("user_id")

    # Determinar filtros de multitenancy
    taller_id = None
    if rol == "taller":
        taller_id = user_id
    elif rol == "superadmin":
        # En superadmin no aplicamos filtros de tenant salvo que se provea en headers/params (por defecto no)
        pass
    elif rol == "admin":
        # Admin es del tenant, puede ver todos los talleres de ese tenant
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para acceder a métricas de taller"
        )

    # 1. Obtener rango de fechas
    start_date, end_date = parse_date_range(
        tipo_filtro, fecha, mes, anio, mes_inicio, mes_fin, fecha_inicio, fecha_fin
    )

    # 2. Consultas Base
    # Filtrado por Taller y Tenant en Asistencia
    asis_filters = [
        models.Asistencia.fecha_hora_asignacion >= start_date,
        models.Asistencia.fecha_hora_asignacion <= end_date
    ]
    if taller_id:
        asis_filters.append(models.Asistencia.id_taller == taller_id)
    if id_tenant:
        asis_filters.append(models.Asistencia.id_tenant == id_tenant)

    # Incidentes asociados a las asistencias de este taller en este rango
    incident_query = db.query(models.Incidente).join(
        models.Asistencia, models.Incidente.id_incidente == models.Asistencia.id_incidente
    ).filter(*asis_filters)

    incidentes = incident_query.all()
    total_incidentes = len(incidentes)

    # Conteo por estados
    incidentes_completados = sum(1 for inc in incidentes if inc.estado_solicitud in ["Completado", "Atendido"])
    incidentes_cancelados = sum(1 for inc in incidentes if inc.estado_solicitud in ["Cancelado", "Rechazado"])
    
    tasa_exito = round((incidentes_completados / total_incidentes * 100), 2) if total_incidentes > 0 else 0.0

    # 3. Ingresos totales (Pagos y PagoReparacion)
    # Sumar pagos normales
    pago_query = db.query(func.sum(models.Pago.monto_total_cliente)).join(
        models.Asistencia, models.Pago.id_asistencia == models.Asistencia.id_asistencia
    ).filter(
        and_(
            models.Pago.estado_transaccion.in_(["Aprobado", "Completado"]),
            *asis_filters
        )
    )
    ingresos_asistencia = pago_query.scalar() or 0.0

    # Sumar pagos de taller físico (PagoReparacion)
    pago_rep_query = db.query(func.sum(models.PagoReparacion.monto_total_cliente)).join(
        models.OrdenTrabajo, models.PagoReparacion.id_orden == models.OrdenTrabajo.id_orden
    ).join(
        models.Incidente, models.OrdenTrabajo.id_incidente_origen == models.Incidente.id_incidente
    ).join(
        models.Asistencia, models.Incidente.id_incidente == models.Asistencia.id_incidente
    ).filter(
        and_(
            models.PagoReparacion.estado_transaccion == "Completado",
            *asis_filters
        )
    )
    ingresos_reparacion = pago_rep_query.scalar() or 0.0
    
    ingresos_totales = float(ingresos_asistencia) + float(ingresos_reparacion)

    # 4. Productividad de Técnicos
    # Ranking de técnicos
    tecnico_ranking_query = db.query(
        models.Tecnico.id_tecnico,
        models.Tecnico.nombres,
        models.Tecnico.apellidos,
        func.count(models.Asistencia.id_asistencia).label("trabajos_completados")
    ).join(
        models.Asistencia, models.Tecnico.id_tecnico == models.Asistencia.id_tecnico
    ).join(
        models.Incidente, models.Asistencia.id_incidente == models.Incidente.id_incidente
    ).filter(
        and_(
            models.Incidente.estado_solicitud == "Completado",
            *asis_filters
        )
    ).group_by(
        models.Tecnico.id_tecnico,
        models.Tecnico.nombres,
        models.Tecnico.apellidos
    ).order_by(
        func.count(models.Asistencia.id_asistencia).desc()
    )
    
    tecnico_ranking = []
    for r in tecnico_ranking_query.all():
        # Obtener valoración promedio del técnico
        val_promedio = db.query(func.avg(models.Valoracion.puntuacion)).join(
            models.Asistencia, models.Valoracion.id_asistencia == models.Asistencia.id_asistencia
        ).filter(
            models.Asistencia.id_tecnico == r.id_tecnico
        ).scalar() or 5.0
        
        tecnico_ranking.append({
            "id_tecnico": r.id_tecnico,
            "nombre": f"{r.nombres} {r.apellidos}",
            "completados": r.trabajos_completados,
            "calificacion": round(float(val_promedio), 1)
        })

    # 5. Distribución de Estados
    estados_dist = {}
    for inc in incidentes:
        est = inc.estado_solicitud
        estados_dist[est] = estados_dist.get(est, 0) + 1

    # 6. Distribución de Tipo de Problemas
    problemas_dist = {}
    for inc in incidentes:
        prob = inc.tipo_problema
        problemas_dist[prob] = problemas_dist.get(prob, 0) + 1

    # 7. Tendencia Temporal
    # Si el filtro es "mes" o "rango_fechas" (menor a 60 días), agrupamos por día.
    # Si es "anio" o "rango_meses", agrupamos por mes.
    diferencia_dias = (end_date - start_date).days
    tendencia = []
    
    if diferencia_dias <= 62:
        # Agrupar por día
        tendencia_query = db.query(
            func.date(models.Asistencia.fecha_hora_asignacion).label("periodo"),
            func.count(models.Asistencia.id_asistencia).label("conteo")
        ).filter(*asis_filters).group_by(
            func.date(models.Asistencia.fecha_hora_asignacion)
        ).order_by(
            func.date(models.Asistencia.fecha_hora_asignacion)
        ).all()
        
        for t in tendencia_query:
            # Calcular ingresos de ese día específico
            start_day = datetime(t.periodo.year, t.periodo.month, t.periodo.day, 0, 0, 0)
            end_day = datetime(t.periodo.year, t.periodo.month, t.periodo.day, 23, 59, 59)
            
            day_filters = [
                models.Asistencia.fecha_hora_asignacion >= start_day,
                models.Asistencia.fecha_hora_asignacion <= end_day
            ]
            if taller_id:
                day_filters.append(models.Asistencia.id_taller == taller_id)
            if id_tenant:
                day_filters.append(models.Asistencia.id_tenant == id_tenant)

            ing_asis = db.query(func.sum(models.Pago.monto_total_cliente)).join(
                models.Asistencia, models.Pago.id_asistencia == models.Asistencia.id_asistencia
            ).filter(and_(models.Pago.estado_transaccion.in_(["Aprobado", "Completado"]), *day_filters)).scalar() or 0.0

            ing_rep = db.query(func.sum(models.PagoReparacion.monto_total_cliente)).join(
                models.OrdenTrabajo, models.PagoReparacion.id_orden == models.OrdenTrabajo.id_orden
            ).join(
                models.Incidente, models.OrdenTrabajo.id_incidente_origen == models.Incidente.id_incidente
            ).join(
                models.Asistencia, models.Incidente.id_incidente == models.Asistencia.id_incidente
            ).filter(and_(models.PagoReparacion.estado_transaccion == "Completado", *day_filters)).scalar() or 0.0

            tendencia.append({
                "periodo": t.periodo.strftime("%d %b"),
                "incidentes": t.conteo,
                "ingresos": float(ing_asis) + float(ing_rep)
            })
    else:
        # Agrupar por mes
        # Para sqlite/postgresql/mysql compatible, usaremos extracción de año y mes
        tendencia_query = db.query(
            func.strftime("%Y-%m", models.Asistencia.fecha_hora_asignacion).label("periodo"),
            func.count(models.Asistencia.id_asistencia).label("conteo")
        ).filter(*asis_filters).group_by(
            func.strftime("%Y-%m", models.Asistencia.fecha_hora_asignacion)
        ).order_by(
            func.strftime("%Y-%m", models.Asistencia.fecha_hora_asignacion)
        ).all()

        for t in tendencia_query:
            y, m = map(int, t.periodo.split("-"))
            last_d = calendar.monthrange(y, m)[1]
            start_m = datetime(y, m, 1, 0, 0, 0)
            end_m = datetime(y, m, last_d, 23, 59, 59)
            
            month_filters = [
                models.Asistencia.fecha_hora_asignacion >= start_m,
                models.Asistencia.fecha_hora_asignacion <= end_m
            ]
            if taller_id:
                month_filters.append(models.Asistencia.id_taller == taller_id)
            if id_tenant:
                month_filters.append(models.Asistencia.id_tenant == id_tenant)

            ing_asis = db.query(func.sum(models.Pago.monto_total_cliente)).join(
                models.Asistencia, models.Pago.id_asistencia == models.Asistencia.id_asistencia
            ).filter(and_(models.Pago.estado_transaccion.in_(["Aprobado", "Completado"]), *month_filters)).scalar() or 0.0

            ing_rep = db.query(func.sum(models.PagoReparacion.monto_total_cliente)).join(
                models.OrdenTrabajo, models.PagoReparacion.id_orden == models.OrdenTrabajo.id_orden
            ).join(
                models.Incidente, models.OrdenTrabajo.id_incidente_origen == models.Incidente.id_incidente
            ).join(
                models.Asistencia, models.Incidente.id_incidente == models.Asistencia.id_incidente
            ).filter(and_(models.PagoReparacion.estado_transaccion == "Completado", *month_filters)).scalar() or 0.0

            meses_nombres = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            tendencia.append({
                "periodo": f"{meses_nombres[m]} {y}",
                "incidentes": t.conteo,
                "ingresos": float(ing_asis) + float(ing_rep)
            })

    # 8. Puntos para Mapa de Calor
    mapa_calor = [
        {
            "id_incidente": inc.id_incidente,
            "lat": inc.ubicacion_latitud,
            "lng": inc.ubicacion_longitud,
            "tipo_problema": inc.tipo_problema,
            "estado": inc.estado_solicitud,
            "fecha": inc.fecha_hora_reporte.strftime("%Y-%m-%d %H:%M") if inc.fecha_hora_reporte else "N/A",
            "cliente": f"{inc.cliente.nombres} {inc.cliente.apellidos}" if inc.cliente else "Conductor en Ruta"
        }
        for inc in incidentes if inc.ubicacion_latitud and inc.ubicacion_longitud
    ]

    return {
        "resumen": {
            "ingresos_totales": ingresos_totales,
            "total_incidentes": total_incidentes,
            "incidentes_completados": incidentes_completados,
            "incidentes_cancelados": incidentes_cancelados,
            "tasa_exito": tasa_exito
        },
        "tecnicos": tecnico_ranking,
        "estados": estados_dist,
        "problemas": problemas_dist,
        "tendencia": tendencia,
        "mapa_calor": mapa_calor
    }
