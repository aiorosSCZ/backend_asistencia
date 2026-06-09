import requests
import json

def run_test():
    base_url = "http://localhost:8000"
    
    # login
    login_payload = {
        "correo": "asiscar.asistente@gmail.com",
        "password": "123456789"
    }
    r = requests.post(f"{base_url}/api/admin/login", json=login_payload)
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== LIVE ENDPOINT RESPONSE ===")
    r_kpis_mes = requests.get(f"{base_url}/api/admin/kpis?filter_type=mes&filter_value=2026-06", headers=headers)
    k_mes = r_kpis_mes.json()
    print(json.dumps(k_mes, indent=2))

run_test()









