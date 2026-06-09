import requests

def test_endpoints():
    base_url = "http://localhost:8000"
    
    # 1. Login
    print("Logging in as SuperAdmin...")
    login_url = f"{base_url}/api/admin/login"
    login_payload = {
        "correo": "asiscar.asistente@gmail.com",
        "password": "AsiscarAsistente2026"
    }
    
    try:
        r_login = requests.post(login_url, json=login_payload)
        r_login.raise_for_status()
        token = r_login.json().get("access_token")
        print("Login successful. Token obtained.")
    except Exception as e:
        print(f"Error logging in: {e}")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2. Test metrics endpoint (to check lat and lng of workshops)
    print("\nTesting /api/admin/metrics...")
    try:
        r_metrics = requests.get(f"{base_url}/api/admin/metrics", headers=headers)
        r_metrics.raise_for_status()
        metrics_data = r_metrics.json()
        print("Metrics API responded successfully.")
        
        talleres = metrics_data.get("talleres", [])
        if talleres:
            taller = talleres[0]
            print(f"Sample Workshop: {taller.get('razon_social')}")
            print(f"  Coordinates: Lat={taller.get('lat')}, Lng={taller.get('lng')}")
        else:
            print("No workshops found.")
    except Exception as e:
        print(f"Error calling /api/admin/metrics: {e}")

    # 3. Test kpis endpoint (to check registrations timeline)
    print("\nTesting /api/admin/kpis...")
    try:
        r_kpis = requests.get(f"{base_url}/api/admin/kpis?filter_type=historico", headers=headers)
        r_kpis.raise_for_status()
        kpis_data = r_kpis.json()
        print("KPIs API responded successfully.")
        
        timeline = kpis_data.get("registros_timeline", [])
        print(f"Total entries in registrations timeline: {len(timeline)}")
        if timeline:
            print("Sample Timeline entries:")
            for entry in timeline[:5]:
                print(f"  Period: {entry.get('periodo')} | Workshops: {entry.get('talleres')} | Clients: {entry.get('clientes')}")
        
        print(f"Total workshops registered in period: {kpis_data.get('total_talleres_registrados')}")
        print(f"Total drivers registered in period: {kpis_data.get('total_conductores_registrados')}")
        
    except Exception as e:
        print(f"Error calling /api/admin/kpis: {e}")

if __name__ == "__main__":
    test_endpoints()
