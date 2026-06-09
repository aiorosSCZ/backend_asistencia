with open(r'c:\app_asistencia_vehicular_tenant\app-cliente\lib\pages\tracking_page.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Por Pagar' in line or 'Ingresado a Taller' in line or 'checkout' in line:
        print(f"{i+1}: {line.strip()}")
