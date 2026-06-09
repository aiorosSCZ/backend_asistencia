import os
import sys
import json

# Agregar el directorio backend al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService

audio_file = "uploads/audio_c799e741-dc5c-421d-9ae7-c8ae016f4b9d.m4a"
foto_file = None
descripcion = ""

try:
    result = AIService.analizar_incidente(audio_file, foto_file, descripcion)
    with open("scratch/ai_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print("Éxito: El resultado se guardó en scratch/ai_output.json")
except Exception as e:
    import traceback
    with open("scratch/ai_error.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    print("Error: Se produjo una excepción. El traceback se guardó en scratch/ai_error.txt")
