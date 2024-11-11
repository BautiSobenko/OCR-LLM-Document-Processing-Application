import os

def analyzeDocument(textract_client, file_path):
    return textract_client.analyze_document(
        Document={
            'S3Object': {
                'Bucket': os.getenv('BUCKET_NAME'),
                'Name': file_path
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )