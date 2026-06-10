import sys
import os

# Asegurarnos de que el script pueda importar módulos del backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
from crud import get_password_hash

def change_password(email, new_password):
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).filter(models.Admin.correo == email).first()
        if not admin:
            print(f"[ERROR] No se encontro ningun administrador con el correo: {email}")
            return False

        admin.password_hash = get_password_hash(new_password)
        db.commit()
        print(f"[SUCCESS] Contrasena para {email} actualizada exitosamente!")
        return True
    except Exception as e:
        print(f"[ERROR] Error al actualizar la contrasena: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python change_admin_password.py <nueva_contraseña> [correo]")
        sys.exit(1)
        
    new_password = sys.argv[1]
    email = sys.argv[2] if len(sys.argv) > 2 else "asiscar.asistente@gmail.com"
        
    change_password(email, new_password)
