import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:Acnologia123.@localhost/emergencias_vehiculares?client_encoding=utf8"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database to alter column type...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE incidentes ALTER COLUMN estado_solicitud TYPE VARCHAR(50);"))
        conn.commit()
        print("Successfully altered incidentes.estado_solicitud to VARCHAR(50)!")
    except Exception as e:
        print(f"Error altering column: {e}")
