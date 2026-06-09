import requests

def test_report():
    url = "http://localhost:8000/api/incidentes/reportar"
    data = {
        "id_cliente": 2,
        "id_vehiculo": 1,
        "ubicacion_latitud": -17.7833,
        "ubicacion_longitud": -63.1821,
        "descripcion_manual": "Prueba de reporte desde script"
    }
    
    try:
        response = requests.post(url, data=data)
        print("Status Code:", response.statusCode if hasattr(response, "statusCode") else response.status_code)
        print("Response Content:", response.text)
    except Exception as e:
        print("Error connecting to server:", e)

if __name__ == "__main__":
    test_report()
