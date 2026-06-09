import os
import sys

# Agregar el directorio backend al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService

audio_file = "uploads/audio_c799e741-dc5c-421d-9ae7-c8ae016f4b9d.m4a"
foto_file = None
descripcion = ""

print(f"Probando AIService con:")
print(f"- Audio: {audio_file} (existe: {os.path.exists(audio_file)})")
print(f"- Foto: {foto_file}")
print(f"- Descripción: '{descripcion}'")

try:
    result = AIService.analizar_incidente(audio_file, foto_file, descripcion)
    print("\n--- Resultado de la IA ---")
    print(result)
except Exception as e:
    import traceback
    print("\n--- Error Ejecutando AIService ---")
    traceback.print_exc()
