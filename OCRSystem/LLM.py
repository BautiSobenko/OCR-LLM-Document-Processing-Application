from groq import Groq
import os
import json

class LLM:
    
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def correctJson(self):
        with open('OCRSystem\ocr_result.txt', 'r') as ocr_result_file:
            ocr_json = ocr_result_file.read()
            
        completion = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages = [
                {
                    "role": "user",
                    "content": f"""Corrige el siguiente JSON y devuelve únicamente el JSON corregido sin explicaciones ni texto adicional: {ocr_json}

                    Formato y Precisión de Datos:

                    - Si el valor en hora_entrada o hora_salida contiene elementos como "hs", "horas", "h", "hr", u otros indicadores de tiempo, elimina estos caracteres y deja solo la hora en formato hh:mm.
                    - Si el valor de hora_entrada o hora_salida contiene algún carácter incorrecto o de difícil interpretación (por ejemplo, 0B:00), reemplázalo por el número de mayor similitud (08:00 en el caso de 0B:00).
                    - Si hora_entrada o hora_salida tiene solo dos dígitos (ej., 22), agrégale :00 para que tenga el formato hh:mm (por ejemplo, 22 -> 22:00).
                    - Si el valor de fecha no está en formato dd-mm-aaaa, corrígelo. Si incluye caracteres incorrectos, reemplázalos por el número de mayor similitud (ejemplo: 7-P-24 -> 7-9-24).
                    - Si el valor en fecha, hora_entrada, o hora_salida contiene texto sin relación con una fecha u hora, cambia el valor a null.

                    Mantener Contexto:

                    - Respeta los nombres, direcciones y localidades sin alterarlos, pero asegúrate de que las horas y fechas sean consistentes con el contexto de una planilla de asistencia.
                    - Si el atributo es domicilio o localidad, asegúrate de que los valores sean coherentes con direcciones o nombres de lugares pertenecientes a una localidad o domicilio real de la Argentina.
                    - Si el atributo es nombre en caso de encontrar nombres ilogicos o que no correspondan a nombres coherentes de personas, adaptarlo al de mayor similitud. Ejemplo "Aerot Robert" -> Araoz Roberto
                    - No agregues valores inventados en campos con null. Mantén el valor null sin cambios.

                    Proporciona **únicamente** el JSON corregido siguiendo los requerimientos mencionados anteriormente, sin añadir texto adicional. No incluyas backticks, etiquetas de código, ni comentarios.
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

        response_text_clean = response_text.strip().strip('`')
        response_text_clean = response_text_clean.replace('“', '"').replace('”', '"')

        try:
            corrected_json = json.loads(response_text_clean)
            return corrected_json
        except json.JSONDecodeError as e:
            print(f"Error al parsear el JSON: {e}")
            print("JSON que causó el error:")
            print(response_text_clean)
            return None
