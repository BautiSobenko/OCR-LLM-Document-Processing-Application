from aws_facade import AWSFacade

class Command:
    def ejecutar(self):
        pass

class SubirArchivoCommand(Command):
    def __init__(self, aws_facade: AWSFacade, filepath, filename):
        self.aws_facade = aws_facade
        self.filepath = filepath
        self.filename = filename

    def ejecutar(self):
        self.aws_facade.upload_document(self.filepath, self.filename)

class AnalizarDocumentoCommand:
    def __init__(self, aws_facade, filename):
        self.aws_facade = aws_facade
        self.filename = filename
        

    def ejecutar(self):
        resultado = self.aws_facade.analyze_document(self.filename)
        self.aws_facade.eliminar_archivo_s3(self.filename)
        return resultado

