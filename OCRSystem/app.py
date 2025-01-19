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

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
# Agregamos 'tiff' para que coincida con los formatos soportados por Textract
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'tiff'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Verifica si la extensión del archivo está entre las permitidas.
    OJO: Esto NO garantiza que el contenido sea válido ni que el PDF esté libre de contraseña.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    start_time = time.perf_counter()
    try:
        # 1) OBTENER ARCHIVOS
        # -------------------------------------------------------------------
        files = request.files.getlist('file')  # Puede ser 1 archivo o varios

        if not files or len(files) == 0:
            return jsonify({"error": "No se encontró el archivo en la solicitud."}), 400

        aws_facade = AWSFacade()

        results = []
        for file in files:
            if file.filename == '':
                results.append({
                    "filename": None,
                    "error": "No se seleccionó ningún archivo."
                })
                continue

            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Subir al bucket
                subir_command = SubirArchivoCommand(aws_facade, filepath, filename)
                subir_command.ejecutar()

                # Analizar con Textract
                try:
                    analizar_command = AnalizarDocumentoCommand(aws_facade, filename)
                    parsed_response = analizar_command.ejecutar()
                except aws_facade.textract_client.exceptions.UnsupportedDocumentException:
                    # Captura específica para formatos no soportados
                    results.append({
                        "filename": filename,
                        "error": (
                            "Documento no soportado por Textract. "
                            "Asegúrate de subir un PDF, JPG, PNG o TIFF válido."
                        )
                    })
                    # Eliminamos el archivo local y continuamos
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    continue
                except Exception as exc:
                    # Si ocurre cualquier otro error con Textract
                    results.append({
                        "filename": filename,
                        "error": f"Error durante el análisis con Textract: {str(exc)}"
                    })
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    continue

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

                # Guardar resultado en la lista final
                results.append({
                    "filename": filename,
                    "result": json_fixed
                })
            else:
                # Tipo de archivo no permitido (según extensión)
                results.append({
                    "filename": file.filename,
                    "error": "Tipo de archivo no permitido."
                })

        end_time = time.perf_counter()
        print(f"Tiempo transcurrido en upload_file: {end_time - start_time:.4f} segundos")

        # Devolvemos un array con la información de cada archivo
        return jsonify(results), 200

    except Exception as e:
        print(f"Error en el endpoint /upload: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor."}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
