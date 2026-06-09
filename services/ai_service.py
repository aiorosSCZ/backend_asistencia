import os
import time
from typing import Dict, Any, Literal
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(override=True)

# Cargar la API Key desde el entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configurar el cliente de Google GenAI
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 10})

# Esquema de respuesta estructurado para Gemini
class DiagnosticoSchema(BaseModel):
    categoria: Literal[
        "Falla Eléctrica y Electrónica",
        "Frenos y Suspensión",
        "Combustible o Carga de Emergencia",
        "Cerrajería Automotriz",
        "Remolque y Grúa",
        "Mecánica de Motor",
        "Sistema de Enfriamiento",
        "Chapería y Pintura",
        "Paso de Corriente (Batería)",
        "Auxilio de Llanta Pinchada",
        "Aire Acondicionado y Calefacción",
        "Transmisión y Embrague",
        "Alineación y Balanceo",
        "Inspección Técnica y Diagnóstico",
        "Lavado y Estética Automotriz",
        "Vehículos Eléctricos e Híbridos"
    ] = Field(description="Categoría del problema que coincida exactamente con las opciones del catálogo.")
    urgencia: Literal["Alta", "Media", "Baja"] = Field(description="Nivel de urgencia del incidente.")
    diagnostico_ia: str = Field(description="Diagnóstico técnico breve (máx 2 oraciones) para el mecánico.")
    herramientas_sugeridas: str = Field(description="Herramientas recomendadas para que el técnico las lleve en su maletín, separadas por comas.")
    diagnostico_cliente: str = Field(description="Mensaje tranquilizador de Asiscar para el conductor, indicando precauciones básicas de seguridad (luces intermitentes, posicionamiento, etc.). Máx 2 oraciones.")
    especialidad_requerida: str = Field(description="Especialidad recomendada para el técnico de auxilio.")

class AIService:
    @staticmethod
    def analizar_incidente(audio_path: str, foto_path: str, descripcion_texto: str) -> Dict[str, Any]:
        """
        Envía los datos multimodales (Audio, Foto, Texto) a Gemini para 
        determinar la categoría del problema y nivel de urgencia de manera estructurada.
        """
        if not GEMINI_API_KEY or not client:
            # Fallback simulado por si no hay API Key configurada todavía
            return {
                "categoria": "Falla Eléctrica y Electrónica",
                "urgencia": "Media",
                "diagnostico_ia": "Simulado: Parece un problema con el sistema de arranque o batería. Se requiere revisión física y herramientas de diagnóstico eléctrico.",
                "diagnostico_cliente": "Asiscar ha recibido tu reporte. Por favor mantén la calma, enciende tus luces de parqueo y un técnico irá en camino a revisarlo.",
                "especialidad_requerida": "Electricista Automotriz"
            }
        
        # Preparar los contenidos para el modelo
        contents = []
        if descripcion_texto:
            contents.append(f"Texto o transcripción del conductor: {descripcion_texto}")
        else:
            contents.append("El conductor no especificó texto descriptivo.")

        # Cargar Foto si existe
        if foto_path and os.path.exists(foto_path):
            try:
                import PIL.Image
                img = PIL.Image.open(foto_path)
                contents.append(img)
            except Exception as img_err:
                print(f"Error cargando imagen para la IA: {img_err}")
                
        # Cargar Audio si existe
        if audio_path and os.path.exists(audio_path):
            try:
                audio_file = client.files.upload(file=audio_path)
                contents.append(audio_file)
            except Exception as audio_err:
                print(f"Error subiendo audio para la IA: {audio_err}")

        # Intentar llamada a la API con reintentos y exponencial backoff
        max_retries = 3
        backoff = 2.0
        
        try:
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=DiagnosticoSchema,
                            system_instruction=(
                                "Eres la Inteligencia Artificial oficial de Asiscar, una plataforma inteligente de auxilio vial y asistencia técnica. "
                                "Tu tarea es analizar los datos de la emergencia (audio, foto, texto) y proporcionar un veredicto estructurado. "
                                "Reglas para 'urgencia':\n"
                                "- Alta: Riesgo inmediato o peligro físico (fuegos, falla total de frenos en marcha).\n"
                                "- Media: Auto varado sin peligro físico inmediato (batería descargada, llanta pinchada).\n"
                                "- Baja: Problema mecánico menor que permite conducir (aire acondicionado inactivo, ruidos leves).\n\n"
                                "Reglas de síntesis:\n"
                                "1. Unifica los datos recibidos (texto, imagen, audio). Si el texto describe un problema y la foto muestra la causa, "
                                "conéctalos en el diagnóstico técnico.\n"
                                "2. Selecciona la 'categoria' estrictamente de las opciones del catálogo proporcionadas en el esquema."
                            )
                        )
                    )
                    
                    import json
                    result = json.loads(response.text)
                    
                    # Formatear el diagnóstico para el mecánico agregando herramientas recomendadas
                    if result.get("herramientas_sugeridas") and result.get("diagnostico_ia"):
                        result["diagnostico_ia"] = f"{result['diagnostico_ia']}\n\nHerramientas sugeridas: {result['herramientas_sugeridas']}."
                        
                    return result
                    
                except Exception as e:
                    print(f"Intento {attempt + 1} fallido de la API de Gemini: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(backoff ** attempt)
                        continue
                    else:
                        # En el último intento, lanzar la excepción para ir al fallback
                        raise e
        except Exception as fallback_trigger_err:
            print(f"[FALLBACK] Iniciando fallback debido a fallos en la API de Gemini: {fallback_trigger_err}")
                    
        # Fallback de seguridad en caso de fallo crítico de comunicación (sin propagar el error crudo al usuario)
        try:
            desc_lower = (descripcion_texto or "").lower()
            if "llanta" in desc_lower or "pinch" in desc_lower or "rueda" in desc_lower:
                fallback_cat = "Auxilio de Llanta Pinchada"
                fallback_esp = "Técnico en Suspensión y Neumáticos"
            elif "bateria" in desc_lower or "arranc" in desc_lower or "corriente" in desc_lower:
                fallback_cat = "Paso de Corriente (Batería)"
                fallback_esp = "Electricista Automotriz"
            elif "grua" in desc_lower or "remolqu" in desc_lower or "choqu" in desc_lower:
                fallback_cat = "Remolque y Grúa"
                fallback_esp = "Operador de Grúas y Rescate"
            else:
                fallback_cat = "Inspección Técnica y Diagnóstico"
                fallback_esp = "Mecánico de Auxilio Rápido"
                
            return {
                "categoria": fallback_cat,
                "urgencia": "Media",
                "diagnostico_ia": "Servicio de auxilio solicitado en ruta. Se requiere inspección física directa debido a una interrupción temporal del asistente automatizado.",
                "diagnostico_cliente": "Asiscar ha recibido tu reporte de auxilio vial. Por favor mantén la calma, enciende las luces intermitentes de tu vehículo y espera a salvo. Un técnico va en camino.",
                "especialidad_requerida": fallback_esp
            }
        except Exception as fallback_err:
            print(f"Error en fallback secundario: {fallback_err}")
            return {
                "categoria": "Inspección Técnica y Diagnóstico",
                "urgencia": "Media",
                "diagnostico_ia": "Servicio en ruta solicitado. Inspeccionar fallas generales.",
                "diagnostico_cliente": "Asiscar ha recibido tu reporte de auxilio vial. Por favor mantén la calma, un técnico va en camino.",
                "especialidad_requerida": "Mecánico de Auxilio Rápido"
            }
