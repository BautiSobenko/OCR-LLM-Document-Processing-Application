from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from aws_facade import AWSFacade
from commands import SubirArchivoCommand, AnalizarDocumentoCommand
from LLM import LLM
import json
from flask_cors import CORS
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'tiff'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Verifica si la extensión del archivo está entre las permitidas.
    (Esto no garantiza que el PDF no esté cifrado o sea válido; 
    solo es una primera comprobación.)
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    start_time = time.perf_counter()

    # Función local que encapsula la lógica de "procesar 1 archivo"
    def handle_single_file(file_obj):
        """
        - Verifica si es un archivo permitido.
        - Guarda el archivo localmente.
        - Sube a S3 y analiza con Textract.
        - Procesa el resultado con LLM.
        - Elimina el archivo local.
        - Retorna un dict con 'filename' y 'result' o 'error'.
        """

        if file_obj.filename == '':
            return {
                "filename": None,
                "error": "No se seleccionó ningún archivo."
            }

        if allowed_file(file_obj.filename):
            filename = secure_filename(file_obj.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_obj.save(filepath)

            # Subir al bucket
            subir_command = SubirArchivoCommand(aws_facade, filepath, filename)
            subir_command.ejecutar()

            # Analizar con Textract
            try:
                analizar_command = AnalizarDocumentoCommand(aws_facade, filename)
                parsed_response = analizar_command.ejecutar()
            except aws_facade.textract_client.exceptions.UnsupportedDocumentException:
                # Captura específica para formatos no soportados
                try:
                    os.remove(filepath)  # limpiamos archivo local
                except:
                    pass
                return {
                    "filename": filename,
                    "error": (
                        "Documento no soportado por Textract. "
                        "Asegúrate de subir un PDF, JPG, PNG o TIFF válido."
                    )
                }
            except Exception as exc:
                # Cualquier otro error de Textract
                try:
                    os.remove(filepath)
                except:
                    pass
                return {
                    "filename": filename,
                    "error": f"Error durante el análisis con Textract: {str(exc)}"
                }

            # Procesar resultado con LLM (opcional)
            if parsed_response is not None:
                parsed_response_str = json.dumps(parsed_response, indent=4)
                language_model = LLM()
                json_fixed = language_model.correctJson(parsed_response_str)
            else:
                json_fixed = {"error": f"Procesamiento fallido en Textract: {filename}"}

            # Eliminar archivo local
            try:
                os.remove(filepath)
                print(f"Archivo '{filepath}' eliminado exitosamente.")
            except Exception as e:
                print(f"Error al eliminar el archivo '{filepath}': {e}")

            return {
                "filename": filename,
                "result": json_fixed
            }
        else:
            # Tipo de archivo no permitido (según extensión)
            return {
                "filename": file_obj.filename,
                "error": "Tipo de archivo no permitido."
            }

    try:
        # Obtenemos 1..N archivos de la key "file"
        files = request.files.getlist('file')
        if not files or len(files) == 0:
            return jsonify({"error": "No se encontró el archivo en la solicitud."}), 400

        # Instanciamos AWSFacade
        global aws_facade
        aws_facade = AWSFacade()

        # Ejecutamos el proceso de cada archivo en un hilo distinto
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {}
            for f in files:
                # Asignamos una tarea (un hilo) para cada archivo
                future = executor.submit(handle_single_file, f)
                future_to_file[future] = f.filename

            # A medida que las tareas finalicen, recogemos resultados
            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Si algo explotó fuera del try/except de handle_single_file
                    results.append({
                        "filename": file_name,
                        "error": f"Excepción no controlada: {str(e)}"
                    })

        end_time = time.perf_counter()
        print(f"Tiempo transcurrido en /upload: {end_time - start_time:.4f} segundos")

        # Devolvemos un array con la información de cada archivo
        return jsonify(results), 200

    except Exception as e:
        print(f"Error en el endpoint /upload: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor."}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
