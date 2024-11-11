from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from aws_facade import AWSFacade
from commands import SubirArchivoCommand, AnalizarDocumentoCommand
from LLM import LLM
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

UPLOAD_FOLDER = 'uploads'  
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la solicitud."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        aws_facade = AWSFacade()
        subir_command = SubirArchivoCommand(aws_facade, filepath, filename)
        subir_command.ejecutar()

        analizar_command = AnalizarDocumentoCommand(aws_facade, filename)
        parsed_response = analizar_command.ejecutar()

        with open('OCRSystem/ocr_result.txt', 'w') as ocr_result_file:
            parsed_response_str = json.dumps(parsed_response, indent=4)
            ocr_result_file.write(parsed_response_str)

        language_model = LLM()
        json_fixed = language_model.correctJson()

        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error al eliminar el archivo '{filepath}': {e}")

        return jsonify(json_fixed), 200
    else:
        return jsonify({"error": "Tipo de archivo no permitido."}), 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)