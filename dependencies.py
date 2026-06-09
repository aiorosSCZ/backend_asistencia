from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import utils
from typing import Optional

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = utils.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_current_tenant_id(current_user: dict = Depends(get_current_user)) -> Optional[int]:
    rol = (current_user.get("role") or current_user.get("rol") or "").lower()
    id_tenant = current_user.get("id_tenant")

    # Rol SuperAdmin explícito: no tiene id_tenant
    if rol == "superadmin":
        return None

    # Roles administrativos/operativos vinculados a un taller o tenant
    if rol in ["admin", "taller", "tecnico"]:
        if id_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: id_tenant es requerido para este rol administrativo u operativo"
            )
        return id_tenant

    # Para clientes u otros roles no vinculados a un tenant, permitimos None (será global)
    return id_tenant
