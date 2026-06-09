import os
import subprocess
import urllib.parse as urlparse
import json
from datetime import datetime
from database import SQLALCHEMY_DATABASE_URL, engine
from sqlalchemy import MetaData

def parse_db_url(url_str):
    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql://", 1)
    
    parsed = urlparse.urlparse(url_str)
    return {
        "username": parsed.username,
        "password": parsed.password,
        "hostname": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path[1:] if parsed.path else ""
    }

def get_pg_dump_backup():
    db_info = parse_db_url(SQLALCHEMY_DATABASE_URL)
    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]
    
    cmd = [
        "pg_dump",
        "-h", db_info["hostname"],
        "-p", str(db_info["port"]),
        "-U", db_info["username"],
        "-F", "p",
        db_info["database"]
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
        if result.returncode == 0:
            return result.stdout, "sql"
        else:
            print(f"Error en pg_dump (Código {result.returncode}): {result.stderr}")
            return None, None
    except FileNotFoundError:
        print("pg_dump no está instalado. Se usará fallback JSON.")
        return None, None
    except Exception as e:
        print(f"Excepción al ejecutar pg_dump: {e}")
        return None, None

def get_json_backup():
    metadata = MetaData()
    metadata.reflect(bind=engine)
    backup_data = {}
    
    with engine.connect() as conn:
        for table_name, table in metadata.tables.items():
            try:
                result = conn.execute(table.select())
                rows = [dict(row._mapping) for row in result]
                
                for r in rows:
                    for k, v in r.items():
                        if hasattr(v, 'isoformat'):
                            r[k] = v.isoformat()
                        elif isinstance(v, (bytes, bytearray)):
                            r[k] = v.hex()
                        elif hasattr(v, '__str__') and not isinstance(v, (int, float, str, bool, type(None))):
                            r[k] = str(v)
                backup_data[table_name] = rows
            except Exception as table_err:
                print(f"Error respaldando tabla {table_name}: {table_err}")
                backup_data[table_name] = []
                
    return json.dumps(backup_data, indent=2, ensure_ascii=False), "json"

def generate_backup():
    content, ext = get_pg_dump_backup()
    if content:
        return content, ext
    return get_json_backup()

def save_automatic_backup():
    try:
        content, ext = generate_backup()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.{ext}"
        
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups_historial")
        os.makedirs(backup_dir, exist_ok=True)
        
        filepath = os.path.join(backup_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Backup automatico guardado exitosamente: {filename}")
        
        # Limpieza de backups antiguos (mantener últimos 7)
        all_backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("backup_")],
            key=os.path.getmtime
        )
        while len(all_backups) > 7:
            oldest = all_backups.pop(0)
            os.remove(oldest)
            print(f"Eliminado backup antiguo: {os.path.basename(oldest)}")
            
        return filename
    except Exception as e:
        print(f"Error al guardar backup automatico: {e}")
        return None
