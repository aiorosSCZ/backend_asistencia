import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:Acnologia123.@localhost/emergencias_vehiculares?client_encoding=utf8"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database to run migrations...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # SQL Queries to add columns
    # We use direct raw SQL with ALTER TABLE
    print("Running ALTER TABLE queries...")
    try:
        conn.execute(text("ALTER TABLE asistencias ADD COLUMN IF NOT EXISTS monto_adicional NUMERIC(10, 2) DEFAULT 0.00;"))
        conn.execute(text("ALTER TABLE asistencias ADD COLUMN IF NOT EXISTS motivo_adicional TEXT;"))
        
        # Limpiar emojis en las tablas incidentes y servicios
        print("Limpiando emojis de incidentes.tipo_problema...")
        conn.execute(text("UPDATE incidentes SET tipo_problema = regexp_replace(tipo_problema, '^[^a-zA-Z0-9ÁÉÍÓÚáéíóúÑñ ]+\\s*', '');"))
        print("Limpiando emojis de servicios.nombre_servicio...")
        conn.execute(text("UPDATE servicios SET nombre_servicio = regexp_replace(nombre_servicio, '^[^a-zA-Z0-9ÁÉÍÓÚáéíóúÑñ ]+\\s*', '');"))
        
        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
