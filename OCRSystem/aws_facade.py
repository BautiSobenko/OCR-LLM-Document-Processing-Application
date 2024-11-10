# aws_facade.py
import boto3
import trp
from utils import analyzeDocument
from parsers import TextractParser
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME    = os.getenv("BUCKET_NAME")
REGION         = os.getenv("REGION")
   
class AWSFacade:
    def __init__(self):
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=AWS_ACCESS_KEY,
                                      aws_secret_access_key=AWS_SECRET_KEY,
                                      region_name=REGION)
        self.textract_client = boto3.client('textract',
                                            aws_access_key_id=AWS_ACCESS_KEY,
                                            aws_secret_access_key=AWS_SECRET_KEY,
                                            region_name=REGION)
        self.parser = TextractParser()

    def upload_document(self, filepath, filename):
        self.s3_client.upload_file(filepath, BUCKET_NAME, filename)
    
    def analyze_document(self, filename):
            response = analyzeDocument(self.textract_client, filename)
            parsed_result = self.parser.parse(response)
            return parsed_result

    def eliminar_archivo_s3(self, object_name):
        try:
            response = self.s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_name)
            print(f"Archivo '{object_name}' eliminado del bucket '{BUCKET_NAME}'.")
            return True
        except Exception as e:
            print(f"Error al eliminar el archivo '{object_name}': {e}")
            return False