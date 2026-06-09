import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import io
from datetime import datetime

import dependencies
from backup_service.backups import generate_backup, save_automatic_backup

router = APIRouter(
    prefix="/admin/backups",
    tags=["Backups Administration"]
)

# Directorio de almacenamiento de backups automáticos
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups_historial")

def verify_superadmin(current_user: dict = Depends(dependencies.get_current_user)):
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    if rol != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: Solo el Superadministrador puede gestionar las copias de seguridad."
        )
    return current_user

@router.post("/manual")
def trigger_manual_backup(current_user: dict = Depends(verify_superadmin)):
    """Genera una copia de seguridad en caliente y la descarga inmediatamente."""
    try:
        content, ext = generate_backup()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo generar el contenido del backup."
            )
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_manual_{timestamp}.{ext}"
        
        # Stream de texto en memoria
        buffer = io.BytesIO(content.encode("utf-8"))
        
        media_type = "application/sql" if ext == "sql" else "application/json"
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar backup manual: {str(e)}"
        )

@router.get("/historial")
def get_backups_history(current_user: dict = Depends(verify_superadmin)):
    """Lista las últimas copias de seguridad automáticas almacenadas localmente en el servidor."""
    if not os.path.exists(BACKUP_DIR):
        return []
        
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith("backup_"):
            path = os.path.join(BACKUP_DIR, f)
            stat = os.stat(path)
            backups.append({
                "filename": f,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
            
    # Ordenar por fecha de creación (descendente)
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups

@router.get("/descargar/{filename}")
def download_historical_backup(filename: str, current_user: dict = Depends(verify_superadmin)):
    """Descarga un backup automático específico del historial."""
    filepath = os.path.join(BACKUP_DIR, filename)
    # Validar path traversal
    if not os.path.abspath(filepath).startswith(os.path.abspath(BACKUP_DIR)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre de archivo inválido")
        
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup no encontrado")
        
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.post("/automatico-test")
def trigger_automatic_backup_test(current_user: dict = Depends(verify_superadmin)):
    """Fuerza la ejecución de la tarea del backup automático de forma manual para pruebas."""
    filename = save_automatic_backup()
    if not filename:
        raise HTTPException(status_code=500, detail="Fallo la prueba del backup automático")
    return {"status": "success", "filename": filename}
