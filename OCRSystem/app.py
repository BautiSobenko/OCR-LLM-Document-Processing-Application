# app.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from aws_facade import AWSFacade
from commands import SubirArchivoCommand, AnalizarDocumentoCommand

app = Flask(__name__)
UPLOAD_FOLDER = '/content/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return '''
    <!doctype html>
    <title>Upload Document</title>
    <h1>Upload a Document</h1>
    <form method=post enctype=multipart/form-data action="/upload">
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Usar AWSFacade y Command
    aws_facade = AWSFacade()
    subir_command = SubirArchivoCommand(aws_facade, filepath, filename)
    subir_command.ejecutar()

    analizar_command = AnalizarDocumentoCommand(aws_facade, filename)
    parsed_response = analizar_command.ejecutar()

    # Devolver la respuesta procesada
    return jsonify(parsed_response)

if __name__ == "__main__":
    app.run(port=5000)
