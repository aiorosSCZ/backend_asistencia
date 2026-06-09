"""
Script para actualizar incidentes con tipo_problema='Buscando...'
a 'No clasificado'. NO borra ningún registro.
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="emergencias_vehiculares",
    user="postgres",
    password="1234"
)

cur = conn.cursor()

# Primero veamos cuántos hay
cur.execute("SELECT COUNT(*) FROM incidentes WHERE tipo_problema = 'Buscando...'")
count = cur.fetchone()[0]
print(f"Incidentes con tipo_problema='Buscando...': {count}")

if count > 0:
    cur.execute("UPDATE incidentes SET tipo_problema = 'No clasificado' WHERE tipo_problema = 'Buscando...'")
    conn.commit()
    print(f"✅ {count} registro(s) actualizado(s) a 'No clasificado'.")
else:
    print("No hay registros que actualizar.")

cur.close()
conn.close()
