from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from database import engine
import models
import os
from pathlib import Path
import mimetypes

models.Base.metadata.create_all(bind=engine)

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="API - Plataforma Inteligente de Emergencias Vehiculares",
    description="Backend para la gestión de incidentes vehiculares, talleres y técnicos",
    version="1.0.0"
)

def send_bytes_range_requests(file_path: Path, start: int, end: int, chunk_size: int = 1024 * 64):
    """Retorna fragmentos del archivo en el rango de bytes solicitado."""
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data

@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str, request: Request):
    file_path = Path("uploads") / filename
    
    # Prevenir Path Traversal
    abs_uploads = Path("uploads").resolve()
    abs_file = file_path.resolve()
    if not str(abs_file).startswith(str(abs_uploads)):
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Identificar tipo de medio
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Forzar tipo de audio correcto para archivos m4a grabados por la app móvil
    if filename.endswith(".m4a") and mime_type == "application/octet-stream":
        mime_type = "audio/mp4"

    is_media = mime_type.startswith("audio/") or mime_type.startswith("video/") or filename.endswith(".m4a")
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not is_media or not range_header:
        return FileResponse(file_path, media_type=mime_type, headers={"Accept-Ranges": "bytes"})

    try:
        # Extraer rango bytes: bytes=start-end
        range_value = range_header.strip().replace("bytes=", "")
        range_match = range_value.split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cabecera Range Inválida")

    if start >= file_size or end >= file_size or start > end:
        return Response(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": mime_type,
    }

    return StreamingResponse(
        send_bytes_range_requests(file_path, start, end),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
    )

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configuración de CORS para permitir peticiones desde Flutter y Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, id_taller: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[id_taller] = websocket

    def disconnect(self, id_taller: int):
        if id_taller in self.active_connections:
            del self.active_connections[id_taller]

    async def send_personal_message(self, message: dict, id_taller: int):
        print(f"[INFO] Intentando enviar alerta al taller ID {id_taller}", flush=True)
        if id_taller in self.active_connections:
            try:
                await self.active_connections[id_taller].send_json(message)
                print(f"[SUCCESS] Alerta enviada con éxito al taller ID {id_taller}", flush=True)
            except Exception as e:
                print(f"[ERROR] Falló envío al taller ID {id_taller}: {e}", flush=True)
                self.disconnect(id_taller)
        else:
            print(f"[WARNING] El taller ID {id_taller} NO está conectado por WebSocket. Conexiones activas: {list(self.active_connections.keys())}", flush=True)

manager = ConnectionManager()

@app.websocket("/ws/talleres/{id_taller}")
async def websocket_endpoint(websocket: WebSocket, id_taller: int):
    await manager.connect(id_taller, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(id_taller)

@app.get("/")
def read_root():
    return {
        "status": "up",
        "message": "Bienvenido a la API de Plataforma Inteligente de Emergencias Vehiculares"
    }

from routers import clientes, talleres, incidentes, pagos, admin, auth, reparaciones, admin_backups, kpis

app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(talleres.router, prefix="/api/talleres", tags=["Talleres"])
app.include_router(incidentes.router, prefix="/api/incidentes", tags=["Incidentes"])
app.include_router(pagos.router)
app.include_router(admin.router)
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(reparaciones.router, prefix="/api/reparaciones", tags=["Reparaciones en Taller"])
app.include_router(admin_backups.router, prefix="/api", tags=["Copias de Seguridad"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["KPIs"])

import threading
import time
import datetime
from backup_service.backups import save_automatic_backup

def run_backup_scheduler():
    # Esperar 15 segundos para no sobrecargar el inicio del servidor
    time.sleep(15)
    print("⏰ Planificador de copias de seguridad iniciado. Ejecutando primer backup al arrancar...", flush=True)
    save_automatic_backup()
    
    while True:
        # Calcular los segundos restantes para las 2:00 AM
        now = datetime.datetime.now()
        target = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        
        print(f"⏰ Siguiente copia de seguridad programada para {target}. Durmiendo por {sleep_seconds:.1f} segundos...", flush=True)
        time.sleep(sleep_seconds)
        
        print("⏰ Ejecutando copia de seguridad diaria (2:00 AM)...", flush=True)
        save_automatic_backup()

@app.on_event("startup")
def startup_event():
    # Iniciar la tarea programada en un hilo secundario
    threading.Thread(target=run_backup_scheduler, daemon=True).start()

