# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from aws_facade import AWSFacade
from commands import SubirArchivoCommand, AnalizarDocumentoCommand
from LLM import LLM
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'  # Cambia el directorio si es necesario
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return render_template('upload_form.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        error_message = "No se encontró el archivo en la solicitud."
        return render_template('upload_form.html', error=error_message)
    file = request.files['file']
    if file.filename == '':
        error_message = "No se seleccionó ningún archivo."
        return render_template('upload_form.html', error=error_message)

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Usar AWSFacade y Command
    aws_facade = AWSFacade()
    subir_command = SubirArchivoCommand(aws_facade, filepath, filename)
    subir_command.ejecutar()

    analizar_command = AnalizarDocumentoCommand(aws_facade, filename)
    parsed_response = analizar_command.ejecutar()

    with open('OCRSystem/ocr_result.txt', 'w', encoding="utf-8") as ocr_result_file:
        parsed_response_str = json.dumps(parsed_response, indent=4)
        ocr_result_file.write(parsed_response_str)

    language_model = LLM()
    json_fixed = language_model.correctJson()

    # Renderizar el resultado en una página HTML
    return render_template('result.html', result=json_fixed)

if __name__ == "__main__":
    app.run(port=3636, debug=True)
