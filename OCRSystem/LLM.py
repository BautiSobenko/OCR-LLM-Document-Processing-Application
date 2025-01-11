from groq import Groq
import os
import json
import time

class LLM:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def correctJson(self, ocr_json_str):
        # Iniciamos el contador
        start_time = time.perf_counter()

        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages = [
                {
                    "role": "user",
                    "content": f"""Corrige exclusivamente el siguiente JSON y devuelve **solo** el JSON final, sin texto adicional ni explicaciones:

                    {ocr_json_str}

                    ### Instrucciones:

                    1. **Fechas (dd-mm-aaaa)**:
                    - Corrige cualquier formato inválido o caracteres extraños (p. ej. "7-P-24" → "7-9-24").
                    - Si una fecha no puede interpretarse, cámbiala a null.
                    - Las fechas deben ser coherentes y lineales (sin retroceder o cambiar a un año previo).  
                        Si la fecha previa es "7-9-24", no puede venir después "4-5-24" en la misma secuencia. Corrige o pon null si no hay forma de deducirla.
                    - El año que mas encuentres es el predominante. Todos los registros deberian ajustarse a este año predominante.

                    2. **Horas (hora_entrada, hora_salida)**:
                    - Elimina “hs”, “horas”, “h”, “hr” y ajusta al formato 24 horas (hh:mm).
                    - Si solo hay dos dígitos (“22”), agrégales “:00” → “22:00”.
                    - Si hay caracteres ambiguos (“0B:00”), reemplázalos por la cifra más parecida (“08:00”).
                    - Si no se puede determinar la hora, cámbiala a null.
                    - Si no hay horario de salida pon NULL

                    3. **Coherencia de turnos**:
                    - En toda la planilla suelen usarse **los mismos dos horarios** de entrada y salida (p. ej. 22:00 a 10:00, 20:00 a 08:00, etc.).  
                    - Si ves algo incompatible como “22:00 a 07:00” pero la planilla establece que se sale a “10:00”, corrígelo a “22:00 a 10:00”.  
                    - Mantén esta lógica flexible; si en otra planilla los horarios fueran 20:00 y 08:00, aplica el mismo criterio (cualquier combinación que no encaje con los dos horarios reales, corrígela al más probable).

                    4. **Nombres, domicilios y localidades**:
                    - Respeta el texto salvo por errores evidentes (p. ej. “Aerot Robert” → “Araoz Roberto”).
                    - Si “domicilio” o “localidad” lucen imposibles, haz ajustes mínimos para mantener coherencia con ubicaciones argentinas o déjalo en null si es irreparable.

                    5. **Valores null**:
                    - No inventes nada en campos ya marcados como null; mantén null sin alterarlo.
                    - Si un campo no se puede interpretar conforme a su categoría (fecha/hora/nombre/etc.), ponlo en null.

                    **No incluyas** texto adicional, explicaciones o backticks. Devuelve **exclusivamente** el JSON corregido.


                    """
                }
            ],
            temperature=0,
            max_tokens=2048,
            top_p=1,
            stream=False,
            stop=None,
        )
        response_text = completion.choices[0].message.content
        print("Respuesta del modelo:")
        print(response_text)

        # Limpiamos la respuesta para asegurarnos de que sea un JSON válido
        response_text_clean = response_text.strip().strip('`')
        response_text_clean = response_text_clean.replace('“', '"').replace('”', '"')

        # Si la cadena comienza con "json", lo removemos
        if response_text_clean.startswith("json"):
            response_text_clean = response_text_clean[4:].strip()

        corrected_json = None
        try:
            corrected_json = json.loads(response_text_clean)
        except json.JSONDecodeError as e:
            print(f"Error al parsear el JSON: {e}")
            print("JSON que causó el error:")
            print(response_text_clean)

        # Terminamos el contador (NO MODIFICAR)
        end_time = time.perf_counter()
        print(f"Tiempo transcurrido en correctJson: {end_time - start_time:.4f} segundos")

        return corrected_json

