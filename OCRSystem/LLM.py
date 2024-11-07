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
                "content": """Corrige el siguiente JSON: """ + ocr_json + """ en función de los valores y nombres de los atributos de cada campo. Ten en cuenta las siguientes reglas y el contexto de cada campo:
                
                        1. **Ajuste de valores por tipo de dato**: Los valores deben respetar el sentido y el tipo de dato de acuerdo con el nombre del atributo:
                            - Para cualquier atributo con `null`, no agregues ni inventes datos; mantén el valor `null` sin cambios.
                            - Si algun valor en hora_entrada o hora_salida termina en hs, horas, h, hr, o algun otro valor que indique horas, elimina ese valor y deja solo la hora, por ejemplo: 22hs -> 22:00
                            - Si el atributo es `hora_entrada` o `hora_salida`, asegúrate de que los valores sigan un formato de 24 horas (`hh:mm`) y que no incluyan caracteres o valores fuera de lo común, como letras o símbolos. Estos valores deben ser coherentes como horas.
                            - Si el atributo es `fecha`, utiliza el formato `dd-mm-aaaa` para todas las fechas.
                            - Si el atributo es `hora_entrada` o `hora_salida', y en caso de encontrar un valor con un caracter, cambialo por el numero de mayor similitud, aquel que tenga la forma mas parecida y cercana al caracter. por ejemplo: 0B:00 -> 08:00, BHS -> 08:00, BHP -> 08:00, 0S:00 -> 05:00
                            - Si el atributo es `domicilio` o `localidad`, asegúrate de que los valores sean coherentes con direcciones o nombres de lugares pertenecientes a una localidad o domicilio real de la Argentina.

                                
                        2. **Mantener contexto y sentido de los campos**: Corrige valores incorrectos solo en función de su campo y asegúrate de que el JSON refleje el contexto de una planilla de asistencia y registro de horarios de entrada y salida. Los valores deben tener sentido en este contexto. No alteres el contenido de atributos como nombres o direcciones, pero corrige los errores en los valores relacionados con horas o fechas, si existen.

                        Proporciona el JSON corregido siguiendo los requerimientos mencionados anteriormente.
                        """
            }
            ],
            temperature=0,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )

        corrected_json = json.loads(completion.choices[0].message.content)
        return corrected_json








